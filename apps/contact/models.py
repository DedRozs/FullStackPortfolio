from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=300, blank=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.name} ({self.email}) - {self.submitted_at:%Y-%m-%d}'
