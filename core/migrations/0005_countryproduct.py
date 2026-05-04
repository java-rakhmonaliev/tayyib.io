from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_productcommunityscore_productcommunityreport"),
    ]

    operations = [
        migrations.CreateModel(
            name="CountryProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("barcode", models.CharField(db_index=True, max_length=100)),
                (
                    "country_code",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=2,
                        help_text="ISO 3166-1 alpha-2, e.g. KR, DE, US. Blank = global.",
                    ),
                ),
                ("product_name", models.CharField(blank=True, max_length=500)),
                ("ingredients_text", models.TextField(blank=True)),
                ("brand", models.CharField(blank=True, max_length=200)),
                ("image_url", models.URLField(blank=True)),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("openfoodfacts", "Open Food Facts"),
                            ("ai_agent", "AI Web Search Agent"),
                            ("manual", "Manual Entry"),
                        ],
                        default="openfoodfacts",
                        max_length=20,
                    ),
                ),
                ("low_confidence", models.BooleanField(default=False)),
                ("last_fetched", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-last_fetched"],
            },
        ),
        migrations.AddConstraint(
            model_name="countryproduct",
            constraint=models.UniqueConstraint(
                fields=["barcode", "country_code"], name="unique_barcode_country"
            ),
        ),
        migrations.AddIndex(
            model_name="countryproduct",
            index=models.Index(
                fields=["barcode", "country_code"], name="countryproduct_barcode_cc_idx"
            ),
        ),
    ]
