# Generated by Django 3.2.20 on 2023-09-27 11:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mfa", "0002_authenticator_timestamps"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authenticator",
            name="type",
            field=models.CharField(
                choices=[
                    ("recovery_codes", "Recovery codes"),
                    ("totp", "TOTP Authenticator"),
                    ("webauthn", "WebAuthn"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="authenticator",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="authenticator",
            constraint=models.UniqueConstraint(
                condition=models.Q(("type__in", ("totp", "recovery_codes"))),
                fields=("user", "type"),
                name="unique_authenticator_type",
            ),
        ),
    ]
