from django import forms
from django.core.validators import MaxValueValidator
from .models import FundLoad

class LoadsPerDayValidator(MaxValueValidator):
    message = "Exceeded %(limit_value)s load attempts per day"

    def clean(self, obj):
        self.limit_value = obj.LIMITS[self.limit_value]
        return type(obj).objects.by_customer(obj).daily_count(obj) + 1


class WeeklyAmountValidator(MaxValueValidator):
    message = "Weekly limit of %(limit_value)s exceeded"

    def clean(self, obj):
        self.limit_value = obj.LIMITS[self.limit_value]
        return type(obj).objects.by_customer(obj).weekly_total(obj) + obj.load_amount


class DailyAmountValidator(MaxValueValidator):
    message = "Daily limit of %(limit_value)s exceeded"

    def clean(self, obj):
        self.limit_value = obj.LIMITS[self.limit_value]
        return type(obj).objects.by_customer(obj).daily_total(obj) + obj.load_amount


class PrimedAmountValidator(MaxValueValidator):
    message = "Load amount exceeds %(limit_value)s limit for prime IDs"

    def clean(self, obj):
        self.limit_value = obj.LIMITS[self.limit_value]
        return obj.load_amount if obj.is_prime else 0


class PrimesPerDayValidator(MaxValueValidator):
    message = "Exceeded %(limit_value)s prime IDs per day"

    def clean(self, obj):
        self.limit_value = obj.LIMITS[self.limit_value]
        return (type(obj).objects.daily_primes_count(obj) - 1) if obj.is_prime else 0


class FundLoadForm(forms.ModelForm):

    class Meta:
        model = FundLoad
        fields = 'id', 'load_amount', 'time', 'customer_id'

    def _post_clean(self):
        super()._post_clean()
        instance = self.instance

        LoadsPerDayValidator('LOADS_PER_DAY')(instance)
        DailyAmountValidator('DAILY')(instance)
        WeeklyAmountValidator('WEEKLY')(instance)
        PrimedAmountValidator('PRIME')(instance)
        PrimesPerDayValidator('PRIMES_PER_DAY')(instance)
