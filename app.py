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

dark_mode = True  # force dark theme

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
  /* Sidebar title (markdown) */
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
    position: absolute !important;
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
    # ... add other logos ...
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
    # Fetch live NBA scores, disable SSL verification if needed
    date = datetime.utcnow().strftime("%Y%m%d")
    url = f"https://data.nba.net/prod/v1/{date}/scoreboard.json"
    try:
        # disable SSL verification to avoid SSLError in some environments
        res = requests.get(url, verify=False)
        res.raise_for_status()
        return res.json().get("games", [])
    except Exception:
        return []("games", [])
    except:
        return []

live_games = fetch_live_scores()

# -----------------------
# --- Odds Fetching -----
# -----------------------
API_KEY = os.getenv("ODDS_API_KEY", "3d4eabb1db321b1add71a25189a77697")
@st.cache_data(show_spinner=False)
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"apiKey": API_KEY, "regions": "us", "markets": "spreads,totals,h2h", "oddsFormat": "american"}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

try:
    raw_odds = fetch_odds()
except Exception:
    st.warning("⚠️ Using sample odds data")
    raw_odds = [{"home_team":"Lakers","away_team":"Warriors","bookmakers":[{"markets":[{"key":"spreads","outcomes":[{"name":"Lakers","price":-110},{"name":"Warriors","price":100}]}]}]}]

# Build odds DataFrame
def estimate_prob(o): return round(1/(1+10**(-o/400)),4)
def calc_ev(p,o): imp=(100/(100+o)) if o>0 else (abs(o)/(100+abs(o))); ev=p*(o if o>0 else 100)-(1-p)*100; return round(ev,2)

rows=[]
today = datetime.today().strftime("%Y-%m-%d")
for g in raw_odds:
    home, away = g.get("home_team"), g.get("away_team")
    if not home or not away: continue
    matchup = f"{away} @ {home}"
    for b in g.get("bookmakers",[]):
        for mk in b.get("markets",[]):
            for o in mk.get("outcomes",[]):
                price = o.get("price")
                if price is None: continue
                ev = calc_ev(estimate_prob(price), price)
                rows.append({"Date": today, "Matchup": matchup, "Team": o.get("name"), "Market": mk.get("key"), "Odds": price, "EV%": ev})
df = pd.DataFrame(rows)

# Session state
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "user_bets" not in st.session_state: st.session_state.user_bets=[]

# -----------------------
# --- Dashboard View ----
# -----------------------
if page == "Dashboard":
    st.title("Dashboard")

    # Live Scores Section
    st.markdown("<div class='section'><h3>🏀 Live Game Scores</h3></div>", unsafe_allow_html=True)
    if live_games:
        for game in live_games:
            v = game["vTeam"]["triCode"]
            h = game["hTeam"]["triCode"]
            vs = game["vTeam"].get("score", "")
            hs = game["hTeam"].get("score", "")
            status = game.get("statusNum")
            if status == 1:
                time = game.get("startTimeUTC", "")
                st.markdown(f"**{v}** vs **{h}** at {time}")
            else:
                period = game.get("period", {}).get("current", "")
                clock = game.get("clock", "")
                st.markdown(f"**{v}** {vs} - {hs} **{h}**   P{period} {clock}")
    else:
        st.markdown("No live games at the moment.")

    st.markdown("<div class='section'><h3>📊 Odds & EV Distribution</h3></div>", unsafe_allow_html=True)
    if df.empty:
        st.info("No betting data available.")
    else:
        ev_cut = st.slider("Minimum EV%", -100, 100, -100)
        df_f = df[df["EV%"] >= ev_cut]
        st.plotly_chart(
            px.histogram(df_f, x="EV%", nbins=20, color_discrete_sequence=["#00ff88"]),
            use_container_width=True
        )
        st.markdown("<div class='section'><h3>🔥 Top Picks</h3></div>", unsafe_allow_html=True)
        for _, r in df_f.sort_values("EV%", ascending=False).head(5).iterrows():
            st.markdown(
                f"<div style='background:#111; padding:8px; margin:4px 0; border-left:4px solid #00ff88; color:#e0e0e0;'>{r['Matchup']} — {r['Odds']} ({r['EV%']}%)</div>",
                unsafe_allow_html=True
            )

# -----------------------
# --- Post Bets View ----
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
