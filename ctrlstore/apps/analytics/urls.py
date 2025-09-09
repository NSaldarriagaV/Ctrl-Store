from django.urls import path
from .views import TopSellersView

app_name = "analytics"

urlpatterns = [
    path("top-sellers/", TopSellersView.as_view(), name="top_sellers"),
]
