# Generated by Django 5.2 on 2025-04-29 09:58

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GeospatialLayer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('layer_type', models.CharField(help_text="e.g., 'solar_resource', 'grid', 'population'", max_length=50)),
                ('source_url', models.URLField(blank=True, help_text='URL to the data source', null=True)),
                ('enabled', models.BooleanField(default=True)),
                ('color_scale', models.CharField(blank=True, help_text="e.g., 'viridis', 'plasma'", max_length=100, null=True)),
                ('opacity', models.FloatField(default=0.7)),
                ('min_lat', models.FloatField(blank=True, null=True)),
                ('max_lat', models.FloatField(blank=True, null=True)),
                ('min_lon', models.FloatField(blank=True, null=True)),
                ('max_lon', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('capacity_mw', models.FloatField(help_text='Capacity in megawatts')),
                ('project_type', models.CharField(help_text="e.g., 'solar', 'wind'", max_length=50)),
                ('capex', models.FloatField(blank=True, help_text='Capital expenditure (total)', null=True)),
                ('capex_per_mw', models.FloatField(blank=True, help_text='Capital expenditure per MW', null=True)),
                ('opex_per_year', models.FloatField(blank=True, help_text='Operating expenditure per year', null=True)),
                ('opex_per_mw', models.FloatField(blank=True, help_text='Operating expenditure per MW per year', null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('commercial_operation_date', models.DateField(blank=True, null=True)),
                ('expected_lifetime_years', models.IntegerField(default=25)),
                ('status', models.CharField(default='planning', help_text='planning, construction, operational, decommissioned', max_length=50)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(default='project', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='SolarProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='projects.project')),
                ('panel_type', models.CharField(blank=True, help_text="e.g., 'monocrystalline', 'polycrystalline', 'thin-film'", max_length=50, null=True)),
                ('panel_efficiency', models.FloatField(blank=True, help_text='efficiency percentage', null=True)),
                ('num_panels', models.IntegerField(blank=True, null=True)),
                ('panel_capacity_w', models.FloatField(blank=True, help_text='capacity per panel in watts', null=True)),
                ('tilt_angle', models.FloatField(blank=True, help_text='for fixed-tilt systems', null=True)),
                ('azimuth', models.FloatField(blank=True, help_text='orientation', null=True)),
                ('degradation_rate', models.FloatField(default=0.5, help_text='annual degradation rate (%)')),
                ('performance_ratio', models.FloatField(default=0.75, help_text='ratio of actual to theoretical energy output')),
                ('land_area_acres', models.FloatField(blank=True, help_text='land area in acres', null=True)),
                ('tracking_type', models.CharField(default='fixed', help_text='fixed, single-axis, dual-axis', max_length=50)),
            ],
            bases=('projects.project',),
        ),
        migrations.CreateModel(
            name='FinancialMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('npv', models.FloatField(blank=True, help_text='Net Present Value', null=True)),
                ('irr', models.FloatField(blank=True, help_text='Internal Rate of Return (%)', null=True)),
                ('payback_period', models.FloatField(blank=True, help_text='Payback period in years', null=True)),
                ('lcoe', models.FloatField(blank=True, help_text='Levelized Cost of Energy ($/MWh)', null=True)),
                ('mirr', models.FloatField(blank=True, help_text='Modified Internal Rate of Return (%)', null=True)),
                ('profitability_index', models.FloatField(blank=True, help_text='Profitability Index', null=True)),
                ('debt_service_coverage_ratio', models.FloatField(blank=True, help_text='DSCR', null=True)),
                ('discount_rate', models.FloatField(blank=True, help_text='Discount rate used (%)', null=True)),
                ('inflation_rate', models.FloatField(blank=True, help_text='Inflation rate used (%)', null=True)),
                ('debt_ratio', models.FloatField(blank=True, help_text='Debt to total capital ratio', null=True)),
                ('interest_rate', models.FloatField(blank=True, help_text='Interest rate on debt (%)', null=True)),
                ('ppa_price', models.FloatField(blank=True, help_text='Power Purchase Agreement price ($/MWh)', null=True)),
                ('ppa_escalation', models.FloatField(blank=True, help_text='Annual escalation rate for PPA (%)', null=True)),
                ('ppa_term', models.IntegerField(blank=True, help_text='PPA term in years', null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='financial_metrics', to='projects.project')),
            ],
        ),
        migrations.CreateModel(
            name='CashFlow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(help_text='0 for initial investment, 1-N for operational years')),
                ('capex', models.FloatField(default=0.0, help_text='Capital expenditures (negative)')),
                ('revenue', models.FloatField(default=0.0, help_text='Revenue from electricity sales')),
                ('opex', models.FloatField(default=0.0, help_text='Operating expenses (negative)')),
                ('maintenance', models.FloatField(default=0.0, help_text='Maintenance costs (negative)')),
                ('insurance', models.FloatField(default=0.0, help_text='Insurance costs (negative)')),
                ('taxes', models.FloatField(default=0.0, help_text='Taxes (negative)')),
                ('debt_service', models.FloatField(default=0.0, help_text='Debt payments (negative)')),
                ('incentives', models.FloatField(default=0.0, help_text='Tax credits, grants, etc. (positive)')),
                ('salvage_value', models.FloatField(default=0.0, help_text='End-of-life value')),
                ('energy_production_mwh', models.FloatField(default=0.0, help_text='Energy produced in MWh')),
                ('net_cash_flow', models.FloatField(default=0.0, help_text='Net cash flow for the period')),
                ('cumulative_cash_flow', models.FloatField(default=0.0, help_text='Running total of cash flows')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cash_flows', to='projects.project')),
            ],
            options={
                'ordering': ['project', 'year'],
            },
        ),
    ]
