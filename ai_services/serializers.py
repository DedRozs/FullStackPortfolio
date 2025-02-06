from rest_framework import serializers
from .models import AIService

class AIServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIService
        fields = '__all__'
