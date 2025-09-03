from django.urls import path
from . import views
from .views_performance import PerformanceAnalyticsView

app_name = 'papers'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('analytics/', PerformanceAnalyticsView.as_view(), name='analytics'),  # Use optimized view
    path('analytics-legacy/', views.AnalyticsView.as_view(), name='analytics_legacy'),  # Keep old for backup
    path('predatory-analysis/', views.PredatoryJournalAnalysisView.as_view(), name='predatory_analysis'),
    path('democracy-analysis/', views.DemocracyAnalysisView.as_view(), name='democracy_analysis'),
    path('paper/<str:record_id>/', views.PaperDetailView.as_view(), name='detail'),
    path('export-search/', views.ExportSearchView.as_view(), name='export_search'),
    
    # AJAX endpoints
    path('api/search-autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('api/paper/<str:record_id>/citations/', views.paper_citations_json, name='paper_citations_json'),
    path('api/post-retraction-analytics/', views.PostRetractionAnalyticsAPIView.as_view(), name='post_retraction_analytics_api'),
    path('api/analytics-data/', views.AnalyticsDataAPIView.as_view(), name='analytics_data_api'),
    path('api/analytics-realtime/', views.analytics_data_ajax, name='analytics_realtime_api'),
    path('api/export/', views.export_data, name='export_data'),
    
    # Democracy Analysis API endpoints
    path('api/democracy/overview/', views.DemocracyAnalysisAPIView.as_view(), name='democracy_analysis_api'),
    path('api/democracy/raw-data/', views.DemocracyRawDataAPIView.as_view(), name='democracy_raw_data_api'),
    path('api/democracy/visualizations/', views.DemocracyVisualizationsAPIView.as_view(), name='democracy_visualizations_api'),
    path('api/democracy/model-diagnostics/', views.DemocracyModelDiagnosticsAPIView.as_view(), name='democracy_model_diagnostics_api'),
    path('api/democracy/statistical-results/', views.DemocracyStatisticalResultsAPIView.as_view(), name='democracy_statistical_results_api'),
    path('api/democracy/methodology/', views.DemocracyMethodologyAPIView.as_view(), name='democracy_methodology_api'),
] 