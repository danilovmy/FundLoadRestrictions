from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from sympy import is_prime
from  django.utils.timezone import now
from django.utils.functional import cached_property


class FundLoadQuerySet(models.QuerySet):

    def weekly_total(self, *args, **kwargs):
        return self.weekly(*args, **kwargs).total()

    def daily_total(self, *args, **kwargs):
        return self.daily(*args, **kwargs).total()

    def total(self, *args, **kwargs):
        return self.aggregate(models.Sum('load_amount')).get('sum') or 0

    def weekly(self, *args, time=None, **kwargs):
        week = time and time.date or now().date
        week = time and time.date or now().date
        return self.weekly(week)

    def daily(self, *args, time=None, **kwargs):
        day = time and time.date or now().date
        return self.filter(time__date=day)

    def daily_count(self, *args, **kwargs):
        return self.daily(*args, **kwargs).count()

    def daily_primes_count(self, *args, **kwargs):
        return self.daily(*args, **kwargs).primes().count()

    def primes(self, *args, **kwargs):
        return self.filter(is_prime=True)

    def by_customer(self, customer=None):
        return self.filter(customer_id=getattr(customer, 'pk', None) or customer or 0)


class FundLoad(models.Model):
    LIMITS = {'MIN_AMOUNT': 0.01, 'DAILY': 5000, 'WEEKLY': 20000, 'PRIME': 9999, 'LOADS_PER_DAY': 3, 'PRIMES_PER_DAY': 1 }
    customer_id = models.ForeignKey('auth.User', on_delete=models.DO_NOTHING, index=True)
    load_amount = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(LIMITS['MIN_AMOUNT']), MaxValueValidator(LIMITS['DAILY'])], index=True)
    time = models.DateTimeField(index=True)
    is_prime = models.BooleanField(default=False, index=True, editable=False)

    objects = FundLoadQuerySet.as_manager()

    @cached_property
    def is_prime_id(self):
        return is_prime(self.id or 0)

    def get_day_of_week(self):
        return self.time.isoweekday()

    def get_week_of_year(self):
        return self.time.isocalendar()[1] # year, week, weekday


    def save(self):
        self.is_prime = self.is_prime_id
        super(self).save()
