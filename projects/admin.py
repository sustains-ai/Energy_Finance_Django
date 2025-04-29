"""
Admin configuration for the Energy Finance application.
"""

from django.contrib import admin
from .models import Project, SolarProject, CashFlow, FinancialMetric, GeospatialLayer


class CashFlowInline(admin.TabularInline):
    model = CashFlow
    extra = 0


class FinancialMetricInline(admin.StackedInline):
    model = FinancialMetric
    can_delete = False
    max_num = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_type', 'capacity_mw', 'location', 'status')
    list_filter = ('project_type', 'status')
    search_fields = ('name', 'location')
    inlines = [FinancialMetricInline, CashFlowInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'project_type', 'status')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Technical Details', {
            'fields': ('capacity_mw',)
        }),
        ('Financial Parameters', {
            'fields': ('capex', 'capex_per_mw', 'opex_per_year', 'opex_per_mw')
        }),
        ('Timeline', {
            'fields': ('start_date', 'commercial_operation_date', 'expected_lifetime_years')
        })
    )


@admin.register(SolarProject)
class SolarProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity_mw', 'location', 'panel_type', 'status')
    list_filter = ('status', 'panel_type', 'tracking_type')
    search_fields = ('name', 'location')
    inlines = [FinancialMetricInline, CashFlowInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude', 'tilt_angle', 'azimuth')
        }),
        ('Technical Details', {
            'fields': ('capacity_mw', 'panel_type', 'panel_efficiency', 'num_panels', 
                       'panel_capacity_w', 'tracking_type', 'land_area_acres')
        }),
        ('Performance', {
            'fields': ('degradation_rate', 'performance_ratio')
        }),
        ('Financial Parameters', {
            'fields': ('capex', 'capex_per_mw', 'opex_per_year', 'opex_per_mw')
        }),
        ('Timeline', {
            'fields': ('start_date', 'commercial_operation_date', 'expected_lifetime_years')
        })
    )


@admin.register(FinancialMetric)
class FinancialMetricAdmin(admin.ModelAdmin):
    list_display = ('project', 'npv', 'irr', 'payback_period', 'lcoe')
    list_filter = ('project__project_type',)
    search_fields = ('project__name',)


@admin.register(GeospatialLayer)
class GeospatialLayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'layer_type', 'enabled')
    list_filter = ('layer_type', 'enabled')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'layer_type', 'source_url', 'enabled')
        }),
        ('Visualization Settings', {
            'fields': ('color_scale', 'opacity')
        }),
        ('Bounds', {
            'fields': ('min_lat', 'max_lat', 'min_lon', 'max_lon')
        })
    )