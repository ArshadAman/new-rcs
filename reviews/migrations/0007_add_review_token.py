# Generated migration to add review_token field

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0006_auto_20251119_1500'),
    ]
    
    # This migration was manually created - the field was added via SQL
    # Marking as already applied to avoid conflicts

    operations = [
        migrations.AddField(
            model_name='review',
            name='review_token',
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
    ]

