# Generated by Django 3.2.9 on 2021-11-16 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookmarks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmark',
            name='deleted',
            field=models.DateTimeField(null=True),
        ),
    ]
