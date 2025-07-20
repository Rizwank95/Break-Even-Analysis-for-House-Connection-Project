import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import io

# Your information
about_info = {
    "name": "Muhammad Rizwan Khan",
    "company": "RAPCO Contracting and Industrial Construction Services",
    "contact": "muhammad.rizwan@rapcogroups.com",
    "project": "Water and Sewer Connection Project, Saudi Arabia",
    "last_updated": "July 2025"
}

def water_connection_value(size, length):
    value = 0
    if size == 25:
        connection = 2200
        water_meter = 750
        meter_box = 170
        value = connection + water_meter + meter_box
        if length > 5:
            value += (length - 5) * 190
    elif size == 32:
        connection = 2300
        water_meter = 950
        meter_box = 170
        value = connection + water_meter + meter_box
        if length > 5:
            value += (length - 5) * 195
    return value

def sewer_connection_value(type_, length):
    value = 0
    if type_ == "mainline":
        connection = 4700
        cleanout = 1600
        value = connection + cleanout
        if length > 5:
            value += (length - 5) * 360
    elif type_ == "manhole":
        connection = 4200
        cleanout = 1600
        value = connection + cleanout
        if length > 5:
            value += (length - 5) * 360
    return value

def water_connection_material_cost(size, length, pipe_cost, meter_cost, asphalt_cost, bedding_cost):
    total_length = length + 1.5
    pipe_cost = total_length * pipe_cost
    meter_cost = meter_cost
    fitting_cost = 0.2 * pipe_cost
    asphalt_cost = 0.8 * 0.85 * length * 0.417 * asphalt_cost
    bedding_cost = ((size / 1000) + 0.15) * 0.8 * length * 44
    total_cost = (pipe_cost + meter_cost + fitting_cost + asphalt_cost + bedding_cost) * 1.15
    return total_cost

def sewer_connection_material_cost(length, pipe_cost, asphalt_cost, bedding_cost):
    total_length = length + 1.5
    pipe_cost = total_length * pipe_cost
    fitting_cost = 0.2 * pipe_cost
    asphalt_cost = 0.8 * 0.85 * length * 0.417 * asphalt_cost
    bedding_cost = (0.15) * 0.8 * length * 44
    total_cost = (pipe_cost + fitting_cost + asphalt_cost + bedding_cost) * 1.15
    return total_cost

def calculate_break_even(current_expenses, invoices_received, store_stock_value, water_params, sewer_params, monthly_direct_cost, monthly_indirect_cost, connection_rate=None, duration_months=None, prob_water=50, prob_25mm=50, prob_mainline=50):
    prob_water = prob_water / 100
    prob_25mm = prob_25mm / 100
    prob_mainEOL = prob_mainline / 100

    if prob_water < 0 or prob_water > 1 or prob_25mm < 0 or prob_25mm > 1 or prob_mainline < 0 or prob_mainline > 1:
        return {"error": "Proportions and probabilities must be between 0 and 100"}
    if current_expenses < 0 or invoices_received < 0 or store_stock_value < 0 or monthly_direct_cost < 0 or monthly_indirect_cost < 0:
        return {"error": "Expenses, invoices, stock value, and costs must be positive"}
    if (connection_rate is None and duration_months is None) or (connection_rate is not None and duration_months is not None):
        return {"error": "Provide either connection rate or duration, not both or neither"}
    if connection_rate is not None and connection_rate <= 0:
        return {"error": "Connection rate must be positive"}
    if duration_months is not None and duration_months <= 0:
        return {"error": "Duration must be positive"}
    if water_params['min_length'] < 0 or water_params['max_length'] < water_params['min_length']:
        return {"error": "Connection lengths must be positive, and max_length must be at least min_length"}
    if sewer_params['min_length'] < 0 or sewer_params['max_length'] < sewer_params['min_length']:
        return {"error": "Connection lengths must be positive, and max_length must be at least min_length"}

    net_current_expenses = current_expenses - invoices_received - store_stock_value
    if net_current_expenses < 0:
        return {"error": "Invoices received and store stock value cannot exceed current expenses"}

    avg_water_length = (water_params['min_length'] + water_params['max_length']) / 2
    avg_sewer_length = (sewer_params['min_length'] + sewer_params['max_length']) / 2

    water_value_25 = water_connection_value(25, avg_water_length)
    water_value_32 = water_connection_value(32, avg_water_length)
    avg_water_value = (prob_25mm * water_value_25) + ((1 - prob_25mm) * water_value_32)
    water_material_cost_25 = water_connection_material_cost(
        25, avg_water_length, water_params['pipe_cost_25'], water_params['meter_cost_25'],
        water_params['asphalt_cost'], water_params['bedding_cost']
    )
    water_material_cost_32 = water_connection_material_cost(
        32, avg_water_length, water_params['pipe_cost_32'], water_params['meter_cost_32'],
        water_params['asphalt_cost'], water_params['bedding_cost']
    )
    avg_water_material_cost = (prob_25mm * water_material_cost_25) + ((1 - prob_25mm) * water_material_cost_32)

    sewer_value_mainline = sewer_connection_value('mainline', avg_sewer_length)
    sewer_value_manhole = sewer_connection_value('manhole', avg_sewer_length)
    avg_sewer_value = (prob_mainline * sewer_value_mainline) + ((1 - prob_mainline) * sewer_value_manhole)
    sewer_material_cost_mainline = sewer_connection_material_cost(
        avg_sewer_length, sewer_params['pipe_cost'], sewer_params['asphalt_cost'], sewer_params['bedding_cost']
    )
    sewer_material_cost_manhole = sewer_connection_material_cost(
        avg_sewer_length, sewer_params['pipe_cost'], sewer_params['asphalt_cost'], sewer_params['bedding_cost']
    )
    avg_sewer_material_cost = (prob_mainline * sewer_material_cost_mainline) + ((1 - prob_mainline) * sewer_material_cost_manhole)

    avg_value_per_connection = (prob_water * avg_water_value) + ((1 - prob_water) * avg_sewer_value)
    avg_material_cost_per_connection = (prob_water * avg_water_material_cost) + ((1 - prob_water) * avg_sewer_material_cost)

    max_connection_rate = 50
    min_direct_cost = monthly_direct_cost / max_connection_rate
    min_indirect_cost = monthly_indirect_cost / max_connection_rate
    min_total_cost = avg_material_cost_per_connection + min_direct_cost + min_indirect_cost
    min_net_revenue = avg_value_per_connection - min_total_cost
    min_break_even_connections = net_current_expenses / min_net_revenue if min_net_revenue > 0 else float('inf')
    min_duration = min_break_even_connections / max_connection_rate if min_break_even_connections != float('inf') else float('inf')

    if connection_rate is not None:
        direct_cost_per_connection = monthly_direct_cost / connection_rate
        indirect_cost_per_connection = monthly_indirect_cost / connection_rate
        total_cost_per_connection = avg_material_cost_per_connection + direct_cost_per_connection + indirect_cost_per_connection
        net_revenue_per_connection = avg_value_per_connection - total_cost_per_connection
        if net_revenue_per_connection <= 0:
            return {
                "error": (
                    f"Average value per connection (SAR {avg_value_per_connection:,.2f}) "
                    f"must exceed total cost per connection (SAR {total_cost_per_connection:,.2f}). "
                    f"Minimum feasible duration with {max_connection_rate} connections/month: {min_duration:,.2f} months. "
                    f"Try reducing monthly costs (direct: SAR {monthly_direct_cost:,.2f}, indirect: SAR {monthly_indirect_cost:,.2f}) "
                    f"or increasing connection value."
                )
            }
        break_even_connections = net_current_expenses / net_revenue_per_connection
        break_even_connections_rounded = round(break_even_connections)
        break_even_months = break_even_connections / connection_rate
    else:
        break_even_connections = (net_current_expenses + (monthly_direct_cost + monthly_indirect_cost) * duration_months) / (avg_value_per_connection - avg_material_cost_per_connection)
        connection_rate = break_even_connections / duration_months
        if connection_rate <= 0:
            return {
                "error": (
                    f"Required connection rate ({connection_rate:,.2f} connections/month) is infeasible for the given duration ({duration_months} months). "
                    f"Minimum feasible duration with {max_connection_rate} connections/month: {min_duration:,.2f} months. "
                    f"Try increasing duration, reducing monthly costs (direct: SAR {monthly_direct_cost:,.2f}, indirect: SAR {monthly_indirect_cost:,.2f}), "
                    f"or increasing connection value."
                )
            }
        direct_cost_per_connection = monthly_direct_cost / connection_rate
        indirect_cost_per_connection = monthly_indirect_cost / connection_rate
        total_cost_per_connection = avg_material_cost_per_connection + direct_cost_per_connection + indirect_cost_per_connection
        net_revenue_per_connection = avg_value_per_connection - total_cost_per_connection
        if net_revenue_per_connection <= 0:
            return {
                "error": (
                    f"Average value per connection (SAR {avg_value_per_connection:,.2f}) "
                    f"must exceed total cost per connection (SAR {total_cost_per_connection:,.2f}) for the given duration ({duration_months} months). "
                    f"Minimum feasible duration with {max_connection_rate} connections/month: {min_duration:,.2f} months. "
                    f"Try increasing duration, reducing monthly costs (direct: SAR {monthly_direct_cost:,.2f}, indirect: SAR {monthly_indirect_cost:,.2f}), "
                    f"or increasing connection value."
                )
            }
        break_even_connections_rounded = round(break_even_connections)
        break_even_months = duration_months

    start_date = datetime(2025, 8, 1)
    break_even_date = start_date + relativedelta(months=int(break_even_months), days=round((break_even_months % 1) * 30))
    total_expenses = net_current_expenses + (break_even_connections_rounded * total_cost_per_connection)

    return {
        'current_expenses': current_expenses,
        'invoices_received': invoices_received,
        'store_stock_value': store_stock_value,
        'net_current_expenses': net_current_expenses,
        'avg_water_value': avg_water_value,
        'avg_sewer_value': avg_sewer_value,
        'avg_value_per_connection': avg_value_per_connection,
        'avg_water_material_cost': avg_water_material_cost,
        'avg_sewer_material_cost': avg_sewer_material_cost,
        'avg_material_cost_per_connection': avg_material_cost_per_connection,
        'direct_cost_per_connection': direct_cost_per_connection,
        'indirect_cost_per_connection': indirect_cost_per_connection,
        'total_cost_per_connection': total_cost_per_connection,
        'net_revenue_per_connection': net_revenue_per_connection,
        'connection_rate': connection_rate,
        'break_even_connections': break_even_connections,
        'break_even_connections_rounded': break_even_connections_rounded,
        'break_even_months': break_even_months,
        'break_even_date': break_even_date.strftime('%B %Y'),
        'total_expenses_at_break_even': total_expenses,
        'total_revenue_at_break_even': break_even_connections_rounded * avg_value_per_connection
    }

def plot_break_even(result):
    if "error" in result:
        st.warning("Cannot generate plot due to error in calculations: " + result["error"])
        return None

    # Create subplots: two rows, one column
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Revenue vs. Expenses by Connections", "Revenue vs. Expenses by Time"),
        vertical_spacing=0.15
    )

    # Data for plots
    connections = list(range(0, int(result['break_even_connections_rounded'] * 1.5) + 1))
    revenue = [c * result['avg_value_per_connection'] for c in connections]
    total_expenses = [result['net_current_expenses'] + (c * result['total_cost_per_connection']) for c in connections]
    start_date = datetime(2025, 8, 1)
    months = [c / result['connection_rate'] for c in connections]
    month_labels = [(start_date + relativedelta(months=int(m))).strftime('%b %Y') for m in months]
    month_ticks = months[::max(1, int(len(months)/5))]
    month_labels_ticks = month_labels[::max(1, int(len(months)/5))]

    # Plot 1: Revenue and Expenses by Connections
    fig.add_trace(
        go.Scatter(x=connections, y=revenue, mode='lines', name='Revenue', line=dict(color='#1f77b4', width=3)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=connections, y=total_expenses, mode='lines', name='Total Expenses', line=dict(color='#ff7f0e', width=3, dash='dash')),
        row=1, col=1
    )
    fig.add_vline(x=result['break_even_connections'], line=dict(color='#2ca02c', dash='dot', width=2), row=1, col=1)
    be_conn = result['break_even_connections']
    be_value = be_conn * result['avg_value_per_connection']
    fig.add_annotation(
        x=be_conn, y=be_value,
        text=f"Break-Even: {int(be_conn)} Connections<br>SAR {be_value:,.0f}",
        showarrow=True, arrowhead=1, ax=50, ay=-30,
        font=dict(size=10), bgcolor="white", bordercolor="black", borderwidth=1,
        row=1, col=1
    )

    # Plot 2: Revenue and Expenses by Time
    fig.add_trace(
        go.Scatter(x=months, y=revenue, mode='lines', name='Revenue', line=dict(color='#1f77b4', width=3), showlegend=False),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=months, y=total_expenses, mode='lines', name='Total Expenses', line=dict(color='#ff7f0e', width=3, dash='dash'), showlegend=False),
        row=2, col=1
    )
    fig.add_vline(x=result['break_even_months'], line=dict(color='#2ca02c', dash='dot', width=2), row=2, col=1)
    be_months = result['break_even_months']
    be_date = result['break_even_date']
    fig.add_annotation(
        x=be_months, y=be_value,
        text=f"Break-Even: {be_date}",
        showarrow=True, arrowhead=1, ax=50, ay=-30,
        font=dict(size=10), bgcolor="white", bordercolor="black", borderwidth=1,
        row=2, col=1
    )

    # Update layout for a beautiful, professional look
    fig.update_layout(
        title=dict(
            text="Break-Even Analysis for Water and Sewer Connection Project",
            font=dict(size=18, family="Arial", color="#333333"),
            x=0.5, xanchor="center", y=0.98
        ),
        height=800,
        showlegend=True,
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.8)", bordercolor="black", borderwidth=1),
        template="plotly_white",
        margin=dict(t=100, b=100, l=80, r=80)
    )
    fig.update_xaxes(title_text="Number of Connections", row=1, col=1, title_font=dict(size=14), tickfont=dict(size=12))
    fig.update_yaxes(title_text="Amount (SAR)", row=1, col=1, title_font=dict(size=14), tickfont=dict(size=12), tickformat=",.0f")
    fig.update_xaxes(
        title_text="Time (Months)", row=2, col=1, title_font=dict(size=14), tickfont=dict(size=12),
        tickvals=month_ticks, ticktext=month_labels_ticks, tickangle=45
    )
    fig.update_yaxes(title_text="Amount (SAR)", row=2, col=1, title_font=dict(size=14), tickfont=dict(size=12), tickformat=",.0f")

    return fig

def main():
    st.title("Break-Even Calculator for House Connection Project")
    st.write("Enter project details to calculate the break-even point for a water and sewer connection project in Saudi Arabia (all monetary values in SAR).")

    # Sidebar with your information
    with st.sidebar:
        st.header("About")
        st.write(f"**Developed by**: {about_info['name']}")
        st.write(f"**Company**: {about_info['company']}")
        st.write(f"**Contact**: {about_info['contact']}")
        st.write(f"**Project**: {about_info['project']}")
        st.write(f"**Last Updated**: {about_info['last_updated']}")

    with st.form("input_form"):
        st.subheader("Project Expenses")
        current_expenses = st.number_input("Current project expenses (SAR)", min_value=0.0, step=1000.0, format="%.2f")
        invoices_received = st.number_input("Invoices already received (SAR)", min_value=0.0, step=1000.0, format="%.2f")
        store_stock_value = st.number_input("Store stock value (SAR)", min_value=0.0, step=1000.0, format="%.2f")

        st.subheader("Connection Lengths")
        min_connection_length = st.number_input("Minimum connection length (meters)", min_value=0.0, step=1.0, format="%.2f")
        max_connection_length = st.number_input("Maximum connection length (meters)", min_value=0.0, step=1.0, format="%.2f")

        st.subheader("Material Costs")
        water_pipe_cost_25 = st.number_input("Water pipe cost for 25mm (SAR/meter)", min_value=0.0, step=10.0, format="%.2f")
        water_pipe_cost_32 = st.number_input("Water pipe cost for 32mm (SAR/meter)", min_value=0.0, step=10.0, format="%.2f")
        water_meter_cost_25 = st.number_input("Water meter cost for 25mm (SAR)", min_value=0.0, step=100.0, format="%.2f")
        water_meter_cost_32 = st.number_input("Water meter cost for 32mm (SAR)", min_value=0.0, step=100.0, format="%.2f")
        asphalt_cost = st.number_input("Asphalt cost (SAR/unit)", min_value=0.0, step=100.0, format="%.2f")
        bedding_cost = st.number_input("Bedding cost (SAR/unit)", min_value=0.0, step=100.0, format="%.2f")
        sewer_pipe_cost = st.number_input("Sewer pipe cost (SAR/meter)", min_value=0.0, step=10.0, format="%.2f")

        st.subheader("Probabilities")
        prob_water = st.number_input("Probability of water connection (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f")
        prob_25mm = st.number_input("Probability of 25mm water connection (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f")
        prob_mainline = st.number_input("Probability of mainline sewer connection (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f")

        st.subheader("Monthly Costs")
        monthly_direct_cost = st.number_input("Monthly direct cost (e.g., labor, equipment) (SAR)", min_value=0.0, step=1000.0, format="%.2f")
        monthly_indirect_cost = st.number_input("Monthly indirect cost (e.g., overhead) (SAR)", min_value=0.0, step=1000.0, format="%.2f")

        st.subheader("Calculation Option")
        option = st.radio("Choose calculation option", ("Option 1: Enter connection rate", "Option 2: Enter desired duration"))
        connection_rate = None
        duration_months = None
        if option == "Option 1: Enter connection rate":
            connection_rate = st.number_input("Connection rate (connections per month)", min_value=0.01, step=1.0, format="%.2f")
        else:
            duration_months = st.number_input("Desired break-even duration (months)", min_value=0.01, step=1.0, format="%.2f")

        submitted = st.form_submit_button("Calculate Break-Even")

    water_params = {
        'min_length': min_connection_length,
        'max_length': max_connection_length,
        'pipe_cost_25': water_pipe_cost_25,
        'pipe_cost_32': water_pipe_cost_32,
        'meter_cost_25': water_meter_cost_25,
        'meter_cost_32': water_meter_cost_32,
        'asphalt_cost': asphalt_cost,
        'bedding_cost': bedding_cost
    }
    sewer_params = {
        'min_length': min_connection_length,
        'max_length': max_connection_length,
        'pipe_cost': sewer_pipe_cost,
        'asphalt_cost': asphalt_cost,
        'bedding_cost': bedding_cost
    }

    if submitted:
        result = calculate_break_even(
            current_expenses, invoices_received, store_stock_value, water_params, sewer_params,
            monthly_direct_cost, monthly_indirect_cost, connection_rate, duration_months,
            prob_water, prob_25mm, prob_mainline
        )

        if "error" in result:
            st.error(result["error"])
        else:
            st.subheader("Break-Even Analysis Results")
            st.write(f"**Current Project Expenses**: SAR {result['current_expenses']:,.2f}")
            st.write(f"**Invoices Already Received**: SAR {result['invoices_received']:,.2f}")
            st.write(f"**Store Stock Value**: SAR {result['store_stock_value']:,.2f}")
            st.write(f"**Net Current Expenses**: SAR {result['net_current_expenses']:,.2f}")
            st.write(f"**Average Water Connection Value**: SAR {result['avg_water_value']:,.2f}")
            st.write(f"**Average Sewer Connection Value**: SAR {result['avg_sewer_value']:,.2f}")
            st.write(f"**Average Value per Connection**: SAR {result['avg_value_per_connection']:,.2f}")
            st.write(f"**Average Water Material Cost per Connection**: SAR {result['avg_water_material_cost']:,.2f}")
            st.write(f"**Average Sewer Material Cost per Connection**: SAR {result['avg_sewer_material_cost']:,.2f}")
            st.write(f"**Average Material Cost per Connection**: SAR {result['avg_material_cost_per_connection']:,.2f}")
            st.write(f"**Direct Cost per Connection**: SAR {result['direct_cost_per_connection']:,.2f}")
            st.write(f"**Indirect Cost per Connection**: SAR {result['indirect_cost_per_connection']:,.2f}")
            st.write(f"**Total Cost per Connection**: SAR {result['total_cost_per_connection']:,.2f}")
            st.write(f"**Net Revenue per Connection**: SAR {result['net_revenue_per_connection']:,.2f}")
            st.write(f"**Connection Rate**: {result['connection_rate']:.2f} connections/month")
            st.write(f"**Connections Needed to Break Even**: {result['break_even_connections_rounded']} "
                     f"({result['break_even_connections']:,.2f} unrounded)")
            st.write(f"**Time to Break Even**: {result['break_even_months']:,.2f} months")
            st.write(f"**Break-Even Date**: {result['break_even_date']}")
            st.write(f"**Total Expenses at Break Even**: SAR {result['total_expenses_at_break_even']:,.2f}")
            st.write(f"**Total Revenue at Break Even**: SAR {result['total_revenue_at_break_even']:,.2f}")

            fig = plot_break_even(result)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Plot could not be generated. Please check input values.")

            df = pd.DataFrame([result])
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            st.download_button(
                label="Download Results as CSV",
                data=buffer.getvalue(),
                file_name="breakeven_results.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()