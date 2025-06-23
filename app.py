import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import urllib3

# Disable SSL warnings
urllib3.disable_warnings()

# -----------------------
# --- Page Config ------
# -----------------------
st.set_page_config(page_title="ParlayPlay", layout="wide")

dark_mode = True  # force dark theme

# -----------------------
# --- Simple Auth -------
# -----------------------
# Hardcoded credentials (in production, use a secure store)
VALID_USERS = {"admin": "password123", "user1": "pass1"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Login form
if not st.session_state.logged_in:
    st.title("🔐 ParlayPlay Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if VALID_USERS.get(username) == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# -----------------------
# --- Global CSS -------
# -----------------------
st.markdown("""
<style>
  /* Hide default menu/header/footer */
  #MainMenu, header, footer {visibility: hidden !important;}

  /* Sidebar styling */
  [data-testid="stSidebar"] {
    background-color: #000 !important;
    padding-top: 2rem;
  }
  /* Sidebar title */
  [data-testid="stSidebar"] .css-1d391kg .css-1v3fvcr {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #00ff88 !important;
    text-align: center !important;
    margin-bottom: 1rem;
  }
  /* Sidebar nav labels */
  [data-testid="stSidebar"] input[type="radio"] + label {
    color: #00ff88 !important;
    font-size: 1.25rem !important;
    text-align: center !important;
    padding: 0.75rem 1rem !important;
    display: block !important;
  }
  [data-testid="stSidebar"] input[type="radio"] + label:hover {
    background-color: #003300 !important;
  }

  /* Banner styling */
  .banner {
    position: fixed !important;
    top: 0; left: 0;
    width: 100%; height: 50px;
    background-color: #000;
    display: flex; align-items: center;
    overflow: hidden; z-index: 9999;
  }
  .banner img {
    height: 40px; margin: 0 8px;
    animation: scroll 20s linear infinite;
  }
  @keyframes scroll {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
  }

  /* Main content offset */
  .content-wrapper {
    padding-top: 60px;
    padding-left: 16px;
    padding-right: 16px;
  }

  /* Section styling */
  .section {
    background: linear-gradient(135deg, #001f3f, #003366);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    color: #FFDF00;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  }
</style>
""", unsafe_allow_html=True)

# -----------------------
# --- Sidebar Nav -------
# -----------------------
st.sidebar.markdown(f"# ParlayPlay\n\n👤 {st.session_state.username}")
page = st.sidebar.radio(
    "",
    ["Dashboard", "Post Bets"],
    index=0,
    format_func=lambda x: f"🎲 {x}" if x == "Dashboard" else f"📝 {x}"
)

# -----------------------
# --- Top Banner --------
# -----------------------
NBA_LOGOS = [
    "https://loodibee.com/wp-content/uploads/nba-atlanta-hawks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    # ...
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
st.markdown('<div class="banner">' + ''.join(f'<img src="{u}"/>' for u in NBA_LOGOS) + '</div>', unsafe_allow_html=True)
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

# -----------------------
# --- Live Scores -------
# -----------------------
@st.cache_data(ttl=30)
def fetch_live_scores():
    today_key = datetime.utcnow().strftime("%Y%m%d")
    endpoints = [
        f"https://data.nba.net/prod/v1/{today_key}/scoreboard.json",
        "https://data.nba.net/prod/v1/scoreboard.json"
    ]
    for url in endpoints:
        try:
            res = requests.get(url, verify=False)
            res.raise_for_status()
            games = res.json().get("games", [])
            if games:
                return games
        except:
            continue
    return []

live_games = fetch_live_scores()

# -----------------------
# --- Odds Fetching -----
# -----------------------
API_KEY = os.getenv("ODDS_API_KEY", "3d4eabb1db321b1add71a25189a77697")
@st.cache_data(show_spinner=False)
def fetch_odds():
    base = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"apiKey":API_KEY, "regions":"us", "markets":"spreads,totals,h2h", "oddsFormat":"american"}
    try:
        r = requests.get(base, params=params)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            st.warning("API unsupported markets, falling back.")
            params["markets"] = "spreads,totals,h2h"
            r = requests.get(base, params=params); r.raise_for_status()
            return r.json()
        st.error(f"Failed to fetch odds: {e}")
        return []

try:
    raw_odds = fetch_odds()
except:
    raw_odds = []

# Process odds
rows=[]; dt = datetime.today().strftime("%Y-%m-%d")
def ep(o): return round(1/(1+10**(-o/400)),4)
def ev_calc(p,o): return round(p*(o if o>0 else 100)-(1-p)*100,2)
for g in raw_odds:
    h,a = g.get("home_team"), g.get("away_team")
    if not h or not a: continue
    m = f"{a} @ {h}"
    for b in g.get("bookmakers",[]):
        for mk in b.get("markets",[]):
            for o in mk.get("outcomes",[]):
                pr = o.get("price")
                if pr is None: continue
                rows.append({"Date":dt,"Matchup":m,"Team":o.get("name"),"Market":mk.get("key"),"Odds":pr,"EV%":ev_calc(ep(pr),pr)})
odds_df = pd.DataFrame(rows)

# -----------------------
# --- Dashboard View ----
# -----------------------
if page == "Dashboard":
    st.title("Dashboard")
    st.markdown("<div class='section'><h3>🏀 Live Game Scores</h3></div>", unsafe_allow_html=True)
    if live_games:
        df_ls = pd.DataFrame([{
            "Visitor":g["vTeam"]["triCode"],
            "Visitor Score":g["vTeam"].get("score","-"),
            "Home":g["hTeam"]["triCode"],
            "Home Score":g["hTeam"].get("score","-"),
            "Status":(
                f"Scheduled {g.get('startTimeUTC','')[11:16]} UTC" if g.get("statusNum")==1 else
                f"P{g.get('period',{}).get('current','')} {g.get('clock','')}" if g.get("statusNum")==2 else
                "Final"
            )
        } for g in live_games])
        st.table(df_ls)
    else:
        st.info("No live games right now.")

    st.markdown("<div class='section'><h3>📊 Odds & EV Distribution</h3></div>", unsafe_allow_html=True)
    if odds_df.empty:
        st.info("No betting data.")
    else:
        cut = st.slider("Minimum EV%", -100,100,-100)
        fdf = odds_df[odds_df["EV%"]>=cut]
        st.plotly_chart(px.histogram(fdf,x="EV%",nbins=20,color_discrete_sequence=["#00ff88"]),use_container_width=True)
        st.markdown("<div class='section'><h3>🔥 Top Picks</h3></div>", unsafe_allow_html=True)
        for _,r in fdf.sort_values("EV%",ascending=False).head(5).iterrows():
            st.markdown(f"<div style='background:#111;padding:8px;margin:4px 0;border-left:4px solid #00ff88;color:#e0e0e0;'>{r['Matchup']} — {r['Odds']} ({r['EV%']}%)</div>",unsafe_allow_html=True)

# -----------------------
# --- Post Bets View ----
# -----------------------
else:
    st.title("Post Bets")
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
