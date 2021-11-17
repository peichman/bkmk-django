# Generated by Django 3.2.9 on 2021-11-16 22:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', models.CharField(max_length=1024, unique=True)),
                ('title', models.CharField(max_length=1024)),
                ('tags', models.ManyToManyField(related_name='resources', to='bookmarks.Tag')),
            ],
        ),
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('modified', models.DateTimeField()),
                ('deleted', models.DateTimeField()),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookmark', to='bookmarks.resource')),
            ],
        ),
    ]
