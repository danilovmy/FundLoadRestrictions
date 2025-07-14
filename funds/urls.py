from django.urls import path
from .views import FundLoadView

urlpatterns = [
    path('load/', FundLoadView.as_view(), name='fund-load'),
]