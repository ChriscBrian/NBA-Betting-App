import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import altair as alt
from datetime import datetime
import os

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual key
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# --- STYLES ---
st.markdown("""
<style>
body {
    background-color: #000000;
    color: #39FF14;
}
[data-testid="stAppViewContainer"] {
    background-color: #000000;
}
h1, h2, h3, h4, h5, h6, p, div {
    color: #39FF14;
}
.section {
    background: #111;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 4px 12px rgba(0,255,0,0.2);
}
.section h3 {
    color: #39FF14;
}
.card {
    background: linear-gradient(135deg, #013220, #0B6623);
    border: 2px solid #39FF14;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
}
#trophy {
    position: absolute;
    top: 20px;
    right: 40px;
    z-index: 999;
}
</style>
""", unsafe_allow_html=True)

# --- TROPHY IMAGE ---
st.markdown(f"""
<div id="trophy">
    <img src="https://nbsater.streamlit.app/files/trophy.jpg" width="100">
</div>
""", unsafe_allow_html=True)

# --- NBA BANNER WITH 30 TEAM LOGOS ---
nba_logos = [
    "atlanta-hawks", "boston-celtics", "brooklyn-nets", "charlotte-hornets",
    "chicago-bulls", "cleveland-cavaliers", "dallas-mavericks", "denver-nuggets",
    "detroit-pistons", "golden-state-warriors", "houston-rockets", "indiana-pacers",
    "la-clippers", "los-angeles-lakers", "memphis-grizzlies", "miami-heat",
    "milwaukee-bucks", "minnesota-timberwolves", "new-orleans-pelicans", "new-york-knicks",
    "oklahoma-city-thunder", "orlando-magic", "philadelphia-76ers", "phoenix-suns",
    "portland-trail-blazers", "sacramento-kings", "san-antonio-spurs", "toronto-raptors",
    "utah-jazz", "washington-wizards"
]
st.markdown("""
<div style="overflow:hidden; white-space:nowrap; background-color:black; padding:10px 0;">
    <marquee behavior="scroll" direction="left" scrollamount="8">
""", unsafe_allow_html=True)

for team in nba_logos:
    st.markdown(
        f'<img src="https://loodibee.com/wp-content/uploads/nba-{team}-logo.png" height="40" style="margin-right:15px;">',
        unsafe_allow_html=True
    )

st.markdown("</marquee></div>", unsafe_allow_html=True)

st.markdown("<h1>NBA Betting Insights</h1>", unsafe_allow_html=True)

# --- ODDS FETCHING ---
@st.cache_data(show_spinner=False)
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "spreads,totals,h2h",
        "oddsFormat": "american"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch odds: {e}")
        return []

def estimate_model_probability(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except:
        return 0.5

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()

# === FILTERS ===
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 🎯 Filters")
ev_threshold = st.slider("Minimum Expected Value (EV%)", -100, 100, 0)
team_filter = st.selectbox("Filter by Team (Optional)", options=["All Teams"] + sorted({t for g in odds_data for t in g.get("teams", [])}))
market_filter = st.radio("Filter by Market", options=["All", "h2h", "spreads", "totals"], horizontal=True)
st.markdown("</div>", unsafe_allow_html=True)

# === DATA PROCESSING ===
rows = []
for game in odds_data:
    home = game.get("home_team")
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [t for t in teams if t != home][0]
    if team_filter != "All Teams" and team_filter not in (home, away):
        continue
    matchup = f"{away} @ {home}"
    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market_filter != "All" and market["key"] != market_filter:
                continue
            for outcome in market.get("outcomes", []):
                label = outcome.get("name")
                odds_val = outcome.get("price")
                model_prob = estimate_model_probability(odds_val)
                ev, model_pct, implied_pct = calc_ev(model_prob, odds_val)
                if ev >= ev_threshold:
                    rows.append({
                        "Date": today,
                        "Matchup": matchup,
                        "Market": market["key"],
                        "Bet": label,
                        "Odds": odds_val,
                        "Model Win%": model_pct,
                        "Implied%": implied_pct,
                        "EV%": ev,
                        "Bookmaker": bookmaker["title"]
                    })

bets_df = pd.DataFrame(rows)

# === FULL TABLE ===
if not bets_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("### 📋 All Bets")
    st.dataframe(bets_df, use_container_width=True)
    st.download_button("📥 Download Today's Bets", bets_df.to_csv(index=False), f"bets_{today}.csv")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No bets matched the filters or EV threshold.")
