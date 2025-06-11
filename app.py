# NBA Betting Insights - Full Streamlit App with Floating Ticker and EV Filtering

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

# ========== CONFIG ==========
API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your Odds API key

st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# ========== STYLES ==========
st.markdown("""
<style>
body { margin: 0; }
.main-title {
    font-size: 3em;
    font-weight: bold;
    color: #1E88E5;
    padding-top: 60px;
    padding-bottom: 20px;
}
.bet-card {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.ticker {
    position: fixed;
    top: 0;
    width: 100%;
    background-color: transparent;
    padding: 10px 0;
    overflow: hidden;
    white-space: nowrap;
    z-index: 9999;
}
.ticker span {
    display: inline-block;
    padding: 0 1.5rem;
    animation: scroll-left 40s linear infinite;
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

# ========== NBA LOGOS ==========
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
ticker_html = ''.join([f'<img src="{logo}" />' for logo in nba_logos])
st.markdown(f"<div class='ticker'><span>{ticker_html}</span></div>", unsafe_allow_html=True)

# ========== HEADER ==========
st.markdown("<div class='main-title'>NBA Betting Insights</div>", unsafe_allow_html=True)

# ========== FETCH ODDS ==========
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
    except Exception as e:
        st.error(f"Failed to fetch odds: {e}")
        return []

# ========== MODEL CALCS ==========
def estimate_model_probability(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except Exception:
        return 0.5

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

# ========== MAIN DISPLAY ==========
odds_data = fetch_odds()
today = datetime.today().strftime("%Y-%m-%d")
st.markdown(f"## 🏀 Top Model-Picked Bets Today")

ev_threshold = st.slider("Minimum Expected Value (%)", -100, 100, 0)

top_bets = []

for game in odds_data:
    home = game.get("home_team")
    teams = game.get("teams")
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [team for team in teams if team != home][0]
    matchup = f"{away} @ {home}"

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                team = outcome["name"]
                odds = outcome.get("price", 0)
                prob = estimate_model_probability(odds)
                ev, prob_pct, implied = calc_ev(prob, odds)
                if ev >= ev_threshold:
                    top_bets.append({
                        "Date": today,
                        "Matchup": matchup,
                        "Team": team,
                        "Market": market["key"],
                        "Odds": odds,
                        "Model Prob": prob_pct,
                        "EV%": ev,
                        "Implied": implied
                    })

df = pd.DataFrame(top_bets)

if not df.empty:
    def color_ev(val):
        color = "green" if val > 0 else "red" if val < 0 else "black"
        return f"color: {color}"

    st.dataframe(
        df.style.applymap(color_ev, subset=["EV%"]),
        use_container_width=True
    )

    st.markdown("### 📈 EV Distribution")
    fig, ax = plt.subplots()
    df["EV%"].hist(bins=15, ax=ax, color="#1976D2")
    ax.set_title("EV% Distribution")
    st.pyplot(fig)
else:
    st.warning("No valid betting data available to display.")
