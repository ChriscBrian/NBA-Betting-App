# NBA Betting Insights with Floating Box Layout, Banner, Parlay Generator

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io
import random

# === CONFIG ===
API_KEY = "3d4eabb1db321b1add71a25189a77697"
st.set_page_config(page_title="NBAster - Betting Insights", layout="wide")

# === STYLES ===
st.markdown("""
<style>
body {
    background-color: #f0f4f8;
}
.banner-container {
    overflow: hidden;
    white-space: nowrap;
    padding: 10px 0;
    margin-bottom: 10px;
}
.banner-container img {
    height: 30px;
    margin: 0 15px;
    animation: scroll 40s linear infinite;
}
@keyframes scroll {
  0% { transform: translateX(100%) }
  100% { transform: translateX(-100%) }
}
.section-box {
    background: linear-gradient(135deg, #001f3f 20%, #003366 80%);
    color: white;
    border-radius: 20px;
    padding: 20px;
    margin: 10px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}
h3 {
    color: #FFDF00;
}
</style>
""", unsafe_allow_html=True)

# === TEAM BANNER ===
TEAM_LOGO_URLS = [
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-miami-heat-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-los-angeles-lakers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-golden-state-warriors-logo.png"
]
st.markdown("<div class='banner-container'>" + "".join(
    [f"<img src='{logo}'/>" for logo in TEAM_LOGO_URLS * 3]) + "</div>", unsafe_allow_html=True)

st.title("🏀 NBAster - Betting Insights & Picks")

# === FUNCTIONS ===
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
        st.error(f"Error fetching odds: {e}")
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

def generate_parlay(players):
    if len(players) < 3:
        return []
    return [
        {"Player": random.choice(players), "Type": "Points"},
        {"Player": random.choice(players), "Type": "Rebounds"},
        {"Player": random.choice(players), "Type": "Assists"},
        {"Player": random.choice(players), "Type": "Points"},
        {"Player": random.choice(players), "Type": random.choice(["Rebounds", "Assists"])}
    ]

# === DATA LOAD ===
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()
history_path = "daily_history.csv"
full_history_df = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()

# === FILTERS ===
ev_threshold = st.slider("🎯 Minimum EV%", -100, 100, 0)
teams = sorted({team for g in odds_data for team in [g.get("home_team"), *g.get("teams", [])] if team})
team_filter = st.selectbox("Team Filter", ["All Teams"] + teams)
market_filter = st.radio("Market Type", ["All", "h2h", "spreads", "totals"], horizontal=True)

# === ANALYSIS ===
top_bets, history_data = [], []
for game in odds_data:
    home, teams_list = game.get("home_team"), game.get("teams", [])
    if not teams_list or home not in teams_list or len(teams_list) != 2:
        continue
    away = [t for t in teams_list if t != home][0]
    if team_filter != "All Teams" and team_filter not in (home, away):
        continue
    matchup = f"{away} @ {home}"
    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            if market_filter != "All" and market["key"] != market_filter:
                continue
            for outcome in market.get("outcomes", []):
                label = outcome.get("name")
                odds = outcome.get("price")
                model_prob = estimate_model_probability(odds)
                ev, model_pct, implied_pct = calc_ev(model_prob, odds)
                if ev >= ev_threshold:
                    row = {
                        "Date": today, "Matchup": matchup, "Bet": label,
                        "Odds": odds, "Model Win%": model_pct,
                        "EV%": ev, "Implied%": implied_pct,
                        "Result": "Pending", "Market": market["key"]
                    }
                    top_bets.append((ev, matchup, label, odds, model_pct, implied_pct))
                    history_data.append(row)

# === SAVE HISTORY ===
new_data = pd.DataFrame(history_data)
if not new_data.empty:
    full_history_df = pd.concat([full_history_df, new_data], ignore_index=True)
    full_history_df.to_csv(history_path, index=False)

# === 4-BOX LAYOUT ===
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='section-box'><h3>🔥 Top Bets</h3>", unsafe_allow_html=True)
    for ev, matchup, label, odds, model_pct, implied_pct in sorted(top_bets, reverse=True)[:3]:
        st.write(f"**{matchup}**: {label} @ {odds:+}")
        st.write(f"Model: {model_pct}% | EV: {ev}% | Implied: {implied_pct}%")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='section-box'><h3>🎯 Balanced Parlay</h3>", unsafe_allow_html=True)
    sample_players = ["Shai Gilgeous-Alexander", "Obi Toppin", "Tyrese Haliburton", "Jalen Williams"]
    parlay = generate_parlay(sample_players)
    for leg in parlay:
        st.write(f"{leg['Player']} - {leg['Type']}")
    st.markdown("</div>", unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    st.markdown("<div class='section-box'><h3>📈 EV Distribution</h3>", unsafe_allow_html=True)
    if not new_data.empty:
        fig, ax = plt.subplots()
        new_data["EV%"].hist(bins=15, ax=ax, color="#FFDF00")
        ax.set_title("Distribution of EV%")
        st.pyplot(fig)
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("<div class='section-box'><h3>📊 EV Trend</h3>", unsafe_allow_html=True)
    if not full_history_df.empty:
        trend = full_history_df.groupby("Date")["EV%"].mean().reset_index()
        fig2, ax2 = plt.subplots()
        ax2.plot(trend["Date"], trend["EV%"], marker='o', color="#FFDF00")
        ax2.set_title("Avg EV% by Date")
        ax2.tick_params(axis="x", rotation=45)
        st.pyplot(fig2)
    st.markdown("</div>", unsafe_allow_html=True)

# === BET TABLE ===
if not new_data.empty:
    st.markdown("<div class='section-box'><h3>📋 All Bets</h3>", unsafe_allow_html=True)
    st.dataframe(new_data, use_container_width=True)
    st.download_button("📥 Download CSV", new_data.to_csv(index=False), f"nba_bets_{today}.csv")
    st.markdown("</div>", unsafe_allow_html=True)

# === PERFORMANCE ===
if not full_history_df.empty:
    st.markdown("<div class='section-box'><h3>✅ Model Hit Rate</h3>", unsafe_allow_html=True)
    resolved = full_history_df[full_history_df["Result"].isin(["Win", "Loss"])]
    if not resolved.empty:
        win_rate = (resolved["Result"] == "Win").mean()
        st.metric("Hit Rate", f"{win_rate*100:.1f}%")
    st.markdown("</div>", unsafe_allow_html=True)
