import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------
# --- Page & Theme -----
# -----------------------
st.set_page_config(page_title="ParlayPlay", layout="wide")

# -----------------------
# --- Sidebar Nav -------
# -----------------------
st.markdown(
    """
    <style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #111111;
        color: #00ff88;
        padding-top: 2rem;
    }
    .css-hi6a2p { /* nav item container */
        color: #ccc;
        padding: 0.5rem 1rem;
        font-size: 1rem;
    }
    .css-hi6a2p:hover {
        background-color: #003300;
        color: #00ff88;
    }
    .css-1d391kg .css-1v3fvcr {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #00ff88;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title in sidebar
st.sidebar.markdown("# ParlayPlay")

# Navigation
page = st.sidebar.radio(
    "",
    ["Dashboard", "Post Bets"],
    index=0,
    format_func=lambda x: f"🎲 {x}" if x=="Dashboard" else f"📝 {x}"
)

# Force dark background
st.markdown(
    """
    <style>
    .css-1bd0h47 { background-color: #000000 !important; }
    .css-18ni7ap { background-color: #000000 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

dark_mode = True

# -----------------------
# --- Fetch & Parse ----
# -----------------------
API_KEY = os.getenv("ODDS_API_KEY", "3d4eabb1db321b1add71a25189a77697")

@st.cache_data
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"apiKey": API_KEY, "regions": "us", "markets": "spreads,totals,h2h", "oddsFormat": "american"}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

# Try fetching or fallback
try:
    raw = fetch_odds()
    st.success(f"✅ Retrieved {len(raw)} games")
except:
    st.warning("⚠️ Using sample data")
    raw = [{"home_team":"Lakers","away_team":"Warriors","bookmakers":[{"markets":[{"key":"spreads","outcomes":[{"name":"Lakers","price":-110},{"name":"Warriors","price":100}]}]}]}]

# Build DataFrame
rows = []
date = datetime.today().strftime("%Y-%m-%d")
def prob(o): return round(1/(1+10**(-o/400)),4)
def ev_calc(p,o): imp=(100/(100+o)) if o>0 else (abs(o)/(100+abs(o))); ev=p*(o if o>0 else 100)-(1-p)*100; return round(ev,2), round(p*100,1), round(imp*100,1)
for g in raw:
    home, away = g.get("home_team"), g.get("away_team")
    if not home or not away: continue
    matchup = f"{away} @ {home}"
    for b in g.get("bookmakers",[]):
        for mk in b.get("markets",[]):
            for o in mk.get("outcomes",[]):
                price = o.get("price")
                if price is None: continue
                p = prob(price)
                ev, mp, ip = ev_calc(p, price)
                rows.append({"Date": date, "Matchup": matchup, "Team": o["name"], "Market": mk["key"], "Odds": price, "EV%": ev})
df = pd.DataFrame(rows)

# -----------------------
# --- Session State ----
# -----------------------
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "user_bets" not in st.session_state: st.session_state.user_bets=[]

# -----------------------
# --- Dashboard View ---
# -----------------------
if page == "Dashboard":
    st.title("Dashboard")
    if df.empty:
        st.info("No data available.")
    else:
        st.markdown("---")
        min_ev = st.slider("Minimum EV%", -100, 100, -100)
        df2 = df[df["EV%"] >= min_ev]
        st.plotly_chart(
            px.histogram(df2, x="EV%", nbins=20, color_discrete_sequence=["#00ff88"]),
            use_container_width=True
        )
        st.markdown("---")
        st.subheader("Top Picks")
        for _, r in df2.sort_values("EV%", ascending=False).head(5).iterrows():
            st.markdown(f"<div style='background:#111; padding:8px; margin:4px 0; border-left:4px solid #00ff88; color:#e0e0e0;'>{r['Matchup']} — {r['Odds']} ({r['EV%']}%)</div>", unsafe_allow_html=True)

# -----------------------
# --- Post Bets View ---
# -----------------------
elif page == "Post Bets":
    st.title("Post Bets")
    if not st.session_state.logged_in:
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            st.session_state.logged_in = True
            st.success(f"Welcome, {user}!")
    else:
        bet = st.text_area("Your Bet")
        if st.button("Submit Bet"):
            st.session_state.user_bets.append(bet)
            st.success("Bet posted!")
        if st.session_state.user_bets:
            st.subheader("Your Bets")
            for b in st.session_state.user_bets:
                st.markdown(f"- {b}")
