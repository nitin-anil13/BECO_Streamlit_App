import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="BECO Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# BECO-STYLE CSS
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #F5F2EA;
    }

    .main-title {
        font-size: 42px;
        font-weight: 700;
        color: #123F3F;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #555555;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .metric-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 4px 5px 12px rgba(0,0,0,0.15);
        text-align: center;
    }

    .metric-title {
        color: #555555;
        font-size: 15px;
    }

    .metric-value {
        color: #123F3F;
        font-size: 30px;
        font-weight: 700;
    }

    h2 {
        color: #123F3F !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Clean_Sales.csv")
    return df

df = load_data()

# -----------------------------
# COLUMN CHECK
# -----------------------------
required_columns = [
    "CHANNEL_CLEAN",
    "NET_REVENUE",
    "CM2"
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    st.error(f"Missing columns in Clean_Sales.csv: {missing}")
    st.write("Available columns:")
    st.write(df.columns.tolist())
    st.stop()

# -----------------------------
# TITLE
# -----------------------------
st.markdown(
    '<div class="main-title">BECO Sales & Profitability Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Interactive Sales & Channel Performance Analysis</div>',
    unsafe_allow_html=True
)

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("Dashboard Filters")

# Channel filter
channels = sorted(df["CHANNEL_CLEAN"].dropna().unique().tolist())

selected_channels = st.sidebar.multiselect(
    "Channel",
    channels,
    default=channels
)

# Category filter
category_column = None

for col in ["CATEGORY_CLEAN", "CATEGORY", "Category"]:
    if col in df.columns:
        category_column = col
        break

if category_column:
    categories = sorted(
        df[category_column].dropna().unique().tolist()
    )

    selected_categories = st.sidebar.multiselect(
        "Category",
        categories,
        default=categories
    )
else:
    selected_categories = None

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered_df = df[
    df["CHANNEL_CLEAN"].isin(selected_channels)
].copy()

if category_column and selected_categories:
    filtered_df = filtered_df[
        filtered_df[category_column].isin(selected_categories)
    ]

# -----------------------------
# KPI CALCULATIONS
# -----------------------------
total_revenue = filtered_df["NET_REVENUE"].sum()
total_cm2 = filtered_df["CM2"].sum()

# -----------------------------
# KPI CARDS
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Total Net Revenue</div>
            <div class="metric-value">₹{total_revenue/1e6:.2f}M</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">CM2</div>
            <div class="metric-value">₹{total_cm2/1e6:.2f}M</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------
# REVENUE BY CHANNEL
# -----------------------------
st.subheader("Net Revenue by Channel")

channel_data = (
    filtered_df
    .groupby("CHANNEL_CLEAN", as_index=False)["NET_REVENUE"]
    .sum()
    .sort_values("NET_REVENUE", ascending=False)
)

fig = px.bar(
    channel_data,
    x="CHANNEL_CLEAN",
    y="NET_REVENUE",
    text_auto=".2s",
    title="Revenue Contribution by Channel"
)

fig.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="#123F3F"),
    xaxis_title="Channel",
    yaxis_title="Net Revenue",
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# CATEGORY BREAKDOWN
# -----------------------------
if category_column:

    st.subheader("Revenue by Category")

    category_data = (
        filtered_df
        .groupby(category_column, as_index=False)["NET_REVENUE"]
        .sum()
        .sort_values("NET_REVENUE", ascending=False)
    )

    fig2 = px.bar(
        category_data,
        x=category_column,
        y="NET_REVENUE",
        text_auto=".2s",
        title="Category Revenue Breakdown"
    )

    fig2.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#123F3F"),
        xaxis_title="Category",
        yaxis_title="Net Revenue",
        showlegend=False
    )

    st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# DATA PREVIEW
# -----------------------------
with st.expander("View Filtered Data"):
    st.dataframe(
        filtered_df.head(100),
        use_container_width=True
    )

st.caption("BECO Sales & Profitability Analysis | Streamlit")
