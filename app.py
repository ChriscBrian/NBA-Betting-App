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
  /* Hide default menu and header/footer */
  #MainMenu, header, footer {visibility: hidden !important;}
  /* Sidebar background */
  [data-testid="stSidebar"] {
    background-color: #000000 !important;
  }
  /* Sidebar title styling (via markdown) */
  /* Sidebar radio labels */
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
  /* Top banner styling */
  .banner {
    position: absolute !important;
    top: 0; left: 0;
    width: 100%; height: 50px;
    background-color: #000000;
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
  /* Push main content below banner */
  .content-wrapper {
    padding-top: 60px;
    padding-left: 16px;
    padding-right: 16px;
  }
</style>
""", unsafe_allow_html=True)

# -----------------------
# --- Sidebar -----------
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
    # ... add additional logo URLs here ...
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
logo_html = '<div class="banner">' + ''.join(f'<img src="{url}" />' for url in NBA_LOGOS) + '</div>'
st.markdown(logo_html, unsafe_allow_html=True)

# Wrap content to avoid banner
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

# -----------------------
# --- Data Fetching -----
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
    raw = fetch_odds()
    st.success(f"✅ Retrieved {len(raw)} games")
except Exception:
    st.warning("⚠️ Using sample data")
    raw = [{"home_team":"Lakers","away_team":"Warriors","bookmakers":[{"markets":[{"key":"spreads","outcomes":[{"name":"Lakers","price":-110},{"name":"Warriors","price":100}]}]}]}]

# -----------------------
# --- Data Processing ---
# -----------------------
rows = []
today = datetime.today().strftime("%Y-%m-%d")

def estimate_prob(o):
    return round(1 / (1 + 10 ** (-o / 400)), 4)

def calc_ev(p, o):
    implied = (100 / (100 + o)) if o > 0 else (abs(o) / (100 + abs(o)))
    ev = p * (o if o > 0 else 100) - (1 - p) * 100
    return round(ev, 2)

for game in raw:
    home = game.get("home_team")
    away = game.get("away_team")
    if not home or not away:
        continue
    matchup = f"{away} @ {home}"
    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                price = outcome.get("price")
                if price is None:
                    continue
                ev = calc_ev(estimate_prob(price), price)
                rows.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Team": outcome.get("name"),
                    "Market": market.get("key"),
                    "Odds": price,
                    "EV%": ev
                })

df = pd.DataFrame(rows)

# -----------------------
# --- Session State ----
# -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_bets" not in st.session_state:
    st.session_state.user_bets = []

# -----------------------
# --- Dashboard ---------
# -----------------------
if page == "Dashboard":
    st.title("Dashboard")
    if df.empty:
        st.info("No data available.")
    else:
        st.markdown("---")
        ev_cut = st.slider("Minimum EV%", -100, 100, -100)
        df_f = df[df["EV%"] >= ev_cut]
        st.plotly_chart(
            px.histogram(df_f, x="EV%", nbins=20, color_discrete_sequence=["#00ff88"]),
            use_container_width=True
        )
        st.markdown("---")
        st.subheader("Top Picks")
        for _, r in df_f.sort_values("EV%", ascending=False).head(5).iterrows():
            st.markdown(
                f"<div style='background:#111; padding:8px; margin:4px 0; border-left:4px solid #00ff88; color:#e0e0e0;'>{r['Matchup']} — {r['Odds']} ({r['EV%']}%)</div>",
                unsafe_allow_html=True
            )

# -----------------------
# --- Post Bets ---------
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

