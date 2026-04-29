from django.urls import path
from . import views, api_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views, api_views, auth_views
from . import views, api_views, auth_views, community_views

urlpatterns = [
    # Web routes
    path('', views.index, name='index'),
    path('analyze/text/', views.analyze_text, name='analyze_text'),
    path('analyze/barcode/', views.analyze_barcode, name='analyze_barcode'),
    path('analyze/image/', views.analyze_image, name='analyze_image'),
    path('result/<int:pk>/', views.result_detail, name='result_detail'),

    # API routes
    path('api/analyze/text/', api_views.api_analyze_text, name='api_analyze_text'),
    path('api/analyze/barcode/', api_views.api_analyze_barcode, name='api_analyze_barcode'),
    path('api/analyze/image/', api_views.api_analyze_image, name='api_analyze_image'),
    path('api/results/', api_views.api_results, name='api_results'),
    path('api/results/<int:pk>/', api_views.api_result_detail, name='api_result_detail'),

    # API Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Auth API
    path('api/auth/register/', auth_views.register, name='api_register'),
    path('api/auth/login/', auth_views.login, name='api_login'),
    path('api/auth/profile/', auth_views.profile, name='api_profile'),
    path('api/auth/profile/update/', auth_views.update_profile, name='api_update_profile'),

    # Community
    path('api/community/report/', community_views.submit_report, name='community_report'),
    path('api/community/score/<str:barcode>/', community_views.get_score, name='community_score'),
    path('api/community/my-vote/<str:barcode>/', community_views.my_vote, name='community_my_vote'),
]