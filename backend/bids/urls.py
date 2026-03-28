from django.urls import path
from . import views

urlpatterns = [
    path('', views.BidSubmitView.as_view(), name='bid-submit'),
    path('<int:rfq_id>/', views.BidListView.as_view(), name='bid-list'),
]
