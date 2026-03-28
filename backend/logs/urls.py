from django.urls import path
from . import views

urlpatterns = [
    path('<int:rfq_id>/', views.ActivityLogListView.as_view(), name='activity-log-list'),
]
