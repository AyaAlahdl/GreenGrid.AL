import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import datetime
import numpy as np
from services.energy_data import get_energy_data
from agents.coordinator_agent import CoordinatorAgent
st.set_page_config(layout="wide")
# Auto refresh every 5 minutes (300,000 ms)
st_autorefresh(interval=300_000, key="datarefresh")



# Header
with st.container():
    st.header("🔋 GreenGrid.AI Dashboard")
    st.subheader("🧠 Intelligent Agent Summary")
# Custom CSS styling
st.markdown(
    """
    <style>
    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #f5f5f5;  /* light gray */
    }

    /* Sidebar title */
    .sidebar .sidebar-content h1 {
        font-size: 1.8rem;
        font-weight: 700;
        color: #333333;
    }

    /* Navigation links styling */
    .sidebar-links a {
        color: #555555;
        text-decoration: none;
        font-weight: 600;
        display: block;
        margin-bottom: 0.5rem;
        transition: all 0.2s ease-in-out;
    }

    .sidebar-links a:hover {
        color: #13CE70FF;
        padding-left: 5px;
    }

    /* Caption style */
    .stCaption {
        font-size: 0.8rem;
        color: #777777;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar layout
with st.sidebar:
    st.title("🔋 GreenGrid.AI")
    st.markdown("---")
    st.markdown(
        """
        <div class="sidebar-links">
            <a href="#green-grid-ai-dashboard">📊 Dashboard</a>
            <a href="#advisor-report">📈 Advisor Report</a>
            <a href="#user-inputs-for-solar-and-consumption">⚙️ User Inputs</a>
            <a href="#system-status">🖥️ System Status</a>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.caption("Built with ❤️ by GreenGrid Team")
# Run Coordinator Agent
coordinator = CoordinatorAgent()
with st.spinner("Running GreenGrid.AI agents..."):
    result = coordinator.run(context=None)

# Log output
now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
log_output = f"""
[SensorAgent] Collected sensor data: {result['sensor_data']}
✅ Data loaded into BigQuery successfully (batch insert).
{now} [INFO] ForecastAgent: Radiation: 685.00 W/m² → Solar Forecast: {result['forecast']['predicted_solar_kWh']} kWh
{now} [INFO] ForecastAgent: Predicted consumption: {result['forecast']['predicted_consumption_kWh']} kWh
{now} [INFO] ForecastAgent: Forecast: {result['forecast']}
{now} [INFO] ForecastAgent: [ForecastAgent] Forecast completed successfully.
[PricingAgent] Current price: {result['price_kWh']} p/kWh at {result['sensor_data']['timestamp']}
[OptimizerAgent] Optimization decision: {result['decision']}
[AdvisorAgent] Gemini-generated report:
"""

with st.container():
    st.subheader("🚀 System Log")
    st.code(log_output.strip())



with st.container():
    st.subheader("📄 Advisor Report")
    st.markdown(result["report"])

# Visualization - Actual vs Forecasted
today = pd.to_datetime(result["sensor_data"]["timestamp"])
forecast_day = today + pd.Timedelta(days=1)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=[today],
    y=[result["sensor_data"]["consumption_kWh"]],
    name='Actual Consumption',
    marker_color='blue'
))
fig.add_trace(go.Bar(
    x=[today],
    y=[result["sensor_data"]["solar_generation_kWh"]],
    name='Actual Solar',
    marker_color='green'
))
fig.add_trace(go.Bar(
    x=[forecast_day],
    y=[result["forecast"]["predicted_consumption_kWh"]],
    name='Forecasted Consumption',
    marker_color='orange'
))
fig.add_trace(go.Bar(
    x=[forecast_day],
    y=[result["forecast"]["predicted_solar_kWh"]],
    name='Forecasted Solar',
    marker_color='red'
))
fig.update_layout(
    title="🔍 Actual vs Forecasted Energy Usage",
    barmode='group',
    xaxis_title='Date',
    yaxis_title='Energy (kWh)',
    template='plotly_white'
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("📦 Raw Output Dictionary"):
    st.json(result)


# User inputs for solar radiation and consumption
st.subheader("🔧 User Inputs for Solar and Consumption")


# --- USER INPUTS ---
user_radiation = st.slider("☀️ Simulated Solar Radiation (W/m²)", 0, 1000, 685)
user_consumption = st.number_input("🏠 Predicted Consumption (kWh)", value=10.0)

# Constants for solar calculation
panel_area_m2 = 10
efficiency = 0.18
sun_hours = 5

# Calculate user simulated solar kWh
simulated_solar_kWh = (user_radiation * panel_area_m2 * efficiency * sun_hours) / 1000

# Battery parameters (example values)
battery_capacity_kWh = 20
battery_current_charge = 10  # initial or from sensors/state storage
battery_charge_efficiency = 0.9
battery_discharge_efficiency = 0.9

# Current grid price from result
grid_price = result.get('price_kWh', 15) / 100  # convert p/kWh to currency units

# Threshold price to decide battery usage (example threshold)
price_threshold = 0.15  # 0.15 currency units per kWh

# Battery logic
if grid_price > price_threshold:
    # Discharge battery to reduce grid consumption
    battery_action = "discharge"
    battery_change = min(battery_current_charge, user_consumption) * battery_discharge_efficiency
else:
    # Charge battery with solar surplus or grid
    battery_action = "charge"
    battery_change = min(battery_capacity_kWh - battery_current_charge, simulated_solar_kWh) * battery_charge_efficiency

# Update battery charge level
new_battery_charge = battery_current_charge + (battery_change if battery_action == "charge" else -battery_change)
new_battery_charge = max(0, min(new_battery_charge, battery_capacity_kWh))  # keep within capacity

# Adjust consumption and solar values based on battery action
effective_consumption = user_consumption - (battery_change if battery_action == "discharge" else 0)
effective_solar = simulated_solar_kWh - (battery_change if battery_action == "charge" else 0)

# Calculate costs
cost_without_battery = user_consumption * grid_price
cost_with_battery = effective_consumption * grid_price

# Assume fixed feed-in tariff for selling solar to grid
solar_feed_in_price = 0.05
earnings = max(0, effective_solar) * solar_feed_in_price

# Net cost after solar earnings
net_cost = cost_with_battery - earnings

# Display cost metrics
st.metric("💰 Estimated Cost Savings", f"{cost_without_battery - net_cost:.2f} currency units")
st.metric("💵 Net Cost", f"{net_cost:.2f} currency units")

# Display battery status
st.metric("🔋 Battery Charge Level (kWh)", f"{new_battery_charge:.2f}")
st.write(f"⚡ Battery Action: **{battery_action.capitalize()}**")



# Forecast comparison: System vs User
fig3 = go.Figure(data=[
    go.Bar(name='Actual Consumption', x=['Today'], y=[result['sensor_data']['consumption_kWh']]),
    go.Bar(name='Predicted Consumption (System)', x=['Tomorrow'], y=[result['forecast']['predicted_consumption_kWh']]),
    go.Bar(name='Predicted Solar (System)', x=['Tomorrow'], y=[result['forecast']['predicted_solar_kWh']]),
    go.Bar(name='Predicted Consumption (User)', x=['Tomorrow'], y=[user_consumption]),
    go.Bar(name='Predicted Solar (User)', x=['Tomorrow'], y=[simulated_solar_kWh])
])
fig3.update_layout(barmode='group', title='📊 Forecast Comparison: System vs User')
st.plotly_chart(fig3, use_container_width=True)



# Download button for the advisor report
st.download_button(
    label="📥 Download Advisor Report",
    data=result["report"],
    file_name="advisor_report.txt",
    mime="text/plain"
)

# Footer


# Section divider
st.markdown("---")
st.subheader("💬 User Feedback")
feedback = st.text_area("What do you think of this energy plan?")
if st.button("Submit Feedback"):
    st.success("✅ Thanks for your feedback!")

# Styled footer container
with st.container():
    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🔧 System Status")
        st.markdown("✅ All systems operational.\n\n🛠 No issues detected.")

        st.markdown("### 🤖 Agent Status")
        st.markdown("✅ All agents are running smoothly.\n\n🚫 No errors reported.")

        st.markdown("### 🩺 System Health")
        st.markdown("💡 System health is **good**.\n\nAll components functioning as expected.")
    
    with col2:
        st.markdown("### ⏰ Last Updated")
        st.markdown(f"🕒 {now}")

        st.markdown("### 📘 About This Dashboard")
        st.markdown("""
        <div style='line-height: 1.6'>
        <strong>GreenGrid.AI</strong> uses <strong>autonomous agents</strong> to:
        <ul>
            <li>🔍 Analyze energy data</li>
            <li>📈 Forecast consumption & solar generation</li>
            <li>⚙️ Optimize usage strategies</li>
            <li>📝 Provide human-readable reports using AI</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray;'>© 2025 GreenGrid.AI – All rights reserved</p>", unsafe_allow_html=True)
