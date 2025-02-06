from rest_framework import viewsets
from .models import BlogPost
from .serializers import BlogPostSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import generics, permissions

class BlogCreateView(generics.CreateAPIView):
    """
    API view to create a new blog post.
    Requires authentication.
    """
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class BlogListView(generics.ListAPIView):
    """
    API view to list all blog posts.
    """
    queryset = BlogPost.objects.all().order_by("-created_at")  # Ensure no filters are applied
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.AllowAny]  # Adjust permissions if necessary


class BlogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a blog post.
    - Read access: Any user.
    - Edit/Delete access: Only the author.
    """
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Limits the queryset so users can only update/delete their own blog posts.
        """
        if self.request.user.is_authenticated:
            return BlogPost.objects.filter(author=self.request.user)
        return BlogPost.objects.none()
