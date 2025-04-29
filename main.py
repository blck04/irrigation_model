import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys
from datetime import datetime
import csv

class IrrigationSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Maize Irrigation Simulator - Mashonaland East, Zimbabwe")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Data storage
        self.climate_data = None
        self.soil_data = None
        self.kc_data = None
        self.simulation_results = None
        
        # Default values
        self.field_capacity = 150  # mm/m
        self.wilting_point = 75    # mm/m
        self.irrigation_threshold = 75  # mm/m (50% of field capacity)
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the input frame
        self.create_input_frame()
        
        # Create the output frame
        self.create_output_frame()
    
    def create_input_frame(self):
        input_frame = ttk.LabelFrame(self.main_frame, text="Input Parameters", padding=10)
        input_frame.pack(fill=tk.X, pady=10)
        
        # File upload section
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        # Climate data file
        ttk.Label(file_frame, text="Climate Data:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.climate_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.climate_file_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file('climate')).grid(row=0, column=2, padx=5)
        
        # Soil data file
        ttk.Label(file_frame, text="Soil Data:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.soil_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.soil_file_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file('soil')).grid(row=1, column=2, padx=5)
        
        # Crop coefficient data file
        ttk.Label(file_frame, text="Crop Coefficient Data:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.kc_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.kc_file_var, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file('kc')).grid(row=2, column=2, padx=5)
        
        # Parameters section
        param_frame = ttk.Frame(input_frame)
        param_frame.pack(fill=tk.X, pady=10)
        
        # Field capacity
        ttk.Label(param_frame, text="Field Capacity (mm/m):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.field_capacity_var = tk.StringVar(value=str(self.field_capacity))
        ttk.Entry(param_frame, textvariable=self.field_capacity_var, width=10).grid(row=0, column=1, padx=5)
        
        # Wilting point
        ttk.Label(param_frame, text="Wilting Point (mm/m):").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.wilting_point_var = tk.StringVar(value=str(self.wilting_point))
        ttk.Entry(param_frame, textvariable=self.wilting_point_var, width=10).grid(row=0, column=3, padx=5)
        
        # Irrigation threshold
        ttk.Label(param_frame, text="Irrigation Threshold (mm/m):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.irrigation_threshold_var = tk.StringVar(value=str(self.irrigation_threshold))
        ttk.Entry(param_frame, textvariable=self.irrigation_threshold_var, width=10).grid(row=1, column=1, padx=5)
        
        # Year selection
        ttk.Label(param_frame, text="Select Year:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(param_frame, textvariable=self.year_var, width=10, state="readonly")
        self.year_combo['values'] = ('2015', '2016', '2017', '2018', '2019', '2020')
        self.year_combo.current(0)
        self.year_combo.grid(row=1, column=3, padx=5)
        
        # Run simulation button
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Run Simulation", command=self.run_simulation, style='Accent.TButton').pack(pady=10)
        
        # Load sample data button
        ttk.Button(button_frame, text="Load Sample Data", command=self.load_sample_data).pack(pady=5)
    
    def create_output_frame(self):
        output_frame = ttk.LabelFrame(self.main_frame, text="Simulation Results", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(output_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab for graph
        self.graph_frame = ttk.Frame(notebook)
        notebook.add(self.graph_frame, text="Soil Moisture Graph")
        
        # Tab for data table
        self.table_frame = ttk.Frame(notebook)
        notebook.add(self.table_frame, text="Data Table")
        
        # Tab for summary
        self.summary_frame = ttk.Frame(notebook)
        notebook.add(self.summary_frame, text="Summary")
        
        # Export button
        export_frame = ttk.Frame(output_frame)
        export_frame.pack(fill=tk.X, pady=5)
        ttk.Button(export_frame, text="Export Results", command=self.export_results).pack(side=tk.RIGHT, padx=5)
    
    def browse_file(self, file_type):
        filename = filedialog.askopenfilename(
            title=f"Select {file_type.capitalize()} Data File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if filename:
            if file_type == 'climate':
                self.climate_file_var.set(filename)
            elif file_type == 'soil':
                self.soil_file_var.set(filename)
            elif file_type == 'kc':
                self.kc_file_var.set(filename)
    
    def load_sample_data(self):
        # URLs for the sample data files
        climate_url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/synthetic_climate_data_mashonaland_2015_2020-uA2MCrodwtL1GCMNrhkrwhhsaGZl82.csv"
        soil_url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/synthetic_soil_data_mashonaland-SxJodIsyZBdLdASxLJcMB04DZuscYD.csv"
        kc_url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/synthetic_maize_kc_data-3KZiJhSc7BgkjjKc2WbIO8FsuQi2Yb.csv"
        
        try:
            # Load the data directly from URLs
            self.climate_data = pd.read_csv(climate_url)
            self.soil_data = pd.read_csv(soil_url)
            self.kc_data = pd.read_csv(kc_url)
            
            # Set the file paths in the UI
            self.climate_file_var.set("Sample Climate Data (loaded)")
            self.soil_file_var.set("Sample Soil Data (loaded)")
            self.kc_file_var.set("Sample Crop Coefficient Data (loaded)")
            
            messagebox.showinfo("Data Loaded", "Sample data has been loaded successfully.")
            
            # Update field capacity and wilting point from soil data
            if not self.soil_data.empty:
                self.field_capacity = self.soil_data.iloc[0]['Field Capacity (mm/m)']
                self.wilting_point = self.soil_data.iloc[0]['Wilting Point (mm/m)']
                self.field_capacity_var.set(str(self.field_capacity))
                self.wilting_point_var.set(str(self.wilting_point))
                self.irrigation_threshold_var.set(str(self.field_capacity / 2))
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sample data: {str(e)}")
    
    def load_data(self):
        try:
            # Load climate data
            if self.climate_data is None:
                climate_file = self.climate_file_var.get()
                if climate_file:
                    self.climate_data = pd.read_csv(climate_file)
                else:
                    raise ValueError("Climate data file not specified")
            
            # Load soil data
            if self.soil_data is None:
                soil_file = self.soil_file_var.get()
                if soil_file:
                    self.soil_data = pd.read_csv(soil_file)
                else:
                    raise ValueError("Soil data file not specified")
            
            # Load crop coefficient data
            if self.kc_data is None:
                kc_file = self.kc_file_var.get()
                if kc_file:
                    self.kc_data = pd.read_csv(kc_file)
                else:
                    raise ValueError("Crop coefficient data file not specified")
            
            # Process the data
            self.process_data()
            return True
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            return False
    
    def process_data(self):
        # Convert date column to datetime
        self.climate_data['Date'] = pd.to_datetime(self.climate_data['Date'])
        
        # Extract parameters from UI
        self.field_capacity = float(self.field_capacity_var.get())
        self.wilting_point = float(self.wilting_point_var.get())
        self.irrigation_threshold = float(self.irrigation_threshold_var.get())
        
        # Filter data for selected year and growing season (October to March)
        selected_year = int(self.year_var.get())
        start_date = pd.Timestamp(f"{selected_year}-10-01")
        end_date = pd.Timestamp(f"{selected_year+1}-03-31")
        
        self.season_data = self.climate_data[
            (self.climate_data['Date'] >= start_date) & 
            (self.climate_data['Date'] <= end_date)
        ].copy()
        
        # Calculate days after planting
        self.season_data['Day'] = (self.season_data['Date'] - start_date).dt.days
    
    def calculate_eto(self, row):
        """Calculate reference evapotranspiration using Hargreaves method"""
        t_avg = (row['T2M_MAX (°C)'] + row['T2M_MIN (°C)']) / 2
        t_range = row['T2M_MAX (°C)'] - row['T2M_MIN (°C)']
        
        # Convert solar radiation from MJ/m²/day to mm/day equivalent
        # 1 MJ/m² ≈ 0.408 mm of water
        ra = row['ALLSKY_SFC_SW_DWN (MJ/m²)'] * 0.408
        
        # Hargreaves equation
        eto = 0.0023 * (t_avg + 17.8) * (t_range ** 0.5) * ra
        return eto
    
    def get_kc_for_day(self, day):
        """Get crop coefficient (Kc) for a specific day after planting"""
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
    
    def run_simulation(self):
        if not self.load_data():
            return
        
        # Initialize results dataframe
        results = self.season_data.copy()
        results['ETo (mm)'] = results.apply(self.calculate_eto, axis=1)
        results['Kc'] = results['Day'].apply(self.get_kc_for_day)
        results['ETc (mm)'] = results['ETo (mm)'] * results['Kc']
        
        # Initialize soil moisture and irrigation columns
        results['Soil Moisture (mm/m)'] = 0.0
        results['Irrigation (mm)'] = 0.0
        
        # Set initial soil moisture (assume 70% of field capacity at planting)
        initial_moisture = 0.7 * self.field_capacity
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
        
        # Store results
        self.simulation_results = results
        
        # Display results
        self.display_results()
    
    def display_results(self):
        if self.simulation_results is None:
            messagebox.showinfo("No Results", "Please run the simulation first.")
            return
        
        # Clear previous results
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        
        # Create the graph
        self.create_graph()
        
        # Create the data table
        self.create_data_table()
        
        # Create the summary
        self.create_summary()
    
    def create_graph(self):
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot soil moisture
        ax.plot(self.simulation_results['Date'], self.simulation_results['Soil Moisture (mm/m)'], 
                label='Soil Moisture', color='blue', linewidth=2)
        
        # Plot irrigation events
        irrigation_days = self.simulation_results[self.simulation_results['Irrigation (mm)'] > 0]
        if not irrigation_days.empty:
            ax.scatter(irrigation_days['Date'], irrigation_days['Soil Moisture (mm/m)'], 
                      color='green', marker='^', s=100, label='Irrigation Events')
        
        # Plot rainfall events
        significant_rain = self.simulation_results[self.simulation_results['PRECTOT (mm)'] > 5]
        if not significant_rain.empty:
            ax.scatter(significant_rain['Date'], significant_rain['Soil Moisture (mm/m)'], 
                      color='blue', marker='o', s=50, label='Significant Rainfall (>5mm)')
        
        # Add threshold lines
        ax.axhline(y=self.field_capacity, color='black', linestyle='-', label='Field Capacity')
        ax.axhline(y=self.irrigation_threshold, color='red', linestyle='--', label='Irrigation Threshold')
        ax.axhline(y=self.wilting_point, color='brown', linestyle='-.', label='Wilting Point')
        
        # Set labels and title
        ax.set_xlabel('Date')
        ax.set_ylabel('Soil Moisture (mm/m)')
        ax.set_title(f'Soil Moisture and Irrigation Events - {self.year_var.get()} Growing Season')
        
        # Add legend
        ax.legend(loc='best')
        
        # Format x-axis dates
        fig.autofmt_xdate()
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_data_table(self):
        # Create a frame for the table
        table_container = ttk.Frame(self.table_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbars
        vscrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL)
        vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        hscrollbar = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL)
        hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create treeview
        columns = ('Date', 'Rainfall', 'T_Max', 'T_Min', 'ETo', 'Kc', 'ETc', 'Soil_Moisture', 'Irrigation')
        tree = ttk.Treeview(table_container, columns=columns, show='headings',
                           yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)
        
        # Configure scrollbars
        vscrollbar.config(command=tree.yview)
        hscrollbar.config(command=tree.xview)
        
        # Define column headings
        tree.heading('Date', text='Date')
        tree.heading('Rainfall', text='Rainfall (mm)')
        tree.heading('T_Max', text='T Max (°C)')
        tree.heading('T_Min', text='T Min (°C)')
        tree.heading('ETo', text='ETo (mm)')
        tree.heading('Kc', text='Kc')
        tree.heading('ETc', text='ETc (mm)')
        tree.heading('Soil_Moisture', text='Soil Moisture (mm/m)')
        tree.heading('Irrigation', text='Irrigation (mm)')
        
        # Define column widths
        for col in columns:
            tree.column(col, width=100)
        
        # Insert data
        for i, row in self.simulation_results.iterrows():
            tree.insert('', 'end', values=(
                row['Date'].strftime('%Y-%m-%d'),
                f"{row['PRECTOT (mm)']:.2f}",
                f"{row['T2M_MAX (°C)']:.2f}",
                f"{row['T2M_MIN (°C)']:.2f}",
                f"{row['ETo (mm)']:.2f}",
                f"{row['Kc']:.2f}",
                f"{row['ETc (mm)']:.2f}",
                f"{row['Soil Moisture (mm/m)']:.2f}",
                f"{row['Irrigation (mm)']:.2f}"
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
    
    def create_summary(self):
        # Calculate summary statistics
        total_irrigation = self.simulation_results['Irrigation (mm)'].sum()
        total_rainfall = self.simulation_results['PRECTOT (mm)'].sum()
        total_etc = self.simulation_results['ETc (mm)'].sum()
        irrigation_events = (self.simulation_results['Irrigation (mm)'] > 0).sum()
        
        # Calculate water use efficiency
        conventional_irrigation = 500  # mm/season (given in requirements)
        water_savings = conventional_irrigation - total_irrigation
        water_savings_percent = (water_savings / conventional_irrigation) * 100 if conventional_irrigation > 0 else 0
        
        # Create summary frame
        summary_container = ttk.Frame(self.summary_frame, padding=20)
        summary_container.pack(fill=tk.BOTH, expand=True)
        
        # Add summary information
        ttk.Label(summary_container, text="Irrigation Summary", font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ttk.Label(summary_container, text="Growing Season:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{self.year_var.get()} October - {int(self.year_var.get())+1} March").grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(summary_container, text="Total Irrigation Applied:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{total_irrigation:.2f} mm").grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(summary_container, text="Total Rainfall:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{total_rainfall:.2f} mm").grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(summary_container, text="Total Crop Water Use (ETc):").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{total_etc:.2f} mm").grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(summary_container, text="Number of Irrigation Events:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{irrigation_events}").grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(summary_container, text="Conventional Irrigation (Fixed Schedule):").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{conventional_irrigation} mm").grid(row=6, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(summary_container, text="Water Savings:").grid(row=7, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{water_savings:.2f} mm ({water_savings_percent:.2f}%)").grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # Add a separator
        ttk.Separator(summary_container, orient=tk.HORIZONTAL).grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Add yield potential information
        ttk.Label(summary_container, text="Yield Potential Assessment", font=('Arial', 14, 'bold')).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Calculate days under water stress
        stress_days = (self.simulation_results['Soil Moisture (mm/m)'] < self.irrigation_threshold).sum()
        severe_stress_days = (self.simulation_results['Soil Moisture (mm/m)'] < (self.wilting_point + 10)).sum()
        
        ttk.Label(summary_container, text="Days Under Water Stress:").grid(row=10, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{stress_days}").grid(row=10, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(summary_container, text="Days Under Severe Water Stress:").grid(row=11, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=f"{severe_stress_days}").grid(row=11, column=1, sticky=tk.W, pady=5)
        
        # Estimate yield potential
        if severe_stress_days > 10:
            yield_potential = "Low (< 5 tons/ha)"
            yield_notes = "Significant water stress detected during critical growth stages."
        elif stress_days > 20:
            yield_potential = "Medium (5-6 tons/ha)"
            yield_notes = "Some water stress detected, but not severe enough to significantly impact yield."
        else:
            yield_potential = "High (6-7 tons/ha)"
            yield_notes = "Minimal water stress detected, optimal growing conditions maintained."
        
        ttk.Label(summary_container, text="Estimated Yield Potential:").grid(row=12, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=yield_potential).grid(row=12, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(summary_container, text="Notes:").grid(row=13, column=0, sticky=tk.W, pady=5)
        ttk.Label(summary_container, text=yield_notes, wraplength=400).grid(row=13, column=1, sticky=tk.W, pady=5)
    
    def export_results(self):
        if self.simulation_results is None:
            messagebox.showinfo("No Results", "Please run the simulation first.")
            return
        
        # Ask for file location
        filename = filedialog.asksaveasfilename(
            title="Export Simulation Results",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Export the results
            export_data = self.simulation_results[[
                'Date', 'PRECTOT (mm)', 'T2M_MAX (°C)', 'T2M_MIN (°C)', 
                'ETo (mm)', 'Kc', 'ETc (mm)', 'Soil Moisture (mm/m)', 'Irrigation (mm)'
            ]]
            
            export_data.to_csv(filename, index=False)
            
            # Also export summary to a text file
            summary_filename = filename.replace('.csv', '_summary.txt')
            with open(summary_filename, 'w') as f:
                f.write(f"Maize Irrigation Simulation Summary\n")
                f.write(f"===================================\n\n")
                f.write(f"Location: Mashonaland East, Zimbabwe\n")
                f.write(f"Growing Season: {self.year_var.get()} October - {int(self.year_var.get())+1} March\n\n")
                
                f.write(f"Soil Parameters:\n")
                f.write(f"  Field Capacity: {self.field_capacity} mm/m\n")
                f.write(f"  Wilting Point: {self.wilting_point} mm/m\n")
                f.write(f"  Irrigation Threshold: {self.irrigation_threshold} mm/m\n\n")
                
                f.write(f"Simulation Results:\n")
                f.write(f"  Total Irrigation Applied: {self.simulation_results['Irrigation (mm)'].sum():.2f} mm\n")
                f.write(f"  Total Rainfall: {self.simulation_results['PRECTOT (mm)'].sum():.2f} mm\n")
                f.write(f"  Total Crop Water Use (ETc): {self.simulation_results['ETc (mm)'].sum():.2f} mm\n")
                f.write(f"  Number of Irrigation Events: {(self.simulation_results['Irrigation (mm)'] > 0).sum()}\n\n")
                
                conventional_irrigation = 500
                water_savings = conventional_irrigation - self.simulation_results['Irrigation (mm)'].sum()
                water_savings_percent = (water_savings / conventional_irrigation) * 100
                
                f.write(f"Water Efficiency:\n")
                f.write(f"  Conventional Irrigation (Fixed Schedule): {conventional_irrigation} mm\n")
                f.write(f"  Water Savings: {water_savings:.2f} mm ({water_savings_percent:.2f}%)\n\n")
                
                stress_days = (self.simulation_results['Soil Moisture (mm/m)'] < self.irrigation_threshold).sum()
                severe_stress_days = (self.simulation_results['Soil Moisture (mm/m)'] < (self.wilting_point + 10)).sum()
                
                f.write(f"Yield Assessment:\n")
                f.write(f"  Days Under Water Stress: {stress_days}\n")
                f.write(f"  Days Under Severe Water Stress: {severe_stress_days}\n")
                
                if severe_stress_days > 10:
                    f.write(f"  Estimated Yield Potential: Low (< 5 tons/ha)\n")
                    f.write(f"  Notes: Significant water stress detected during critical growth stages.\n")
                elif stress_days > 20:
                    f.write(f"  Estimated Yield Potential: Medium (5-6 tons/ha)\n")
                    f.write(f"  Notes: Some water stress detected, but not severe enough to significantly impact yield.\n")
                else:
                    f.write(f"  Estimated Yield Potential: High (6-7 tons/ha)\n")
                    f.write(f"  Notes: Minimal water stress detected, optimal growing conditions maintained.\n")
            
            messagebox.showinfo("Export Complete", f"Results exported to:\n{filename}\nSummary exported to:\n{summary_filename}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    
    # Configure styles
    style = ttk.Style()
    style.configure('Accent.TButton', font=('Arial', 11, 'bold'))
    
    app = IrrigationSimulator(root)
    root.mainloop()