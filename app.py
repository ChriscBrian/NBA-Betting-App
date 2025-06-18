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

dark_mode = True  # force dark theme

# -----------------------
# --- Sidebar Nav -------
# -----------------------
sidebar_css = '''
<style>
/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #111111;
    color: #e0e0e0;
    padding-top: 2rem;
}
/* Title styling */
[data-testid="stSidebar"] .css-1d391kg .css-1v3fvcr {
    font-size: 1.5rem;
    font-weight: 700;
    color: #00ff88 !important;
    padding-left: 1rem;
}
/* Nav label styling */
[data-testid="stSidebar"] .stRadio > label,
[data-testid="stSidebar"] .stRadio {
    color: #e0e0e0 !important;
}
[data-testid="stSidebar"] .stRadio > div {
    padding: 0.5rem 1rem;
    border-radius: 4px;
}
[data-testid="stSidebar"] .stRadio > div:hover {
    background-color: #003300;
    color: #00ff88 !important;
}
</style>
'''
st.markdown(sidebar_css, unsafe_allow_html=True)

# Sidebar content
st.sidebar.markdown("# ParlayPlay")
page = st.sidebar.radio("", ["Dashboard", "Post Bets"], index=0,
                         format_func=lambda x: f"🎲 {x}" if x == "Dashboard" else f"📝 {x}")

# -----------------------
# --- Banner CSS & HTML-
# -----------------------
banner_css = '''
<style>
/* Banner styling: absolute top, above all */
.banner {
  position: absolute !important;
  top: 0 !important;
  left: 0;
  width: 100%;
  height: 50px !important;
  background-color: #000 !important;
  overflow: hidden !important;
  display: flex !important;
  align-items: center !important;
  z-index: 2000 !important;
}
.banner img {
  height: 40px !important;
  margin: 0 8px !important;
  animation: scroll 20s linear infinite !important;
}
@keyframes scroll {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
.content-wrapper {
  padding-top: 60px !important; /* account for banner height */
  padding-left: 16px;
  padding-right: 16px;
}
</style>
'''
st.markdown(banner_css, unsafe_allow_html=True)

# Banner images
NBA_LOGOS = [
    "https://loodibee.com/wp-content/uploads/nba-atlanta-hawks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    # ... add other logos here ...
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
logo_html = '<div class="banner">' + ''.join(f'<img src="{url}" />' for url in NBA_LOGOS) + '</div>'
st.markdown(logo_html, unsafe_allow_html=True)

# Wrap main content
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

# -----------------------
# --- Data Fetching ----
# -----------------------
API_KEY = os.getenv("ODDS_API_KEY", 3d4eabb1db321b1add71a25189a77697")

@st.cache_data
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"apiKey": API_KEY, "regions": "us", "markets": "spreads,totals,h2h", "oddsFormat": "american"}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

try:
    raw = fetch_odds()
    st.success(f"✅ Retrieved {len(raw)} games")
except:
    st.warning("⚠️ Using sample data")
    raw = [{"home_team":"Lakers","away_team":"Warriors","bookmakers":[{"markets":[{"key":"spreads","outcomes":[{"name":"Lakers","price":-110},{"name":"Warriors","price":100}]}]}]}]

# -----------------------
# --- Data Processing --
# -----------------------
rows = []
today = datetime.today().strftime("%Y-%m-%d")
def prob(o): return round(1/(1+10**(-o/400)),4)
def ev_calc(p,o): imp=(100/(100+o)) if o>0 else (abs(o)/(100+abs(o))); ev=p*(o if o>0 else 100)-(1-p)*100; return round(ev,2), round(p*100,1), round(imp*100,1)
for g in raw:
    h,a = g.get("home_team"),g.get("away_team")
    if not h or not a: continue
    m = f"{a} @ {h}"
    for b in g.get("bookmakers",[]):
        for mk in b.get("markets",[]):
            for o in mk.get("outcomes",[]):
                price = o.get("price")
                if price is None: continue
                ev,_,_ = ev_calc(prob(price),price)
                rows.append({"Date":today,"Matchup":m,"Team":o.get("name"),"Market":mk.get("key"),"Odds":price,"EV%":ev})
df = pd.DataFrame(rows)

# -----------------------
# --- Session State ----
# -----------------------
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_bets" not in st.session_state: st.session_state.user_bets = []

# -----------------------
# --- Dashboard View ----
# -----------------------
if page == "Dashboard":
    st.title("Dashboard")
    if df.empty:
        st.info("No data available.")
    else:
        st.markdown("---")
        ev_cut = st.slider("Minimum EV%", -100, 100, -100)
        df2 = df[df["EV%"] >= ev_cut]
        st.plotly_chart(px.histogram(df2, x="EV%", nbins=20, color_discrete_sequence=["#00ff88"]), use_container_width=True)
        st.markdown("---")
        st.subheader("Top Picks")
        for _, r in df2.sort_values("EV%", ascending=False).head(5).iterrows():
            st.markdown(f"<div style='background:#111; padding:8px; margin:4px 0; border-left:4px solid #00ff88; color:#e0e0e0;'>{r['Matchup']} — {r['Odds']} ({r['EV%']}%)</div>", unsafe_allow_html=True)

# -----------------------
# --- Post Bets View ---
# -----------------------
else:
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

# Close wrapper
st.markdown('</div>', unsafe_allow_html=True)
