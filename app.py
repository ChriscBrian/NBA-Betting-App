# NBA Betting Insights MVP - Full Streamlit App with Ticker, Charts, Table, Filters, and Tooltips

# 1. DATA INGESTION
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual key

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

# MODEL FUNCTIONS
def estimate_model_probability(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except Exception:
        return 0.50

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

# STREAMLIT SETUP
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# STYLING + TICKER
st.markdown("""
<style>
.main-title {
    font-size: 3em;
    font-weight: bold;
    color: #1E88E5;
    padding-top: 80px;
    padding-bottom: 10px;
}
.ticker {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 999;
    background-color: transparent;
    padding: 5px 0;
    overflow: hidden;
    white-space: nowrap;
}
.ticker span {
    display: inline-block;
    padding: 0 1.5rem;
    animation: scroll-left 30s linear infinite;
}
.ticker img {
    height: 32px;
    margin: 0 8px;
    vertical-align: middle;
}
@keyframes scroll-left {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>
""", unsafe_allow_html=True)

nba_logos = [
    "https://loodibee.com/wp-content/uploads/nba-atlanta-hawks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-brooklyn-nets-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-charlotte-hornets-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-chicago-bulls-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-cleveland-cavaliers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-dallas-mavericks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-denver-nuggets-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-detroit-pistons-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-golden-state-warriors-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-houston-rockets-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-la-clippers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-la-lakers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-memphis-grizzlies-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-miami-heat-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-milwaukee-bucks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-minnesota-timberwolves-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-new-orleans-pelicans-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-new-york-knicks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-orlando-magic-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-philadelphia-76ers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-phoenix-suns-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-portland-trail-blazers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-sacramento-kings-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-san-antonio-spurs-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-toronto-raptors-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-utah-jazz-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]

st.markdown(f"""
<div class='ticker'><span>{''.join([f'<img src="{logo}" />' for logo in nba_logos])}</span></div>
""", unsafe_allow_html=True)

# HEADER
st.markdown("<div class='main-title'>NBA Betting Insights</div>", unsafe_allow_html=True)

# LOAD ODDS
odds_data = fetch_odds()
if not odds_data:
    st.warning("No betting data available.")
    st.stop()

# PARSE DATA
bet_list = []
for game in odds_data:
    home = game.get('home_team')
    teams = game.get('teams', [])
    if not home or not teams or home not in teams:
        continue
    away = [team for team in teams if team != home]
    if not away:
        continue
    away = away[0]

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                team = outcome["name"]
                odds = outcome.get("price", 0)
                prob = estimate_model_probability(odds)
                ev, prob_pct, implied = calc_ev(prob, odds)
                bet_list.append({
                    "Matchup": f"{away} @ {home}",
                    "Team": team,
                    "Market": market["key"],
                    "Odds": odds,
                    "Model Prob": prob_pct,
                    "EV%": ev,
                    "Implied": implied
                })

df = pd.DataFrame(bet_list)

# FILTERS + EV TOOLTIP
st.markdown("## 📊 Top Model-Picked Bets Today")
min_ev = st.slider("Minimum Expected Value (%)", -100, 100, 0)

st.markdown("""
<style>
.tooltip {
  display: inline-block;
  position: relative;
  cursor: help;
}
.tooltip .tooltiptext {
  visibility: hidden;
  width: 200px;
  background-color: #555;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px;
  position: absolute;
  z-index: 1;
  bottom: 125%;
  left: 50%;
  margin-left: -100px;
  opacity: 0;
  transition: opacity 0.3s;
}
.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}
</style>
<p>
  <span class="tooltip">EV%<span class="tooltiptext">Expected Value based on model vs implied odds</span></span>
  |
  <span class="tooltip">Model Prob<span class="tooltiptext">Probability from rating-based model</span></span>
</p>
""", unsafe_allow_html=True)

# DISPLAY
filtered_df = df[df["EV%"] >= min_ev].copy()

def color_ev(val):
    color = "green" if val > 0 else "red" if val < 0 else "black"
    return f"color: {color}"

st.dataframe(
    filtered_df.style.applymap(color_ev, subset=["EV%"]),
    use_container_width=True
)
