from django.urls import path
from . import views

urlpatterns = [
    path('<int:rfq_id>/status/', views.AuctionStatusView.as_view(), name='auction-status'),
    path('<int:rfq_id>/ranking/', views.AuctionRankingView.as_view(), name='auction-ranking'),
]
