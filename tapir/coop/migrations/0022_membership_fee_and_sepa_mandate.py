from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coop", "0021_shareowner_willing_to_gift_a_share"),
    ]

    operations = [
        migrations.AddField(
            model_name="shareowner",
            name="signed_sepa_mandate",
            field=models.BooleanField(
                default=False, verbose_name="Signed SEPA mandate"
            ),
        ),
        migrations.AddField(
            model_name="shareowner",
            name="is_paying",
            field=models.BooleanField(default=False, verbose_name="Pays membership fee"),
        ),
        migrations.AddField(
            model_name="shareowner",
            name="sepa_account_holder",
            field=models.CharField(default="", verbose_name="SEPA Account Holder", max_length=150),
        ),
        migrations.AddField(
            model_name="shareowner",
            name="sepa_iban",
            field=models.CharField(default="", verbose_name="SEPA IBAN", max_length=34),
        ),

    ]
