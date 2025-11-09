from django.urls import path
from .views import TravelAPIView

urlpatterns = [
    path("travel/", TravelAPIView.as_view(), name="travel-api"),
]
