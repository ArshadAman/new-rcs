from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_customuser_max_branches_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="business_description",
            field=models.TextField(blank=True),
        ),
    ]

