import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import tempfile
import json
import os

from plain import parse, main
from plain import (
    get_divider_by_day, daily, daily_amount, weekly_amount, by_customer,
    validate_min_amount, validate_max_amount, validate_prime_max_amount,
    validate_loads_per_day, validate_primes_per_day, validate_daily_amount,
    validate_weekly_amount, clean, store, is_valid, prepare_response
)

from pathlib import Path
from unittest.mock import patch


class TestStorageFunctions(unittest.TestCase):

    def setUp(self):
        self.customer_id = 1
        self.time = datetime(2025, 7, 10, tzinfo=timezone.utc)
        by_customer(customer_id=self.customer_id).clear()

    def test_get_divider_by_day(self):
        time = datetime(2023, 10, 9)  # Monday
        self.assertEqual(get_divider_by_day(time=time), 2)
        time = datetime(2023, 10, 10)  # Not Monday
        self.assertEqual(get_divider_by_day(time=time), 1)

    def test_daily(self):
        time = datetime(2023, 10, 9)
        self.assertEqual(daily(time=time, customer_id=1), [])

    def test_by_customer(self):
        self.assertEqual(by_customer(customer_id=1), {})

    def test_by_customer_default(self):
        storage = by_customer(customer_id=self.customer_id)
        self.assertIsInstance(storage, dict)

    def test_daily_storage_returns_list(self):
        result = daily(customer_id=self.customer_id, time=self.time)
        self.assertIsInstance(result, list)

    def test_daily_amount_calculation(self):
        data = {"customer_id": self.customer_id, "time": self.time, 'prime': False}
        store(data | {'load_amount': Decimal('10.00')})
        store(data | {'load_amount': Decimal('5.00')})
        self.assertEqual(daily_amount(**data), Decimal('15.00'))

    def test_weekly_amount_calculation(self):
        data = {"customer_id": self.customer_id, "time": self.time, 'load_amount': Decimal('10.00'), 'prime': False}
        for i in range(-6, 6):
            store(data | {'time': self.time + timedelta(days=i)})
        total = weekly_amount(**data)
        # we have 10.00 every day, but monday has a divider of 2
        self.assertEqual(total, Decimal('80.00'))


class TestBusinessLogicFunctions(unittest.TestCase):

    def setUp(self):
        self.time = datetime(2025, 7, 10)
        self.valid_load = {
            "id": 17,
            "customer_id": 123,
            "load_amount": Decimal('100.00'),
            "time": self.time,
            "prime": False
        }

    def test_validate_min_amount_ok(self):
        validate_min_amount(self.valid_load)

    def test_validate_min_amount_fail(self):
        load = self.valid_load.copy()
        load["load_amount"] = Decimal('0.001')
        with self.assertRaises(ValueError):
            validate_min_amount(load)

    def test_validate_max_amount_ok(self):
        validate_max_amount(self.valid_load)

    def test_validate_max_amount_fail(self):
        load = self.valid_load.copy()
        load["load_amount"] = Decimal('6000.00')
        with self.assertRaises(ValueError):
            validate_max_amount(load)

    def test_validate_prime_max_amount_fail(self):
        load = self.valid_load.copy()
        load["prime"] = True
        load["load_amount"] = Decimal('10000.00')
        with self.assertRaises(ValueError):
            validate_prime_max_amount(load)

    def test_validate_loads_per_day_fail(self):
        load = self.valid_load.copy()
        for _ in range(3):
            daily(**load).append(Decimal('10.00'))
        with self.assertRaises(ValueError):
            validate_loads_per_day(load)

    def test_validate_primes_per_day_fail(self):
        load = self.valid_load.copy()
        load["prime"] = True
        for _ in range(1):
            daily(customer_id="prime", time=load["time"]).append(Decimal('10.00'))
        with self.assertRaises(ValueError):
            validate_primes_per_day(load)

    def test_validate_daily_amount_fail(self):
        load = self.valid_load.copy()
        daily(**load).extend([Decimal('3000.00'), Decimal('2500.00')])
        with self.assertRaises(ValueError):
            validate_daily_amount(load)

    def test_validate_weekly_amount_fail(self):
        load = self.valid_load.copy()
        for i in range(7):
            day = load['time'] - timedelta(days=i)
            daily(customer_id=load["customer_id"], time=day).append(Decimal('3000.00'))
        with self.assertRaises(ValueError):
            validate_weekly_amount(load)

    def test_validate_min_amount(self):
        sentinel = ValueError("validate_max_amount raised ValueError unexpectedly!")
        with self.assertRaises(ValueError) as error:
            validate_min_amount({'load_amount': Decimal('0.01')})
            raise sentinel
        self.assertIs(error.exception, sentinel)


    def test_validate_max_amount(self):
        sentinel = ValueError("validate_max_amount raised ValueError unexpectedly!")
        with self.assertRaises(ValueError) as error:
            validate_max_amount({'load_amount': Decimal('5000')})
            raise sentinel
        self.assertIs(error.exception, sentinel)

    def test_is_valid(self):
        load = { 'id': 1, 'customer_id': 1, 'load_amount': Decimal('100'), 'time': datetime(2023, 10, 9, tzinfo=timezone.utc), 'prime': False }
        self.assertTrue(is_valid(load))


class TestGeneralFunctions(unittest.TestCase):
    def setUp(self):
        self.customer_id = 1
        self.time = datetime.now()
        by_customer(customer_id=self.customer_id).clear()
        by_customer(customer_id="prime").clear()

    def test_clean_valid_input(self):
        load = { "id": "7", "customer_id": "10", "load_amount": "$12.34", "time": "2025-07-10T10:00:00Z" }
        result = clean(**load)
        self.assertEqual(result["id"], 7)
        self.assertEqual(result["customer_id"], 10)
        self.assertEqual(result["load_amount"], Decimal('12.34'))
        self.assertTrue(isinstance(result["time"], datetime))

    def test_store_adds_to_storage(self):
        load = { "id": 2, "customer_id": 5, "load_amount": Decimal('50.00'), "time": datetime(2025, 7, 10), "prime": False }
        store(load)
        result = daily(**load)
        self.assertIn(Decimal('50.00'), result)

    def test_prime_value_is_stored(self):
        load = { "id": 7, "customer_id": 10, "load_amount": Decimal('12.34'), "time": datetime(2025, 7, 10), "prime": True }
        store(load)

        # check "prime" storage
        prime_bucket_loads = daily(customer_id="prime",time=load['time'])
        self.assertIn(load['load_amount'], prime_bucket_loads)

    def test_is_valid_true(self):
        load = { "id": 4, "customer_id": 9, "load_amount": Decimal('10.00'), "time": datetime(2025, 7, 10), "prime": False }
        self.assertTrue(is_valid(load))

    def test_prepare_response_false(self):
        # too high amount
        load = { "id": 1, "customer_id": 99, "load_amount": Decimal('1000000.00'), "time": datetime(2025, 7, 10), "prime": False }
        result = prepare_response(load)
        self.assertEqual(result["accepted"], False)

    def test_clean(self):
        load = clean(id='1', load_amount='$100.00', time='2023-10-09T00:00:00Z', customer_id='1')
        expected = { 'id': 1, 'customer_id': 1, 'load_amount': Decimal('100.00'), 'time': datetime(2023, 10, 9, 0, 0, tzinfo=timezone.utc), 'prime': False }
        self.assertEqual(load, expected)

    def test_prepare_response(self):
        load = { 'id': 1, 'customer_id': 1, 'load_amount': Decimal('100'), 'time': datetime(2023, 10, 9, tzinfo=timezone.utc), 'prime': False }
        response = prepare_response(load)
        expected = {"id": 1, "customer_id": 1, "accepted": True}
        self.assertEqual(response, expected)

class TestFileFunctions(unittest.TestCase):

    def setUp(self):
        self.temp_input = tempfile.NamedTemporaryFile(mode='w+', delete=False, delete_on_close=True)
        self.temp_output = Path(self.temp_input.name).parent / 'output.txt'
        self.sample_data = { "id": "2", "customer_id": "99", "load_amount": "$100.00", "time": "2025-07-10T12:00:00Z" }
        self.sample_load = clean(**self.sample_data)
        by_customer(customer_id=self.sample_load['customer_id']).clear()
        by_customer(customer_id="prime").clear()


    def tearDown(self):
        if os.path.exists(self.temp_input.name):
            self.temp_input.close()
        if os.path.exists(self.temp_output):
            os.remove(self.temp_output)

    def test_parse_yields_cleaned_entries(self):
        self.temp_input.write(json.dumps(self.sample_data) + '\n')
        self.temp_input.seek(0)

        with patch('plain.BASE_PATH', Path(self.temp_input.name).parent):
            result = list(parse(filename=Path(self.temp_input.name).name))
            self.assertEqual(len(result), 1)
            cleaned = result[0]
            self.assertEqual(cleaned['id'], 2)
            self.assertEqual(cleaned['customer_id'], 99)
            self.assertEqual(cleaned['load_amount'], Decimal('100.00'))
            self.assertIsInstance(cleaned['time'], datetime)

    def test_main_creates_output_file(self):
        self.temp_input.write(json.dumps(self.sample_data) + '\n')
        self.temp_input.seek(0)

        with patch('plain.BASE_PATH', Path(self.temp_input.name).parent):
            main(filename=Path(self.temp_input.name).name)

        self.assertTrue(self.temp_output.exists())

        with open(self.temp_output) as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            response = json.loads(lines[0])
            self.assertEqual(response['id'], 2)
            self.assertEqual(response['customer_id'], 99)
            self.assertIn('accepted', response)


if __name__ == "__main__":
    unittest.main()