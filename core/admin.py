from django.contrib import admin
from .models import Ingredient, AnalysisResult


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'aliases']
    ordering = ['name']


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'overall_status', 'madhab', 'ai_used', 'created_at']
    list_filter = ['overall_status', 'madhab', 'ai_used']
    search_fields = ['product_name', 'barcode', 'raw_text']
    readonly_fields = ['raw_text', 'ingredient_results', 'unknown_ingredients', 'created_at']
    ordering = ['-created_at']

from .models import Ingredient, AnalysisResult, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'madhab', 'country', 'total_scans', 'created_at']
    list_filter = ['madhab', 'country']
    search_fields = ['user__username', 'user__email']


from .models import Ingredient, AnalysisResult, UserProfile, ProductCommunityReport, ProductCommunityScore

@admin.register(ProductCommunityReport)
class ProductCommunityReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'barcode', 'product_name', 'vote', 'madhab', 'created_at']
    list_filter = ['vote', 'madhab']
    search_fields = ['barcode', 'product_name', 'user__username']

@admin.register(ProductCommunityScore)
class ProductCommunityScoreAdmin(admin.ModelAdmin):
    list_display = ['barcode', 'product_name', 'community_verdict', 'total_votes', 'confirmed_halal_count', 'found_issue_count']
    list_filter = ['community_verdict']
    search_fields = ['barcode', 'product_name']