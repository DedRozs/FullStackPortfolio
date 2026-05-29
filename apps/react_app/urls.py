from django.urls import path

from . import views

app_name = 'react_app'

urlpatterns = [
    path('', views.index, name='index'),
]
