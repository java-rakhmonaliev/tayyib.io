from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('analyze/text/', views.analyze_text, name='analyze_text'),
    path('analyze/barcode/', views.analyze_barcode, name='analyze_barcode'),
    path('analyze/image/', views.analyze_image, name='analyze_image'),
    path('result/<int:pk>/', views.result_detail, name='result_detail'),
]