# Generated by Django 5.1.2 on 2024-11-17 02:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0053_chesslobby_black_rank_start_chesslobby_match_type_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gamehistorytable',
            old_name='black_rank_new',
            new_name='black_rank_change',
        ),
        migrations.RenameField(
            model_name='gamehistorytable',
            old_name='white_rank_new',
            new_name='white_rank_change',
        ),
    ]