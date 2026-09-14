from django.urls import path
from . import views

urlpatterns = [
    path('', views.panorama_view, name='panorama'),
]