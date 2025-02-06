from django.db import models

class SearchIndex(models.Model):
    text = models.TextField()
    embedding = models.BinaryField()  # Store FAISS-compatible embeddings

    def __str__(self):
        return self.text[:50]  # Show first 50 characters
