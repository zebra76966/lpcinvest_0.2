# Generated by Django 3.1.7 on 2022-12-13 06:49

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0013_auto_20221212_1251'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConstructionUpdates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30)),
                ('desc', models.TextField(blank=True, default=' ')),
                ('pub_date', models.DateField(default=datetime.datetime(2022, 12, 13, 12, 19, 25, 952992))),
            ],
        ),
        migrations.AlterField(
            model_name='profile',
            name='city',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='profile',
            name='email',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='profile',
            name='fname',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='profile',
            name='lname',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='profile',
            name='mobile',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AlterField(
            model_name='properties',
            name='pub_date',
            field=models.DateField(default=datetime.datetime(2022, 12, 13, 12, 19, 25, 928554)),
        ),
        migrations.CreateModel(
            name='ConstructionUpdatesImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('images', models.FileField(upload_to='media/property_updates')),
                ('property_update_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='home.constructionupdates')),
            ],
        ),
        migrations.AddField(
            model_name='constructionupdates',
            name='property',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='home.properties'),
        ),
    ]
