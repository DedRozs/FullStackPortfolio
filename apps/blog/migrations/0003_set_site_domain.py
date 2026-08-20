"""
Migration: point the django.contrib.sites record at the real domain.

The syndication framework builds absolute URLs in the RSS feed from the Site
record for SITE_ID. That record still held the framework default of
"example.com", so every link the feed emitted was dead.
"""

from django.conf import settings
from django.db import migrations

_DOMAIN = 'www.thejosephprince.com'
_NAME = 'Joseph Prince'
_DEFAULT_DOMAIN = 'example.com'


def set_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        pk=settings.SITE_ID,
        defaults={'domain': _DOMAIN, 'name': _NAME},
    )


def restore_default_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(pk=settings.SITE_ID).update(
        domain=_DEFAULT_DOMAIN,
        name=_DEFAULT_DOMAIN,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_add_blog_fields'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(set_site_domain, restore_default_domain),
    ]
