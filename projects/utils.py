"""
Utility functions for the Energy Finance application.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Project, SolarProject, CashFlow, FinancialMetric


def generate_project_templates():
    """
    Generate template Excel and CSV files for project data import.
    
    Returns:
        tuple: Paths to the generated Excel and CSV files
    """
    # Create a DataFrame with sample data and all required columns
    sample_data = {
        'name': ['Example Solar Project'],
        'description': ['A 10 MW solar PV installation in Arizona'],
        'location': ['Phoenix, AZ'],
        'capacity_mw': [10.0],
        'project_type': ['solar'],
        'capex': [15000000.0],
        'capex_per_mw': [1500000.0],
        'opex_per_year': [150000.0],
        'opex_per_mw': [15000.0],
        'start_date': [datetime.now().strftime('%Y-%m-%d')],
        'commercial_operation_date': [(datetime.now()).strftime('%Y-%m-%d')],
        'expected_lifetime_years': [25],
        'status': ['planning'],
        'panel_type': ['monocrystalline'],
        'panel_efficiency': [0.22],
        'num_panels': [30000],
        'panel_capacity_w': [400.0],
        'latitude': [33.4484],
        'longitude': [-112.0740],
        'tilt_angle': [30.0],
        'azimuth': [180.0],
        'degradation_rate': [0.5],
        'performance_ratio': [0.75],
        'land_area_acres': [50.0],
        'tracking_type': ['fixed']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create the templates directory if it doesn't exist
    templates_dir = os.path.join(settings.MEDIA_ROOT, 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Save templates
    excel_path = os.path.join(templates_dir, 'solar_project_template.xlsx')
    csv_path = os.path.join(templates_dir, 'solar_project_template.csv')
    
    df.to_excel(excel_path, index=False)
    df.to_csv(csv_path, index=False)
    
    return excel_path, csv_path


def calculate_financial_metrics(project, discount_rate=0.08, inflation_rate=0.025, debt_ratio=0.7, interest_rate=0.05):
    """
    Calculate financial metrics for a project.
    
    Parameters:
    - project: A Project instance
    - discount_rate: Discount rate (default 8%)
    - inflation_rate: Inflation rate (default 2.5%)
    - debt_ratio: Debt to capital ratio (default 70%)
    - interest_rate: Interest rate on debt (default 5%)
    
    Returns: FinancialMetric instance
    """
    # Get or create a financial metric instance for this project
    financial_metric, created = FinancialMetric.objects.get_or_create(project=project)
    
    # Set input parameters
    financial_metric.discount_rate = discount_rate
    financial_metric.inflation_rate = inflation_rate
    financial_metric.debt_ratio = debt_ratio
    financial_metric.interest_rate = interest_rate
    
    # Get all cash flows for this project, ordered by year
    cash_flows = project.cash_flows.all().order_by('year')
    
    if not cash_flows:
        # Generate cash flows if none exist
        _generate_cash_flows(project, discount_rate, inflation_rate, debt_ratio, interest_rate)
        cash_flows = project.cash_flows.all().order_by('year')
    
    # Extract cash flow data for calculations
    years = [cf.year for cf in cash_flows]
    net_cash_flows = [cf.net_cash_flow for cf in cash_flows]
    
    if not net_cash_flows or all(ncf == 0 for ncf in net_cash_flows):
        # Default values if we can't calculate
        financial_metric.npv = 0
        financial_metric.irr = 0
        financial_metric.payback_period = project.expected_lifetime_years
        financial_metric.lcoe = 0
        financial_metric.mirr = 0
        financial_metric.profitability_index = 0
        financial_metric.debt_service_coverage_ratio = 0
        financial_metric.save()
        return financial_metric
    
    # Calculate NPV
    npv = _calculate_npv(net_cash_flows, discount_rate)
    financial_metric.npv = npv
    
    # Calculate IRR
    try:
        irr = np.irr(net_cash_flows) * 100  # Convert to percentage
        if np.isnan(irr) or not np.isfinite(irr):
            irr = 0
        financial_metric.irr = irr
    except:
        financial_metric.irr = 0
    
    # Calculate payback period
    cum_cash_flows = np.cumsum(net_cash_flows)
    if cum_cash_flows[-1] <= 0:
        # Project never pays back
        payback_period = project.expected_lifetime_years
    else:
        payback_indices = np.where(cum_cash_flows > 0)[0]
        if len(payback_indices) > 0:
            payback_idx = payback_indices[0]
            # Simple linear interpolation for fractional year
            if payback_idx > 0:
                prev_cf = cum_cash_flows[payback_idx - 1]
                curr_cf = cum_cash_flows[payback_idx]
                if curr_cf - prev_cf != 0:
                    fraction = -prev_cf / (curr_cf - prev_cf)
                else:
                    fraction = 0
                payback_period = payback_idx - 1 + fraction
            else:
                payback_period = payback_idx
        else:
            payback_period = project.expected_lifetime_years
    
    financial_metric.payback_period = payback_period
    
    # Calculate LCOE (Levelized Cost of Energy)
    total_energy_mwh = sum(cf.energy_production_mwh for cf in cash_flows)
    total_costs = sum(cf.capex + cf.opex + cf.maintenance + cf.insurance for cf in cash_flows)
    if total_energy_mwh > 0:
        lcoe = total_costs / total_energy_mwh
    else:
        lcoe = 0
    financial_metric.lcoe = lcoe
    
    # Calculate MIRR
    try:
        # Separate positive and negative cash flows
        pos_flows = [max(cf, 0) for cf in net_cash_flows]
        neg_flows = [min(cf, 0) for cf in net_cash_flows]
        
        # Replace zeros with a small number to avoid division by zero
        neg_flows = [-0.000001 if nf == 0 else nf for nf in neg_flows]
        
        # Calculate MIRR
        n = len(net_cash_flows) - 1  # Number of periods
        neg_pv = np.npv(interest_rate, neg_flows)
        pos_fv = np.sum(np.array(pos_flows) * np.power(1 + discount_rate, np.arange(n + 1)))
        
        if neg_pv != 0 and pos_fv > 0:
            mirr = (pow(pos_fv / -neg_pv, 1 / n) - 1) * 100
            if np.isnan(mirr) or not np.isfinite(mirr) or mirr > 100:
                mirr = 0
        else:
            mirr = 0
        financial_metric.mirr = mirr
    except:
        financial_metric.mirr = 0
    
    # Calculate Profitability Index
    initial_investment = abs(net_cash_flows[0]) if net_cash_flows[0] < 0 else 1
    if initial_investment > 0:
        profitability_index = (npv + initial_investment) / initial_investment
    else:
        profitability_index = 0
    financial_metric.profitability_index = profitability_index
    
    # Calculate Debt Service Coverage Ratio
    annual_debt_service = sum(cf.debt_service for cf in cash_flows) / len(cash_flows)
    if annual_debt_service != 0:
        operating_income = sum(cf.revenue for cf in cash_flows) - sum(cf.opex for cf in cash_flows)
        dscr = operating_income / abs(annual_debt_service)
    else:
        dscr = 0
    financial_metric.debt_service_coverage_ratio = dscr
    
    financial_metric.save()
    return financial_metric


def _calculate_npv(cash_flows, discount_rate):
    """Calculate Net Present Value of cash flows"""
    try:
        npv = np.npv(discount_rate, cash_flows)
        if np.isnan(npv) or not np.isfinite(npv):
            return 0
        return npv
    except:
        return 0


def _generate_cash_flows(project, discount_rate=0.08, inflation_rate=0.025, debt_ratio=0.7, interest_rate=0.05):
    """Generate cash flow projections for a project"""
    # Clear existing cash flows
    project.cash_flows.all().delete()
    
    lifetime = project.expected_lifetime_years
    
    # Year 0: Initial investment
    initial_capex = project.capex if project.capex else (project.capex_per_mw * project.capacity_mw if project.capex_per_mw else 0)
    
    # Calculate debt and equity portions
    debt_amount = initial_capex * debt_ratio
    equity_amount = initial_capex * (1 - debt_ratio)
    
    # Calculate annual debt service (assuming equal payments over 15 years or project lifetime)
    loan_term = min(15, lifetime)
    if debt_amount > 0 and interest_rate > 0:
        annual_debt_service = -debt_amount * (interest_rate * (1 + interest_rate) ** loan_term) / ((1 + interest_rate) ** loan_term - 1)
    else:
        annual_debt_service = 0
    
    # Year 0 cash flow
    CashFlow.objects.create(
        project=project,
        year=0,
        capex=-initial_capex,
        net_cash_flow=-equity_amount,  # Only equity portion affects cash flow
        cumulative_cash_flow=-equity_amount
    )
    
    # Years 1 to end of life
    cumulative_cash_flow = -equity_amount
    
    for year in range(1, lifetime + 1):
        # Calculate energy production
        if isinstance(project, SolarProject):
            energy_production = estimate_energy_production(project, year)
        else:
            # Simple estimation for non-solar projects
            energy_production = project.capacity_mw * 8760 * 0.3  # Assuming 30% capacity factor
        
        # Annual O&M costs with inflation
        annual_opex = project.opex_per_year if project.opex_per_year else (project.opex_per_mw * project.capacity_mw if project.opex_per_mw else 0)
        annual_opex *= (1 + inflation_rate) ** (year - 1)
        
        # Maintenance and insurance (simplified)
        maintenance = -annual_opex * 0.3  # 30% of OPEX for maintenance
        insurance = -annual_opex * 0.1    # 10% of OPEX for insurance
        
        # Revenue (simplified)
        # Assuming $50/MWh base power price with inflation
        ppa_price = 50 * (1 + inflation_rate) ** (year - 1)
        revenue = energy_production * ppa_price
        
        # Debt service (only until loan term)
        debt_service = annual_debt_service if year <= loan_term else 0
        
        # Tax calculation (simplified)
        taxable_income = revenue + annual_opex + maintenance + insurance + debt_service * 0.5  # Assume 50% of interest is deductible
        taxes = -taxable_income * 0.21 if taxable_income > 0 else 0  # Simplified corporate tax rate
        
        # Salvage value in final year
        salvage_value = initial_capex * 0.1 if year == lifetime else 0  # Assume 10% salvage value
        
        # Net cash flow
        net_cash_flow = revenue + annual_opex + maintenance + insurance + debt_service + taxes + salvage_value
        
        # Cumulative cash flow
        cumulative_cash_flow += net_cash_flow
        
        # Create cash flow record
        CashFlow.objects.create(
            project=project,
            year=year,
            revenue=revenue,
            opex=annual_opex,
            maintenance=maintenance,
            insurance=insurance,
            debt_service=debt_service,
            taxes=taxes,
            salvage_value=salvage_value,
            energy_production_mwh=energy_production,
            net_cash_flow=net_cash_flow,
            cumulative_cash_flow=cumulative_cash_flow
        )
    
    return project.cash_flows.all()


def estimate_energy_production(solar_project, year):
    """
    Estimate energy production for a solar project in a given year.
    
    Parameters:
    - solar_project: A SolarProject instance
    - year: Year of operation (1-based, where 1 is the first year)
    
    Returns: Estimated energy production in MWh
    """
    # Basic calculation without site-specific data
    capacity_mw = solar_project.capacity_mw
    hours_per_year = 8760
    
    # Base capacity factor based on tracking type
    base_capacity_factor = {
        'fixed': 0.20,
        'single-axis': 0.25,
        'dual-axis': 0.30
    }.get(solar_project.tracking_type, 0.20)
    
    # Adjust for degradation over time
    degradation_rate = solar_project.degradation_rate / 100 if solar_project.degradation_rate else 0.005
    degradation_factor = (1 - degradation_rate) ** (year - 1)
    
    # Adjust for performance ratio
    performance_ratio = solar_project.performance_ratio if solar_project.performance_ratio else 0.75
    
    # Calculate annual energy production in MWh
    energy_production = capacity_mw * hours_per_year * base_capacity_factor * degradation_factor * performance_ratio
    
    return energy_production


def import_project_from_file(file):
    """
    Import project data from a CSV or Excel file.
    
    Parameters:
    - file: The uploaded file object
    
    Returns:
        tuple: (success, message, project)
    """
    try:
        # Determine file extension
        file_ext = file.name.split('.')[-1].lower()
        
        # Read data based on file type
        if file_ext == 'csv':
            df = pd.read_csv(file)
        elif file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(file)
        else:
            return False, "Unsupported file format. Please upload a CSV or Excel file.", None
        
        # Check if dataframe is empty
        if df.empty:
            return False, "The uploaded file contains no data.", None
        
        # Check required columns
        required_columns = ['name', 'capacity_mw', 'project_type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}", None
        
        # Get first row of data
        row = df.iloc[0]
        
        # Determine project type
        project_type = row.get('project_type', 'solar').lower()
        
        # Create project based on type
        if project_type == 'solar':
            project = SolarProject()
        else:
            project = Project()
        
        # Set project attributes from dataframe
        for column in df.columns:
            # Skip NaN values
            if pd.isna(row[column]):
                continue
            
            # Check if the column exists in the model
            if hasattr(project, column):
                setattr(project, column, row[column])
        
        # Ensure project_type is set
        project.project_type = project_type
        
        # Save the project
        project.save()
        
        return True, "Project imported successfully.", project
        
    except Exception as e:
        return False, f"Error importing project: {str(e)}", None


def calculate_risk_scores(project):
    """
    Calculate risk scores based on risk assessment factors.
    
    Parameters:
    - project: A Project instance
    
    Returns: Updated Project instance with risk scores
    """
    # Country risk score (based on home/target country)
    country_risk = _calculate_country_risk(project.home_country, project.target_country)
    project.country_risk_score = country_risk
    
    # Technology risk score
    tech_risk = _calculate_technology_risk(project.project_type, project.technology_risk_factor)
    project.technology_risk_score = tech_risk
    
    # Project status risk score
    status_risk = _calculate_status_risk(project.project_status_risk)
    project.status_risk_score = status_risk
    
    # Off-taker risk score
    off_taker_risk = _calculate_off_taker_risk(project.off_taker_rating)
    project.off_taker_risk_score = off_taker_risk
    
    # Calculate overall risk score (weighted average)
    weights = {
        'country': 0.25,
        'technology': 0.25,
        'status': 0.20,
        'off_taker': 0.30
    }
    
    overall_risk = (
        weights['country'] * (country_risk or 0) +
        weights['technology'] * (tech_risk or 0) +
        weights['status'] * (status_risk or 0) +
        weights['off_taker'] * (off_taker_risk or 0)
    )
    
    project.overall_risk_score = overall_risk
    project.save()
    
    return project


def _calculate_country_risk(home_country, target_country):
    """Calculate risk score based on home/target country."""
    # Risk scores based on regions/countries (1-5 scale, where 5 is highest risk)
    country_risk_map = {
        # Low risk countries
        'united states': 1.0,
        'usa': 1.0,
        'canada': 1.0,
        'australia': 1.0,
        'germany': 1.0,
        'united kingdom': 1.0,
        'uk': 1.0,
        'france': 1.0,
        'japan': 1.0,
        'south korea': 1.0,
        'singapore': 1.0,
        
        # Medium risk countries
        'mexico': 2.0,
        'brazil': 2.5,
        'china': 2.5,
        'india': 2.5,
        'south africa': 2.5,
        'turkey': 2.5,
        'thailand': 2.0,
        'malaysia': 2.0,
        'indonesia': 2.5,
        'chile': 2.0,
        
        # Higher risk countries
        'nigeria': 3.5,
        'egypt': 3.0,
        'pakistan': 3.5,
        'ukraine': 3.5,
        'iraq': 4.0,
        'venezuela': 4.0,
        'libya': 4.5,
        'afghanistan': 5.0,
        'syria': 5.0,
        'yemen': 5.0,
    }
    
    # Default risk if countries not specified
    if not home_country and not target_country:
        return 2.5  # Medium risk
    
    # Get risk scores for home and target countries
    home_risk = country_risk_map.get(str(home_country).lower(), 2.5) if home_country else 2.5
    target_risk = country_risk_map.get(str(target_country).lower(), 3.0) if target_country else 3.0
    
    # Calculate weighted average (target country has more impact)
    country_risk = (home_risk * 0.3) + (target_risk * 0.7)
    
    return country_risk


def _calculate_technology_risk(project_type, tech_risk_factor=None):
    """Calculate risk score based on technology type and risk factor."""
    # Base technology risk by project type (1-5 scale)
    base_tech_risk = {
        'solar': 1.5,  # Solar is relatively low risk
        'wind': 1.8,   # Wind slightly higher
        'hydro': 2.2,  # Hydro has more variables
        'biomass': 2.5,
        'geothermal': 2.8,
        'tidal': 3.5,  # Emerging technologies higher risk
        'wave': 3.8,
        'hydrogen': 4.0,
    }.get(str(project_type).lower(), 3.0)  # Default for unknown types
    
    # If tech risk factor is provided, use it to adjust the base risk
    if tech_risk_factor is not None:
        # Ensure tech_risk_factor is between 0 and 1
        factor = min(max(float(tech_risk_factor), 0), 1)
        
        # Scale factor to have appropriate impact (1-5 scale)
        tech_risk = base_tech_risk * (1 + factor)
        
        # Ensure final risk score is in range 1-5
        tech_risk = min(max(tech_risk, 1.0), 5.0)
        
        return tech_risk
    
    return base_tech_risk


def _calculate_status_risk(project_status):
    """Calculate risk score based on project development status."""
    # Risk scores by project status (1-5 scale)
    status_risk_map = {
        'early_stage': 4.5,     # Highest risk
        'development': 3.5,
        'construction': 2.5,
        'operational': 1.5      # Lowest risk
    }
    
    return status_risk_map.get(project_status, 3.0)  # Default for unknown status


def _calculate_off_taker_risk(off_taker_rating):
    """Calculate risk score based on off-taker credit rating."""
    # Risk scores by credit rating (1-5 scale)
    rating_risk_map = {
        'AAA': 1.0,
        'AA+': 1.1,
        'AA': 1.2,
        'AA-': 1.3,
        'A+': 1.5,
        'A': 1.7,
        'A-': 1.9,
        'BBB+': 2.1,
        'BBB': 2.3,
        'BBB-': 2.5,
        'BB+': 2.7,
        'BB': 2.9,
        'BB-': 3.1,
        'B+': 3.3,
        'B': 3.5,
        'B-': 3.7,
        'CCC+': 4.0,
        'CCC': 4.3,
        'CCC-': 4.5,
        'CC': 4.7,
        'C': 4.9,
        'D': 5.0,
    }
    
    if not off_taker_rating:
        return 3.0  # Default medium risk
    
    return rating_risk_map.get(off_taker_rating.upper(), 3.0)