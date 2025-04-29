"""
Views for the Energy Finance application.
"""

import os
import json
import pandas as pd
import numpy as np
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.edit import FormView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum, Avg, Min, Max

from .models import Project, SolarProject, CashFlow, FinancialMetric, GeospatialLayer
from .forms import ProjectForm, SolarProjectForm, FinancialMetricForm, ProjectImportForm
from .utils import (calculate_financial_metrics, generate_project_templates, 
                   import_project_from_file, calculate_risk_scores)
from .ml_models import PowerGenerationPredictor


class ProjectListView(ListView):
    """View to display a list of projects"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    

class ProjectDetailView(DetailView):
    """View to display project details"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Get cash flows
        cash_flows = project.cash_flows.all().order_by('year')
        context['cash_flows'] = cash_flows
        
        # Prepare chart data
        years = [cf.year for cf in cash_flows]
        net_cash_flows = [cf.net_cash_flow for cf in cash_flows]
        cumulative_cash_flows = [cf.cumulative_cash_flow for cf in cash_flows]
        
        context['chart_data'] = {
            'years': years,
            'net_cash_flows': net_cash_flows,
            'cumulative_cash_flows': cumulative_cash_flows
        }
        
        # Get financial metrics
        try:
            metrics = project.financial_metrics
            context['metrics'] = metrics
        except FinancialMetric.DoesNotExist:
            context['metrics'] = None
        
        return context


class ProjectCreateView(CreateView):
    """View to create a new project"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Calculate risk scores for the new project
        calculate_risk_scores(self.object)
        messages.success(self.request, "Project created successfully.")
        return response


class SolarProjectCreateView(CreateView):
    """View to create a new solar project"""
    model = SolarProject
    form_class = SolarProjectForm
    template_name = 'projects/solar_project_form.html'
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.project_type = 'solar'
        response = super().form_valid(form)
        # Calculate risk scores for the new solar project
        calculate_risk_scores(self.object)
        messages.success(self.request, "Solar project created successfully.")
        return response


class ProjectUpdateView(UpdateView):
    """View to update a project"""
    model = Project
    template_name = 'projects/project_form.html'
    
    def get_form_class(self):
        if isinstance(self.get_object(), SolarProject):
            return SolarProjectForm
        return ProjectForm
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Re-calculate risk scores after project update
        calculate_risk_scores(self.object)
        messages.success(self.request, "Project updated successfully.")
        return response


class ProjectDeleteView(DeleteView):
    """View to delete a project"""
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Project deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ProjectImportView(FormView):
    """View to import a project from file"""
    template_name = 'projects/project_import.html'
    form_class = ProjectImportForm
    success_url = reverse_lazy('projects:project_list')
    
    def form_valid(self, form):
        file = form.cleaned_data['file']
        success, message, project = import_project_from_file(file)
        
        if success:
            messages.success(self.request, message)
            if project:
                # Calculate risk scores for the imported project
                calculate_risk_scores(project)
                return redirect('projects:project_detail', pk=project.pk)
        else:
            messages.error(self.request, message)
            return self.form_invalid(form)
            
        return super().form_valid(form)


class FinancialAnalysisView(FormView):
    """View to perform financial analysis on a project"""
    template_name = 'projects/financial_analysis.html'
    form_class = FinancialMetricForm
    
    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.kwargs['pk']})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not kwargs.get('instance'):
            project = get_object_or_404(Project, pk=self.kwargs['pk'])
            try:
                kwargs['instance'] = project.financial_metrics
            except FinancialMetric.DoesNotExist:
                pass
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        
        # Extract form data
        discount_rate = form.cleaned_data['discount_rate'] or 0.08
        inflation_rate = form.cleaned_data['inflation_rate'] or 0.025
        debt_ratio = form.cleaned_data['debt_ratio'] or 0.7
        interest_rate = form.cleaned_data['interest_rate'] or 0.05
        
        # Calculate metrics
        metrics = calculate_financial_metrics(
            project, 
            discount_rate=discount_rate,
            inflation_rate=inflation_rate,
            debt_ratio=debt_ratio,
            interest_rate=interest_rate
        )
        
        messages.success(self.request, "Financial metrics calculated successfully.")
        return super().form_valid(form)


def generate_template_view(request):
    """View to generate and download project templates"""
    if request.method == 'GET':
        format_type = request.GET.get('format', 'excel')
        
        # Generate templates
        excel_path, csv_path = generate_project_templates()
        
        # Return the appropriate file for download
        if format_type == 'csv':
            with open(csv_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename=solar_project_template.csv'
                return response
        else:
            with open(excel_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=solar_project_template.xlsx'
                return response
    
    # If not a GET request, redirect to import page
    return redirect('projects:project_import')


def calculate_metrics_api(request):
    """API endpoint for calculating financial metrics"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            
            if not project_id:
                return JsonResponse({'error': 'Project ID is required'}, status=400)
            
            project = get_object_or_404(Project, pk=project_id)
            
            # Get parameters from request or use defaults
            discount_rate = data.get('discount_rate', 0.08)
            inflation_rate = data.get('inflation_rate', 0.025)
            debt_ratio = data.get('debt_ratio', 0.7)
            interest_rate = data.get('interest_rate', 0.05)
            
            # Calculate metrics
            metrics = calculate_financial_metrics(
                project, 
                discount_rate=discount_rate,
                inflation_rate=inflation_rate,
                debt_ratio=debt_ratio,
                interest_rate=interest_rate
            )
            
            # Prepare response
            response_data = {
                'npv': metrics.npv,
                'irr': metrics.irr,
                'payback_period': metrics.payback_period,
                'lcoe': metrics.lcoe,
                'mirr': metrics.mirr,
                'profitability_index': metrics.profitability_index,
                'debt_service_coverage_ratio': metrics.debt_service_coverage_ratio
            }
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST requests are supported'}, status=405)


class IndexView(TemplateView):
    """Home page view"""
    template_name = 'projects/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_projects'] = Project.objects.count()
        context['solar_projects'] = Project.objects.filter(project_type='solar').count()
        context['latest_projects'] = Project.objects.order_by('-created_at')[:5]
        return context


class GeospatialMapView(TemplateView):
    """View to display all projects on a map"""
    template_name = 'projects/geospatial_map.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all available layers
        context['layers'] = GeospatialLayer.objects.filter(enabled=True)
        
        # Get project summary stats
        context['project_count'] = Project.objects.count()
        context['total_capacity'] = Project.objects.aggregate(Sum('capacity_mw'))['capacity_mw__sum'] or 0
        
        # Get solar project specific stats
        solar_projects = Project.objects.filter(project_type='solar')
        context['solar_project_count'] = solar_projects.count()
        context['solar_capacity'] = solar_projects.aggregate(Sum('capacity_mw'))['capacity_mw__sum'] or 0
        
        # Get map center coordinates (average of all project coordinates)
        projects_with_coords = Project.objects.filter(
            latitude__isnull=False, 
            longitude__isnull=False
        )
        
        if projects_with_coords.exists():
            avg_coords = projects_with_coords.aggregate(
                avg_lat=Avg('latitude'),
                avg_lon=Avg('longitude')
            )
            context['map_center'] = {
                'lat': avg_coords['avg_lat'],
                'lon': avg_coords['avg_lon'],
                'zoom': 5
            }
        else:
            # Default to US center if no projects with coordinates
            context['map_center'] = {
                'lat': 39.8283,
                'lon': -98.5795,
                'zoom': 4
            }
        
        return context


class ProjectMapView(DetailView):
    """View to display a single project on a map with related geospatial data"""
    model = Project
    template_name = 'projects/project_map.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Get available layers
        context['layers'] = GeospatialLayer.objects.filter(enabled=True)
        
        # Set map center to project location or default
        if project.latitude and project.longitude:
            context['map_center'] = {
                'lat': project.latitude,
                'lon': project.longitude,
                'zoom': 10
            }
        else:
            # Default center if no coordinates
            context['map_center'] = {
                'lat': 39.8283,
                'lon': -98.5795,
                'zoom': 4
            }
        
        return context


def map_data_api(request):
    """API endpoint to get geospatial data for all projects"""
    try:
        # Filter for projects with coordinates
        projects = Project.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Apply any filters from query params
        project_type = request.GET.get('project_type')
        if project_type:
            projects = projects.filter(project_type=project_type)
        
        status = request.GET.get('status')
        if status:
            projects = projects.filter(status=status)
        
        min_capacity = request.GET.get('min_capacity')
        if min_capacity:
            projects = projects.filter(capacity_mw__gte=float(min_capacity))
        
        # Build GeoJSON response
        features = []
        for project in projects:
            # Get financial metrics if available
            try:
                metrics = {
                    'npv': project.financial_metrics.npv,
                    'irr': project.financial_metrics.irr,
                    'payback_period': project.financial_metrics.payback_period,
                    'lcoe': project.financial_metrics.lcoe
                }
            except (FinancialMetric.DoesNotExist, AttributeError):
                metrics = {
                    'npv': None,
                    'irr': None,
                    'payback_period': None,
                    'lcoe': None
                }
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [project.longitude, project.latitude]
                },
                'properties': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'project_type': project.project_type,
                    'capacity_mw': project.capacity_mw,
                    'status': project.status,
                    'metrics': metrics,
                    'url': reverse('projects:project_detail', kwargs={'pk': project.id})
                }
            }
            
            # Add solar-specific properties if applicable
            if project.project_type == 'solar' and hasattr(project, 'solarproject'):
                solar = project.solarproject
                feature['properties'].update({
                    'panel_type': solar.panel_type,
                    'panel_efficiency': solar.panel_efficiency,
                    'tracking_type': solar.tracking_type,
                    'land_area_acres': solar.land_area_acres
                })
            
            features.append(feature)
        
        # Create GeoJSON object
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return JsonResponse(geojson)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def project_map_data_api(request, pk):
    """API endpoint to get geospatial data for a specific project"""
    try:
        project = get_object_or_404(Project, pk=pk)
        
        # Check if project has coordinates
        if not project.latitude or not project.longitude:
            return JsonResponse({'error': 'Project does not have geographic coordinates'}, status=400)
        
        # Get financial metrics if available
        try:
            metrics = {
                'npv': project.financial_metrics.npv,
                'irr': project.financial_metrics.irr,
                'payback_period': project.financial_metrics.payback_period,
                'lcoe': project.financial_metrics.lcoe
            }
        except (FinancialMetric.DoesNotExist, AttributeError):
            metrics = {
                'npv': None,
                'irr': None,
                'payback_period': None,
                'lcoe': None
            }
        
        # Build GeoJSON feature
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [project.longitude, project.latitude]
            },
            'properties': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'project_type': project.project_type,
                'capacity_mw': project.capacity_mw,
                'status': project.status,
                'metrics': metrics
            }
        }
        
        # Add solar-specific properties if applicable
        if project.project_type == 'solar' and hasattr(project, 'solarproject'):
            solar = project.solarproject
            feature['properties'].update({
                'panel_type': solar.panel_type,
                'panel_efficiency': solar.panel_efficiency,
                'tracking_type': solar.tracking_type,
                'land_area_acres': solar.land_area_acres
            })
        
        # Create GeoJSON object
        geojson = {
            'type': 'FeatureCollection',
            'features': [feature]
        }
        
        return JsonResponse(geojson)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class SolarRadiationView(DetailView):
    """View to display solar radiation data for a solar project"""
    model = SolarProject
    template_name = 'projects/solar_radiation.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Ensure we have coordinates
        if not project.latitude or not project.longitude:
            context['error'] = "This project does not have geographic coordinates defined."
            return context
        
        # Set initial values
        context['initial_capacity'] = project.capacity_mw * 1000  # Convert MW to kW
        
        return context


def solar_radiation_api(request, pk):
    """API endpoint to get solar radiation data for a project"""
    from .solar_service import SolarRadiationService
    
    try:
        project = get_object_or_404(SolarProject, pk=pk)
        
        # Get parameters from request
        capacity = float(request.GET.get('capacity', project.capacity_mw * 1000))  # kW
        data_type = request.GET.get('data_type', 'monthly')  # daily, monthly, annual
        
        # Check if project has coordinates
        if not project.latitude or not project.longitude:
            return JsonResponse({
                'error': 'Project does not have geographic coordinates'
            }, status=400)
        
        # Initialize service
        service = SolarRadiationService()
        
        # Get requested data
        if data_type == 'daily':
            data = service.get_daily_solar_data(project.latitude, project.longitude, capacity)
            response_data = {
                'daily_data': data
            }
        elif data_type == 'monthly':
            data = service.get_monthly_solar_data(project.latitude, project.longitude, capacity)
            response_data = {
                'monthly_data': data
            }
        elif data_type == 'annual':
            data = service.get_annual_production(project.latitude, project.longitude, capacity)
            response_data = data
        else:
            return JsonResponse({
                'error': f"Invalid data_type: {data_type}. Must be one of 'daily', 'monthly', or 'annual'"
            }, status=400)
        
        return JsonResponse(response_data)
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class MLPowerPredictionView(TemplateView):
    """View for machine learning power generation prediction"""
    template_name = 'projects/ml_power_prediction.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create predictor model
        predictor = PowerGenerationPredictor()
        
        # Generate sample data for demonstration
        X, y = predictor.generate_sample_data(n_samples=1000)
        
        # Evaluate model
        eval_metrics = predictor.evaluate_model(X, y)
        
        # Sample prediction
        sample_inputs = X.iloc[[0, 100, 200, 300, 400]].copy()  # Get a few sample rows for demonstration
        sample_predictions = predictor.predict(sample_inputs)
        
        # Convert to list for JSON serialization
        prediction_examples = []
        for i, (_, row) in enumerate(sample_inputs.iterrows()):
            prediction_examples.append({
                'input': {
                    'solar_irradiance': round(row['solar_irradiance'], 2),
                    'temperature': round(row['temperature'], 2),
                    'cloud_cover': round(row['cloud_cover'], 2),
                    'system_capacity': round(row['system_capacity'], 2),
                    'tilt_angle': round(row['tilt_angle'], 2),
                    'azimuth': round(row['azimuth'], 2),
                    'panel_efficiency': round(row['panel_efficiency'], 2),
                    'hour_of_day': int(row['hour_of_day']),
                    'month': int(row['month'])
                },
                'predicted_power': round(float(sample_predictions[i]), 2)
            })
        
        # Prepare data for visualization
        visualization_data = {
            'irradiance_vs_power': [],
            'cloud_cover_vs_power': [],
            'temperature_vs_power': [],
            'efficiency_vs_power': []
        }
        
        # Sample 100 points for visualization
        sample_size = min(100, len(X))
        indices = np.random.choice(len(X), sample_size, replace=False)
        
        # Convert to lists for easier handling
        irradiance_values = X['solar_irradiance'].values[indices].tolist()
        cloud_cover_values = X['cloud_cover'].values[indices].tolist()
        temperature_values = X['temperature'].values[indices].tolist()
        efficiency_values = X['panel_efficiency'].values[indices].tolist()
        power_values = y.tolist()
        power_samples = [power_values[i] for i in indices]
        
        # Create visualization data points
        for i in range(sample_size):
            visualization_data['irradiance_vs_power'].append({
                'x': float(irradiance_values[i]),
                'y': float(power_samples[i])
            })
            visualization_data['cloud_cover_vs_power'].append({
                'x': float(cloud_cover_values[i]),
                'y': float(power_samples[i])
            })
            visualization_data['temperature_vs_power'].append({
                'x': float(temperature_values[i]),
                'y': float(power_samples[i])
            })
            visualization_data['efficiency_vs_power'].append({
                'x': float(efficiency_values[i]),
                'y': float(power_samples[i])
            })
            
        # Add data to context
        context['eval_metrics'] = {
            'mse': round(eval_metrics['mse'], 4),
            'rmse': round(eval_metrics['rmse'], 4),
            'mae': round(eval_metrics['mae'], 4),
            'r_squared': round(eval_metrics['r_squared'], 4)
        }
        context['prediction_examples'] = prediction_examples
        context['visualization_data'] = visualization_data
        
        # Get all solar projects for model application
        context['solar_projects'] = SolarProject.objects.all()
        
        return context
