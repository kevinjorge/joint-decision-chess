# Generated by Django 4.2.7 on 2023-12-05 04:48

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import main.user_settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_chesslobby_opponent_connected'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('settings_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('themes', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), default=main.user_settings.default_themes, size=None)),
                ('username', models.CharField(max_length=150)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]