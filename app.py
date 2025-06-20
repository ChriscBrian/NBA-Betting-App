import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------
# --- Page Config ------
# -----------------------
st.set_page_config(page_title="ParlayPlay", layout="wide")

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
st.sidebar.markdown("# ParlayPlay")
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
    # ... add your other logos ...
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
logo_html = '<div class="banner">' + ''.join(f'<img src="{url}" />' for url in NBA_LOGOS) + '</div>'
st.markdown(logo_html, unsafe_allow_html=True)

# Wrap content
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

# -----------------------
# --- Live Scores -------
# -----------------------
@st.cache_data(ttl=30)
def fetch_live_scores():
    today_key = datetime.utcnow().strftime("%Y%m%d")
    url = f"https://data.nba.net/prod/v1/{today_key}/scoreboard.json"
    data = requests.get(url).json().get("games", [])
    records = []
    for g in data:
        v = g["vTeam"]["triCode"]
        h = g["hTeam"]["triCode"]
        vs = g["vTeam"].get("score", "-")
        hs = g["hTeam"].get("score", "-")
        status = g.get("statusNum")
        if status == 1:
            # Scheduled
            t = g.get("startTimeUTC", "")[11:16] + " UTC"
            stat = f"Scheduled {t}"
        elif status == 2:
            # In Progress
            period = g.get("period", {}).get("current", "")
            clock = g.get("clock", "")
            stat = f"P{period} {clock}"
        else:
            stat = "Final"
        records.append({
            "Visitor": v,
            "Visitor Score": vs,
            "Home": h,
            "Home Score": hs,
            "Status": stat
        })
    return pd.DataFrame(records)

scores_df = fetch_live_scores()

# -----------------------
# --- Odds Fetching -----
# -----------------------
API_KEY = os.getenv("ODDS_API_KEY", "3d4eabb1db321b1add71a25189a77697")
@st.cache_data(show_spinner=False)
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"apiKey": API_KEY, "regions": "us", "markets": "spreads,totals,h2h", "oddsFormat": "american"}
    return requests.get(url, params=params).json()

try:
    raw_odds = fetch_odds()
except:
    st.warning("⚠️ Using sample odds data")
    raw_odds = [{
        "home_team":"Lakers","away_team":"Warriors",
        "bookmakers":[{"markets":[{"key":"spreads","outcomes":[{"name":"Lakers","price":-110},{"name":"Warriors","price":100}]}]}]
    }]

def estimate_prob(o): return round(1/(1+10**(-o/400)),4)
def calc_ev(p,o): return round(p*(o if o>0 else 100)-(1-p)*100,2)

rows = []
dt = datetime.today().strftime("%Y-%m-%d")
for g in raw_odds:
    home, away = g.get("home_team"), g.get("away_team")
    if not home or not away: continue
    mu = f"{away} @ {home}"
    for b in g["bookmakers"]:
        for mk in b["markets"]:
            for o in mk["outcomes"]:
                pr = o.get("price")
                if pr is None: continue
                rows.append({"Date":dt,"Matchup":mu,"Team":o["name"],"Market":mk["key"],"Odds":pr,"EV%":calc_ev(estimate_prob(pr),pr)})
odds_df = pd.DataFrame(rows)

# Session state
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_bets"   not in st.session_state: st.session_state.user_bets = []

# -----------------------
# --- Dashboard View ----
# -----------------------
if page == "Dashboard":
    st.title("Dashboard")

    st.markdown("<div class='section'><h3>🏀 Live Game Scores</h3></div>", unsafe_allow_html=True)
    if not scores_df.empty:
        st.table(scores_df)
    else:
        st.markdown("No live games at the moment.")

    st.markdown("<div class='section'><h3>📊 Odds & EV Distribution</h3></div>", unsafe_allow_html=True)
    if odds_df.empty:
        st.info("No betting data available.")
    else:
        cutoff = st.slider("Minimum EV%", -100, 100, -100)
        filt = odds_df[odds_df["EV%"] >= cutoff]
        st.plotly_chart(
            px.histogram(filt, x="EV%", nbins=20, color_discrete_sequence=["#00ff88"]),
            use_container_width=True
        )
        st.markdown("<div class='section'><h3>🔥 Top Picks</h3></div>", unsafe_allow_html=True)
        for _, r in filt.sort_values("EV%", ascending=False).head(5).iterrows():
            st.markdown(
                f"<div style='background:#111; padding:8px; margin:4px 0; "
                f"border-left:4px solid #00ff88; color:#e0e0e0;'>{r['Matchup']} — {r['Odds']} ({r['EV%']}%)</div>",
                unsafe_allow_html=True
            )

# -----------------------
# --- Post Bets View ----
# -----------------------
else:
    st.title("Post Bets")
    if not st.session_state.logged_in:
        user = st.text_input("Username")
        pwd  = st.text_input("Password", type="password")
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
