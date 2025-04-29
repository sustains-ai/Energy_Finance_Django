"""
Models for the Energy Finance application.
These models represent energy projects, financial metrics, and cash flows
to help energy analysts evaluate project viability with geospatial features.
"""

from django.db import models
from django.utils import timezone
from datetime import datetime


class Project(models.Model):
    """Base model for energy projects"""
    
    # Basic info
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    capacity_mw = models.FloatField(help_text="Capacity in megawatts")
    project_type = models.CharField(max_length=50, help_text="e.g., 'solar', 'wind'")
    
    # Financial data
    capex = models.FloatField(blank=True, null=True, help_text="Capital expenditure (total)")
    capex_per_mw = models.FloatField(blank=True, null=True, help_text="Capital expenditure per MW")
    opex_per_year = models.FloatField(blank=True, null=True, help_text="Operating expenditure per year")
    opex_per_mw = models.FloatField(blank=True, null=True, help_text="Operating expenditure per MW per year")
    
    # Timeline
    start_date = models.DateField(blank=True, null=True)
    commercial_operation_date = models.DateField(blank=True, null=True)
    expected_lifetime_years = models.IntegerField(default=25)
    
    # Status
    status = models.CharField(max_length=50, default='planning', 
                              help_text="planning, construction, operational, decommissioned")
    
    # Geospatial data
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    # Risk assessment factors
    home_country = models.CharField(max_length=100, blank=True, null=True, 
                                    help_text="Country of origin for investment")
    target_country = models.CharField(max_length=100, blank=True, null=True,
                                      help_text="Target country for the project")
    target_state_province = models.CharField(max_length=100, blank=True, null=True,
                                            help_text="State/province within target country")
    technology_risk_factor = models.FloatField(blank=True, null=True,
                                              help_text="Energy yield variability factor (0-1)")
    project_status_risk = models.CharField(max_length=50, blank=True, null=True,
                                          choices=[
                                              ('early_stage', 'Early Stage (Higher Risk)'),
                                              ('development', 'Development'),
                                              ('construction', 'Construction'),
                                              ('operational', 'Operational (Lower Risk)')
                                          ],
                                          help_text="Project development status risk level")
    asset_life_years = models.IntegerField(blank=True, null=True, 
                                          help_text="Target years of operation")
    off_taker_rating = models.CharField(max_length=50, blank=True, null=True,
                                       help_text="Credit rating of energy buyer (impacts revenue)")
    funding_leverage = models.FloatField(blank=True, null=True,
                                        help_text="Debt to equity ratio (impacts capex and cash flow)")
    
    # Risk scores (calculated)
    country_risk_score = models.FloatField(blank=True, null=True,
                                          help_text="Risk score based on home/target country")
    technology_risk_score = models.FloatField(blank=True, null=True,
                                             help_text="Risk score based on technology type")
    status_risk_score = models.FloatField(blank=True, null=True,
                                         help_text="Risk score based on project status")
    off_taker_risk_score = models.FloatField(blank=True, null=True,
                                            help_text="Risk score based on off-taker rating")
    overall_risk_score = models.FloatField(blank=True, null=True,
                                          help_text="Aggregate risk score for the project")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Type field for inheritance
    type = models.CharField(max_length=50, default='project')
    
    def __str__(self):
        return f"{self.name} ({self.capacity_mw} MW {self.project_type})"


class SolarProject(Project):
    """Model for solar energy projects"""
    
    # Panel details
    panel_type = models.CharField(max_length=50, blank=True, null=True, 
                                 help_text="e.g., 'monocrystalline', 'polycrystalline', 'thin-film'")
    panel_efficiency = models.FloatField(blank=True, null=True, help_text="efficiency percentage")
    num_panels = models.IntegerField(blank=True, null=True)
    panel_capacity_w = models.FloatField(blank=True, null=True, help_text="capacity per panel in watts")
    
    # Location details (inherited latitude/longitude from Project)
    tilt_angle = models.FloatField(blank=True, null=True, help_text="for fixed-tilt systems")
    azimuth = models.FloatField(blank=True, null=True, help_text="orientation")
    
    # Performance parameters
    degradation_rate = models.FloatField(default=0.5, help_text="annual degradation rate (%)")
    performance_ratio = models.FloatField(default=0.75, help_text="ratio of actual to theoretical energy output")
    
    # Physical parameters
    land_area_acres = models.FloatField(blank=True, null=True, help_text="land area in acres")
    
    # Technical details
    tracking_type = models.CharField(max_length=50, default='fixed', 
                                    help_text="fixed, single-axis, dual-axis")
    
    def save(self, *args, **kwargs):
        self.type = 'solar'
        self.project_type = 'solar'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Solar: {self.name} ({self.capacity_mw} MW)"


class CashFlow(models.Model):
    """Model for tracking project cash flows"""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cash_flows')
    year = models.IntegerField(help_text="0 for initial investment, 1-N for operational years")
    
    # Financial flows
    capex = models.FloatField(default=0.0, help_text="Capital expenditures (negative)")
    revenue = models.FloatField(default=0.0, help_text="Revenue from electricity sales")
    opex = models.FloatField(default=0.0, help_text="Operating expenses (negative)")
    maintenance = models.FloatField(default=0.0, help_text="Maintenance costs (negative)")
    insurance = models.FloatField(default=0.0, help_text="Insurance costs (negative)")
    taxes = models.FloatField(default=0.0, help_text="Taxes (negative)")
    debt_service = models.FloatField(default=0.0, help_text="Debt payments (negative)")
    incentives = models.FloatField(default=0.0, help_text="Tax credits, grants, etc. (positive)")
    salvage_value = models.FloatField(default=0.0, help_text="End-of-life value")
    
    # Energy data
    energy_production_mwh = models.FloatField(default=0.0, help_text="Energy produced in MWh")
    
    # Cash flow totals
    net_cash_flow = models.FloatField(default=0.0, help_text="Net cash flow for the period")
    cumulative_cash_flow = models.FloatField(default=0.0, help_text="Running total of cash flows")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.project.name} - Year {self.year}"
    
    class Meta:
        ordering = ['project', 'year']


class FinancialMetric(models.Model):
    """Model for storing calculated financial metrics for a project"""
    
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='financial_metrics')
    
    # Key metrics
    npv = models.FloatField(blank=True, null=True, help_text="Net Present Value")
    irr = models.FloatField(blank=True, null=True, help_text="Internal Rate of Return (%)")
    payback_period = models.FloatField(blank=True, null=True, help_text="Payback period in years")
    lcoe = models.FloatField(blank=True, null=True, help_text="Levelized Cost of Energy ($/MWh)")
    
    # Advanced metrics
    mirr = models.FloatField(blank=True, null=True, help_text="Modified Internal Rate of Return (%)")
    profitability_index = models.FloatField(blank=True, null=True, help_text="Profitability Index")
    debt_service_coverage_ratio = models.FloatField(blank=True, null=True, help_text="DSCR")
    
    # Input parameters
    discount_rate = models.FloatField(blank=True, null=True, help_text="Discount rate used (%)")
    inflation_rate = models.FloatField(blank=True, null=True, help_text="Inflation rate used (%)")
    debt_ratio = models.FloatField(blank=True, null=True, help_text="Debt to total capital ratio")
    interest_rate = models.FloatField(blank=True, null=True, help_text="Interest rate on debt (%)")
    
    # PPA details
    ppa_price = models.FloatField(blank=True, null=True, help_text="Power Purchase Agreement price ($/MWh)")
    ppa_escalation = models.FloatField(blank=True, null=True, help_text="Annual escalation rate for PPA (%)")
    ppa_term = models.IntegerField(blank=True, null=True, help_text="PPA term in years")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Metrics for {self.project.name}"


class GeospatialLayer(models.Model):
    """Model for storing geospatial layers for mapping"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    layer_type = models.CharField(max_length=50, help_text="e.g., 'solar_resource', 'grid', 'population'")
    source_url = models.URLField(blank=True, null=True, help_text="URL to the data source")
    enabled = models.BooleanField(default=True)
    
    # Visualization settings
    color_scale = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'viridis', 'plasma'")
    opacity = models.FloatField(default=0.7)
    
    # Bounds (if applicable)
    min_lat = models.FloatField(blank=True, null=True)
    max_lat = models.FloatField(blank=True, null=True)
    min_lon = models.FloatField(blank=True, null=True)
    max_lon = models.FloatField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']