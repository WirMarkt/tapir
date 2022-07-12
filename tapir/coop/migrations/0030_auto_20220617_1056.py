# Generated by Django 3.2.13 on 2022-06-17 08:56

import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("log", "0004_auto_20211003_0941"),
        ("coop", "0029_auto_20220605_1200"),
    ]

    operations = [
        migrations.CreateModel(
            name="CreateShareOwnershipsLogEntry",
            fields=[
                (
                    "logentry_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="log.logentry",
                    ),
                ),
                ("num_shares", models.PositiveIntegerField()),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, db_index=True, null=True)),
            ],
            bases=("log.logentry",),
        ),
        migrations.CreateModel(
            name="UpdateShareOwnershipLogEntry",
            fields=[
                (
                    "logentry_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="log.logentry",
                    ),
                ),
                ("old_values", django.contrib.postgres.fields.hstore.HStoreField()),
                ("new_values", django.contrib.postgres.fields.hstore.HStoreField()),
                ("share_ownership_id", models.PositiveIntegerField()),
            ],
            options={
                "abstract": False,
            },
            bases=("log.logentry",),
        ),
        migrations.AlterField(
            model_name="incomingpayment",
            name="credited_member",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="credited_payments",
                to="coop.shareowner",
                verbose_name="Credited member",
            ),
        ),
        migrations.AlterField(
            model_name="incomingpayment",
            name="paying_member",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="debited_payments",
                to="coop.shareowner",
                verbose_name="Paying member",
            ),
        ),
    ]
