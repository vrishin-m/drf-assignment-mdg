from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("studios", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="studio",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
