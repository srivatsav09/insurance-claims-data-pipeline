"""
Insurance Claims Analytics Dashboard
Connects to the warehouse marts for real-time KPIs and visualizations.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from db import (
    get_monthly_claims,
    get_fact_claims,
    get_claims_by_vehicle,
    get_claims_by_region,
    get_claims_by_age_group,
)

# --- Page Config ---
st.set_page_config(
    page_title="Insurance Claims Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Insurance Claims Analytics Dashboard")
st.markdown("Real-time insights from the insurance claims data warehouse")

# --- Load Data ---
try:
    monthly_df = get_monthly_claims()
    fact_df = get_fact_claims()
    vehicle_df = get_claims_by_vehicle()
    region_df = get_claims_by_region()
    age_df = get_claims_by_age_group()
except Exception as e:
    st.error(f"Could not connect to the warehouse database. Make sure the pipeline has run at least once.\n\nError: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

claim_types = fact_df["claim_type"].dropna().unique().tolist()
selected_types = st.sidebar.multiselect(
    "Claim Type",
    options=claim_types,
    default=claim_types,
)

regions = fact_df["region_name"].dropna().unique().tolist()
selected_regions = st.sidebar.multiselect(
    "Region",
    options=sorted(regions),
    default=sorted(regions),
)

fraud_filter = st.sidebar.radio(
    "Fraud Flag",
    options=["All", "Fraud Only", "Non-Fraud Only"],
    index=0,
)

# Apply filters
filtered_df = fact_df.copy()
filtered_df = filtered_df[filtered_df["claim_type"].isin(selected_types)]
filtered_df = filtered_df[filtered_df["region_name"].isin(selected_regions)]

if fraud_filter == "Fraud Only":
    filtered_df = filtered_df[filtered_df["fraud_flag"] == True]
elif fraud_filter == "Non-Fraud Only":
    filtered_df = filtered_df[filtered_df["fraud_flag"] == False]

# --- KPI Cards ---
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

total_claims = len(filtered_df)
avg_amount = filtered_df["claim_amount"].mean() if total_claims > 0 else 0
approval_rate = (
    (filtered_df["claim_status"] == "Approved").sum() / total_claims * 100
    if total_claims > 0 else 0
)
fraud_rate = (
    filtered_df["fraud_flag"].sum() / total_claims * 100
    if total_claims > 0 else 0
)

col1.metric("Total Claims", f"{total_claims:,}")
col2.metric("Avg Claim Amount", f"${avg_amount:,.2f}")
col3.metric("Approval Rate", f"{approval_rate:.1f}%")
col4.metric("Fraud Rate", f"{fraud_rate:.1f}%")

# --- Row 1: Monthly Trend + Claims by Type ---
st.markdown("---")
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Monthly Claims Trend")
    fig_monthly = px.line(
        monthly_df,
        x="month",
        y="total_claims",
        markers=True,
    )
    fig_monthly.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Claims",
        height=400,
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

with row1_col2:
    st.subheader("Claims by Type")
    type_counts = filtered_df["claim_type"].value_counts().reset_index()
    type_counts.columns = ["claim_type", "count"]
    fig_type = px.bar(
        type_counts,
        x="claim_type",
        y="count",
        color="claim_type",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_type.update_layout(
        xaxis_title="Claim Type",
        yaxis_title="Count",
        showlegend=False,
        height=400,
    )
    st.plotly_chart(fig_type, use_container_width=True)

# --- Row 2: Region + Fraud Trend ---
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Claims by Region")
    fig_region = px.bar(
        region_df,
        x="region_name",
        y="claim_count",
        color="region_name",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_region.update_layout(
        xaxis_title="Region",
        yaxis_title="Number of Claims",
        showlegend=False,
        height=400,
    )
    st.plotly_chart(fig_region, use_container_width=True)

with row2_col2:
    st.subheader("Fraud Rate Over Time")
    fig_fraud = px.line(
        monthly_df,
        x="month",
        y="fraud_rate_pct",
        markers=True,
        color_discrete_sequence=["#e74c3c"],
    )
    fig_fraud.update_layout(
        xaxis_title="Month",
        yaxis_title="Fraud Rate (%)",
        height=400,
    )
    st.plotly_chart(fig_fraud, use_container_width=True)

# --- Row 3: Claim Amount Distribution + Top Vehicles ---
row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.subheader("Claim Amount Distribution")
    fig_dist = px.histogram(
        filtered_df,
        x="claim_amount",
        nbins=50,
        color_discrete_sequence=["#3498db"],
    )
    fig_dist.update_layout(
        xaxis_title="Claim Amount ($)",
        yaxis_title="Frequency",
        height=400,
    )
    st.plotly_chart(fig_dist, use_container_width=True)

with row3_col2:
    st.subheader("Top 10 Vehicle Makes by Claims")
    top_vehicles = vehicle_df.head(10)
    fig_vehicles = px.bar(
        top_vehicles,
        x="claim_count",
        y="make",
        orientation="h",
        color_discrete_sequence=["#2ecc71"],
    )
    fig_vehicles.update_layout(
        xaxis_title="Number of Claims",
        yaxis_title="Vehicle Make",
        height=400,
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig_vehicles, use_container_width=True)

# --- Row 4: Age Group + Approval/Denial Rates ---
row4_col1, row4_col2 = st.columns(2)

with row4_col1:
    st.subheader("Claims by Age Group")
    fig_age = px.bar(
        age_df,
        x="age_group",
        y="claim_count",
        color="avg_claim_amount",
        color_continuous_scale="Oranges",
    )
    fig_age.update_layout(
        xaxis_title="Age Group",
        yaxis_title="Number of Claims",
        height=400,
    )
    st.plotly_chart(fig_age, use_container_width=True)

with row4_col2:
    st.subheader("Monthly Approval vs Denial Rate")
    fig_rates = go.Figure()
    fig_rates.add_trace(go.Scatter(
        x=monthly_df["month"],
        y=monthly_df["approval_rate_pct"],
        name="Approval Rate",
        mode="lines+markers",
        line=dict(color="#2ecc71"),
    ))
    fig_rates.add_trace(go.Scatter(
        x=monthly_df["month"],
        y=monthly_df["denial_rate_pct"],
        name="Denial Rate",
        mode="lines+markers",
        line=dict(color="#e74c3c"),
    ))
    fig_rates.update_layout(
        xaxis_title="Month",
        yaxis_title="Rate (%)",
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )
    st.plotly_chart(fig_rates, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.caption("Data sourced from the insurance claims warehouse | Built with Streamlit + Plotly")
