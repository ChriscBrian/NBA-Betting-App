# NBA Betting Insights MVP with Floating NBA Team Icon Banner

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual Odds API key

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
    except Exception:
        return 0.50

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

# STREAMLIT PAGE CONFIG
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# FLOATING TICKER STYLES AND NBA LOGOS
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

st.markdown("""
    <style>
    .ticker {
        position: fixed;
        top: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.0);  /* Transparent */
        z-index: 9999;
        overflow: hidden;
        white-space: nowrap;
    }
    .ticker span {
        display: inline-block;
        animation: scroll-left 30s linear infinite;
    }
    .ticker img {
        height: 40px;
        margin: 0 20px;
    }
    @keyframes scroll-left {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    </style>
    <div class='ticker'><span>
    """ + "".join([f"<img src='{logo}' />" for logo in nba_logos]) + "</span></div>", unsafe_allow_html=True)

# HEADER
st.markdown("<h1 style='padding-top:60px; color:#1E88E5;'>NBA Betting Insights</h1>", unsafe_allow_html=True)
st.subheader("🏀 Top Model-Picked Bets Today")

# FETCH DATA
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()

ev_threshold = st.slider("Minimum Expected Value (%)", -100, 100, 0)
history_path = "daily_history.csv"
full_history_df = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()

TEAM_LOGOS = {
    "Indiana Pacers": "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png",
    "Oklahoma City Thunder": "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png"
}

top_bets, history_data = [], []

for game in odds_data:
    home = game['home_team']
    away = [team for team in game['teams'] if team != home][0]
    matchup = f"{home} vs {away}"
    home_logo = TEAM_LOGOS.get(home)
    away_logo = TEAM_LOGOS.get(away)

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market["key"] in ["spreads", "totals", "h2h"]:
                for outcome in market.get("outcomes", []):
                    label = outcome.get("name")
                    odds = outcome.get("price")
                    model_prob = estimate_model_probability(odds)
                    ev, model_pct, implied_pct = calc_ev(model_prob, odds)
                    if ev >= ev_threshold:
                        row = {
                            "Date": today,
                            "Matchup": matchup,
                            "Bet": label,
                            "Odds": odds,
                            "Model Win%": model_pct,
                            "EV%": ev,
                            "Implied%": implied_pct,
                            "Result": "Pending",
                            "Market": market["key"]
                        }
                        history_data.append(row)
                        top_bets.append((ev, matchup, label, odds, model_pct, implied_pct, home_logo, away_logo))

# SAVE HISTORY
new_data = pd.DataFrame(history_data)
if not new_data.empty:
    full_history_df = pd.concat([full_history_df, new_data], ignore_index=True)
    full_history_df.to_csv(history_path, index=False)

# TOP 3 DISPLAY
if top_bets:
    st.markdown("### 🔥 Top 3 Bets")
    for ev, matchup, label, odds, model_pct, implied_pct, home_logo, away_logo in sorted(top_bets, reverse=True)[:3]:
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if away_logo: st.image(away_logo, width=50)
            with col2:
                st.markdown(f"**{matchup}**")
                st.write(f"**Bet:** {label} @ {odds:+}")
                st.write(f"Model: {model_pct}% | EV: {ev}% | Implied: {implied_pct}%")
            with col3:
                if home_logo: st.image(home_logo, width=50)

# FULL TABLE AND CHART
if not new_data.empty:
    st.markdown("### 📊 Full Bet Table")
    st.dataframe(new_data, use_container_width=True)

    st.markdown("### 📈 EV Distribution")
    fig, ax = plt.subplots()
    new_data["EV%"].hist(bins=20, ax=ax, color="#1E88E5")
    st.pyplot(fig)

    if not full_history_df.empty:
        st.markdown("### 📆 EV Trend")
        trend = full_history_df.groupby("Date")["EV%"].mean().reset_index()
        fig2, ax2 = plt.subplots()
        ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#EF6C00")
        st.pyplot(fig2)
