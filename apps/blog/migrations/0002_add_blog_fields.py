"""
Migration: add Tag model and update Post model for full blog feature.

Adds:
- Tag model (name, slug, created_at)
- Post.excerpt field (replaces summary)
- Post.status field (replaces published BooleanField)
- Post.author FK (nullable; domain enforces non-null at create time)
- Post.featured_image ImageField
- Post.reading_time_minutes PositiveIntegerField
- Post.tags ManyToManyField to Tag

Removes:
- Post.summary (replaced by excerpt)
- Post.published (replaced by status)
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Create Tag model
        migrations.CreateModel(
            name='Tag',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        # 2. Add excerpt field
        migrations.AddField(
            model_name='post',
            name='excerpt',
            field=models.TextField(
                default='',
                help_text='Short summary (max 500 chars) for post listings and AI embedding context.',
            ),
            preserve_default=False,
        ),
        # 3. Add status field
        migrations.AddField(
            model_name='post',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('published', 'Published')],
                db_index=True,
                default='draft',
                max_length=20,
            ),
        ),
        # 4. Add author FK (nullable to avoid requiring a default for existing rows)
        migrations.AddField(
            model_name='post',
            name='author',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='blog_posts',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # 5. Add featured_image field
        migrations.AddField(
            model_name='post',
            name='featured_image',
            field=models.ImageField(blank=True, null=True, upload_to='blog/images/'),
        ),
        # 6. Add reading_time_minutes field
        migrations.AddField(
            model_name='post',
            name='reading_time_minutes',
            field=models.PositiveIntegerField(default=1),
        ),
        # 7. Add tags M2M
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(
                blank=True, related_name='posts', to='blog.tag'
            ),
        ),
        # 8. Remove legacy summary field (replaced by excerpt)
        migrations.RemoveField(
            model_name='post',
            name='summary',
        ),
        # 9. Remove legacy published BooleanField (replaced by status)
        migrations.RemoveField(
            model_name='post',
            name='published',
        ),
    ]
