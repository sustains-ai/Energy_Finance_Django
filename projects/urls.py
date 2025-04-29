"""
URL patterns for the projects app.
"""

from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Basic views
    path('', views.IndexView.as_view(), name='index'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    
    # Project CRUD operations
    path('projects/new/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/solar/new/', views.SolarProjectCreateView.as_view(), name='solar_project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    
    # Financial analysis
    path('projects/<int:pk>/analyze/', views.FinancialAnalysisView.as_view(), name='financial_analysis'),
    
    # Geospatial visualization
    path('map/', views.GeospatialMapView.as_view(), name='geospatial_map'),
    path('projects/<int:pk>/map/', views.ProjectMapView.as_view(), name='project_map'),
    
    # Solar radiation analysis
    path('projects/<int:pk>/solar-radiation/', views.SolarRadiationView.as_view(), name='solar_radiation'),
    
    # Machine Learning
    path('ml/power-prediction/', views.MLPowerPredictionView.as_view(), name='ml_power_prediction'),
    
    # API endpoints
    path('api/calculate-metrics/', views.calculate_metrics_api, name='calculate_metrics_api'),
    path('api/map-data/', views.map_data_api, name='map_data_api'),
    path('api/project-map-data/<int:pk>/', views.project_map_data_api, name='project_map_data_api'),
    path('api/solar-radiation/<int:pk>/', views.solar_radiation_api, name='solar_radiation_api'),
    
    # Import/Export
    path('projects/import/', views.ProjectImportView.as_view(), name='project_import'),
    path('projects/generate-template/', views.generate_template_view, name='generate_template'),
]