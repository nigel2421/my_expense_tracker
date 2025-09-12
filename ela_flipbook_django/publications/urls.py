# publications/urls.py

from django.urls import path
from . import views

app_name = 'publications' # This is for namespacing

urlpatterns = [
    path('', views.home_view, name='home'),
    path('publication/<int:pk>/', views.publication_detail_view, name='detail'),
]