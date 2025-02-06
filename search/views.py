from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from search.models import SearchIndex
from search.serializers import SearchIndexSerializer
from search.utils import generate_embedding, save_faiss_index, search_similar
import numpy as np

class AddTextToIndexView(APIView):
    """Adds new text data to FAISS search index."""
    
    def post(self, request):
        serializer = SearchIndexSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data["text"]
            embedding = generate_embedding(text).astype(np.float32).tobytes()

            # Save to DB
            SearchIndex.objects.create(text=text, embedding=embedding)
            save_faiss_index()  # Update FAISS index
            
            return Response({"message": "Text added to index."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SearchView(APIView):
    """Handles search queries and returns relevant results."""

    def get(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({"error": "Query parameter required"}, status=status.HTTP_400_BAD_REQUEST)
        
        results = search_similar(query)
        return Response({"results": results}, status=status.HTTP_200_OK)
