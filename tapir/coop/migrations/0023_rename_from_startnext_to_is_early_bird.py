from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coop", "0022_membership_fee_and_sepa_mandate"),
    ]

    operations = [
        migrations.RenameField(
            model_name="draftuser",
            old_name="from_startnext",
            new_name="is_early_bird",
        ),
        migrations.RenameField(
            model_name="shareowner",
            old_name="from_startnext",
            new_name="is_early_bird",
        ),

    ]
