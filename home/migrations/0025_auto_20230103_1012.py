# Generated by Django 3.1.7 on 2023-01-03 04:42

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0024_auto_20230102_1323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='constructionupdates',
            name='pub_date',
            field=models.DateField(default=datetime.datetime(2023, 1, 3, 10, 12, 39, 694652)),
        ),
        migrations.AlterField(
            model_name='properties',
            name='pub_date',
            field=models.DateField(default=datetime.datetime(2023, 1, 3, 10, 12, 39, 635717)),
        ),
    ]
