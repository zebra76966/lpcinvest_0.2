# Generated by Django 3.1.7 on 2022-12-01 06:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='properties',
            name='pub_date',
            field=models.DateField(default=datetime.datetime(2022, 12, 1, 12, 25, 11, 197400)),
        ),
    ]
