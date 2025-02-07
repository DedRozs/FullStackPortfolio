from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.CharField(max_length=255)
    github_link = models.URLField(blank=True, null=True)

class Skill(models.Model):
    name = models.CharField(max_length=100)
    proficiency_level = models.IntegerField()

class Experience(models.Model):
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    duration = models.CharField(max_length=100)
    description = models.TextField()
