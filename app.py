# NBA Betting Insights App

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

# Set your API Key
API_KEY = "3d4eabb1db321b1add71a25189a77697"

st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# --- Custom Styles ---
st.markdown("""
<style>
body {
    background-color: #f0f4f8;
}
.banner {
    background: #001f3f;
    padding: 10px 0;
    overflow: hidden;
}
.banner img {
    height: 50px;
    margin-right: 30px;
    animation: move 20s linear infinite;
}
@keyframes move {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
.section-title {
    font-size: 24px;
    font-weight: 700;
    color: gold;
    padding-bottom: 10px;
}
.card {
    background-color: #001f3f;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    color: white;
}
.grid-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    grid-gap: 20px;
}
</style>
""", unsafe_allow_html=True)

# --- NBA Banner ---
NBA_TEAM_LOGOS = [
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-miami-heat-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-la-lakers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-golden-state-warriors-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png"
]
st.markdown('<div class="banner">' +
            ''.join([f'<img src="{logo}">' for logo in NBA_TEAM_LOGOS]) +
            '</div>', unsafe_allow_html=True)

st.title("🏀 NBA Betting Insights")

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

# Fetch Odds
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()

# Filters
ev_threshold = st.slider("Minimum Expected Value (%)", -100, 100, 0)
all_teams = sorted({game.get("home_team") for game in odds_data if "home_team" in game})
team_filter = st.selectbox("Filter by Team", ["All Teams"] + all_teams)
market_filter = st.radio("Market", ["All", "h2h", "spreads", "totals"], horizontal=True)

# Data
TEAM_LOGOS = {
    "Indiana Pacers": NBA_TEAM_LOGOS[5],
    "Oklahoma City Thunder": NBA_TEAM_LOGOS[4]
}

top_bets = []
history_data = []

for game in odds_data:
    home = game.get("home_team")
    away = [team for team in game.get("teams", []) if team != home][0]
    if team_filter != "All Teams" and team_filter not in (home, away):
        continue
    matchup = f"{away} @ {home}"
    home_logo = TEAM_LOGOS.get(home)
    away_logo = TEAM_LOGOS.get(away)

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market_filter != "All" and market["key"] != market_filter:
                continue
            for outcome in market.get("outcomes", []):
                odds = outcome.get("price")
                label = outcome.get("name")
                prob_model = estimate_model_probability(odds)
                ev, model_pct, implied_pct = calc_ev(prob_model, odds)
                if ev >= ev_threshold:
                    row = {
                        "Date": today, "Matchup": matchup, "Bet": label, "Odds": odds,
                        "Model Win%": model_pct, "EV%": ev, "Implied%": implied_pct,
                        "Result": "Pending", "Market": market["key"]
                    }
                    history_data.append(row)
                    top_bets.append((ev, matchup, label, odds, model_pct, implied_pct, home_logo, away_logo))

# Save history
history_path = "daily_history.csv"
new_data = pd.DataFrame(history_data)
full_history_df = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()
if not new_data.empty:
    full_history_df = pd.concat([full_history_df, new_data], ignore_index=True)
    full_history_df.to_csv(history_path, index=False)

# --- Grid Layout Display ---
if not new_data.empty:
    st.markdown('<div class="grid-container">', unsafe_allow_html=True)

    # Box 1: Top Bets
    with st.container():
        st.markdown('<div class="card"><div class="section-title">🔥 Top Bets</div>', unsafe_allow_html=True)
        for ev, matchup, label, odds, model_pct, implied_pct, home_logo, away_logo in sorted(top_bets, reverse=True)[:2]:
            st.write(f"**{matchup}** — {label} @ {odds:+}")
            st.write(f"EV: {ev}% | Model Win: {model_pct}% | Implied: {implied_pct}%")
        st.markdown("</div>", unsafe_allow_html=True)

    # Box 2: EV Histogram
    with st.container():
        st.markdown('<div class="card"><div class="section-title">📊 EV Distribution</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots()
        new_data["EV%"].hist(bins=20, ax=ax, color="#FFDF00")
        ax.set_title("EV% Distribution")
        ax.set_xlabel("EV%")
        ax.set_ylabel("Bets")
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    # Box 3: EV Trend
    with st.container():
        st.markdown('<div class="card"><div class="section-title">📆 EV Trend</div>', unsafe_allow_html=True)
        if not full_history_df.empty:
            trend = full_history_df.groupby("Date")["EV%"].mean().reset_index()
            fig2, ax2 = plt.subplots()
            ax2.plot(trend["Date"], trend["EV%"], marker="o", color="gold")
            ax2.set_title("Average EV% by Date")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("EV%")
            ax2.tick_params(axis="x", rotation=45)
            st.pyplot(fig2)
        st.markdown("</div>", unsafe_allow_html=True)

    # Box 4: Model Hit Rate
    with st.container():
        st.markdown('<div class="card"><div class="section-title">✅ Model Performance</div>', unsafe_allow_html=True)
        resolved = full_history_df[full_history_df["Result"].isin(["Win", "Loss"])]
        if not resolved.empty:
            win_rate = (resolved["Result"] == "Win").mean()
            st.metric("Win Rate", f"{win_rate*100:.1f}%")
        else:
            st.info("No resolved results yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No valid betting data available today.")
