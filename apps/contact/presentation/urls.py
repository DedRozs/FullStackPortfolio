from django.urls import path

from apps.contact.presentation.views import ContactMessageListView

app_name = 'contact'

urlpatterns = [
    path('messages/', ContactMessageListView.as_view(), name='messages'),
]
