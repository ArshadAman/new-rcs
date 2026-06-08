from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_customuser_marketing_banner'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='business_logo',
            field=models.ImageField(blank=True, null=True, upload_to='business_logos/'),
        ),
    ]
