# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-05 08:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0005_auto_20170705_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disk',
            name='slot',
            field=models.CharField(max_length=64, verbose_name='插槽位'),
        ),
    ]