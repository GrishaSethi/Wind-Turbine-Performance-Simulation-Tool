import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import weibull_min
import pandas as pd
import base64
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="Wind Turbine Performance Simulation Tool",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Main header with gradient */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Card styling */
    .metric-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin: 0.5rem 0;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Section headers */
    .section-header {
        color: #2c3e50;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

def calculate_power_output(wind_speed, air_density, blade_radius, power_coefficient):
    """
    Calculate power output using the wind power equation:
    P = 0.5 * ρ * A * Cp * V³
    """
    swept_area = np.pi * blade_radius ** 2
    power = 0.5 * air_density * swept_area * power_coefficient * (wind_speed ** 3)
    return power

def generate_weibull_wind_speeds(shape_factor, scale_factor, num_samples=10000):
    """
    Generate random wind speeds using Weibull distribution
    """
    return weibull_min.rvs(shape_factor, scale=scale_factor, size=num_samples)

def calculate_capacity_factor(power_outputs, rated_power):
    """
    Calculate capacity factor
    """
    average_power = np.mean(power_outputs)
    return average_power / rated_power

def get_preset_parameters(preset_name):
    """Return parameters for preset turbine models"""
    presets = {
        "Small (1 MW)": {
            "blade_radius": 32.0,
            "power_coefficient": 0.42,
            "rated_power": 1000
        },
        "Medium (2 MW)": {
            "blade_radius": 45.0,
            "power_coefficient": 0.45,
            "rated_power": 2000
        },
        "Large (5 MW)": {
            "blade_radius": 63.0,
            "power_coefficient": 0.48,
            "rated_power": 5000
        }
    }
    return presets.get(preset_name, {})

def create_download_link(df, filename="wind_turbine_simulation_data.csv"):
    """Generate a download link for DataFrame"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="stButton">📥 Download CSV</a>'
    return href

def main():
    # Modern Header with Gradient
    st.markdown("""
    <div class="main-header">
        <h1>🌬️ Wind Turbine Performance Simulation Tool</h1>
        <p>Advanced modeling and visualization of wind turbine power generation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for simulation control
    if 'run_simulation' not in st.session_state:
        st.session_state.run_simulation = False
    if 'auto_run' not in st.session_state:
        st.session_state.auto_run = False

    # Sidebar for user inputs
    with st.sidebar:
        st.header("⚙️ Simulation Parameters")
        
        # Preset selector
        st.subheader("Turbine Presets")
        preset = st.selectbox(
            "Choose turbine model:",
            ["Custom", "Small (1 MW)", "Medium (2 MW)", "Large (5 MW)"],
            help="Pre-configured turbine models with typical parameters"
        )
        
        # Turbine design parameters
        st.subheader("🎯 Turbine Design")
        
        if preset != "Custom":
            preset_params = get_preset_parameters(preset)
            blade_radius = st.slider(
                "Blade Radius (m)", 
                min_value=10.0, max_value=100.0, 
                value=preset_params["blade_radius"], step=1.0,
                help="Length of turbine blades from hub to tip"
            )
            power_coefficient = st.slider(
                "Power Coefficient (Cp)", 
                min_value=0.1, max_value=0.59, 
                value=preset_params["power_coefficient"], step=0.01,
                help="Betz limit: Maximum theoretical efficiency is 59.3% (0.593)"
            )
            rated_power = st.number_input(
                "Rated Power (kW)",
                min_value=100, max_value=10000,
                value=preset_params["rated_power"], step=100,
                help="Maximum power output of the turbine"
            )
        else:
            blade_radius = st.slider(
                "Blade Radius (m)", 
                min_value=10.0, max_value=100.0, 
                value=40.0, step=1.0,
                help="Length of turbine blades from hub to tip"
            )
            power_coefficient = st.slider(
                "Power Coefficient (Cp)", 
                min_value=0.1, max_value=0.59, 
                value=0.42, step=0.01,
                help="Betz limit: Maximum theoretical efficiency is 59.3% (0.593)"
            )
            rated_power = st.number_input(
                "Rated Power (kW)",
                min_value=100, max_value=10000,
                value=2000, step=100,
                help="Maximum power output of the turbine"
            )
        
        rated_power_watts = rated_power * 1000  # Convert to Watts
        
        # Environmental parameters
        st.subheader("🌍 Environmental Conditions")
        air_density = st.slider(
            "Air Density (kg/m³)", 
            min_value=1.0, max_value=1.3, 
            value=1.225, step=0.01,
            help="Standard sea level air density is 1.225 kg/m³"
        )
        
        # Wind distribution parameters
        st.subheader("💨 Wind Speed Distribution")
        shape_factor = st.slider(
            "Weibull Shape Factor (k)", 
            min_value=1.0, max_value=3.0, 
            value=2.0, step=0.1,
            help="Shape parameter of Weibull distribution. ~2.0 is typical for wind"
        )
        scale_factor = st.slider(
            "Weibull Scale Factor (c) m/s", 
            min_value=3.0, max_value=15.0, 
            value=7.0, step=0.5,
            help="Scale parameter of Weibull distribution. Typical range: 5-10 m/s"
        )
        
        # Operational constraints
        st.subheader("⚡ Operational Limits")
        cut_in_speed = st.slider(
            "Cut-in Wind Speed (m/s)",
            min_value=1.0, max_value=5.0,
            value=3.0, step=0.5,
            help="Minimum wind speed for power generation"
        )
        cut_out_speed = st.slider(
            "Cut-out Wind Speed (m/s)",
            min_value=20.0, max_value=30.0,
            value=25.0, step=0.5,
            help="Maximum wind speed for safe operation"
        )
        
        # Simulation control
        st.subheader("🔄 Simulation Control")
        col1, col2 = st.columns(2)
        with col1:
            auto_run = st.checkbox("Auto-run", value=False, help="Run simulation automatically when parameters change")
        with col2:
            num_samples = st.selectbox(
                "Samples",
                options=[1000, 5000, 10000, 50000],
                index=2,
                help="Number of wind speed samples"
            )
        
        run_simulation = st.button("🚀 Run Simulation", type="primary", use_container_width=True)
        
        if run_simulation or auto_run:
            st.session_state.run_simulation = True
            st.session_state.auto_run = auto_run

    # Main content area with tabs
    if st.session_state.run_simulation:
        # Calculate key parameters
        swept_area = np.pi * blade_radius ** 2
        
        # Generate wind speeds and calculate power
        wind_speeds = generate_weibull_wind_speeds(shape_factor, scale_factor, num_samples)
        
        # Calculate power for each wind speed
        power_outputs = []
        for speed in wind_speeds:
            if speed < cut_in_speed or speed > cut_out_speed:
                power_outputs.append(0)
            else:
                power = calculate_power_output(speed, air_density, blade_radius, power_coefficient)
                power_outputs.append(min(power, rated_power_watts))
        
        power_outputs = np.array(power_outputs)
        
        # Calculate performance metrics
        capacity_factor = calculate_capacity_factor(power_outputs, rated_power_watts)
        average_power = np.mean(power_outputs)
        average_wind_speed = np.mean(wind_speeds)
        
        # Energy calculations
        hours_per_year = 8760
        daily_energy = (average_power * 24) / 1000  # kWh
        yearly_energy = (average_power * hours_per_year) / 1000000  # MWh
        
        # Create tabs for organized content
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Performance Metrics", "📊 Visualizations", "💾 Data & Export"])
        
        with tab1:
            # Key Metrics in cards
            st.markdown('<h2 class="section-header">Key Performance Indicators</h2>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Swept Area", f"{swept_area:,.0f} m²", "Turbine Size")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Average Wind Speed", f"{average_wind_speed:.2f} m/s", "Wind Resource")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Capacity Factor", f"{capacity_factor:.2%}", "Utilization")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Annual Energy", f"{yearly_energy:,.0f} MWh", "Production")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Quick insights
            st.markdown('<h2 class="section-header">Performance Insights</h2>', unsafe_allow_html=True)
            
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                st.info(f"**Average Power Output**: {average_power/1000:.1f} kW")
                st.info(f"**Daily Energy Production**: {daily_energy:,.0f} kWh")
                st.info(f"**Theoretical Max Cp**: 59.3% (Betz Limit)")
                
            with insight_col2:
                st.success(f"**Operating Range**: {cut_in_speed} - {cut_out_speed} m/s")
                st.success(f"**Rated Power**: {rated_power:,} kW")
                st.success(f"**Wind Sample Size**: {num_samples:,} data points")
        
        with tab2:
            st.markdown('<h2 class="section-header">Detailed Performance Analysis</h2>', unsafe_allow_html=True)
            
            # Capacity Factor Gauge
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = capacity_factor,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Capacity Factor", 'font': {'size': 24}},
                    gauge = {
                        'axis': {'range': [0, 1], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': "darkblue"},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 0.25], 'color': '#ff6b6b'},
                            {'range': [0.25, 0.5], 'color': '#ffe66d'},
                            {'range': [0.5, 1], 'color': '#51cf66'}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 0.45
                        }
                    }
                ))
                fig_gauge.update_layout(height=400, font={'color': "darkblue", 'family': "Arial"})
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            with col2:
                st.subheader("Performance Summary")
                st.metric("Average Power", f"{average_power/1000:.1f} kW")
                st.metric("Max Theoretical", f"{rated_power:,} kW")
                st.metric("Efficiency", f"{(average_power/rated_power_watts)*100:.1f}%")
                st.metric("Annual Revenue*", f"${yearly_energy * 50:,.0f}")
                st.caption("*Assuming $50/MWh electricity price")
        
        with tab3:
            st.markdown('<h2 class="section-header">Performance Visualizations</h2>', unsafe_allow_html=True)
            
            # Power curve and wind distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Power Curve")
                
                # Y-axis scale selector
                y_scale = st.radio("Y-axis Scale:", ["Linear", "Logarithmic"], horizontal=True, key="y_scale")
                
                theoretical_speeds = np.linspace(0, 30, 100)
                theoretical_power = []
                
                for speed in theoretical_speeds:
                    if speed < cut_in_speed or speed > cut_out_speed:
                        theoretical_power.append(0)
                    else:
                        power = calculate_power_output(speed, air_density, blade_radius, power_coefficient)
                        theoretical_power.append(min(power, rated_power_watts))
                
                fig_power = go.Figure()
                fig_power.add_trace(go.Scatter(
                    x=theoretical_speeds, 
                    y=np.array(theoretical_power)/1000,
                    mode='lines',
                    name='Power Curve',
                    line=dict(color='#667eea', width=4),
                    hovertemplate='<b>Wind Speed</b>: %{x} m/s<br><b>Power</b>: %{y:.1f} kW<extra></extra>'
                ))
                
                # Add operational limits
                fig_power.add_vline(x=cut_in_speed, line_dash="dash", line_color="green", 
                                  annotation_text="Cut-in", annotation_position="top right")
                fig_power.add_vline(x=cut_out_speed, line_dash="dash", line_color="red",
                                  annotation_text="Cut-out", annotation_position="top left")
                
                fig_power.update_layout(
                    title="Turbine Power Curve",
                    xaxis_title="Wind Speed (m/s)",
                    yaxis_title="Power Output (kW)",
                    height=500,
                    yaxis_type="log" if y_scale == "Logarithmic" else "linear",
                    hovermode='x unified'
                )
                st.plotly_chart(fig_power, use_container_width=True)
            
            with col2:
                st.subheader("Wind Speed Distribution")
                fig_wind = px.histogram(
                    x=wind_speeds, 
                    nbins=50,
                    title="Wind Speed Distribution (Weibull)",
                    labels={'x': 'Wind Speed (m/s)', 'y': 'Frequency'},
                    color_discrete_sequence=['#764ba2']
                )
                fig_wind.update_layout(height=500)
                fig_wind.add_vline(x=average_wind_speed, line_dash="dash", line_color="red", 
                                 annotation_text=f"Mean: {average_wind_speed:.2f} m/s")
                fig_wind.update_traces(hovertemplate='<b>Wind Speed</b>: %{x} m/s<br><b>Frequency</b>: %{y}<extra></extra>')
                st.plotly_chart(fig_wind, use_container_width=True)
            
            # Additional charts
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader("Power Output Distribution")
                fig_power_dist = px.histogram(
                    x=power_outputs/1000,
                    nbins=50,
                    title="Power Output Distribution",
                    labels={'x': 'Power Output (kW)', 'y': 'Frequency'},
                    color_discrete_sequence=['#51cf66']
                )
                fig_power_dist.update_layout(height=400)
                fig_power_dist.add_vline(x=average_power/1000, line_dash="dash", line_color="green",
                                       annotation_text=f"Mean: {average_power/1000:.1f} kW")
                fig_power_dist.update_traces(hovertemplate='<b>Power</b>: %{x} kW<br><b>Frequency</b>: %{y}<extra></extra>')
                st.plotly_chart(fig_power_dist, use_container_width=True)
            
            with col4:
                st.subheader("Wind vs Power Scatter")
                # Sample points for scatter plot (for performance)
                sample_indices = np.random.choice(len(wind_speeds), min(1000, len(wind_speeds)), replace=False)
                fig_scatter = px.scatter(
                    x=wind_speeds[sample_indices],
                    y=power_outputs[sample_indices]/1000,
                    title="Wind Speed vs Power Output",
                    labels={'x': 'Wind Speed (m/s)', 'y': 'Power Output (kW)'},
                    opacity=0.6
                )
                fig_scatter.update_layout(height=400)
                fig_scatter.update_traces(hovertemplate='<b>Wind</b>: %{x} m/s<br><b>Power</b>: %{y} kW<extra></extra>')
                st.plotly_chart(fig_scatter, use_container_width=True)
        
        with tab4:
            st.markdown('<h2 class="section-header">Simulation Data & Export</h2>', unsafe_allow_html=True)
            
            # Data table
            st.subheader("Sample Data")
            sample_data = pd.DataFrame({
                'Wind_Speed_m_s': wind_speeds[:100],
                'Power_Output_kW': power_outputs[:100] / 1000,
                'Operating_Status': np.where((wind_speeds[:100] >= cut_in_speed) & (wind_speeds[:100] <= cut_out_speed), 'Operating', 'Idle')
            })
            st.dataframe(sample_data, use_container_width=True)
            
            # Export options
            st.subheader("Export Data")
            col1, col2 = st.columns(2)
            
            with col1:
                # Full dataset download
                full_data = pd.DataFrame({
                    'Wind_Speed_m_s': wind_speeds,
                    'Power_Output_W': power_outputs,
                    'Power_Output_kW': power_outputs / 1000,
                    'Operating_Status': np.where((wind_speeds >= cut_in_speed) & (wind_speeds <= cut_out_speed), 'Operating', 'Idle')
                })
                st.markdown(create_download_link(full_data), unsafe_allow_html=True)
            
            with col2:
                # PDF Report stub
                if st.button("📄 Generate Report (PDF)"):
                    st.info("""
                    **PDF Export Feature Notes:**
                    - Full PDF reporting requires additional dependencies
                    - Suggested implementation: Use `weasyprint` or `reportlab`
                    - Alternative: Export charts as PNG and data as CSV
                    - This is a stub for future implementation
                    """)
            
            # Technical summary
            st.subheader("Technical Summary")
            tech_col1, tech_col2 = st.columns(2)
            
            with tech_col1:
                st.markdown("""
                **Simulation Parameters:**
                - Blade Radius: {:.1f} m
                - Swept Area: {:.0f} m²
                - Power Coefficient: {:.2f}
                - Rated Power: {:,} kW
                """.format(blade_radius, swept_area, power_coefficient, rated_power))
            
            with tech_col2:
                st.markdown("""
                **Wind Conditions:**
                - Weibull k: {:.1f}
                - Weibull c: {:.1f} m/s
                - Avg Wind Speed: {:.2f} m/s
                - Capacity Factor: {:.2%}
                """.format(shape_factor, scale_factor, average_wind_speed, capacity_factor))
    
    else:
        # Welcome screen when simulation hasn't been run
        st.markdown("""
        <div style='text-align: center; padding: 4rem 2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px;'>
            <h2 style='color: #2c3e50; margin-bottom: 1rem;'>🚀 Ready to Simulate</h2>
            <p style='color: #6c757d; font-size: 1.2rem; margin-bottom: 2rem;'>
                Configure your turbine parameters in the sidebar and click "Run Simulation" to start analyzing performance.
            </p>
            <div style='display: inline-block; background: #667eea; color: white; padding: 0.75rem 2rem; border-radius: 8px; font-weight: bold;'>
                ← Use the sidebar to get started
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick feature overview
        st.markdown("""
        ## 📋 Features Overview
        
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin-top: 2rem;'>
            <div style='padding: 1.5rem; background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h4>🎯 Realistic Modeling</h4>
                <p>Weibull distribution for accurate wind speed simulation with operational constraints.</p>
            </div>
            <div style='padding: 1.5rem; background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h4>📊 Interactive Charts</h4>
                <p>Plotly-powered visualizations with hover details and multiple chart types.</p>
            </div>
            <div style='padding: 1.5rem; background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h4>💾 Data Export</h4>
                <p>Download simulation data as CSV for further analysis in external tools.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()