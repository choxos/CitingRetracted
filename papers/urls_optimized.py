from django.urls import path
from . import views_optimized

app_name = 'papers'

urlpatterns = [
    # Optimized main views
    path('', views_optimized.OptimizedHomeView.as_view(), name='home'),
    path('analytics/', views_optimized.OptimizedAnalyticsView.as_view(), name='analytics'),
    path('search/', views_optimized.OptimizedSearchView.as_view(), name='search'),
    path('paper/<str:record_id>/', views_optimized.OptimizedPaperDetailView.as_view(), name='detail'),
    
    # API endpoints for real-time data
    path('api/analytics/', views_optimized.analytics_api, name='analytics_api'),
    path('api/warm-cache/', views_optimized.warm_cache, name='warm_cache'),
] 