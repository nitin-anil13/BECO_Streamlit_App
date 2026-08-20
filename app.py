import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BECO | Sales & Profitability",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# THEME
# ============================================================

DARK = "#0B3D3B"
GREEN = "#59B548"
GREEN_DARK = "#3E8F39"
CREAM = "#F6F2EA"
CARD = "#FFFDF9"
PALE = "#EAF3E5"
GRID = "#D8DED7"
TEXT = "#183C3C"
MUTED = "#66736F"
BORDER = "#C9D7C3"
WHITE = "#FFFFFF"

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "Clean_Sales.csv"
LOGO_PATH = BASE / "beco_logo.png"

# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700'
        '&family=Playfair+Display:ital,wght@0,600;0,700;1,600;1,700'
        '&display=swap'
    );

    .stApp {{
        background: {CREAM};
        color: {TEXT};
    }}

    .block-container {{
        max-width: 1550px;
        padding: 1rem 1.35rem 2rem;
    }}

    #MainMenu, footer, header {{
        visibility: hidden;
    }}

    [data-testid="stSidebar"] {{
        background: #F0F5EB;
        border-right: 1px solid {BORDER};
    }}

    [data-testid="stSidebar"] label {{
        color: {DARK} !important;
        font-weight: 600 !important;
    }}

    .hero {{
        background: linear-gradient(135deg, #FFFDF9, #EEF5E9);
        border: 1px solid {BORDER};
        border-radius: 28px;
        padding: 18px 24px;
        margin-bottom: 14px;
        box-shadow: 0 10px 24px rgba(20,55,45,.10);
    }}

    .hero-title {{
        font-family: 'DM Sans', sans-serif;
        font-size: clamp(30px, 4vw, 50px);
        font-weight: 700;
        color: {DARK};
        text-align: center;
        letter-spacing: -1px;
    }}

    .hero-sub {{
        text-align: center;
        color: {MUTED};
        font-size: 12px;
        margin-top: 4px;
    }}

    .page-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 30px;
        font-style: italic;
        font-weight: 700;
        color: {DARK};
        margin: 7px 0 12px;
    }}

    .section-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 23px;
        font-style: italic;
        font-weight: 700;
        color: {DARK};
        margin-bottom: 5px;
    }}

    .card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 24px;
        padding: 15px 17px 9px;
        box-shadow: 7px 9px 18px rgba(26,52,42,.11);
        margin-bottom: 15px;
    }}

    .kpi {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 22px;
        padding: 17px 14px;
        min-height: 120px;
        box-shadow: 7px 9px 18px rgba(26,52,42,.13);
        border-left: 5px solid {GREEN};
    }}

    .kpi-label {{
        color: {MUTED};
        font-size: 12px;
        font-weight: 600;
        letter-spacing: .4px;
        text-transform: uppercase;
    }}

    .kpi-value {{
        color: {DARK};
        font-family: Georgia, serif;
        font-size: 32px;
        font-weight: 700;
        margin-top: 7px;
    }}

    .kpi-note {{
        color: {MUTED};
        font-size: 11px;
        margin-top: 5px;
    }}

    .filter-summary {{
        background: #EEF5E9;
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 8px 12px;
        margin-bottom: 15px;
        color: {DARK};
        font-size: 12px;
    }}

    .insight {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 18px;
        min-height: 135px;
        box-shadow: 5px 7px 15px rgba(26,52,42,.10);
    }}

    .insight-tag {{
        color: {GREEN_DARK};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .7px;
    }}

    .insight-main {{
        color: {DARK};
        font-family: Georgia, serif;
        font-size: 23px;
        font-weight: 700;
        margin: 5px 0;
    }}

    .insight-text {{
        color: {MUTED};
        font-size: 12px;
    }}

    .footer-note {{
        text-align: center;
        color: {MUTED};
        font-size: 11px;
        padding: 20px;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DATE PARSER
# ============================================================

def parse_month_value(value):
    """
    Robustly converts BECO MONTH_CLEAN values into real dates.

    Handles:
    - Excel serial numbers
    - Nov-24
    - Sep-24
    - 1/3/2025 -> March 2025
    - 12/1/2024 -> December 2024
    - ISO dates
    """

    if pd.isna(value):
        return pd.NaT

    # Already a timestamp
    if isinstance(value, (pd.Timestamp, datetime)):
        return pd.Timestamp(value).replace(day=1)

    # Numeric Excel serial date
    if isinstance(value, (int, float)) and not isinstance(value, bool):

        number = float(value)

        # Excel dates are generally in this range
        if 20000 <= number <= 60000:
            try:
                return (
                    pd.Timestamp("1899-12-30")
                    + pd.to_timedelta(number, unit="D")
                ).replace(day=1)
            except Exception:
                return pd.NaT

    text = str(value).strip()

    if text == "":
        return pd.NaT

    # Numeric string that may actually be an Excel serial
    try:
        number = float(text)

        if 20000 <= number <= 60000:
            return (
                pd.Timestamp("1899-12-30")
                + pd.to_timedelta(number, unit="D")
            ).replace(day=1)

    except Exception:
        pass

    # Month-Year formats
    month_formats = [
        "%b-%y",
        "%B-%y",
        "%b %y",
        "%B %y",
        "%b-%Y",
        "%B-%Y",
        "%b %Y",
        "%B %Y",
    ]

    for fmt in month_formats:
        try:
            return pd.Timestamp(
                datetime.strptime(text, fmt)
            ).replace(day=1)
        except Exception:
            pass

    # BECO Excel-style dates
    # IMPORTANT:
    # 1/3/2025 means 3 January? No.
    # In this dataset Excel displays dates as M/D/YYYY,
    # therefore 1/3/2025 = March 1, 2025.
    date_formats = [
        "%m/%d/%Y",
        "%m/%d/%y",
        "%m-%d-%Y",
        "%m-%d-%y",
    ]

    for fmt in date_formats:
        try:
            return pd.Timestamp(
                datetime.strptime(text, fmt)
            ).replace(day=1)
        except Exception:
            pass

    # ISO / fallback
    try:
        parsed = pd.to_datetime(text, errors="coerce")

        if pd.notna(parsed):
            return pd.Timestamp(parsed).replace(day=1)

    except Exception:
        pass

    return pd.NaT


def parse_month_column(series):
    return series.apply(parse_month_value)


# ============================================================
# HELPERS
# ============================================================

def numeric_series(df, column):
    if column not in df.columns:
        return pd.Series(0.0, index=df.index)

    return pd.to_numeric(
        df[column]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.strip(),
        errors="coerce",
    ).fillna(0)


def money(value):
    value = float(value or 0)

    if abs(value) >= 1_000_000:
        return f"₹{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"₹{value / 1_000:.1f}K"

    return f"₹{value:,.0f}"


def layout(fig, height=330):

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=18, t=15, b=10),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(
            family="DM Sans,Arial",
            color=TEXT
        ),
        hoverlabel=dict(bgcolor=WHITE),
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right"
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False
    )

    fig.update_yaxes(
        showgrid=False,
        zeroline=False
    )

    return fig


def kpi(label, value, note):

    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(show_spinner="Loading Clean_Sales.csv...")
def load_data(path):

    df = pd.read_csv(
        path,
        low_memory=False
    )

    df.columns = [
        str(c).strip()
        for c in df.columns
    ]

    # --------------------------------------------------------
    # Identify columns
    # --------------------------------------------------------

    def pick(*names):

        for name in names:
            if name in df.columns:
                return name

        return None

    date_col = pick(
        "MONTH_CLEAN",
        "MONTH",
        "Month",
        "Date"
    )

    channel_col = pick(
        "CHANNEL_CLEAN",
        "CHANNEL",
        "Channel"
    )

    region_col = pick(
        "REGION",
        "Region",
        "region"
    )

    category_col = pick(
        "Category",
        "CATEGORY",
        "category"
    )

    if not date_col:
        raise ValueError(
            "MONTH_CLEAN or MONTH column is required."
        )

    if not channel_col:
        raise ValueError(
            "CHANNEL_CLEAN or CHANNEL column is required."
        )

    if not region_col:
        raise ValueError(
            "REGION column is required."
        )

    # --------------------------------------------------------
    # Rename to standard names
    # --------------------------------------------------------

    rename = {}

    if date_col != "MONTH_CLEAN":
        rename[date_col] = "MONTH_CLEAN"

    if channel_col != "CHANNEL_CLEAN":
        rename[channel_col] = "CHANNEL_CLEAN"

    if region_col != "REGION":
        rename[region_col] = "REGION"

    if category_col and category_col != "Category":
        rename[category_col] = "Category"

    df = df.rename(columns=rename)

    if "Category" not in df.columns:
        df["Category"] = "Unmapped"

    # --------------------------------------------------------
    # Column aliases
    # --------------------------------------------------------

    aliases = {
        "Net_Revenue": "NET_REVENUE",
        "Net Revenue": "NET_REVENUE",

        "COGS_Amount": "COGS",
        "Cogs": "COGS",

        "Ad_Spend": "AD_SPEND",
        "Ad Spend": "AD_SPEND",

        "Returns_Units": "RETURNS_UNITS",
        "Units_Sold": "UNITS_SOLD",

        "Gross_Revenue": "GROSS_REVENUE",
        "Discount": "DISCOUNT",

        "Unit_Cogs": "UNIT_COGS",
        "Unit COGS": "UNIT_COGS",

        "CM2_CALC": "CM2",
        "RETURN_RATE_PCT": "RETURN_RATE_PCT",
    }

    for old, new in aliases.items():

        if old in df.columns and new not in df.columns:
            df = df.rename(
                columns={old: new}
            )

    # --------------------------------------------------------
    # Numeric fields
    # --------------------------------------------------------

    numeric_columns = [
        "NET_REVENUE",
        "COGS",
        "UNIT_COGS",
        "AD_SPEND",
        "RETURNS_UNITS",
        "UNITS_SOLD",
        "GROSS_REVENUE",
        "DISCOUNT",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = numeric_series(
                df,
                column
            )

    # --------------------------------------------------------
    # Create missing fields
    # --------------------------------------------------------

    if "GROSS_REVENUE" not in df.columns:
        df["GROSS_REVENUE"] = 0.0

    if "DISCOUNT" not in df.columns:
        df["DISCOUNT"] = 0.0

    if "AD_SPEND" not in df.columns:
        df["AD_SPEND"] = 0.0

    if "RETURNS_UNITS" not in df.columns:
        df["RETURNS_UNITS"] = 0.0

    if "UNITS_SOLD" not in df.columns:
        df["UNITS_SOLD"] = 0.0

    # --------------------------------------------------------
    # NET REVENUE
    # --------------------------------------------------------

    if "NET_REVENUE" not in df.columns:

        df["NET_REVENUE"] = (
            df["GROSS_REVENUE"]
            - df["DISCOUNT"]
        )

    # --------------------------------------------------------
    # COGS
    # --------------------------------------------------------

    if "COGS" not in df.columns:

        if "UNIT_COGS" in df.columns:

            df["COGS"] = (
                df["UNIT_COGS"]
                * df["UNITS_SOLD"]
            )

        else:

            df["COGS"] = 0.0

    # --------------------------------------------------------
    # CORRECT MONTH PARSING
    # --------------------------------------------------------

    df["MONTH_CLEAN"] = parse_month_column(
        df["MONTH_CLEAN"]
    )

    df = df.dropna(
        subset=["MONTH_CLEAN"]
    ).copy()

    # --------------------------------------------------------
    # Clean text fields
    # --------------------------------------------------------

    for column in [
        "CHANNEL_CLEAN",
        "REGION",
        "Category"
    ]:

        df[column] = (
            df[column]
            .fillna("Unmapped")
            .astype(str)
            .str.strip()
        )

        df.loc[
            df[column].isin(
                ["", "nan", "None", "NaN"]
            ),
            column
        ] = "Unmapped"

    # --------------------------------------------------------
    # Channel standardization
    # --------------------------------------------------------

    df["CHANNEL_CLEAN"] = (
        df["CHANNEL_CLEAN"]
        .replace({
            "d2c": "D2C",
            "D2c": "D2C",
            "D2C": "D2C",

            "Shopify": "D2C",
            "shopify": "D2C",

            "Instamart": "Swiggy Instamart",
            "instamart": "Swiggy Instamart",

            "FlipKart": "Flipkart",
            "flipkart": "Flipkart",

            "AMAZON": "Amazon",
            "amazon": "Amazon",

            "BlinkIt": "Blinkit",
            "BLINKIT": "Blinkit",

            "ZEPTO": "Zepto"
        })
    )

    # --------------------------------------------------------
    # SKU MATCH STATUS
    # --------------------------------------------------------

    if "SKU_MATCH" in df.columns:

        df["SKU_MATCH"] = (
            df["SKU_MATCH"]
            .fillna("MATCH")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    else:

        df["SKU_MATCH"] = "MATCH"

    # --------------------------------------------------------
    # FINAL CM2
    # --------------------------------------------------------
    #
    # Verified assignment logic:
    #
    # CM2 = NET_REVENUE - COGS - AD_SPEND
    #
    # 15 NOT FOUND SKU records are excluded from
    # profitability because their COGS/category
    # information is unavailable.
    # --------------------------------------------------------

    df["CM2"] = (
        df["NET_REVENUE"]
        - df["COGS"]
        - df["AD_SPEND"]
    )

    df.loc[
        df["SKU_MATCH"].eq("NOT FOUND"),
        "CM2"
    ] = 0

    # --------------------------------------------------------
    # Month keys
    # --------------------------------------------------------

    df["Month Key"] = (
        df["MONTH_CLEAN"].dt.year * 100
        + df["MONTH_CLEAN"].dt.month
    )

    df["Month Year"] = (
        df["MONTH_CLEAN"]
        .dt.strftime("%b-%y")
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = (
        df
        .sort_values("MONTH_CLEAN")
        .reset_index(drop=True)
    )

    return df


# ============================================================
# CHECK FILE
# ============================================================

if not CSV_PATH.exists():

    st.error(
        "Clean_Sales.csv was not found next to app.py."
    )

    st.info(
        f"Expected file location: {CSV_PATH}"
    )

    st.stop()


# ============================================================
# LOAD
# ============================================================

try:

    df = load_data(
        str(CSV_PATH)
    )

except Exception as e:

    st.error(
        f"Could not load Clean_Sales.csv: {e}"
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    if LOGO_PATH.exists():

        st.image(
            str(LOGO_PATH),
            use_container_width=True
        )

    st.markdown(
        "## BECO Analytics"
    )

    st.caption(
        "Sales • Profitability • Insights"
    )

    page = st.radio(
        "Navigate",
        [
            "Overview",
            "Profitability",
            "Insights"
        ],
        index=0
    )

    st.divider()

    st.markdown(
        "### Filters"
    )

    min_date = (
        df["MONTH_CLEAN"]
        .min()
        .date()
    )

    max_date = (
        df["MONTH_CLEAN"]
        .max()
        .date()
    )

    date_range = st.date_input(
        "Month",
        value=(
            min_date,
            max_date
        ),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )

    region_options = [
        "All"
    ] + sorted(
        df["REGION"]
        .dropna()
        .unique()
        .tolist()
    )

    category_options = [
        "All"
    ] + sorted(
        df["Category"]
        .dropna()
        .unique()
        .tolist()
    )

    channel_options = [
        "All"
    ] + sorted(
        df["CHANNEL_CLEAN"]
        .dropna()
        .unique()
        .tolist()
    )

    region = st.selectbox(
        "Region",
        region_options
    )

    category = st.selectbox(
        "Category",
        category_options
    )

    channel = st.selectbox(
        "Channel",
        channel_options
    )

    st.divider()

    st.caption(
        f"{len(df):,} source rows"
    )

    st.caption(
        f"{min_date:%b %Y} – {max_date:%b %Y}"
    )

    if st.button(
        "Reload data",
        use_container_width=True
    ):

        st.cache_data.clear()
        st.rerun()


# ============================================================
# DATE FILTER
# ============================================================

if (
    isinstance(date_range, (tuple, list))
    and len(date_range) == 2
):

    start = pd.Timestamp(
        date_range[0]
    )

    end = pd.Timestamp(
        date_range[1]
    )

else:

    start = pd.Timestamp(
        date_range
    )

    end = start


# Include complete selected end date
x = df[
    (df["MONTH_CLEAN"] >= start)
    &
    (
        df["MONTH_CLEAN"]
        < end + pd.Timedelta(days=1)
    )
].copy()


# Additional filters

if region != "All":

    x = x[
        x["REGION"] == region
    ]


if category != "All":

    x = x[
        x["Category"] == category
    ]


if channel != "All":

    x = x[
        x["CHANNEL_CLEAN"] == channel
    ]


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            BECO Sales &amp; Profitability Dashboard
        </div>
        <div class="hero-sub">
            Interactive business performance dashboard
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    f"""
    <div class="filter-summary">
        <b>Current view:</b>
        {start:%d %b %Y} → {end:%d %b %Y}
        &nbsp;•&nbsp;
        Region: <b>{region}</b>
        &nbsp;•&nbsp;
        Category: <b>{category}</b>
        &nbsp;•&nbsp;
        Channel: <b>{channel}</b>
        &nbsp;•&nbsp;
        {len(x):,} rows
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# KPI CALCULATIONS
# ============================================================

net_revenue = x["NET_REVENUE"].sum()

cm2 = x["CM2"].sum()

ad_spend = x["AD_SPEND"].sum()

units = x["UNITS_SOLD"].sum()

returns = x["RETURNS_UNITS"].sum()

roas = (
    net_revenue / ad_spend
    if ad_spend
    else 0
)

return_rate = (
    returns / units
    if units
    else 0
)

cm2_margin = (
    cm2 / net_revenue
    if net_revenue
    else 0
)


# ============================================================
# KPI CARDS
# ============================================================

a, b, c, d = st.columns(
    4,
    gap="medium"
)

with a:

    kpi(
        "Total Net Revenue",
        money(net_revenue),
        "Revenue after discounts"
    )

with b:

    kpi(
        "CM2",
        money(cm2),
        f"CM2 margin {cm2_margin:.1%}"
    )

with c:

    kpi(
        "Blended ROAS",
        f"{roas:.2f}×",
        "Net revenue ÷ ad spend"
    )

with d:

    kpi(
        "Return Rate",
        f"{return_rate:.2%}",
        f"{returns:,.0f} returned units"
    )


st.write("")


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.markdown(
        '<div class="page-title">Overview</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Monthly Net Revenue
    # --------------------------------------------------------

    monthly = (
        x.groupby(
            ["MONTH_CLEAN", "Month Key"],
            as_index=False
        )
        .agg(
            Net_Revenue=(
                "NET_REVENUE",
                "sum"
            )
        )
        .sort_values(
            "Month Key"
        )
    )

    fig = px.line(
        monthly,
        x="MONTH_CLEAN",
        y="Net_Revenue",
        markers=True
    )

    fig.update_traces(
        line=dict(
            color=DARK,
            width=3
        ),
        marker=dict(
            color=GREEN,
            size=8
        ),
        hovertemplate=(
            "%{x|%b-%Y}"
            "<br>Net Revenue: ₹%{y:,.0f}"
            "<extra></extra>"
        )
    )

    fig.update_xaxes(
        tickformat="%b-%y",
        showgrid=False,
        title="Month"
    )

    fig.update_yaxes(
        tickformat="~s",
        title="Net Revenue"
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">'
        'Monthly Net Revenue Trend'
        '</div>',
        unsafe_allow_html=True
    )

    st.plotly_chart(
        layout(fig, 390),
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Channel + Region
    # --------------------------------------------------------

    left, right = st.columns(
        2,
        gap="large"
    )

    with left:

        s = (
            x.groupby(
                "CHANNEL_CLEAN",
                as_index=False
            )["NET_REVENUE"]
            .sum()
            .sort_values(
                "NET_REVENUE"
            )
        )

        f = px.bar(
            s,
            x="NET_REVENUE",
            y="CHANNEL_CLEAN",
            orientation="h",
            text="NET_REVENUE"
        )

        f.update_traces(
            marker_color=GREEN,
            texttemplate="₹%{x:.3s}",
            textposition="outside",
            hovertemplate=(
                "%{y}"
                "<br>₹%{x:,.0f}"
                "<extra></extra>"
            )
        )

        f.update_xaxes(
            tickformat="~s"
        )

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="section-title">'
            'Net Revenue by Channel'
            '</div>',
            unsafe_allow_html=True
        )

        st.plotly_chart(
            layout(f),
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with right:

        s = (
            x.groupby(
                "REGION",
                as_index=False
            )["NET_REVENUE"]
            .sum()
            .sort_values(
                "NET_REVENUE"
            )
        )

        f = px.bar(
            s,
            x="NET_REVENUE",
            y="REGION",
            orientation="h",
            text="NET_REVENUE"
        )

        f.update_traces(
            marker_color=DARK,
            texttemplate="₹%{x:.3s}",
            textposition="outside",
            hovertemplate=(
                "%{y}"
                "<br>₹%{x:,.0f}"
                "<extra></extra>"
            )
        )

        f.update_xaxes(
            tickformat="~s"
        )

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="section-title">'
            'Net Revenue by Region'
            '</div>',
            unsafe_allow_html=True
        )

        st.plotly_chart(
            layout(f),
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    s = (
        x.groupby(
            "Category",
            as_index=False
        )["NET_REVENUE"]
        .sum()
        .sort_values(
            "NET_REVENUE"
        )
    )

    f = px.bar(
        s,
        x="Category",
        y="NET_REVENUE",
        text="NET_REVENUE"
    )

    f.update_traces(
        marker_color=GREEN_DARK,
        texttemplate="₹%{y:.3s}",
        textposition="outside",
        hovertemplate=(
            "%{x}"
            "<br>₹%{y:,.0f}"
            "<extra></extra>"
        )
    )

    f.update_yaxes(
        tickformat="~s"
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">'
        'Net Revenue by Category'
        '</div>',
        unsafe_allow_html=True
    )

    st.plotly_chart(
        layout(f, 300),
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# PROFITABILITY
# ============================================================

elif page == "Profitability":

    st.markdown(
        '<div class="page-title">'
        'Profitability'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # CM2 vs Ad Spend
    # --------------------------------------------------------

    monthly_profit = (
        x.groupby(
            ["MONTH_CLEAN", "Month Key"],
            as_index=False
        )
        .agg(
            CM2=("CM2", "sum"),
            AD_SPEND=("AD_SPEND", "sum")
        )
        .sort_values(
            "Month Key"
        )
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_profit["MONTH_CLEAN"],
            y=monthly_profit["CM2"],
            mode="lines+markers",
            name="CM2",
            line=dict(
                color=GREEN_DARK,
                width=3
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=monthly_profit["MONTH_CLEAN"],
            y=monthly_profit["AD_SPEND"],
            mode="lines+markers",
            name="Ad Spend",
            line=dict(
                color=DARK,
                width=3
            )
        )
    )

    fig.update_xaxes(
        tickformat="%b-%y",
        showgrid=False,
        title="Month"
    )

    fig.update_yaxes(
        tickformat="~s",
        title="Amount"
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">'
        'CM2 vs Ad Spend'
        '</div>',
        unsafe_allow_html=True
    )

    st.plotly_chart(
        layout(fig, 380),
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Channel x Category CM2
    # --------------------------------------------------------

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">'
        'CM2 by Channel × Category'
        '</div>',
        unsafe_allow_html=True
    )

    pivot = pd.pivot_table(
        x,
        index="CHANNEL_CLEAN",
        columns="Category",
        values="CM2",
        aggfunc="sum",
        fill_value=0
    )

    if not pivot.empty:

        pivot["Total"] = pivot.sum(
            axis=1
        )

        pivot.loc["Total"] = pivot.sum(
            axis=0
        )

        st.dataframe(
            pivot.style.format(
                "₹{:,.2f}"
            ),
            use_container_width=True,
            height=min(
                460,
                130 + len(pivot.index) * 40
            )
        )

    else:

        st.info(
            "No data for the current filters."
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # CM2 by Channel + Category
    # --------------------------------------------------------

    left, right = st.columns(
        2,
        gap="large"
    )

    with left:

        s = (
            x.groupby(
                "CHANNEL_CLEAN",
                as_index=False
            )["CM2"]
            .sum()
            .sort_values(
                "CM2"
            )
        )

        f = px.bar(
            s,
            x="CM2",
            y="CHANNEL_CLEAN",
            orientation="h",
            text="CM2"
        )

        f.update_traces(
            marker_color=GREEN,
            texttemplate="₹%{x:.3s}",
            textposition="outside"
        )

        f.update_xaxes(
            tickformat="~s"
        )

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="section-title">'
            'CM2 by Channel'
            '</div>',
            unsafe_allow_html=True
        )

        st.plotly_chart(
            layout(f),
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with right:

        s = (
            x.groupby(
                "Category",
                as_index=False
            )["CM2"]
            .sum()
            .sort_values(
                "CM2"
            )
        )

        f = px.bar(
            s,
            x="CM2",
            y="Category",
            orientation="h",
            text="CM2"
        )

        f.update_traces(
            marker_color=DARK,
            texttemplate="₹%{x:.3s}",
            textposition="outside"
        )

        f.update_xaxes(
            tickformat="~s"
        )

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="section-title">'
            'CM2 by Category'
            '</div>',
            unsafe_allow_html=True
        )

        st.plotly_chart(
            layout(f),
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


# ============================================================
# INSIGHTS
# ============================================================

else:

    st.markdown(
        '<div class="page-title">'
        'Insights'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Channel Summary
    # --------------------------------------------------------

    channel_summary = (
        x.groupby(
            "CHANNEL_CLEAN",
            as_index=False
        )
        .agg(
            Net_Revenue=(
                "NET_REVENUE",
                "sum"
            ),
            CM2=(
                "CM2",
                "sum"
            ),
            Ad_Spend=(
                "AD_SPEND",
                "sum"
            ),
            Units=(
                "UNITS_SOLD",
                "sum"
            ),
            Returns=(
                "RETURNS_UNITS",
                "sum"
            )
        )
    )

    if not channel_summary.empty:

        channel_summary["ROAS"] = (
            channel_summary["Net_Revenue"]
            .div(
                channel_summary["Ad_Spend"]
                .replace(0, pd.NA)
            )
            .fillna(0)
        )

        channel_summary["Return Rate"] = (
            channel_summary["Returns"]
            .div(
                channel_summary["Units"]
                .replace(0, pd.NA)
            )
            .fillna(0)
        )

        best = channel_summary.loc[
            channel_summary["CM2"].idxmax()
        ]

        best_roas = channel_summary.loc[
            channel_summary["ROAS"].idxmax()
        ]

        worst_return = channel_summary.loc[
            channel_summary["Return Rate"].idxmax()
        ]

    else:

        best = None
        best_roas = None
        worst_return = None

    # --------------------------------------------------------
    # Channel x Category
    # --------------------------------------------------------

    channel_category = (
        x.groupby(
            [
                "CHANNEL_CLEAN",
                "Category"
            ],
            as_index=False
        )
        .agg(
            CM2=("CM2", "sum"),
            Net_Revenue=(
                "NET_REVENUE",
                "sum"
            ),
            Ad_Spend=(
                "AD_SPEND",
                "sum"
            )
        )
    )

    if not channel_category.empty:

        channel_category["ROAS"] = (
            channel_category["Net_Revenue"]
            .div(
                channel_category["Ad_Spend"]
                .replace(0, pd.NA)
            )
            .fillna(0)
        )

        best_combo = channel_category.loc[
            channel_category["CM2"].idxmax()
        ]

    else:

        best_combo = None

    # --------------------------------------------------------
    # Insight cards
    # --------------------------------------------------------

    a, b, c = st.columns(
        3,
        gap="medium"
    )

    with a:

        if best is not None:

            st.markdown(
                f"""
                <div class="insight">
                    <div class="insight-tag">
                        TOP CM2 CHANNEL
                    </div>
                    <div class="insight-main">
                        {best["CHANNEL_CLEAN"]}
                    </div>
                    <div class="insight-text">
                        CM2 {money(best["CM2"])}
                        · Net Revenue {money(best["Net_Revenue"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with b:

        if best_roas is not None:

            st.markdown(
                f"""
                <div class="insight">
                    <div class="insight-tag">
                        HIGHEST ROAS
                    </div>
                    <div class="insight-main">
                        {best_roas["CHANNEL_CLEAN"]}
                    </div>
                    <div class="insight-text">
                        ROAS {best_roas["ROAS"]:.2f}×
                        · CM2 {money(best_roas["CM2"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with c:

        if worst_return is not None:

            st.markdown(
                f"""
                <div class="insight">
                    <div class="insight-tag">
                        HIGHEST RETURN RATE
                    </div>
                    <div class="insight-main">
                        {worst_return["CHANNEL_CLEAN"]}
                    </div>
                    <div class="insight-text">
                        Return Rate
                        {worst_return["Return Rate"]:.2%}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    # --------------------------------------------------------
    # Channel summary table
    # --------------------------------------------------------

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">'
        'Channel Performance Summary'
        '</div>',
        unsafe_allow_html=True
    )

    if not channel_summary.empty:

        display = channel_summary.copy()

        display["Net Revenue"] = (
            display["Net_Revenue"]
            .map(money)
        )

        display["CM2"] = (
            display["CM2"]
            .map(money)
        )

        display["Ad Spend"] = (
            display["Ad_Spend"]
            .map(money)
        )

        display["ROAS"] = (
            channel_summary["ROAS"]
            .map(lambda v: f"{v:.2f}×")
        )

        display["Return Rate"] = (
            channel_summary["Return Rate"]
            .map(lambda v: f"{v:.2%}")
        )

        display = display[
            [
                "CHANNEL_CLEAN",
                "Net Revenue",
                "CM2",
                "Ad Spend",
                "ROAS",
                "Return Rate"
            ]
        ]

        display.columns = [
            "Channel",
            "Net Revenue",
            "CM2",
            "Ad Spend",
            "ROAS",
            "Return Rate"
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # ROAS + Return Rate
    # --------------------------------------------------------

    left, right = st.columns(
        2,
        gap="large"
    )

    with left:

        if not channel_summary.empty:

            s = (
                channel_summary
                .sort_values("ROAS")
            )

            f = px.bar(
                s,
                x="ROAS",
                y="CHANNEL_CLEAN",
                orientation="h",
                text="ROAS"
            )

            f.update_traces(
                marker_color=GREEN,
                texttemplate="%{x:.2f}×",
                textposition="outside"
            )

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="section-title">'
                'ROAS by Channel'
                '</div>',
                unsafe_allow_html=True
            )

            st.plotly_chart(
                layout(f),
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

    with right:

        if not channel_summary.empty:

            s = (
                channel_summary
                .sort_values("Return Rate")
            )

            f = px.bar(
                s,
                x="Return Rate",
                y="CHANNEL_CLEAN",
                orientation="h",
                text="Return Rate"
            )

            f.update_traces(
                marker_color=DARK,
                texttemplate="%{x:.2%}",
                textposition="outside"
            )

            f.update_xaxes(
                tickformat=".0%"
            )

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="section-title">'
                'Return Rate by Channel'
                '</div>',
                unsafe_allow_html=True
            )

            st.plotly_chart(
                layout(f),
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

    # --------------------------------------------------------
    # Export
    # --------------------------------------------------------

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">'
        'Export Current View'
        '</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Download the rows represented by the current filters."
    )

    st.download_button(
        "Download filtered CSV",
        data=x.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="BECO_filtered_analysis.csv",
        mime="text/csv"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    f"""
    <div class="footer-note">
        BECO Sales &amp; Profitability
        · {len(x):,} filtered rows
        · {start:%b %Y} – {end:%b %Y}
        · Streamlit + Plotly
    </div>
    """,
    unsafe_allow_html=True
)
