import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class DataProcessor:
    """
    Class for processing climate, soil, and crop data for irrigation simulation
    """
    
    def __init__(self):
        self.climate_data = None
        self.soil_data = None
        self.kc_data = None
    
    def load_climate_data(self, file_path):
        """Load climate data from CSV file"""
        data = pd.read_csv(file_path)
        data['Date'] = pd.to_datetime(data['Date'])
        self.climate_data = data
        return data
    
    def load_soil_data(self, file_path):
        """Load soil data from CSV file"""
        data = pd.read_csv(file_path)
        self.soil_data = data
        return data
    
    def load_kc_data(self, file_path):
        """Load crop coefficient data from CSV file"""
        data = pd.read_csv(file_path)
        self.kc_data = data
        return data
    
    def filter_growing_season(self, year, start_month=10, end_month=3):
        """
        Filter climate data for the maize growing season (October to March)
        
        Parameters:
        year (int): Starting year of the growing season
        start_month (int): Starting month (default: 10 for October)
        end_month (int): Ending month (default: 3 for March)
        
        Returns:
        DataFrame: Filtered climate data for the growing season
        """
        if self.climate_data is None:
            raise ValueError("Climate data not loaded")
        
        start_date = pd.Timestamp(f"{year}-{start_month:02d}-01")
        
        # End date is in the next year
        end_year = year + 1 if end_month < start_month else year
        # Get the last day of the end month
        if end_month == 12:
            end_date = pd.Timestamp(f"{end_year}-12-31")
        else:
            next_month = end_month + 1
            next_month_year = end_year + 1 if next_month > 12 else end_year
            next_month = 1 if next_month > 12 else next_month
            end_date = pd.Timestamp(f"{next_month_year}-{next_month:02d}-01") - timedelta(days=1)
        
        season_data = self.climate_data[
            (self.climate_data['Date'] >= start_date) & 
            (self.climate_data['Date'] <= end_date)
        ].copy()
        
        # Add day after planting column
        season_data['Day'] = (season_data['Date'] - start_date).dt.days
        
        return season_data
    
    def get_kc_for_day(self, day):
        """
        Get crop coefficient (Kc) for a specific day after planting
        
        Parameters:
        day (int): Day after planting
        
        Returns:
        float: Crop coefficient value
        """
        if self.kc_data is not None:
            # Try to get Kc from loaded data
            closest_day = self.kc_data['Day After Planting'].astype(int)
            closest_day = closest_day[closest_day <= day].max()
            if not pd.isna(closest_day):
                kc = self.kc_data[self.kc_data['Day After Planting'].astype(int) == closest_day]['Kc'].values[0]
                return float(kc)
        
        # Default values if no data or day not found
        if day <= 25:
            return 0.3
        elif day <= 50:
            # Linear interpolation during development stage
            return 0.3 + (1.15 - 0.3) * (day - 25) / (50 - 25)
        elif day <= 90:
            return 1.15
        elif day <= 120:
            return 0.8
        else:
            return 0.8  # Use late season value for any days beyond 120
    
    def calculate_eto_hargreaves(self, tmax, tmin, solar_radiation):
        """
        Calculate reference evapotranspiration using Hargreaves method
        
        Parameters:
        tmax (float): Maximum temperature (°C)
        tmin (float): Minimum temperature (°C)
        solar_radiation (float): Solar radiation (MJ/m²/day)
        
        Returns:
        float: Reference evapotranspiration (mm/day)
        """
        tavg = (tmax + tmin) / 2
        t_range = tmax - tmin
        
        # Convert solar radiation from MJ/m²/day to mm/day equivalent
        # 1 MJ/m² ≈ 0.408 mm of water
        ra = solar_radiation * 0.408
        
        # Hargreaves equation
        eto = 0.0023 * (tavg + 17.8) * (t_range ** 0.5) * ra
        
        return max(0, eto)  # Ensure non-negative value