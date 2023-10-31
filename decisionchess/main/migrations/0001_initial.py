# Generated by Django 4.2.6 on 2023-10-31 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChessLobby',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game_uuid', models.UUIDField(unique=True)),
                ('white_uuid', models.UUIDField(null=True)),
                ('black_uuid', models.UUIDField(null=True)),
                ('initiator_name', models.CharField(default='Anonymous', max_length=150)),
                ('timestamp', models.DateTimeField()),
                ('expire', models.DateTimeField()),
                ('is_open', models.BooleanField(default=True)),
                ('initiator_connected', models.BooleanField(default=False)),
            ],
        ),
    ]
