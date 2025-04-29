import pandas as pd
import numpy as np
from data_processor import DataProcessor

class IrrigationModel:
    """
    Class for simulating irrigation based on soil water balance
    """
    
    def __init__(self, field_capacity=150, wilting_point=75, irrigation_threshold=75):
        """
        Initialize the irrigation model
        
        Parameters:
        field_capacity (float): Field capacity of soil (mm/m)
        wilting_point (float): Wilting point of soil (mm/m)
        irrigation_threshold (float): Soil moisture threshold to trigger irrigation (mm/m)
        """
        self.field_capacity = field_capacity
        self.wilting_point = wilting_point
        self.irrigation_threshold = irrigation_threshold
        self.data_processor = DataProcessor()
    
    def simulate(self, climate_data, initial_moisture=None):
        """
        Run irrigation simulation based on climate data
        
        Parameters:
        climate_data (DataFrame): Climate data with required columns
        initial_moisture (float): Initial soil moisture (mm/m), defaults to 70% of field capacity
        
        Returns:
        DataFrame: Simulation results with soil moisture and irrigation
        """
        if initial_moisture is None:
            initial_moisture = 0.7 * self.field_capacity
        
        # Create a copy of the input data
        results = climate_data.copy()
        
        # Calculate ETo for each day
        results['ETo (mm)'] = results.apply(
            lambda row: self.data_processor.calculate_eto_hargreaves(
                row['T2M_MAX (°C)'], 
                row['T2M_MIN (°C)'], 
                row['ALLSKY_SFC_SW_DWN (MJ/m²)']
            ), 
            axis=1
        )
        
        # Get Kc for each day
        results['Kc'] = results['Day'].apply(self.data_processor.get_kc_for_day)
        
        # Calculate crop evapotranspiration
        results['ETc (mm)'] = results['ETo (mm)'] * results['Kc']
        
        # Initialize soil moisture and irrigation columns
        results['Soil Moisture (mm/m)'] = 0.0
        results['Irrigation (mm)'] = 0.0
        
        # Set initial soil moisture
        results.loc[results.index[0], 'Soil Moisture (mm/m)'] = initial_moisture
        
        # Run daily water balance
        for i in range(1, len(results)):
            prev_moisture = results.loc[results.index[i-1], 'Soil Moisture (mm/m)']
            rainfall = results.loc[results.index[i], 'PRECTOT (mm)']
            etc = results.loc[results.index[i], 'ETc (mm)']
            
            # Calculate soil moisture without irrigation
            moisture = prev_moisture + rainfall - etc
            
            # Check if irrigation is needed
            irrigation = 0
            if moisture < self.irrigation_threshold:
                # Calculate amount needed to bring soil moisture back to field capacity
                irrigation = self.field_capacity - moisture
                moisture += irrigation
            
            # Ensure moisture doesn't exceed field capacity (excess water is lost to drainage)
            if moisture > self.field_capacity:
                moisture = self.field_capacity
            
            # Ensure moisture doesn't go below wilting point
            if moisture < self.wilting_point:
                moisture = self.wilting_point
            
            # Update results
            results.loc[results.index[i], 'Soil Moisture (mm/m)'] = moisture
            results.loc[results.index[i], 'Irrigation (mm)'] = irrigation
        
        return results
    
    def analyze_results(self, results):
        """
        Analyze simulation results
        
        Parameters:
        results (DataFrame): Simulation results
        
        Returns:
        dict: Summary statistics
        """
        summary = {}
        
        # Calculate total irrigation and rainfall
        summary['total_irrigation'] = results['Irrigation (mm)'].sum()
        summary['total_rainfall'] = results['PRECTOT (mm)'].sum()
        summary['total_etc'] = results['ETc (mm)'].sum()
        summary['irrigation_events'] = (results['Irrigation (mm)'] > 0).sum()
        
        # Calculate water use efficiency
        conventional_irrigation = 500  # mm/season (given in requirements)
        summary['conventional_irrigation'] = conventional_irrigation
        summary['water_savings'] = conventional_irrigation - summary['total_irrigation']
        summary['water_savings_percent'] = (summary['water_savings'] / conventional_irrigation) * 100
        
        # Calculate stress days
        summary['stress_days'] = (results['Soil Moisture (mm/m)'] < self.irrigation_threshold).sum()
        summary['severe_stress_days'] = (results['Soil Moisture (mm/m)'] < (self.wilting_point + 10)).sum()
        
        # Estimate yield potential
        if summary['severe_stress_days'] > 10:
            summary['yield_potential'] = "Low (< 5 tons/ha)"
            summary['yield_notes'] = "Significant water stress detected during critical growth stages."
        elif summary['stress_days'] > 20:
            summary['yield_potential'] = "Medium (5-6 tons/ha)"
            summary['yield_notes'] = "Some water stress detected, but not severe enough to significantly impact yield."
        else:
            summary['yield_potential'] = "High (6-7 tons/ha)"
            summary['yield_notes'] = "Minimal water stress detected, optimal growing conditions maintained."
        
        return summary