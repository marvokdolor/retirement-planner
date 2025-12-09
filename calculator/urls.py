from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.retirement_calculator, name='retirement_calculator'),
]
