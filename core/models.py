from django.db import models


class Madhab(models.TextChoices):
    HANAFI = 'hanafi', 'Hanafi'
    MALIKI = 'maliki', 'Maliki'
    SHAFII = 'shafii', "Shafi'i"
    HANBALI = 'hanbali', 'Hanbali'

class IngredientStatus(models.TextChoices):
    HALAL = 'halal', 'Halal'
    HARAM = 'haram', 'Haram'
    QUESTIONABLE = 'questionable', 'Questionable'
    HANAFI_HARAM = 'hanafi_haram', 'Haram (Hanafi only)'
    SHAFII_HARAM = 'shafii_haram', "Haram (Shafi'i only)"
    MALIKI_HARAM = 'maliki_haram', 'Haram (Maliki only)'
    HANBALI_HARAM = 'hanbali_haram', 'Haram (Hanbali only)'

class Ingredient(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    aliases = models.JSONField(default=list, blank=True)  # alternative names / e-codes
    status = models.CharField(max_length=20, choices=IngredientStatus.choices)
    source = models.TextField(blank=True)         # why it's haram/questionable
    source_url = models.URLField(blank=True)      # citation link
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.status})"

    def get_status_for_madhab(self, madhab: str) -> str:
        if self.status == IngredientStatus.HANAFI_HARAM:
            return IngredientStatus.HARAM if madhab == Madhab.HANAFI else IngredientStatus.HALAL
        if self.status == IngredientStatus.SHAFII_HARAM:
            return IngredientStatus.HARAM if madhab == Madhab.SHAFII else IngredientStatus.HALAL
        if self.status == IngredientStatus.MALIKI_HARAM:
            return IngredientStatus.HARAM if madhab == Madhab.MALIKI else IngredientStatus.HALAL
        if self.status == IngredientStatus.HANBALI_HARAM:
            return IngredientStatus.HARAM if madhab == Madhab.HANBALI else IngredientStatus.HALAL
        return self.status

    class Meta:
        ordering = ['name']


class AnalysisResult(models.Model):
    # Input
    raw_text = models.TextField()                          # original ingredient text
    barcode = models.CharField(max_length=50, blank=True)
    product_name = models.CharField(max_length=255, blank=True)
    madhab = models.CharField(max_length=10, choices=Madhab.choices, default=Madhab.HANAFI)

    # Output
    overall_status = models.CharField(max_length=20, choices=IngredientStatus.choices)
    ingredient_results = models.JSONField(default=list)    # per-ingredient breakdown
    unknown_ingredients = models.JSONField(default=list)   # not found in DB, sent to AI
    ai_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name or 'Manual'} — {self.overall_status} ({self.created_at:%Y-%m-%d})"

    class Meta:
        ordering = ['-created_at']


from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    madhab = models.CharField(max_length=10, choices=Madhab.choices, default=Madhab.HANAFI)
    country = models.CharField(max_length=100, blank=True, default='')
    total_scans = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.madhab}"