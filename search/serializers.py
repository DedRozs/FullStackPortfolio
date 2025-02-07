from rest_framework import serializers
from search.models import SearchIndex


class SearchIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchIndex
        fields = ["id", "text"]
