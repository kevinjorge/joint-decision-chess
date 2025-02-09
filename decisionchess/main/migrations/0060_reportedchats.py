# Generated by Django 5.1.4 on 2025-01-13 21:24

import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0059_chesslobby_fen_alter_activegames_fen'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportedChats',
            fields=[
                ('report_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('game_id', models.UUIDField()),
                ('reporting_time', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
