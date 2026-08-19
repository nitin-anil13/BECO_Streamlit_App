import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="BECO | Sales & Profitability",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# THEME
# =========================
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

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,600;1,700&display=swap');
.stApp {{background:{CREAM}; color:{TEXT};}}
.block-container {{max-width:1550px; padding:1rem 1.35rem 2rem;}}
#MainMenu, footer, header {{visibility:hidden;}}
[data-testid="stSidebar"] {{background:#F0F5EB; border-right:1px solid {BORDER};}}
[data-testid="stSidebar"] label {{color:{DARK}!important; font-weight:600!important;}}
.hero {{background:linear-gradient(135deg,#FFFDF9,#EEF5E9); border:1px solid {BORDER};
        border-radius:28px; padding:18px 24px; margin-bottom:14px;
        box-shadow:0 10px 24px rgba(20,55,45,.10);}}
.hero-title {{font-family:'DM Sans'; font-size:clamp(30px,4vw,50px); font-weight:700;
              color:{DARK}; text-align:center; letter-spacing:-1px;}}
.hero-sub {{text-align:center; color:{MUTED}; font-size:12px; margin-top:4px;}}
.page-title {{font-family:'Playfair Display',Georgia,serif; font-size:30px; font-style:italic;
              font-weight:700; color:{DARK}; margin:7px 0 12px;}}
.section-title {{font-family:'Playfair Display',Georgia,serif; font-size:23px; font-style:italic;
                font-weight:700; color:{DARK}; margin-bottom:5px;}}
.card {{background:{CARD}; border:1px solid {BORDER}; border-radius:24px; padding:15px 17px 9px;
        box-shadow:7px 9px 18px rgba(26,52,42,.11); margin-bottom:15px;}}
.kpi {{background:{CARD}; border:1px solid {BORDER}; border-radius:22px; padding:17px 14px;
      min-height:120px; box-shadow:7px 9px 18px rgba(26,52,42,.13);
      border-left:5px solid {GREEN};}}
.kpi-label {{color:{MUTED}; font-size:12px; font-weight:700; text-transform:uppercase;
             letter-spacing:.6px;}}
.kpi-value {{color:{DARK}; font-family:Georgia,serif; font-size:33px; font-weight:700; margin-top:7px;}}
.kpi-note {{color:{MUTED}; font-size:11px; margin-top:5px;}}
.insight {{background:linear-gradient(135deg,#F8FBF4,#EAF3E5); border:1px solid {BORDER};
          border-radius:18px; padding:14px 16px; min-height:105px;}}
.insight-tag {{display:inline-block; background:{PALE}; border:1px solid {BORDER};
              color:{GREEN_DARK}; border-radius:999px; padding:3px 9px; font-size:10px;
              font-weight:700; margin-bottom:5px;}}
.insight-main {{font-weight:700; font-size:18px; color:{DARK};}}
.insight-text {{font-size:11px; color:{MUTED}; margin-top:4px; line-height:1.4;}}
.filter-summary {{background:{PALE}; border:1px solid {BORDER}; border-radius:13px;
                 padding:8px 12px; color:{DARK}; font-size:12px; margin-bottom:12px;}}
.footer-note {{text-align:center; color:{MUTED}; font-size:11px; padding-top:8px;}}
.stDownloadButton > button {{width:100%; background:{GREEN}; color:white; border:0;
                             border-radius:11px; font-weight:700;}}
</style>
""", unsafe_allow_html=True)


# =========================
# DATA
# =========================
@st.cache_data(show_spinner=False)
def load_data(path):
    df = pd.read_csv(path, low_memory=False)

    # Make duplicate headers safe.
    seen, cols = {}, []
    for c in df.columns:
        c = str(c).strip()
        n = seen.get(c, 0)
        cols.append(c if n == 0 else f"{c}_{n}")
        seen[c] = n + 1
    df.columns = cols

    def pick(*names):
        return next((n for n in names if n in df.columns), None)

    date_col = pick("MONTH_CLEAN", "MONTH", "Month", "Date")
    channel_col = pick("CHANNEL_CLEAN", "CHANNEL", "Channel")
    region_col = pick("REGION", "Region", "region")
    category_col = pick("Category", "CATEGORY", "category")

    if not all([date_col, channel_col, region_col]):
        raise ValueError("Need MONTH/MONTH_CLEAN, CHANNEL/CHANNEL_CLEAN and REGION.")

    rename = {date_col:"MONTH_CLEAN", channel_col:"CHANNEL_CLEAN", region_col:"REGION"}
    if category_col:
        rename[category_col] = "Category"
    df = df.rename(columns=rename)

    if "Category" not in df:
        df["Category"] = "Unmapped"

    aliases = {
        "Net_Revenue":"NET_REVENUE", "Net Revenue":"NET_REVENUE",
        "COGS_Amount":"COGS", "Cogs":"COGS",
        "Ad_Spend":"AD_SPEND", "Ad Spend":"AD_SPEND",
        "Returns_Units":"RETURNS_UNITS", "Units_Sold":"UNITS_SOLD",
        "Gross_Revenue":"GROSS_REVENUE", "Discount":"DISCOUNT",
        "CM2_CALC":"CM2", "RETURN_RATE_PCT":"RETURN_RATE_PCT",
    }
    for old, new in aliases.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old:new})

    for c in ["NET_REVENUE","COGS","UNIT_COGS","AD_SPEND","RETURNS_UNITS",
              "UNITS_SOLD","GROSS_REVENUE","DISCOUNT","CM2"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["MONTH_CLEAN"] = pd.to_datetime(df["MONTH_CLEAN"], errors="coerce")
    df = df.dropna(subset=["MONTH_CLEAN"]).copy()

    # Use existing Power BI/Excel derived values when present.
    if "NET_REVENUE" not in df:
        df["NET_REVENUE"] = df.get("GROSS_REVENUE", 0) - df.get("DISCOUNT", 0)

    if "COGS" not in df:
        df["COGS"] = df.get("UNIT_COGS", 0) * df.get("UNITS_SOLD", 0)

    for c in ["AD_SPEND","RETURNS_UNITS","UNITS_SOLD"]:
        if c not in df:
            df[c] = 0

    if "CM2" not in df:
        df["CM2"] = df["NET_REVENUE"] - df["COGS"] - df["AD_SPEND"]

    for c in ["CHANNEL_CLEAN","REGION","Category"]:
        df[c] = df[c].fillna("Unmapped").astype(str).str.strip()
        df.loc[df[c].isin(["","nan","None","NaN"]), c] = "Unmapped"

    df["CHANNEL_CLEAN"] = df["CHANNEL_CLEAN"].replace({
        "d2c":"D2C","D2c":"D2C","Shopify":"D2C","shopify":"D2C",
        "Instamart":"Swiggy Instamart","instamart":"Swiggy Instamart",
        "FlipKart":"Flipkart","flipkart":"Flipkart"
    })

    df["Month Key"] = df["MONTH_CLEAN"].dt.year*100 + df["MONTH_CLEAN"].dt.month
    return df.sort_values("MONTH_CLEAN")


if not CSV_PATH.exists():
    st.error("Clean_Sales.csv was not found next to app.py.")
    st.stop()

try:
    df = load_data(CSV_PATH)
except Exception as e:
    st.error(f"Could not load Clean_Sales.csv: {e}")
    st.stop()


# =========================
# HELPERS
# =========================
def money(v):
    v = float(v or 0)
    if abs(v) >= 1_000_000:
        return f"₹{v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"₹{v/1_000:.1f}K"
    return f"₹{v:,.0f}"


def layout(fig, height=330):
    fig.update_layout(
        height=height, margin=dict(l=10,r=18,t=15,b=10),
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=dict(family="DM Sans,Arial", color=TEXT),
        hoverlabel=dict(bgcolor=WHITE),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


def kpi(label, value, note):
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',
        unsafe_allow_html=True
    )


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)

    st.markdown("## BECO Analytics")
    st.caption("Sales • Profitability • Insights")

    page = st.radio("Navigate", ["Overview","Profitability","Insights"], index=0)

    st.divider()
    st.markdown("### Filters")

    min_date = df["MONTH_CLEAN"].min().date()
    max_date = df["MONTH_CLEAN"].max().date()

    date_range = st.date_input(
        "Month",
        value=(min_date,max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )

    region = st.selectbox("Region", ["All"] + sorted(df["REGION"].unique()))
    category = st.selectbox("Category", ["All"] + sorted(df["Category"].unique()))
    channel = st.selectbox("Channel", ["All"] + sorted(df["CHANNEL_CLEAN"].unique()))

    st.divider()
    st.caption(f"{len(df):,} source rows")
    st.caption(f"{min_date:%b %Y} – {max_date:%b %Y}")

    if st.button("Reload data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if isinstance(date_range, (tuple,list)) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start = end = pd.Timestamp(date_range)

x = df[(df["MONTH_CLEAN"] >= start) &
       (df["MONTH_CLEAN"] < end + pd.Timedelta(days=1))].copy()

if region != "All": x = x[x["REGION"] == region]
if category != "All": x = x[x["Category"] == category]
if channel != "All": x = x[x["CHANNEL_CLEAN"] == channel]


# =========================
# HEADER + KPI
# =========================
st.markdown(
    '<div class="hero"><div class="hero-title">BECO Sales &amp; Profitability Dashboard</div>'
    '<div class="hero-sub">Interactive business performance dashboard</div></div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="filter-summary"><b>Current view:</b> {start:%d %b %Y} → '
    f'{end:%d %b %Y} &nbsp;•&nbsp; Region: <b>{region}</b> &nbsp;•&nbsp; '
    f'Category: <b>{category}</b> &nbsp;•&nbsp; Channel: <b>{channel}</b> '
    f'&nbsp;•&nbsp; {len(x):,} rows</div>',
    unsafe_allow_html=True
)

net_revenue = x["NET_REVENUE"].sum()
cm2 = x["CM2"].sum()
ad_spend = x["AD_SPEND"].sum()
units = x["UNITS_SOLD"].sum()
returns = x["RETURNS_UNITS"].sum()
roas = net_revenue/ad_spend if ad_spend else 0
return_rate = returns/units if units else 0
cm2_margin = cm2/net_revenue if net_revenue else 0

a,b,c,d = st.columns(4, gap="medium")
with a: kpi("Total Net Revenue", money(net_revenue), "Revenue after discounts")
with b: kpi("CM2", money(cm2), f"CM2 margin {cm2_margin:.1%}")
with c: kpi("Blended ROAS", f"{roas:.2f}×", "Net revenue ÷ ad spend")
with d: kpi("Return Rate", f"{return_rate:.2%}", f"{returns:,.0f} returned units")

st.write("")


# =========================
# OVERVIEW
# =========================
if page == "Overview":
    st.markdown('<div class="page-title">Overview</div>', unsafe_allow_html=True)

    monthly = (x.groupby(["MONTH_CLEAN","Month Key"],as_index=False)
               .agg(Net_Revenue=("NET_REVENUE","sum"))
               .sort_values("Month Key"))

    fig = px.line(monthly,x="MONTH_CLEAN",y="Net_Revenue",markers=True)
    fig.update_traces(
        line=dict(color=DARK,width=3), marker=dict(color=GREEN,size=8),
        hovertemplate="%{x|%b-%Y}<br>Net Revenue: ₹%{y:,.0f}<extra></extra>"
    )
    fig.update_xaxes(tickformat="%b-%y",showgrid=False,title="Month")
    fig.update_yaxes(tickformat="~s",title="Net Revenue")
    st.markdown('<div class="card">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Monthly Net Revenue Trend</div>',unsafe_allow_html=True)
    st.plotly_chart(layout(fig,390),use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)

    l,r = st.columns(2,gap="large")

    with l:
        s=x.groupby("CHANNEL_CLEAN",as_index=False)["NET_REVENUE"].sum().sort_values("NET_REVENUE")
        f=px.bar(s,x="NET_REVENUE",y="CHANNEL_CLEAN",orientation="h",text="NET_REVENUE")
        f.update_traces(marker_color=GREEN,texttemplate="₹%{x:.3s}",textposition="outside",
                        hovertemplate="%{y}<br>₹%{x:,.0f}<extra></extra>")
        f.update_xaxes(tickformat="~s")
        st.markdown('<div class="card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">Net Revenue by Channel</div>',unsafe_allow_html=True)
        st.plotly_chart(layout(f),use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    with r:
        s=x.groupby("REGION",as_index=False)["NET_REVENUE"].sum().sort_values("NET_REVENUE")
        f=px.bar(s,x="NET_REVENUE",y="REGION",orientation="h",text="NET_REVENUE")
        f.update_traces(marker_color=DARK,texttemplate="₹%{x:.3s}",textposition="outside",
                        hovertemplate="%{y}<br>₹%{x:,.0f}<extra></extra>")
        f.update_xaxes(tickformat="~s")
        st.markdown('<div class="card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">Net Revenue by Region</div>',unsafe_allow_html=True)
        st.plotly_chart(layout(f),use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div class="card">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Revenue Mix by Category</div>',unsafe_allow_html=True)
    s=x.groupby("Category",as_index=False)["NET_REVENUE"].sum().sort_values("NET_REVENUE",ascending=False)
    f=px.bar(s,x="Category",y="NET_REVENUE",text="NET_REVENUE")
    f.update_traces(marker_color=GREEN_DARK,texttemplate="₹%{y:.3s}",textposition="outside",
                    hovertemplate="%{x}<br>₹%{y:,.0f}<extra></extra>")
    f.update_yaxes(tickformat="~s")
    st.plotly_chart(layout(f,300),use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)


# =========================
# PROFITABILITY
# =========================
elif page == "Profitability":
    st.markdown('<div class="page-title">Profitability</div>',unsafe_allow_html=True)

    m=(x.groupby(["MONTH_CLEAN","Month Key"],as_index=False)
       .agg(CM2=("CM2","sum"),AD_SPEND=("AD_SPEND","sum"))
       .sort_values("Month Key"))

    f=go.Figure()
    f.add_trace(go.Scatter(x=m["MONTH_CLEAN"],y=m["CM2"],mode="lines+markers",
                           name="CM2",line=dict(color=GREEN_DARK,width=3)))
    f.add_trace(go.Scatter(x=m["MONTH_CLEAN"],y=m["AD_SPEND"],mode="lines+markers",
                           name="Ad Spend",line=dict(color=DARK,width=3)))
    f.update_xaxes(tickformat="%b-%y",showgrid=False,title="Month")
    f.update_yaxes(tickformat="~s",title="Amount")
    st.markdown('<div class="card">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">CM2 vs Ad Spend</div>',unsafe_allow_html=True)
    st.plotly_chart(layout(f,380),use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div class="card">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">CM2 by Channel × Category</div>',unsafe_allow_html=True)
    p=pd.pivot_table(x,index="CHANNEL_CLEAN",columns="Category",values="CM2",aggfunc="sum",fill_value=0)
    if not p.empty:
        p["Total"]=p.sum(axis=1)
        p.loc["Total"]=p.sum(axis=0)
        st.dataframe(p.style.format("₹{:,.0f}"),use_container_width=True,
                     height=min(460,130+len(p.index)*40))
    else:
        st.info("No data for the current filters.")
    st.markdown('</div>',unsafe_allow_html=True)

    l,r=st.columns(2,gap="large")
    with l:
        s=x.groupby("CHANNEL_CLEAN",as_index=False)["CM2"].sum().sort_values("CM2")
        f=px.bar(s,x="CM2",y="CHANNEL_CLEAN",orientation="h",text="CM2")
        f.update_traces(marker_color=GREEN,texttemplate="₹%{x:.3s}",textposition="outside")
        f.update_xaxes(tickformat="~s")
        st.markdown('<div class="card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">CM2 by Channel</div>',unsafe_allow_html=True)
        st.plotly_chart(layout(f),use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)

    with r:
        s=x.groupby("Category",as_index=False)["CM2"].sum().sort_values("CM2")
        f=px.bar(s,x="CM2",y="Category",orientation="h",text="CM2")
        f.update_traces(marker_color=DARK,texttemplate="₹%{x:.3s}",textposition="outside")
        f.update_xaxes(tickformat="~s")
        st.markdown('<div class="card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">CM2 by Category</div>',unsafe_allow_html=True)
        st.plotly_chart(layout(f),use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>',unsafe_allow_html=True)


# =========================
# INSIGHTS
# =========================
else:
    st.markdown('<div class="page-title">Insights</div>',unsafe_allow_html=True)

    cs=(x.groupby("CHANNEL_CLEAN",as_index=False)
        .agg(Net_Revenue=("NET_REVENUE","sum"),CM2=("CM2","sum"),
             Ad_Spend=("AD_SPEND","sum"),Units=("UNITS_SOLD","sum"),
             Returns=("RETURNS_UNITS","sum")))
    if not cs.empty:
        cs["ROAS"]=cs["Net_Revenue"].div(cs["Ad_Spend"].replace(0,pd.NA)).fillna(0)
        cs["Return Rate"]=cs["Returns"].div(cs["Units"].replace(0,pd.NA)).fillna(0)
        best=cs.loc[cs["CM2"].idxmax()]
        best_roas=cs.loc[cs["ROAS"].idxmax()]
        worst_return=cs.loc[cs["Return Rate"].idxmax()]
    else:
        best=best_roas=worst_return=None

    cc=(x.groupby(["CHANNEL_CLEAN","Category"],as_index=False)
        .agg(CM2=("CM2","sum"),Net_Revenue=("NET_REVENUE","sum"),
             Ad_Spend=("AD_SPEND","sum")))
    if not cc.empty:
        cc["ROAS"]=cc["Net_Revenue"].div(cc["Ad_Spend"].replace(0,pd.NA)).fillna(0)
        best_combo=cc.loc[cc["CM2"].idxmax()]
    else:
        best_combo=None

    a,b,c=st.columns(3,gap="medium")
    with a:
        if best is not None:
            st.markdown(f'<div class="insight"><div class="insight-tag">TOP CM2</div>'
                        f'<div class="insight-main">{best["CHANNEL_CLEAN"]}</div>'
                        f'<div class="insight-text">CM2 {money(best["CM2"])} · '
                        f'Net Revenue {money(best["Net_Revenue"])}</div></div>',unsafe_allow_html=True)
    with b:
        if best_combo is not None:
            st.markdown(f'<div class="insight"><div class="insight-tag">BEST PROFIT POOL</div>'
                        f'<div class="insight-main">{best_combo["CHANNEL_CLEAN"]} × {best_combo["Category"]}</div>'
                        f'<div class="insight-text">CM2 {money(best_combo["CM2"])} · '
                        f'ROAS {best_combo["ROAS"]:.2f}×</div></div>',unsafe_allow_html=True)
    with c:
        if worst_return is not None:
            st.markdown(f'<div class="insight"><div class="insight-tag">WATCH</div>'
                        f'<div class="insight-main">{worst_return["CHANNEL_CLEAN"]}</div>'
                        f'<div class="insight-text">Highest return rate: '
                        f'{worst_return["Return Rate"]:.2%}</div></div>',unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="card">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Channel Performance</div>',unsafe_allow_html=True)
    if not cs.empty:
        display=cs.rename(columns={"CHANNEL_CLEAN":"Channel","Net_Revenue":"Net Revenue",
                                  "CM2":"CM2","Ad_Spend":"Ad Spend","Units":"Units Sold",
                                  "Returns":"Returns","Return Rate":"Return Rate"}).copy()
        display["Net Revenue"]=display["Net Revenue"].map(money)
        display["CM2"]=display["CM2"].map(money)
        display["Ad Spend"]=display["Ad Spend"].map(money)
        display["Units Sold"]=display["Units Sold"].map(lambda v:f"{v:,.0f}")
        display["Returns"]=display["Returns"].map(lambda v:f"{v:,.0f}")
        display["ROAS"]=display["ROAS"].map(lambda v:f"{v:.2f}×")
        display["Return Rate"]=display["Return Rate"].map(lambda v:f"{v:.2%}")
        st.dataframe(display,use_container_width=True,hide_index=True)
    st.markdown('</div>',unsafe_allow_html=True)

    l,r=st.columns(2,gap="large")
    with l:
        if not cs.empty:
            s=cs.sort_values("ROAS")
            f=px.bar(s,x="ROAS",y="CHANNEL_CLEAN",orientation="h",text="ROAS")
            f.update_traces(marker_color=GREEN,texttemplate="%{x:.2f}×",textposition="outside")
            st.markdown('<div class="card">',unsafe_allow_html=True)
            st.markdown('<div class="section-title">ROAS by Channel</div>',unsafe_allow_html=True)
            st.plotly_chart(layout(f),use_container_width=True,config={"displayModeBar":False})
            st.markdown('</div>',unsafe_allow_html=True)

    with r:
        if not cs.empty:
            s=cs.sort_values("Return Rate")
            f=px.bar(s,x="Return Rate",y="CHANNEL_CLEAN",orientation="h",text="Return Rate")
            f.update_traces(marker_color=DARK,texttemplate="%{x:.2%}",textposition="outside")
            f.update_xaxes(tickformat=".0%")
            st.markdown('<div class="card">',unsafe_allow_html=True)
            st.markdown('<div class="section-title">Return Rate by Channel</div>',unsafe_allow_html=True)
            st.plotly_chart(layout(f),use_container_width=True,config={"displayModeBar":False})
            st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div class="card">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Export Current View</div>',unsafe_allow_html=True)
    st.caption("Download the rows represented by the current filters.")
    st.download_button(
        "Download filtered CSV",
        data=x.to_csv(index=False).encode("utf-8"),
        file_name="BECO_filtered_analysis.csv",
        mime="text/csv",
    )
    st.markdown('</div>',unsafe_allow_html=True)

st.markdown(
    f'<div class="footer-note">BECO Sales &amp; Profitability · {len(x):,} filtered rows · '
    f'{start:%b %Y} – {end:%b %Y} · Streamlit + Plotly</div>',
    unsafe_allow_html=True
)
