from django.urls import path
from . import views

app_name = 'papers'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('paper/<str:record_id>/', views.PaperDetailView.as_view(), name='detail'),
    path('export-search/', views.ExportSearchView.as_view(), name='export_search'),
    
    # AJAX endpoints
    path('api/search-autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('api/paper/<str:record_id>/citations/', views.paper_citations_json, name='paper_citations_json'),
    path('api/post-retraction-analytics/', views.PostRetractionAnalyticsAPIView.as_view(), name='post_retraction_analytics_api'),
    path('api/analytics-data/', views.AnalyticsDataAPIView.as_view(), name='analytics_data_api'),
    path('api/analytics-realtime/', views.analytics_data_ajax, name='analytics_realtime_api'),
    path('api/export/', views.export_data, name='export_data'),
] 