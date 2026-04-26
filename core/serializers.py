from rest_framework import serializers
from .models import Ingredient, AnalysisResult


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'aliases', 'status', 'source', 'source_url', 'notes']


class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = [
            'id', 'product_name', 'barcode', 'madhab',
            'overall_status', 'ingredient_results',
            'unknown_ingredients', 'ai_used', 'created_at'
        ]
