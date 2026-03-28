from django.urls import path
from . import views

urlpatterns = [
    path('', views.RFQListCreateView.as_view(), name='rfq-list-create'),
    path('<int:id>/', views.RFQDetailView.as_view(), name='rfq-detail'),
]
