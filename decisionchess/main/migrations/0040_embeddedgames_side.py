# Generated by Django 5.1.1 on 2024-10-02 02:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0039_rename_tutorial_id_pages_lesson_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='embeddedgames',
            name='side',
            field=models.CharField(default='white', max_length=5),
        ),
    ]