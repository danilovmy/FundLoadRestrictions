import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from sympy.ntheory import isprime as is_prime

BASE_PATH = Path(__file__).parent.resolve()

LIMITS = {'MIN_AMOUNT': 0.01, 'MAX_AMOUNT': 5000, 'DAILY': 5000, 'WEEKLY': 20000, 'PRIME': 9999, 'LOADS_PER_DAY': 3, 'PRIMES_PER_DAY': 1 }
DIVIDER_PER_DAY = {'Monday':2, 'Tuesday':1, 'Wednesday':1, 'Thursday':1, 'Friday':1, 'Saturday':1, 'Sunday':1}

_STORAGE = {'prime':{}}

# work with storage:
def get_divider_by_day(time=None,**kwargs):
    """ Returns multiplier by day of week for given time.
        Multiplier is used to calculate daily load amount."""
    return DIVIDER_PER_DAY.setdefault(time.strftime('%A'), 1)

def daily(default=list, time=None, **kwargs):
    """Returns daily loads for a given customer and time or empty list"""
    return by_customer(**kwargs).setdefault(time.date(), default())

def daily_amount(**kwargs):
    """Returns daily load amount for a given customer and time
        For different days are used different multipliers"""
    return sum(amount * get_divider_by_day(**kwargs) for amount in daily(**kwargs))

def weekly_amount(*args, time=None, **kwargs):
    """Returns weekly load amount for a given customer and time"""
    weekday = time.weekday()
    week = [time + timedelta(days=i) for i in range(-weekday, 7 - weekday)]
    return sum(daily_amount(*args, time=day, **kwargs) for day in week)

def by_customer(*args, default=dict, customer_id=None, **kwargs):
    """Returns dict with daily loads for a given customer, keys are dates"""
    customer = customer_id
    return _STORAGE.setdefault(getattr(customer, 'pk', None) or customer or 0, default())

# validators:
def validate_min_amount(load):
    """Validate min value of load amount"""
    limit = LIMITS['MIN_AMOUNT']
    if load['load_amount'] < Decimal(limit).quantize(Decimal('0.01')):
        raise ValueError(f"Load amount cannot be less than {limit}")

def validate_max_amount(load):
    """Validate max value of load amount"""
    limit = LIMITS['MAX_AMOUNT']
    if load['load_amount'] > Decimal(limit).quantize(Decimal('0.01')):
        raise ValueError(f"Load amount cannot exceed {limit}")

def validate_prime_max_amount(load):
    """Validate max value of load amount for prime IDs"""
    limit = LIMITS['PRIME']
    if load['prime'] and load['load_amount'] > Decimal(limit).quantize(Decimal('0.01')):
            raise ValueError(f"Load amount exceeds {limit} limit for prime IDs")

def validate_loads_per_day(load):
    """Validate max number of loads per day per customer"""
    limit = LIMITS['LOADS_PER_DAY']
    if len(daily(**load)) >= limit:
        raise ValueError(f"Exceeded {limit} load attempts per day")

def validate_primes_per_day(load):
    """Validate max number of prime IDs per day for all customers"""
    limit = LIMITS['PRIMES_PER_DAY']
    if load['prime'] and len(daily(**(load | {'customer_id':'prime'}))) >= limit:
        raise ValueError(f"Exceeded {limit} prime IDs per day")

# calculated limits validators
def validate_daily_amount(load):
    """Validate maximum allowed daily load amount for customer"""
    limit = LIMITS['DAILY']
    if (daily_amount(**load) + load['load_amount']) > Decimal(limit).quantize(Decimal('0.01')):
        raise ValueError(f"Daily limit of {limit} exceeded")

def validate_weekly_amount(load):
    """Validate maximum allowed weekly load amount for customer"""
    limit = LIMITS['WEEKLY']
    if (weekly_amount(**load) + load['load_amount']) > Decimal(limit).quantize(Decimal('0.01')):
        raise ValueError(f"Weekly limit of {limit} exceeded")

# clean an store entity
def clean(id=None, load_amount=None, time=None, customer_id=None, **kwargs):
    """Clean input data and returns dictionary with validated fields"""
    return {"id": int(id),
            "customer_id": int(customer_id),
            "load_amount": Decimal(load_amount.rpartition('$')[-1]).quantize(Decimal('0.01')),
            "time": datetime.fromisoformat(f"{time.rstrip('Z')}+00:00"),
            "prime": is_prime(int(id))
            }

def store(load):
    """Store load entity in storage"""
    daily(**load).append(load.get('load_amount'))
    if load['prime']:
        daily(**(load | {'customer_id':'prime'})).append(load.get('load_amount'))

# Business logic implementation
def is_valid(load):
    """Validates load entity against business rules"""
    try:
        # mix/max validators
        validate_min_amount(load)
        validate_max_amount(load)
        validate_prime_max_amount(load)

        # counters validators
        validate_loads_per_day(load)
        validate_primes_per_day(load)

        # calculated limits validators
        validate_daily_amount(load)
        validate_weekly_amount(load)
        return True

    except Exception as error:  # noqa
        ...

def prepare_response(load):
    """Prepares response for output file"""
    return {"id": load['id'], "customer_id": load['customer_id'], "accepted": bool(is_valid(load))}

def parse(filename='input.txt'):
    """Parses input file iterative, line by line"""
    with (BASE_PATH / filename).open('r') as source:
        for line in source:
            yield clean(**json.loads(line))

def main(*args, **kwargs):
    """ Main entry point.
        Loads input file into memory
        validates each load-record and stores responses line by line"""
    with (BASE_PATH / 'output.txt').open('w') as result:
        for load in parse(*args, **kwargs):
            response = prepare_response(load)
            if response['accepted']:
                store(load)
            result.writelines(json.dumps(response) + '\n')
    print('Success')

if __name__ == '__main__':
    main()  # pragma: no cover