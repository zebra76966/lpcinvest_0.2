# Generated by Django 3.1.7 on 2022-12-01 15:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_auto_20221201_2028'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='properties',
            name='desc',
        ),
        migrations.AlterField(
            model_name='properties',
            name='pub_date',
            field=models.DateField(default=datetime.datetime(2022, 12, 1, 20, 32, 2, 986443)),
        ),
    ]