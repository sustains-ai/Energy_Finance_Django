"""
Solar radiation service for the Energy Finance application.
Interacts with NREL's PVWatts API to get solar production estimates.
"""

import os
import json
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SolarRadiationService:
    """Service to interact with NREL's PVWatts API for solar radiation data"""
    
    def __init__(self):
        self.api_key = os.environ.get('NREL_API_KEY', None)
        if not self.api_key:
            logger.warning("NREL API key is not set in environment variables")
    
    def get_solar_data(self, latitude, longitude, system_capacity=1, azimuth=180, tilt=40, 
                      array_type=1, module_type=1, losses=10, timeframe='hourly'):
        """
        Get solar production estimates from NREL's PVWatts API
        
        Parameters:
        - latitude: Latitude of the location
        - longitude: Longitude of the location
        - system_capacity: System capacity in kW (default: 1)
        - azimuth: Array azimuth in degrees (default: 180, south-facing)
        - tilt: Array tilt in degrees (default: 40)
        - array_type: Array type (default: 1, fixed open rack)
        - module_type: Module type (default: 1, standard)
        - losses: System losses in percent (default: 10)
        - timeframe: Timeframe for results (default: 'hourly')
        
        Returns: Dictionary with solar data
        """
        if not self.api_key:
            raise ValueError("NREL API key is not set")
        
        url = f"https://developer.nrel.gov/api/pvwatts/v8.json"
        params = {
            'api_key': self.api_key,
            'lat': latitude,
            'lon': longitude,
            'system_capacity': system_capacity,
            'azimuth': azimuth,
            'tilt': tilt,
            'array_type': array_type,
            'module_type': module_type,
            'losses': losses,
            'timeframe': timeframe
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching solar data from NREL API: {str(e)}")
            raise
    
    def get_daily_solar_data(self, latitude, longitude, system_capacity=1000.0):
        """
        Get daily average solar production estimates
        
        Parameters:
        - latitude: Latitude of the location
        - longitude: Longitude of the location
        - system_capacity: System capacity in kW (default: 1000.0)
        
        Returns: List of daily averages [{day: 1, avgPower: 123.45}, ...]
        """
        try:
            # Get hourly data from NREL API
            data = self.get_solar_data(latitude, longitude, system_capacity=1)
            
            if 'errors' in data:
                error_message = '; '.join(data['errors'])
                logger.error(f"NREL API returned errors: {error_message}")
                raise ValueError(f"NREL API error: {error_message}")
            
            # Extract AC power output (in W) and convert to kW
            ac_power = [power * system_capacity / 1000 for power in data['outputs']['ac']]
            
            # Aggregate to daily averages (8760 hours → 365 days)
            daily_data = []
            for day in range(365):
                start_hour = day * 24
                end_hour = start_hour + 24
                day_power = ac_power[start_hour:end_hour]
                avg_power = sum(day_power) / len(day_power) if day_power else 0
                
                daily_data.append({
                    'day': day + 1,
                    'avgPower': avg_power
                })
            
            return daily_data
            
        except Exception as e:
            logger.error(f"Error in get_daily_solar_data: {str(e)}")
            raise
    
    def get_monthly_solar_data(self, latitude, longitude, system_capacity=1000.0):
        """
        Get monthly average solar production estimates
        
        Parameters:
        - latitude: Latitude of the location
        - longitude: Longitude of the location
        - system_capacity: System capacity in kW (default: 1000.0)
        
        Returns: List of monthly averages [{month: 'January', avgPower: 123.45}, ...]
        """
        daily_data = self.get_daily_solar_data(latitude, longitude, system_capacity)
        
        # Define month ranges
        month_ranges = []
        current_year = datetime.now().year
        for month in range(1, 13):
            if month == 12:
                next_month = 1
                next_year = current_year + 1
            else:
                next_month = month + 1
                next_year = current_year
            
            start_date = datetime(current_year, month, 1)
            end_date = datetime(next_year, next_month, 1)
            days_in_month = (end_date - start_date).days
            
            month_ranges.append({
                'name': start_date.strftime('%B'),
                'start_day': start_date.timetuple().tm_yday,
                'days': days_in_month
            })
        
        # Calculate monthly averages
        monthly_data = []
        for month_info in month_ranges:
            month_start = month_info['start_day'] - 1  # Adjust for 0-based indexing
            month_days = daily_data[month_start:month_start + month_info['days']]
            
            if month_days:
                avg_power = sum(day['avgPower'] for day in month_days) / len(month_days)
                total_energy = avg_power * 24 * month_info['days']  # kWh for the month
                
                monthly_data.append({
                    'month': month_info['name'],
                    'avgPower': avg_power,
                    'totalEnergy': total_energy
                })
        
        return monthly_data
    
    def get_annual_production(self, latitude, longitude, system_capacity=1000.0):
        """
        Get annual energy production estimate
        
        Parameters:
        - latitude: Latitude of the location
        - longitude: Longitude of the location
        - system_capacity: System capacity in kW (default: 1000.0)
        
        Returns: Dictionary with annual energy in kWh and capacity factor
        """
        try:
            # Get hourly data from NREL API
            data = self.get_solar_data(latitude, longitude, system_capacity=1)
            
            # Calculate total annual energy (kWh)
            ac_annual = data['outputs']['ac_annual'] * system_capacity
            
            # Calculate capacity factor
            capacity_factor = data['outputs'].get('capacity_factor', None)
            
            return {
                'annual_energy': ac_annual,
                'capacity_factor': capacity_factor
            }
            
        except Exception as e:
            logger.error(f"Error in get_annual_production: {str(e)}")
            raise