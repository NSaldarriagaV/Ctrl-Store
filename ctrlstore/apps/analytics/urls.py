from django.urls import path
from .views import TopSellersView, TopViewedAPI

app_name = "analytics"

urlpatterns = [
    path("top-sellers/", TopSellersView.as_view(), name="top_sellers"),
    path("top-viewed/", TopViewedAPI.as_view(), name="top_viewed"),
]
