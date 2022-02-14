from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coop", "0025_draftuser_paid_shares"),
    ]

    operations = [
        migrations.AddField(
            model_name="shareowner",
            name="signed_sepa_mandate",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="shareowner",
            name="sepa_account_holder",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
        migrations.AddField(
            model_name="shareowner",
            name="sepa_iban",
            field=models.CharField(blank=True, default="", max_length=34),
        ),
    ]
