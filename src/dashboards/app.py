"""Streamlit dashboard for APAC expansion decision engine."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import pickle
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.scoring import MarketScorer
from src.models.forecast import generate_scenarios
from src.models.monte_carlo import MonteCarloSimulator


# Page config
st.set_page_config(
    page_title="APAC Expansion Decision Engine",
    page_icon="🌏",
    layout="wide"
)

st.title("🌏 APAC Expansion Decision Engine")
st.markdown("**Data-driven market prioritization and revenue forecasting for B2B SaaS expansion**")

# Load data
@st.cache_data(ttl=60)  # Cache for 60 seconds, then refresh
def load_data():
    """Load processed data."""
    data_path = Path("data/processed/market_features.csv")
    if not data_path.exists():
        st.error("Processed data not found. Please run `python -m src.main` first.")
        st.stop()
    
    # Use file modification time as part of cache key to ensure fresh data
    file_mtime = data_path.stat().st_mtime
    
    df = pd.read_csv(data_path)
    
    # Verify standardized columns exist
    required_std_cols = [
        "market_size_score_standardized",
        "purchasing_power_score_standardized",
        "digital_readiness_score_standardized",
        "governance_risk_score_standardized",
        "corruption_risk_score_standardized"
    ]
    missing_cols = [col for col in required_std_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing standardized columns: {missing_cols}")
        st.info("Please run `python -m src.main` to regenerate data.")
        return df  # Return what we have anyway
    
    # Don't merge with scoring results - we recalculate them in the dashboard anyway
    # This avoids losing columns during merge
    
    return df


def create_radar_chart(df: pd.DataFrame, country_code: str) -> go.Figure:
    """Create radar chart for a specific market."""
    country_data = df[df["country_code"] == country_code].iloc[0]
    
    categories = [
        "Market Size",
        "Purchasing Power",
        "Digital Readiness",
        "Governance",
        "Corruption"
    ]
    
    feature_cols = [
        "market_size_score_standardized",
        "purchasing_power_score_standardized",
        "digital_readiness_score_standardized",
        "governance_risk_score_standardized",
        "corruption_risk_score_standardized"
    ]
    
    values = []
    for col in feature_cols:
        val = country_data.get(col, 0)
        # Normalize to 0-1 scale for radar (assuming z-scores)
        val_normalized = (val + 3) / 6  # Rough normalization
        val_normalized = np.clip(val_normalized, 0, 1)
        values.append(val_normalized)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=country_code,
        line_color='rgb(31, 119, 180)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False,
        title=f"Market Profile: {country_code}",
        height=400
    )
    
    return fig


# Load data
df = load_data()

# Sidebar
st.sidebar.header("Configuration")

# Data status check (collapsible)
with st.sidebar.expander("📊 Data Status", expanded=False):
    if len(df) > 0:
        st.write(f"✅ Markets loaded: {len(df)}")
        std_cols = [col for col in df.columns if 'standardized' in col]
        st.write(f"📈 Standardized columns: {len(std_cols)}")
        if len(std_cols) == 0:
            st.error("⚠️ No standardized columns found!")
            st.info("Run `python -m src.main` to generate them.")
        else:
            st.success("✅ Standardized features ready")
            # Check if key standardized columns exist
            required = [
                "market_size_score_standardized",
                "purchasing_power_score_standardized",
                "digital_readiness_score_standardized",
                "governance_risk_score_standardized",
                "corruption_risk_score_standardized"
            ]
            missing = [c for c in required if c not in df.columns]
            if missing:
                st.error(f"Missing: {missing}")
            else:
                # Show sample values
                sample_vals = df[required].iloc[0] if len(df) > 0 else None
                if sample_vals is not None:
                    st.write("Sample values (first market):")
                    for col in required:
                        val = sample_vals[col]
                        st.write(f"  {col}: {val:.4f}")
        st.write(f"📁 Total columns: {len(df.columns)}")
        if st.button("🔄 Clear Streamlit Cache", help="Force reload data on next refresh"):
            st.cache_data.clear()
            st.success("Cache cleared! Refreshing...")
            st.rerun()
    
    # Additional debug: Check standardized columns are actually present
    if len(df) > 0:
        std_cols_check = [col for col in df.columns if any(x in col for x in ['market_size_score_standardized', 'purchasing_power_score_standardized', 'digital_readiness_score_standardized', 'governance_risk_score_standardized', 'corruption_risk_score_standardized'])]
        if len(std_cols_check) < 5:
            st.sidebar.error(f"⚠️ Missing standardized cols! Found: {std_cols_check}")
    else:
        st.error("❌ No data loaded")

# Weight sliders
st.sidebar.subheader("Criteria Weights")
weights = {}

weight_market_size = st.sidebar.slider(
    "Market Size",
    0.0, 1.0,
    0.25, 0.05
)
weights["market_size"] = weight_market_size

weight_purchasing = st.sidebar.slider(
    "Purchasing Power",
    0.0, 1.0,
    0.20, 0.05
)
weights["purchasing_power"] = weight_purchasing

weight_digital = st.sidebar.slider(
    "Digital Readiness",
    0.0, 1.0,
    0.20, 0.05
)
weights["digital_readiness"] = weight_digital

weight_governance = st.sidebar.slider(
    "Governance Quality",
    0.0, 1.0,
    0.20, 0.05
)
weights["governance_risk"] = weight_governance

weight_corruption = st.sidebar.slider(
    "Corruption Risk (Low)",
    0.0, 1.0,
    0.15, 0.05
)
weights["corruption_risk"] = weight_corruption

total_weight = sum(weights.values())
if abs(total_weight - 1.0) > 0.01:
    st.sidebar.warning(f"Total weight: {total_weight:.2f} (should be 1.0)")
    # Normalize
    weights = {k: v / total_weight for k, v in weights.items()}

# Score markets with current weights (compute once for all tabs)
scorer = MarketScorer(weights)
scored_df = scorer.score_markets(df)

# Debug: Verify scores were calculated properly
if "total_score" in scored_df.columns:
    max_score = scored_df["total_score"].abs().max()
    if max_score < 0.001:
        # This will show a warning but won't stop execution
        pass  # Warning will be shown in the chart section

# Scenario toggle
st.sidebar.subheader("Forecast Scenario")
scenario = st.sidebar.selectbox(
    "Select scenario",
    ["base", "optimistic", "pessimistic"]
)

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["Market Ranking", "Market Profiles", "Forecast", "Sensitivity"])

# Tab 1: Market Ranking
with tab1:
    st.header("Market Ranking")
    
    # Display ranking table
    display_cols = [
        "rank", "country_code", "total_score"
    ]
    
    # Add component scores if available
    for weight_name in weights.keys():
        score_col = f"score_{weight_name}"
        if score_col in scored_df.columns:
            display_cols.append(score_col)
    
    # Filter to only existing columns
    display_cols = [col for col in display_cols if col in scored_df.columns]
    
    if len(scored_df) > 0:
        st.dataframe(
            scored_df[display_cols].round(3),
            use_container_width=True,
            hide_index=True
        )
        
        # Ranking bar chart - Fix: ensure data is valid and properly formatted
        if "total_score" in scored_df.columns:
            # Filter valid data and get top 10
            chart_data = scored_df[["country_code", "total_score"]].copy()
            chart_data = chart_data.dropna(subset=["total_score"])
            chart_data = chart_data.head(10)
            
            # Debug info (collapsible)
            with st.expander("🔍 Debug Info", expanded=False):
                st.write(f"Chart data shape: {chart_data.shape}")
                st.write(f"Chart data columns: {chart_data.columns.tolist()}")
                if len(chart_data) > 0:
                    st.write(f"Total score range: {chart_data['total_score'].min():.4f} to {chart_data['total_score'].max():.4f}")
                    st.write("Chart data preview:")
                    st.dataframe(chart_data)
                st.write("Available columns in scored_df:")
                st.write(scored_df.columns.tolist())
                st.write("Standardized columns present:")
                std_cols = [col for col in scored_df.columns if 'standardized' in col]
                st.write(std_cols)
            
            if len(chart_data) > 0:
                # Check if all scores are zero (which would make bars invisible)
                max_score = chart_data["total_score"].abs().max()
                if max_score < 0.001:
                    st.error("⚠️ **All scores are zero!**")
                    
                    # Debug: Show what's happening with the scoring
                    st.write("**Debugging info:**")
                    required_std_cols = [
                        "market_size_score_standardized",
                        "purchasing_power_score_standardized",
                        "digital_readiness_score_standardized",
                        "governance_risk_score_standardized",
                        "corruption_risk_score_standardized"
                    ]
                    missing = [col for col in required_std_cols if col not in scored_df.columns]
                    if missing:
                        st.write("❌ Missing standardized columns:")
                        for col in missing:
                            st.write(f"  - {col}")
                    else:
                        st.write("✅ All required columns exist")
                        # Show actual values from first market
                        if len(scored_df) > 0:
                            first_market = scored_df.iloc[0]
                            st.write("**First market standardized values:**")
                            for col in required_std_cols:
                                val = first_market.get(col, "N/A")
                                if pd.notna(val):
                                    st.write(f"  - {col}: {val:.4f}")
                                else:
                                    st.write(f"  - {col}: NaN")
                            st.write(f"**Weights being used:** {weights}")
                            st.write(f"**Calculated total_score:** {first_market.get('total_score', 'N/A')}")
                    
                    st.info("💡 **Solution:** If columns exist but scores are zero, try clicking 'Clear Streamlit Cache' in the sidebar and refresh.")
                else:
                    # Sort by score for proper display (lowest to highest for horizontal bars)
                    chart_data = chart_data.sort_values("total_score", ascending=True)
                    
                    # Create the bar chart
                    fig_rank = px.bar(
                        chart_data,
                        x="total_score",
                        y="country_code",
                        orientation="h",
                        title="Market Ranking (Top 10)",
                        labels={"total_score": "Total Score", "country_code": "Country"},
                        color="total_score",
                        color_continuous_scale="Blues",
                        text="total_score"  # Show values on bars
                    )
                    # Format text on bars
                    fig_rank.update_traces(
                        texttemplate='%{text:.3f}',
                        textposition='outside'
                    )
                    # Update layout for better display
                    fig_rank.update_layout(
                        height=max(400, len(chart_data) * 40),
                        showlegend=False,
                        xaxis_title="Total Score",
                        yaxis_title="Country",
                        xaxis=dict(showgrid=True, zeroline=True),
                        yaxis=dict(
                            categoryorder="total ascending",
                            showgrid=False
                        )
                    )
                    st.plotly_chart(fig_rank, use_container_width=True)
            else:
                st.warning("No valid data available for chart")
        else:
            st.error("Missing total_score column. Please run `python -m src.main` first.")
    else:
        st.warning("No data available for ranking")

# Tab 2: Market Profiles
with tab2:
    st.header("Market Profiles")
    
    if len(df) > 0:
        selected_market = st.selectbox(
            "Select market",
            df["country_code"].unique()
        )
        
        # Check if standardized columns exist
        required_cols = [
            "market_size_score_standardized",
            "purchasing_power_score_standardized",
            "digital_readiness_score_standardized",
            "governance_risk_score_standardized",
            "corruption_risk_score_standardized"
        ]
        
        if all(col in df.columns for col in required_cols):
            # Radar chart
            try:
                fig_radar = create_radar_chart(df, selected_market)
                st.plotly_chart(fig_radar, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating radar chart: {e}")
        else:
            st.warning("Standardized feature columns not found. Please run `python -m src.main` first.")
        
        # Market details
        market_data = df[df["country_code"] == selected_market].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Population", f"{market_data.get('population_total', 0):,.0f}")
            st.metric("GDP per Capita", f"${market_data.get('gdp_per_capita_usd', 0):,.0f}")
        
        with col2:
            st.metric("Internet Users %", f"{market_data.get('internet_users_pct', 0):.1f}%")
            st.metric("Rule of Law", f"{market_data.get('rule_of_law', 0):.2f}")
        
        with col3:
            st.metric("Regulatory Quality", f"{market_data.get('regulatory_quality', 0):.2f}")
            st.metric("CPI Score", f"{market_data.get('cpi_score', 0):.0f}")
    else:
        st.warning("No market data available")

# Tab 3: Forecast
with tab3:
    st.header("Revenue Forecast")
    
    if len(df) > 0 and len(scored_df) > 0:
        selected_market_forecast = st.selectbox(
            "Select market for forecast",
            df["country_code"].unique(),
            key="forecast_market"
        )
        
        try:
            # Load assumptions
            import yaml
            with open("config/assumptions.yml", "r") as f:
                assumptions = yaml.safe_load(f)
            
            # Market adjustment based on score
            market_row = scored_df[scored_df["country_code"] == selected_market_forecast].iloc[0]
            market_adjustment = (market_row["total_score"] + 3) / 6  # Rough normalization to 0-1
            market_adjustment = np.clip(market_adjustment, 0.5, 1.5)
            
            # Get forecast months from assumptions, default to 36
            forecast_months = assumptions.get("simulation", {}).get("months", 36)
            
            scenarios = generate_scenarios(
                assumptions,
                market_adjustment=market_adjustment,
                months=forecast_months
            )
            
            forecast_df = scenarios[scenario]
            
            # Plot forecast
            fig_forecast = go.Figure()
            fig_forecast.add_trace(go.Scatter(
                x=forecast_df["month"],
                y=forecast_df["cumulative_net_revenue"],
                mode="lines+markers",
                name="Cumulative Net Revenue",
                line=dict(width=3)
            ))
            fig_forecast.add_hline(
                y=assumptions["costs"]["market_entry_cost_usd"],
                line_dash="dash",
                annotation_text="Entry Cost",
                line_color="red"
            )
            fig_forecast.update_layout(
                title=f"Revenue Forecast: {selected_market_forecast} ({scenario})",
                xaxis_title="Month",
                yaxis_title="USD",
                height=500
            )
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            forecast_months = assumptions.get("simulation", {}).get("months", 36)
            with col1:
                final_revenue = forecast_df.iloc[-1]["cumulative_net_revenue"]
                st.metric(f"Cumulative Net Revenue ({forecast_months}M)", f"${final_revenue:,.0f}")
            with col2:
                final_customers = forecast_df.iloc[-1]["active_customers"]
                st.metric(f"Active Customers (M{forecast_months})", f"{final_customers:.0f}")
            with col3:
                entry_cost = assumptions["costs"]["market_entry_cost_usd"]
                payback = (final_revenue >= entry_cost)
                st.metric(f"Pays Back in {forecast_months}M", "Yes" if payback else "No")
        except Exception as e:
            st.error(f"Error generating forecast: {e}")
            st.info("Make sure you've run `python -m src.main` first to generate processed data.")
    else:
        st.warning("No data available for forecasting")

# Tab 4: Sensitivity
with tab4:
    st.header("Sensitivity Analysis")
    
    # Add explanation
    st.markdown("""
    **What is Sensitivity Analysis?**
    
    This analysis shows how **market rankings change** when you adjust the importance (weight) of different criteria. 
    For example: "If I care more about Market Size, does Australia still rank #1?" 
    
    The chart shows how each market's rank moves up or down as you increase/decrease the selected criterion's weight.
    """)
    
    if len(df) > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            weight_to_analyze = st.selectbox(
                "Select criterion to analyze",
                list(weights.keys()),
                format_func=lambda x: x.replace("_", " ").title(),
                help="Choose which criterion weight to vary. Other weights will adjust proportionally to keep total = 1.0"
            )
        
        with col2:
            num_runs = st.slider(
                "Number of test points",
                min_value=20,
                max_value=100,
                value=50,
                step=10,
                help="More points = smoother curve but slower computation"
            )
        
        # Auto-run when selection changes (no button needed)
        try:
            from src.models.scoring import run_full_sensitivity
            
            with st.spinner(f"Running sensitivity analysis for {weight_to_analyze.replace('_', ' ').title()}..."):
                sensitivity_results = run_full_sensitivity(
                    df,
                    weights,
                    step=0.05,
                    n_runs=num_runs
                )
            
            sens_df = sensitivity_results[weight_to_analyze]
            
            if len(sens_df) > 0:
                # Calculate summary statistics
                market_stability = sens_df.groupby("country_code").agg({
                    "rank": ["mean", "std", "min", "max"],
                    "total_score": ["mean", "std"]
                }).round(2)
                market_stability.columns = ["Avg_Rank", "Rank_StdDev", "Best_Rank", "Worst_Rank", "Avg_Score", "Score_StdDev"]
                market_stability = market_stability.sort_values("Avg_Rank")
                market_stability["Rank_Range"] = market_stability["Worst_Rank"] - market_stability["Best_Rank"]
                
                # Show summary table
                st.subheader("📊 Rank Stability Summary")
                st.markdown("*Markets with smaller rank changes are more stable*")
                summary_display = market_stability.reset_index()[["country_code", "Avg_Rank", "Best_Rank", "Worst_Rank", "Rank_Range"]].copy()
                summary_display.columns = ["Market", "Avg Rank", "Best Rank", "Worst Rank", "Rank Range"]
                summary_display["Stability"] = summary_display["Rank Range"].apply(
                    lambda x: "🔴 High Variation" if x > 3 else "🟡 Medium Variation" if x > 1 else "🟢 Stable"
                )
                st.dataframe(summary_display, use_container_width=True, hide_index=True)
                
                # Market selection for chart
                st.subheader("📈 Sensitivity Chart")
                
                # Get top 5 most affected markets (by rank range)
                top_affected = market_stability.nlargest(5, "Rank_Range").index.tolist()
                
                selected_markets = st.multiselect(
                    "Select markets to display on chart",
                    options=sens_df["country_code"].unique().tolist(),
                    default=top_affected if len(top_affected) >= 3 else sens_df["country_code"].unique()[:5].tolist(),
                    help="Choose which markets to visualize. Showing too many can make the chart cluttered."
                )
                
                if selected_markets:
                    # Filter data for selected markets
                    chart_data = sens_df[sens_df["country_code"].isin(selected_markets)].copy()
                    
                    # Create cleaner visualization
                    fig_sens = go.Figure()
                    
                    # Color palette
                    colors = px.colors.qualitative.Set3
                    
                    for i, market in enumerate(selected_markets):
                        market_data = chart_data[chart_data["country_code"] == market].sort_values("weight_value")
                        fig_sens.add_trace(go.Scatter(
                            x=market_data["weight_value"],
                            y=market_data["rank"],
                            mode='lines+markers',
                            name=market,
                            line=dict(width=2.5),
                            marker=dict(size=6),
                            hovertemplate=f"<b>{market}</b><br>" +
                                        "Weight: %{x:.3f}<br>" +
                                        "Rank: %{y}<br>" +
                                        "<extra></extra>"
                        ))
                    
                    # Add vertical line for current weight
                    current_weight = weights[weight_to_analyze]
                    fig_sens.add_vline(
                        x=current_weight,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Current: {current_weight:.2f}",
                        annotation_position="top"
                    )
                    
                    fig_sens.update_layout(
                        title=f"Market Ranking Sensitivity: {weight_to_analyze.replace('_', ' ').title()}",
                        xaxis_title="Criterion Weight",
                        yaxis_title="Market Rank (1 = Best)",
                        yaxis=dict(
                            autorange="reversed",  # Rank 1 at top
                            tickmode="linear",
                            tick0=1,
                            dtick=1
                        ),
                        height=500,
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig_sens, use_container_width=True)
                    
                    # Interpretation
                    st.markdown("---")
                    st.subheader("💡 Insights")
                    
                    most_stable = market_stability.nsmallest(1, "Rank_Range").index[0]
                    most_variable = market_stability.nlargest(1, "Rank_Range").index[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Most Stable:** {most_stable} - Ranking barely changes regardless of {weight_to_analyze.replace('_', ' ')} weight")
                    with col2:
                        st.warning(f"**Most Sensitive:** {most_variable} - Ranking changes significantly based on {weight_to_analyze.replace('_', ' ')} weight")
                    
                else:
                    st.info("Select at least one market to display on the chart")
                
            else:
                st.warning("No sensitivity results generated")
        except Exception as e:
            st.error(f"Error running sensitivity analysis: {e}")
            st.exception(e)
    else:
        st.warning("No data available for sensitivity analysis")

