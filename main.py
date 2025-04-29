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

# Import the classes from the other modules
from data_processor import DataProcessor
from irrigation_model import IrrigationModel

class IrrigationSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Maize Irrigation Simulator - Mashonaland East, Zimbabwe")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # Data storage
        self.climate_data_df = None # Use a different name to avoid confusion with internal use
        self.soil_data_df = None
        self.kc_data_df = None
        self.simulation_results = None
        self.season_data = None # To store filtered data for the selected season

        # Data Processor instance for loading/initial processing in GUI
        # Note: IrrigationModel will use its own internal DataProcessor for calculations
        self.gui_data_processor = DataProcessor()

        # Default values (will be updated from UI/soil data)
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
        self.year_combo['values'] = ('2015', '2016', '2017', '2018', '2019', '2020') # TODO: Could populate dynamically from data
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
            # Reset stored dataframes if a new file is selected
            if file_type == 'climate':
                self.climate_file_var.set(filename)
                self.climate_data_df = None
            elif file_type == 'soil':
                self.soil_file_var.set(filename)
                self.soil_data_df = None
            elif file_type == 'kc':
                self.kc_file_var.set(filename)
                self.kc_data_df = None

    def load_sample_data(self):
        # URLs for the sample data files
        climate_url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/synthetic_climate_data_mashonaland_2015_2020-uA2MCrodwtL1GCMNrhkrwhhsaGZl82.csv"
        soil_url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/synthetic_soil_data_mashonaland-SxJodIsyZBdLdASxLJcMB04DZuscYD.csv"
        kc_url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/synthetic_maize_kc_data-3KZiJhSc7BgkjjKc2WbIO8FsuQi2Yb.csv"

        try:
            # Load the data directly from URLs using the GUI's data processor instance
            self.climate_data_df = self.gui_data_processor.load_climate_data(climate_url)
            self.soil_data_df = self.gui_data_processor.load_soil_data(soil_url)
            self.kc_data_df = self.gui_data_processor.load_kc_data(kc_url)

            # Set the file paths in the UI to indicate sample data is loaded
            self.climate_file_var.set("Sample Climate Data (loaded)")
            self.soil_file_var.set("Sample Soil Data (loaded)")
            self.kc_file_var.set("Sample Crop Coefficient Data (loaded)")

            messagebox.showinfo("Data Loaded", "Sample data has been loaded successfully.")

            # Update field capacity and wilting point from soil data
            if not self.soil_data_df.empty:
                # Assuming column names are exactly as specified
                self.field_capacity = self.soil_data_df.iloc[0]['Field Capacity (mm/m)']
                self.wilting_point = self.soil_data_df.iloc[0]['Wilting Point (mm/m)']
                # Update UI fields
                self.field_capacity_var.set(str(self.field_capacity))
                self.wilting_point_var.set(str(self.wilting_point))
                # Optionally set irrigation threshold based on loaded FC (e.g., 50%)
                self.irrigation_threshold = self.field_capacity * 0.5 # Example: 50%
                self.irrigation_threshold_var.set(str(self.irrigation_threshold))
            else:
                 messagebox.showwarning("Soil Data Warning", "Sample soil data loaded but seems empty or doesn't contain expected columns ('Field Capacity (mm/m)', 'Wilting Point (mm/m)'). Using default parameters.")


        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sample data: {str(e)}")
            # Clear loaded data on error
            self.climate_data_df = None
            self.soil_data_df = None
            self.kc_data_df = None
            self.climate_file_var.set("")
            self.soil_file_var.set("")
            self.kc_file_var.set("")


    def load_data(self):
        """Loads data from files specified in the UI if not already loaded."""
        try:
            # Load climate data if not already loaded
            if self.climate_data_df is None:
                climate_file = self.climate_file_var.get()
                if climate_file and "loaded" not in climate_file: # Avoid reloading sample data via path
                    self.climate_data_df = self.gui_data_processor.load_climate_data(climate_file)
                elif self.climate_data_df is None: # Handles case where field is empty or still shows "loaded"
                     raise ValueError("Climate data file not specified or loaded.")

            # Load soil data if not already loaded
            if self.soil_data_df is None:
                soil_file = self.soil_file_var.get()
                if soil_file and "loaded" not in soil_file:
                    self.soil_data_df = self.gui_data_processor.load_soil_data(soil_file)
                    # Update parameters from file if loaded successfully
                    if not self.soil_data_df.empty:
                         try:
                              self.field_capacity = float(self.soil_data_df.iloc[0]['Field Capacity (mm/m)'])
                              self.wilting_point = float(self.soil_data_df.iloc[0]['Wilting Point (mm/m)'])
                              self.field_capacity_var.set(str(self.field_capacity))
                              self.wilting_point_var.set(str(self.wilting_point))
                              # Optionally update threshold based on newly loaded FC
                              self.irrigation_threshold = self.field_capacity * 0.5 # Example
                              self.irrigation_threshold_var.set(str(self.irrigation_threshold))
                         except (KeyError, IndexError, ValueError) as soil_err:
                              messagebox.showwarning("Soil Data Warning", f"Could not read soil parameters from file: {soil_err}. Using existing/default values.")
                elif self.soil_data_df is None:
                    # It might be acceptable to run without soil file if defaults are okay
                     messagebox.showwarning("Soil Data Missing", "Soil data file not specified or loaded. Using default/current parameters.")
                     # Ensure UI values are used if no file loaded
                     self.field_capacity = float(self.field_capacity_var.get())
                     self.wilting_point = float(self.wilting_point_var.get())


            # Load crop coefficient data if not already loaded
            if self.kc_data_df is None:
                kc_file = self.kc_file_var.get()
                if kc_file and "loaded" not in kc_file:
                    self.kc_data_df = self.gui_data_processor.load_kc_data(kc_file)
                elif self.kc_data_df is None:
                    # Allow running without Kc file, model will use defaults
                    messagebox.showwarning("Kc Data Missing", "Crop coefficient data file not specified or loaded. Model will use default Kc values.")


            # Process the loaded climate data for the selected season
            return self.process_data() # Returns True if successful

        except FileNotFoundError as e:
             messagebox.showerror("File Not Found", f"Error loading data: {str(e)}")
             return False
        except ValueError as e:
             messagebox.showerror("Input Error", f"{str(e)}")
             return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or process data: {str(e)}")
            return False

    def process_data(self):
        """Filters climate data for the selected growing season and adds 'Day' column."""
        if self.climate_data_df is None:
             messagebox.showerror("Error", "Climate data must be loaded first.")
             return False

        try:
            # Extract parameters from UI (ensure they are up-to-date)
            # These will be passed to the IrrigationModel
            self.field_capacity = float(self.field_capacity_var.get())
            self.wilting_point = float(self.wilting_point_var.get())
            self.irrigation_threshold = float(self.irrigation_threshold_var.get())

            if self.wilting_point >= self.irrigation_threshold:
                messagebox.showwarning("Parameter Check", "Wilting point is greater than or equal to the irrigation threshold. Irrigation may not trigger correctly.")
            if self.irrigation_threshold >= self.field_capacity:
                 messagebox.showwarning("Parameter Check", "Irrigation threshold is greater than or equal to field capacity. Irrigation may not trigger correctly.")


            # Ensure Date column is datetime type
            if not pd.api.types.is_datetime64_any_dtype(self.climate_data_df['Date']):
                 self.climate_data_df['Date'] = pd.to_datetime(self.climate_data_df['Date'])

            # Filter data for selected year and growing season (October to March)
            selected_year = int(self.year_var.get())
            start_date = pd.Timestamp(f"{selected_year}-10-01")
            # Calculate end date correctly (last day of March in the following year)
            end_date = pd.Timestamp(f"{selected_year+1}-03-31")

            # Filter the dataframe
            self.season_data = self.climate_data_df[
                (self.climate_data_df['Date'] >= start_date) &
                (self.climate_data_df['Date'] <= end_date)
            ].copy()

            if self.season_data.empty:
                 messagebox.showerror("Data Error", f"No climate data found for the selected growing season: {selected_year}-10-01 to {selected_year+1}-03-31.")
                 return False

            # Calculate days after planting (Day 0 is the start_date)
            self.season_data['Day'] = (self.season_data['Date'] - start_date).dt.days

            # Check for required columns needed by the model
            required_cols = ['T2M_MAX (°C)', 'T2M_MIN (°C)', 'ALLSKY_SFC_SW_DWN (MJ/m²)', 'PRECTOT (mm)', 'Day']
            missing_cols = [col for col in required_cols if col not in self.season_data.columns]
            if missing_cols:
                 messagebox.showerror("Data Error", f"Filtered climate data is missing required columns: {', '.join(missing_cols)}")
                 return False

            return True # Data loaded and processed successfully

        except ValueError as e:
             messagebox.showerror("Parameter Error", f"Please check input parameters (e.g., Year, FC, WP): {str(e)}")
             return False
        except KeyError as e:
             messagebox.showerror("Data Error", f"Missing expected column in climate data: {str(e)}")
             return False
        except Exception as e:
            messagebox.showerror("Processing Error", f"Failed to process data: {str(e)}")
            return False


    # --- REMOVED calculate_eto method ---
    # --- REMOVED get_kc_for_day method ---


    def run_simulation(self):
        """Loads data, runs the simulation using IrrigationModel, and displays results."""
        # Load and process data first
        if not self.load_data():
            return # Stop if data loading/processing failed

        if self.season_data is None or self.season_data.empty:
             messagebox.showerror("Error", "Cannot run simulation, no valid seasonal data available.")
             return

        # --- Use IrrigationModel ---
        try:
            # 1. Instantiate the model with parameters from the UI/loaded data
            # Ensure parameters are floats
            fc = float(self.field_capacity_var.get())
            wp = float(self.wilting_point_var.get())
            thresh = float(self.irrigation_threshold_var.get())

            model = IrrigationModel(
                field_capacity=fc,
                wilting_point=wp,
                irrigation_threshold=thresh
            )

            # 2. Pass the loaded Kc data (if available) to the model's internal data processor
            if self.kc_data_df is not None:
                model.data_processor.kc_data = self.kc_data_df.copy() # Pass the loaded Kc data


            # 3. Prepare the climate input data (already done in process_data -> self.season_data)
            # Ensure self.season_data has the required columns
            climate_input = self.season_data.copy()


            # 4. Define initial moisture (e.g., 70% of FC)
            initial_moisture = 0.7 * fc


            # 5. Run the simulation using the dedicated model class
            print("Running simulation with IrrigationModel...") # Debug print
            self.simulation_results = model.simulate(climate_input, initial_moisture=initial_moisture)
            print("Simulation finished.") # Debug print


            # Basic check on results
            if self.simulation_results is None or self.simulation_results.empty:
                 messagebox.showerror("Simulation Error", "Simulation did not produce results.")
                 return
            if 'Irrigation (mm)' not in self.simulation_results.columns:
                 messagebox.showerror("Simulation Error", "'Irrigation (mm)' column missing in simulation results.")
                 return
            if self.simulation_results['Irrigation (mm)'].isnull().any():
                 messagebox.showwarning("Simulation Warning", "Some NaN values found in 'Irrigation (mm)' column.")
                 # Optionally fill NaN with 0 if appropriate for display
                 # self.simulation_results['Irrigation (mm)'].fillna(0, inplace=True)


            print(f"Total calculated irrigation: {self.simulation_results['Irrigation (mm)'].sum():.2f} mm") # Debug print

        except Exception as e:
             messagebox.showerror("Simulation Error", f"An error occurred during simulation: {str(e)}")
             self.simulation_results = None # Clear results on error
             return # Stop execution

        # --- Display results ---
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
        try:
            ax.plot(self.simulation_results['Date'], self.simulation_results['Soil Moisture (mm/m)'],
                    label='Soil Moisture', color='blue', linewidth=2)

            # Plot irrigation events
            # Ensure the column exists and handle potential NaNs if not filled earlier
            irrigation_days = self.simulation_results[self.simulation_results['Irrigation (mm)'].fillna(0) > 0]
            if not irrigation_days.empty:
                ax.scatter(irrigation_days['Date'], irrigation_days['Soil Moisture (mm/m)'],
                          color='green', marker='^', s=100, label='Irrigation Events')

            # Plot rainfall events (use PRECTOT column)
            significant_rain = self.simulation_results[self.simulation_results['PRECTOT (mm)'].fillna(0) > 5]
            if not significant_rain.empty:
                # Plotting rain against soil moisture might be confusing, maybe use a secondary axis or different plot type?
                # For now, plotting on the same axis as requested previously.
                 ax.scatter(significant_rain['Date'], significant_rain['Soil Moisture (mm/m)'],
                           color='cyan', marker='o', s=50, label='Significant Rainfall (>5mm)')


            # Add threshold lines (using the actual values used in the simulation)
            fc = float(self.field_capacity_var.get())
            wp = float(self.wilting_point_var.get())
            thresh = float(self.irrigation_threshold_var.get())
            ax.axhline(y=fc, color='black', linestyle='-', label=f'Field Capacity ({fc:.1f})')
            ax.axhline(y=thresh, color='red', linestyle='--', label=f'Irrigation Threshold ({thresh:.1f})')
            ax.axhline(y=wp, color='brown', linestyle='-.', label=f'Wilting Point ({wp:.1f})')

            # Set labels and title
            ax.set_xlabel('Date')
            ax.set_ylabel('Soil Moisture (mm/m)')
            ax.set_title(f'Soil Moisture and Irrigation Events - {self.year_var.get()} Growing Season')
            ax.set_ylim(bottom=min(wp * 0.9, self.simulation_results['Soil Moisture (mm/m)'].min() * 0.95), # Adjust ylim
                        top=fc * 1.1)


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

        except KeyError as e:
             messagebox.showerror("Graph Error", f"Cannot create graph. Missing data column: {e}")
        except Exception as e:
             messagebox.showerror("Graph Error", f"An error occurred while creating the graph: {e}")


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
        # Ensure columns match the DataFrame from IrrigationModel.simulate
        columns = ('Date', 'Rainfall', 'T_Max', 'T_Min', 'ETo', 'Kc', 'ETc', 'Soil_Moisture', 'Irrigation')
        tree = ttk.Treeview(table_container, columns=columns, show='headings',
                           yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)

        # Configure scrollbars
        vscrollbar.config(command=tree.yview)
        hscrollbar.config(command=tree.xview)

        # Define column headings
        tree.heading('Date', text='Date')
        tree.heading('Rainfall', text='Rain (mm)') # PRECTOT (mm)
        tree.heading('T_Max', text='T Max (°C)')
        tree.heading('T_Min', text='T Min (°C)')
        tree.heading('ETo', text='ETo (mm)')
        tree.heading('Kc', text='Kc')
        tree.heading('ETc', text='ETc (mm)')
        tree.heading('Soil_Moisture', text='Moisture (mm/m)')
        tree.heading('Irrigation', text='Irrigation (mm)')

        # Define column widths (adjust as needed)
        tree.column('Date', width=90, anchor=tk.W)
        tree.column('Rainfall', width=80, anchor=tk.E)
        tree.column('T_Max', width=80, anchor=tk.E)
        tree.column('T_Min', width=80, anchor=tk.E)
        tree.column('ETo', width=80, anchor=tk.E)
        tree.column('Kc', width=60, anchor=tk.E)
        tree.column('ETc', width=80, anchor=tk.E)
        tree.column('Soil_Moisture', width=100, anchor=tk.E)
        tree.column('Irrigation', width=100, anchor=tk.E)

        # Insert data
        try:
            # Use .fillna(0) for columns that might have NaN and should be displayed as 0
            # Format numbers for display
            for i, row in self.simulation_results.iterrows():
                tree.insert('', 'end', values=(
                    row['Date'].strftime('%Y-%m-%d'),
                    f"{row['PRECTOT (mm)']:.2f}",
                    f"{row['T2M_MAX (°C)']:.2f}",
                    f"{row['T2M_MIN (°C)']:.2f}",
                    f"{row.get('ETo (mm)', float('nan')):.2f}", # Use .get for safety
                    f"{row.get('Kc', float('nan')):.2f}",
                    f"{row.get('ETc (mm)', float('nan')):.2f}",
                    f"{row.get('Soil Moisture (mm/m)', float('nan')):.2f}",
                    f"{row.get('Irrigation (mm)', 0.0):.2f}" # Default irrigation to 0 if missing/NaN
                ))
        except KeyError as e:
             messagebox.showerror("Table Error", f"Cannot populate table. Missing data column: {e}")
             # Clear the treeview
             for item in tree.get_children():
                  tree.delete(item)
        except Exception as e:
            messagebox.showerror("Table Error", f"An error occurred while populating the table: {e}")
             # Clear the treeview
            for item in tree.get_children():
                  tree.delete(item)

        tree.pack(fill=tk.BOTH, expand=True)

    def create_summary(self):
        # Use the analyze_results method from IrrigationModel if desired,
        # or calculate directly here as before.
        # For consistency, let's use the model's analyzer.

        # Instantiate a temporary model just to use the analysis method
        # (Alternatively, make analyze_results a static method or standalone function)
        try:
            fc = float(self.field_capacity_var.get())
            wp = float(self.wilting_point_var.get())
            thresh = float(self.irrigation_threshold_var.get())
            temp_model = IrrigationModel(field_capacity=fc, wilting_point=wp, irrigation_threshold=thresh)
            summary_data = temp_model.analyze_results(self.simulation_results)

            # Create summary frame
            summary_container = ttk.Frame(self.summary_frame, padding=20)
            summary_container.pack(fill=tk.BOTH, expand=True)

            # Add summary information
            ttk.Label(summary_container, text="Irrigation Summary", font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=10)

            ttk.Label(summary_container, text="Growing Season:").grid(row=1, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{self.year_var.get()} October - {int(self.year_var.get())+1} March").grid(row=1, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Total Irrigation Applied:").grid(row=2, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{summary_data.get('total_irrigation', 0):.2f} mm").grid(row=2, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Total Rainfall:").grid(row=3, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{summary_data.get('total_rainfall', 0):.2f} mm").grid(row=3, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Total Crop Water Use (ETc):").grid(row=4, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{summary_data.get('total_etc', 0):.2f} mm").grid(row=4, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Number of Irrigation Events:").grid(row=5, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{summary_data.get('irrigation_events', 0)}").grid(row=5, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Conventional Irrigation (Fixed Schedule):").grid(row=6, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{summary_data.get('conventional_irrigation', 0)} mm").grid(row=6, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Water Savings:").grid(row=7, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{summary_data.get('water_savings', 0):.2f} mm ({summary_data.get('water_savings_percent', 0):.1f}%)").grid(row=7, column=1, sticky=tk.W, pady=5)

            # Add a separator
            ttk.Separator(summary_container, orient=tk.HORIZONTAL).grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=10)

            # Add yield potential information
            ttk.Label(summary_container, text="Yield Potential Assessment", font=('Arial', 14, 'bold')).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=10)

            ttk.Label(summary_container, text="Days Under Water Stress:").grid(row=10, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{summary_data.get('stress_days', 0)}").grid(row=10, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Days Under Severe Water Stress:").grid(row=11, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=f"{summary_data.get('severe_stress_days', 0)}").grid(row=11, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Estimated Yield Potential:").grid(row=12, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=summary_data.get('yield_potential', 'N/A')).grid(row=12, column=1, sticky=tk.W, pady=5)

            ttk.Label(summary_container, text="Notes:").grid(row=13, column=0, sticky=tk.W, pady=5)
            ttk.Label(summary_container, text=summary_data.get('yield_notes', ''), wraplength=400, justify=tk.LEFT).grid(row=13, column=1, sticky=tk.W, pady=5)

        except Exception as e:
             messagebox.showerror("Summary Error", f"An error occurred while generating the summary: {e}")


    def export_results(self):
        if self.simulation_results is None:
            messagebox.showinfo("No Results", "Please run the simulation first.")
            return

        # Ask for file location
        filename = filedialog.asksaveasfilename(
            title="Export Simulation Results",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"irrigation_results_{self.year_var.get()}.csv" # Suggest a filename
        )

        if not filename:
            return # User cancelled

        try:
            # Export the results DataFrame
            # Select and order columns for export
            export_cols = [
                'Date', 'PRECTOT (mm)', 'T2M_MAX (°C)', 'T2M_MIN (°C)',
                'ALLSKY_SFC_SW_DWN (MJ/m²)', 'ETo (mm)', 'Kc', 'ETc (mm)',
                'Soil Moisture (mm/m)', 'Irrigation (mm)', 'Day'
            ]
            # Ensure only existing columns are selected
            export_data = self.simulation_results[[col for col in export_cols if col in self.simulation_results.columns]]

            export_data.to_csv(filename, index=False, float_format='%.3f') # Format floats

            # --- Also export summary to a text file ---
            summary_filename = filename.replace('.csv', '_summary.txt')

            # Recalculate summary data using the model's analyzer for consistency
            fc = float(self.field_capacity_var.get())
            wp = float(self.wilting_point_var.get())
            thresh = float(self.irrigation_threshold_var.get())
            temp_model = IrrigationModel(field_capacity=fc, wilting_point=wp, irrigation_threshold=thresh)
            summary_data = temp_model.analyze_results(self.simulation_results) # Use model's analysis method

            with open(summary_filename, 'w') as f:
                f.write(f"Maize Irrigation Simulation Summary\n")
                f.write(f"===================================\n\n")
                # Add location if relevant, maybe from input later?
                # f.write(f"Location: Mashonaland East, Zimbabwe\n")
                f.write(f"Growing Season: {self.year_var.get()} October - {int(self.year_var.get())+1} March\n\n")

                f.write(f"Soil Parameters:\n")
                f.write(f"  Field Capacity: {fc:.1f} mm/m\n")
                f.write(f"  Wilting Point: {wp:.1f} mm/m\n")
                f.write(f"  Irrigation Threshold: {thresh:.1f} mm/m\n\n")

                f.write(f"Simulation Totals & Events:\n")
                f.write(f"  Total Irrigation Applied: {summary_data.get('total_irrigation', 0):.2f} mm\n")
                f.write(f"  Total Rainfall: {summary_data.get('total_rainfall', 0):.2f} mm\n")
                f.write(f"  Total Crop Water Use (ETc): {summary_data.get('total_etc', 0):.2f} mm\n")
                f.write(f"  Number of Irrigation Events: {summary_data.get('irrigation_events', 0)}\n\n")

                f.write(f"Water Efficiency:\n")
                f.write(f"  Conventional Irrigation (Assumed): {summary_data.get('conventional_irrigation', 0):.1f} mm\n")
                f.write(f"  Water Savings: {summary_data.get('water_savings', 0):.2f} mm ({summary_data.get('water_savings_percent', 0):.1f}%)\n\n")

                f.write(f"Yield Assessment:\n")
                f.write(f"  Days Under Water Stress (< Threshold): {summary_data.get('stress_days', 0)}\n")
                f.write(f"  Days Under Severe Water Stress (< WP+10mm): {summary_data.get('severe_stress_days', 0)}\n") # Clarify definition
                f.write(f"  Estimated Yield Potential: {summary_data.get('yield_potential', 'N/A')}\n")
                f.write(f"  Notes: {summary_data.get('yield_notes', '')}\n")

            messagebox.showinfo("Export Complete", f"Results exported to:\n{filename}\n\nSummary exported to:\n{summary_filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()

    # Configure styles
    style = ttk.Style()
    # Set a theme for a more modern look (clam, alt, default, classic)
    style.theme_use('clam')
    style.configure('Accent.TButton', font=('Arial', 11, 'bold'), foreground='white', background='#0078D7') # Example accent color
    style.map('Accent.TButton', background=[('active', '#005A9E')])


    app = IrrigationSimulator(root)
    root.mainloop()