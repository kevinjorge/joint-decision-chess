# Generated by Django 5.1.2 on 2024-11-11 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0050_challenge_subvariant_chesslobby_subvariant_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='activegames',
            name='last_submission_time',
            field=models.DateTimeField(null=True),
        ),
    ]