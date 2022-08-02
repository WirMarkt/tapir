# Generated by Django 3.1.13 on 2021-07-29 18:40

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_auto_20210607_1213"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tapiruser",
            name="phone_number",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=128, region=None, verbose_name="Phone Number"
            ),
        ),
    ]
