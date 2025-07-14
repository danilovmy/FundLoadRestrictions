from django.test import TestCase
from django.urls import reverse
import json
from datetime import datetime, timedelta
import sympy  # For prime number checking in the extra credit tests


class FundLoadRestrictionsTestCase(TestCase):
    """
    Test cases for the Fund Load Restrictions API.
    Each test covers a specific requirement from the assessment.
    """

    def setUp(self):
        """Set up common test data and configurations."""
        self.url = reverse('fund-load')  # Assuming you'll define this URL name
        self.customer_id = "528"
        self.base_time = datetime(2000, 1, 1, 10, 0, 0).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Helper function to create a valid load request
        self.create_load_request = lambda id, amount, time=None, customer=None: {
            "id": id,
            "customer_id": customer or self.customer_id,
            "load_amount": f"${amount}",
            "time": time or self.base_time
        }

    def test_valid_load_under_limits(self):
        """Test that a valid load under all limits is accepted."""
        payload = self.create_load_request("12345", "1000.00")

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["id"], "12345")
        self.assertEqual(data["customer_id"], self.customer_id)
        self.assertTrue(data["accepted"])

    def test_daily_limit_exceeded(self):
        """Test that a load exceeding the daily limit of $5,000 is rejected."""
        # First, make a load that's under the limit
        payload1 = self.create_load_request("12345", "3000.00")
        response1 = self.client.post(
            self.url,
            data=json.dumps(payload1),
            content_type='application/json'
        )

        # Then, try to make another load that would exceed the daily limit
        payload2 = self.create_load_request("12346", "2500.00")
        response2 = self.client.post(
            self.url,
            data=json.dumps(payload2),
            content_type='application/json'
        )

        # The first load should be accepted
        data1 = json.loads(response1.content)
        self.assertTrue(data1["accepted"])

        # The second load should be rejected as it would exceed the $5,000 daily limit
        data2 = json.loads(response2.content)
        self.assertFalse(data2["accepted"])

    def test_weekly_limit_exceeded(self):
        """Test that a load exceeding the weekly limit of $20,000 is rejected."""
        # Create loads on different days of the same week
        base_date = datetime(2000, 1, 3, 10, 0, 0)  # Monday

        # Day 1: $5,000
        payload1 = self.create_load_request(
            "12345", "5000.00",
            base_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Day 2: $5,000
        payload2 = self.create_load_request(
            "12346", "5000.00",
            (base_date + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Day 3: $5,000
        payload3 = self.create_load_request(
            "12347", "5000.00",
            (base_date + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Day 4: $5,000 (this should push it to the weekly limit)
        payload4 = self.create_load_request(
            "12348", "5000.00",
            (base_date + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Day 5: Try to add $1 more (should be rejected)
        payload5 = self.create_load_request(
            "12349", "1.00",
            (base_date + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Send all requests
        response1 = self.client.post(self.url, data=json.dumps(payload1), content_type='application/json')
        response2 = self.client.post(self.url, data=json.dumps(payload2), content_type='application/json')
        response3 = self.client.post(self.url, data=json.dumps(payload3), content_type='application/json')
        response4 = self.client.post(self.url, data=json.dumps(payload4), content_type='application/json')
        response5 = self.client.post(self.url, data=json.dumps(payload5), content_type='application/json')

        # First four loads should be accepted
        self.assertTrue(json.loads(response1.content)["accepted"])
        self.assertTrue(json.loads(response2.content)["accepted"])
        self.assertTrue(json.loads(response3.content)["accepted"])
        self.assertTrue(json.loads(response4.content)["accepted"])

        # Fifth load should be rejected as it exceeds the weekly limit
        self.assertFalse(json.loads(response5.content)["accepted"])

    def test_daily_load_count_exceeded(self):
        """Test that exceeding 3 load attempts per day is rejected."""
        # Create 4 small loads on the same day
        payload1 = self.create_load_request("12345", "100.00")
        payload2 = self.create_load_request("12346", "100.00")
        payload3 = self.create_load_request("12347", "100.00")
        payload4 = self.create_load_request("12348", "100.00")

        # Send all requests
        response1 = self.client.post(self.url, data=json.dumps(payload1), content_type='application/json')
        response2 = self.client.post(self.url, data=json.dumps(payload2), content_type='application/json')
        response3 = self.client.post(self.url, data=json.dumps(payload3), content_type='application/json')
        response4 = self.client.post(self.url, data=json.dumps(payload4), content_type='application/json')

        # First three loads should be accepted
        self.assertTrue(json.loads(response1.content)["accepted"])
        self.assertTrue(json.loads(response2.content)["accepted"])
        self.assertTrue(json.loads(response3.content)["accepted"])

        # Fourth load should be rejected as it exceeds the daily load count limit
        self.assertFalse(json.loads(response4.content)["accepted"])

    def test_different_customers_separate_limits(self):
        """Test that different customers have separate limits."""
        # Create loads for two different customers on the same day
        customer1 = "528"
        customer2 = "529"

        # Customer 1: $5,000 (max daily limit)
        payload1 = self.create_load_request("12345", "5000.00", customer=customer1)

        # Customer 2: $5,000 (should be accepted as it's a different customer)
        payload2 = self.create_load_request("12346", "5000.00", customer=customer2)

        # Send requests
        response1 = self.client.post(self.url, data=json.dumps(payload1), content_type='application/json')
        response2 = self.client.post(self.url, data=json.dumps(payload2), content_type='application/json')

        # Both loads should be accepted as they're for different customers
        self.assertTrue(json.loads(response1.content)["accepted"])
        self.assertTrue(json.loads(response2.content)["accepted"])

    def test_loads_on_different_days(self):
        """Test that daily limits reset on different days."""
        # Day 1: Max out the daily limit
        day1 = datetime(2000, 1, 1, 10, 0, 0).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload1 = self.create_load_request("12345", "5000.00", time=day1)

        # Day 2: Should be able to load again
        day2 = datetime(2000, 1, 2, 10, 0, 0).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload2 = self.create_load_request("12346", "5000.00", time=day2)

        # Send requests
        response1 = self.client.post(self.url, data=json.dumps(payload1), content_type='application/json')
        response2 = self.client.post(self.url, data=json.dumps(payload2), content_type='application/json')

        # Both loads should be accepted as they're on different days
        self.assertTrue(json.loads(response1.content)["accepted"])
        self.assertTrue(json.loads(response2.content)["accepted"])

    def test_loads_on_different_weeks(self):
        """Test that weekly limits reset on different weeks."""
        # Week 1: Max out the weekly limit
        week1_day1 = datetime(2000, 1, 3, 10, 0, 0)  # Monday

        # Create 4 loads of $5,000 each to reach the $20,000 weekly limit
        for i in range(4):
            payload = self.create_load_request(
                f"1234{i}", "5000.00",
                (week1_day1 + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
            response = self.client.post(self.url, data=json.dumps(payload), content_type='application/json')
            self.assertTrue(json.loads(response.content)["accepted"])

        # Week 2: Should be able to load again
        week2_day1 = datetime(2000, 1, 10, 10, 0, 0)  # Next Monday
        payload_week2 = self.create_load_request(
            "12350", "5000.00",
            week2_day1.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        response_week2 = self.client.post(self.url, data=json.dumps(payload_week2), content_type='application/json')

        # Load in week 2 should be accepted as weekly limits reset
        self.assertTrue(json.loads(response_week2.content)["accepted"])

    # Extra Credit Tests

    def test_prime_id_restriction(self):
        """Test that only one load with a prime number ID is allowed per day."""
        # Check if an ID is prime
        prime_id1 = "13"  # 13 is prime
        prime_id2 = "17"  # 17 is prime

        # Create two loads with prime IDs on the same day
        payload1 = self.create_load_request(prime_id1, "1000.00")
        payload2 = self.create_load_request(prime_id2, "1000.00")

        # Send requests
        response1 = self.client.post(self.url, data=json.dumps(payload1), content_type='application/json')
        response2 = self.client.post(self.url, data=json.dumps(payload2), content_type='application/json')

        # First prime ID load should be accepted
        self.assertTrue(json.loads(response1.content)["accepted"])

        # Second prime ID load should be rejected
        self.assertFalse(json.loads(response2.content)["accepted"])

    def test_prime_id_amount_restriction(self):
        """Test that a load with a prime ID cannot exceed $9,999."""
        # Create a load with a prime ID and amount > $9,999
        prime_id = "13"  # 13 is prime
        payload = self.create_load_request(prime_id, "10000.00")

        # Send request
        response = self.client.post(self.url, data=json.dumps(payload), content_type='application/json')

        # Load should be rejected as it exceeds the $9,999 limit for prime IDs
        self.assertFalse(json.loads(response.content)["accepted"])

    def test_monday_double_value_rule(self):
        """Test that loads on Monday are counted as double their value."""
        # Create a load on Monday with an amount that would exceed the daily limit if doubled
        monday = datetime(2000, 1, 3, 10, 0, 0)  # January 3, 2000 was a Monday

        # $3,000 normally would be under the $5,000 limit, but doubled to $6,000 would exceed it
        payload = self.create_load_request(
            "12345", "3000.00",
            monday.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Send request
        response = self.client.post(self.url, data=json.dumps(payload), content_type='application/json')

        # Load should be rejected as the doubled value exceeds the daily limit
        self.assertFalse(json.loads(response.content)["accepted"])

    def test_monday_double_value_weekly_limit(self):
        """Test that Monday's double value affects the weekly limit too."""
        # Monday: $3,000 (counted as $6,000)
        monday = datetime(2000, 1, 3, 10, 0, 0)
        payload1 = self.create_load_request(
            "12345", "3000.00",
            monday.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Tuesday: $5,000
        tuesday = monday + timedelta(days=1)
        payload2 = self.create_load_request(
            "12346", "5000.00",
            tuesday.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Wednesday: $5,000
        wednesday = monday + timedelta(days=2)
        payload3 = self.create_load_request(
            "12347", "5000.00",
            wednesday.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Thursday: $4,000 (this should push the total to $20,000 with Monday's double counting)
        thursday = monday + timedelta(days=3)
        payload4 = self.create_load_request(
            "12348", "4000.00",
            thursday.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Friday: Try to add $1 more (should be rejected)
        friday = monday + timedelta(days=4)
        payload5 = self.create_load_request(
            "12349", "1.00",
            friday.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Send all requests
        response1 = self.client.post(self.url, data=json.dumps(payload1), content_type='application/json')
        response2 = self.client.post(self.url, data=json.dumps(payload2), content_type='application/json')
        response3 = self.client.post(self.url, data=json.dumps(payload3), content_type='application/json')
        response4 = self.client.post(self.url, data=json.dumps(payload4), content_type='application/json')
        response5 = self.client.post(self.url, data=json.dumps(payload5), content_type='application/json')

        # First four loads should be accepted
        self.assertTrue(json.loads(response1.content)["accepted"])
        self.assertTrue(json.loads(response2.content)["accepted"])
        self.assertTrue(json.loads(response3.content)["accepted"])
        self.assertTrue(json.loads(response4.content)["accepted"])

        # Fifth load should be rejected as it exceeds the weekly limit
        self.assertFalse(json.loads(response5.content)["accepted"])