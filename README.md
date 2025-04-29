# Maize Irrigation Simulator (Mashonaland East, Zimbabwe)

## Description

This application simulates daily soil water balance for a maize crop, specifically tailored for conditions representative of Mashonaland East, Zimbabwe. It helps estimate irrigation requirements throughout the growing season (October - March) based on climate data, soil properties, and crop water needs. The goal is to provide insights into efficient water use compared to fixed irrigation schedules.

The simulation calculates daily reference evapotranspiration (ETo) using the Hargreaves method, determines crop evapotranspiration (ETc) using crop coefficients (Kc), and tracks soil moisture depletion due to ETc, replenishment by rainfall, and calculated irrigation events.

## Features

* **Graphical User Interface (GUI):** Easy-to-use interface built with Tkinter.
* **Data Input:** Load climate, soil, and crop coefficient (Kc) data from CSV files.
* **Sample Data:** Option to load pre-packaged sample data for demonstration.
* **Parameter Configuration:** Set soil properties (Field Capacity, Wilting Point) and the Irrigation Threshold (soil moisture level at which to irrigate).
* **Growing Season Selection:** Choose the starting year for the simulation (simulates Oct - Mar).
* **Daily Water Balance Simulation:** Calculates daily soil moisture and irrigation needs.
* **Results Visualization:**
    * Plots soil moisture levels over time, showing Field Capacity, Wilting Point, Irrigation Threshold, and irrigation/rainfall events.
    * Displays a detailed table of daily input data and simulation results (Rain, Temps, ETo, Kc, ETc, Soil Moisture, Irrigation).
    * Provides a summary tab with key seasonal totals (Irrigation, Rainfall, ETc), number of irrigation events, water savings potential, stress days, and an estimated yield potential assessment.
* **Data Export:** Export detailed daily results to a CSV file and the summary report to a TXT file.

## Requirements

* Python 3.x
* Required Python libraries:
    * `pandas`
    * `numpy`
    * `matplotlib`
    * `tkinter` (usually included with standard Python distributions)

## Installation

1.  **Clone the repository (if applicable) or download the files.**
    ```bash
    # Example if using Git
    # git clone <repository-url>
    # cd <repository-directory>
    ```
2.  **Install required libraries:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install pandas numpy matplotlib
    ```
    *(Optional: Create a `requirements.txt` file with the library names and versions, then use `pip install -r requirements.txt`)*

## Usage

1.  **Prepare Input Data:** Ensure your CSV files are formatted correctly (see Input Data Format section below).
2.  **Run the Application:**
    ```bash
    python main.py
    ```
3.  **Load Data:**
    * Use the "Browse" buttons to select your climate, soil, and (optionally) Kc data CSV files.
    * Alternatively, click "Load Sample Data" to use the built-in example data.
4.  **Set Parameters:**
    * Verify or adjust the Field Capacity, Wilting Point, and Irrigation Threshold values. If loading soil data from a file, these may be updated automatically.
    * Select the starting year for the growing season simulation.
5.  **Run Simulation:** Click the "Run Simulation" button.
6.  **View Results:** Explore the results in the "Soil Moisture Graph", "Data Table", and "Summary" tabs.
7.  **Export Results:** Click the "Export Results" button and choose a location to save the CSV (detailed data) and TXT (summary) files.

## File Structure

* `main.py`: The main script to run the GUI application. Handles user interaction, calls the simulation model, and displays results.
* `irrigation_model.py`: Contains the `IrrigationModel` class, which implements the core daily water balance simulation logic and results analysis.
* `data_processor.py`: Contains the `DataProcessor` class, used for loading data files and includes functions for ETo and Kc calculations (used internally by `IrrigationModel`).
* `README.md`: This file.

*  Sample data CSV files.

## Input Data Format

Ensure your CSV files have the following columns with the specified headers and units:

1.  **Climate Data CSV:**
    * `Date`: Date in a format recognizable by pandas (e.g., `YYYY-MM-DD`, `DD/MM/YYYY`).
    * `T2M_MAX (°C)`: Daily maximum air temperature in degrees Celsius.
    * `T2M_MIN (°C)`: Daily minimum air temperature in degrees Celsius.
    * `ALLSKY_SFC_SW_DWN (MJ/m²)`: Daily total incoming shortwave solar radiation in Megajoules per square meter.
    * `PRECTOT (mm)`: Daily total precipitation (rainfall) in millimeters.

2.  **Soil Data CSV:** (Can contain data for one or more sites, the simulation uses the first row)
    * `Field Capacity (mm/m)`: Soil water content at field capacity (upper drained limit) in millimeters per meter depth.
    * `Wilting Point (mm/m)`: Soil water content at the permanent wilting point in millimeters per meter depth.
    * *(Other columns can be present but are not used by this simulation)*

3.  **Crop Coefficient (Kc) Data CSV (Optional):** If not provided, the model uses default Kc values based on typical maize growth stages.
    * `Day After Planting`: Integer representing the number of days after the start of the growing season.
    * `Kc`: Crop coefficient value (dimensionless) for that stage. The model uses the Kc value for the latest `Day After Planting` that is less than or equal to the current simulation day.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs or feature suggestions. 
## License

