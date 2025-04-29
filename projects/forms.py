"""
Forms for the Energy Finance application.
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div
from .models import Project, SolarProject, FinancialMetric


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'location', 'capacity_mw', 'project_type',
            'capex', 'capex_per_mw', 'opex_per_year', 'opex_per_mw',
            'start_date', 'commercial_operation_date', 'expected_lifetime_years',
            'status',
            # Risk assessment fields
            'home_country', 'target_country', 'target_state_province',
            'technology_risk_factor', 'project_status_risk', 'asset_life_years',
            'off_taker_rating', 'funding_leverage'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'commercial_operation_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('project_type', css_class='col-md-3'),
                Column('status', css_class='col-md-3'),
                css_class='form-row'
            ),
            Row(
                Column('description', css_class='col-md-12'),
                css_class='form-row'
            ),
            Row(
                Column('location', css_class='col-md-6'),
                Column('capacity_mw', css_class='col-md-6'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Financial Parameters</h4>"),
            Row(
                Column('capex', css_class='col-md-3'),
                Column('capex_per_mw', css_class='col-md-3'),
                Column('opex_per_year', css_class='col-md-3'),
                Column('opex_per_mw', css_class='col-md-3'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Project Timeline</h4>"),
            Row(
                Column('start_date', css_class='col-md-4'),
                Column('commercial_operation_date', css_class='col-md-4'),
                Column('expected_lifetime_years', css_class='col-md-4'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Risk Assessment</h4>"),
            HTML("<h5 class='mt-3'>Investment Regions</h5>"),
            Row(
                Column('home_country', css_class='col-md-4'),
                Column('target_country', css_class='col-md-4'),
                Column('target_state_province', css_class='col-md-4'),
                css_class='form-row'
            ),
            HTML("<h5 class='mt-3'>Project Risk Factors</h5>"),
            Row(
                Column('technology_risk_factor', css_class='col-md-3'),
                Column('project_status_risk', css_class='col-md-3'),
                Column('asset_life_years', css_class='col-md-3'),
                Column('funding_leverage', css_class='col-md-3'),
                css_class='form-row'
            ),
            Row(
                Column('off_taker_rating', css_class='col-md-12'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', 'Save Project', css_class='btn btn-primary'),
                HTML('<a href="{% url \'projects:project_list\' %}" class="btn btn-secondary ms-3">Cancel</a>'),
                css_class='mt-4'
            )
        )


class SolarProjectForm(forms.ModelForm):
    """Form for creating and editing solar projects"""
    
    class Meta:
        model = SolarProject
        fields = [
            'name', 'description', 'location', 'capacity_mw', 'status',
            'capex', 'capex_per_mw', 'opex_per_year', 'opex_per_mw',
            'start_date', 'commercial_operation_date', 'expected_lifetime_years',
            'panel_type', 'panel_efficiency', 'num_panels', 'panel_capacity_w',
            'latitude', 'longitude', 'tilt_angle', 'azimuth',
            'degradation_rate', 'performance_ratio', 'land_area_acres', 'tracking_type',
            # Risk assessment fields
            'home_country', 'target_country', 'target_state_province',
            'technology_risk_factor', 'project_status_risk', 'asset_life_years',
            'off_taker_rating', 'funding_leverage'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'commercial_operation_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('status', css_class='col-md-4'),
                css_class='form-row'
            ),
            Row(
                Column('description', css_class='col-md-12'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Project Basics</h4>"),
            Row(
                Column('location', css_class='col-md-6'),
                Column('capacity_mw', css_class='col-md-6'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Financial Parameters</h4>"),
            Row(
                Column('capex', css_class='col-md-3'),
                Column('capex_per_mw', css_class='col-md-3'),
                Column('opex_per_year', css_class='col-md-3'),
                Column('opex_per_mw', css_class='col-md-3'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Solar Panel Details</h4>"),
            Row(
                Column('panel_type', css_class='col-md-3'),
                Column('panel_efficiency', css_class='col-md-3'),
                Column('num_panels', css_class='col-md-3'),
                Column('panel_capacity_w', css_class='col-md-3'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Location Details</h4>"),
            Row(
                Column('latitude', css_class='col-md-3'),
                Column('longitude', css_class='col-md-3'),
                Column('tilt_angle', css_class='col-md-3'),
                Column('azimuth', css_class='col-md-3'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Performance Parameters</h4>"),
            Row(
                Column('degradation_rate', css_class='col-md-3'),
                Column('performance_ratio', css_class='col-md-3'),
                Column('tracking_type', css_class='col-md-3'),
                Column('land_area_acres', css_class='col-md-3'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Project Timeline</h4>"),
            Row(
                Column('start_date', css_class='col-md-4'),
                Column('commercial_operation_date', css_class='col-md-4'),
                Column('expected_lifetime_years', css_class='col-md-4'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Risk Assessment</h4>"),
            HTML("<h5 class='mt-3'>Investment Regions</h5>"),
            Row(
                Column('home_country', css_class='col-md-4'),
                Column('target_country', css_class='col-md-4'),
                Column('target_state_province', css_class='col-md-4'),
                css_class='form-row'
            ),
            HTML("<h5 class='mt-3'>Project Risk Factors</h5>"),
            Row(
                Column('technology_risk_factor', css_class='col-md-3'),
                Column('project_status_risk', css_class='col-md-3'),
                Column('asset_life_years', css_class='col-md-3'),
                Column('funding_leverage', css_class='col-md-3'),
                css_class='form-row'
            ),
            Row(
                Column('off_taker_rating', css_class='col-md-12'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', 'Save Solar Project', css_class='btn btn-primary'),
                HTML('<a href="{% url \'projects:project_list\' %}" class="btn btn-secondary ms-3">Cancel</a>'),
                css_class='mt-4'
            )
        )


class FinancialMetricForm(forms.ModelForm):
    """Form for entering financial parameters for metric calculation"""
    
    class Meta:
        model = FinancialMetric
        fields = [
            'discount_rate', 'inflation_rate', 'debt_ratio', 'interest_rate',
            'ppa_price', 'ppa_escalation', 'ppa_term'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML("<h4>Financial Parameters</h4>"),
            Row(
                Column('discount_rate', css_class='col-md-3'),
                Column('inflation_rate', css_class='col-md-3'),
                Column('debt_ratio', css_class='col-md-3'),
                Column('interest_rate', css_class='col-md-3'),
                css_class='form-row'
            ),
            HTML("<h4 class='mt-4'>Power Purchase Agreement Details</h4>"),
            Row(
                Column('ppa_price', css_class='col-md-4'),
                Column('ppa_escalation', css_class='col-md-4'),
                Column('ppa_term', css_class='col-md-4'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', 'Calculate Metrics', css_class='btn btn-primary'),
                HTML('<a href="#" class="btn btn-secondary ms-3" onclick="window.history.back();">Cancel</a>'),
                css_class='mt-4'
            )
        )


class ProjectImportForm(forms.Form):
    """Form for importing project data from Excel or CSV"""
    file = forms.FileField(
        label="Import File",
        help_text="Select an Excel or CSV file with project data."
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            'file',
            Div(
                Submit('submit', 'Import Project', css_class='btn btn-primary'),
                HTML('<a href="{% url \'projects:project_list\' %}" class="btn btn-secondary ms-3">Cancel</a>'),
                css_class='mt-4'
            )
        )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = file.name.split('.')[-1].lower()
            if ext not in ['csv', 'xlsx', 'xls']:
                raise forms.ValidationError("Unsupported file format. Please upload a CSV or Excel file.")
        return file