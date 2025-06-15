# 1. DATA INGESTION
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual API key

st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# === STYLES ===
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
.section-box {
    background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
    color: white;
    border-radius: 20px;
    padding: 25px;
    margin: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.section-title {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 15px;
    color: #FFD700;
}
.grid-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
}
.grid-item {
    flex: 0 0 48%;
}
.logo-banner {
    overflow: hidden;
    white-space: nowrap;
    background: #e8f0ff;
    padding: 10px 0;
    margin-bottom: 20px;
}
.logo-banner img {
    height: 40px;
    margin: 0 15px;
    animation: floatScroll 25s linear infinite;
}
@keyframes floatScroll {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>
""", unsafe_allow_html=True)

# === TOP BANNER ===
TEAM_LOGO_URLS = [
    "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-los-angeles-lakers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-golden-state-warriors-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-miami-heat-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png"
]
st.markdown('<div class="logo-banner">' + ''.join(f'<img src="{url}">' for url in TEAM_LOGO_URLS) + '</div>', unsafe_allow_html=True)

# === TITLE ===
st.image("https://loodibee.com/wp-content/uploads/nba-logo.png", width=90)
st.markdown("<h1 style='color:#1E88E5;'>NBA Betting Insights</h1>", unsafe_allow_html=True)

# === API DATA ===
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

ev_threshold = st.slider("Minimum Expected Value (%)", -100, 100, 0)
all_teams = sorted({team for game in odds_data for team in [game.get("home_team"), *game.get("teams", [])] if team})
team_filter = st.selectbox("Filter by Team (Optional)", options=["All Teams"] + all_teams)
market_filter = st.radio("Filter by Market Type", options=["All", "h2h", "spreads", "totals"], horizontal=True)

TEAM_LOGOS = {
    "Indiana Pacers": "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png",
    "Oklahoma City Thunder": "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png"
}

top_bets = []
history_data = []
for game in odds_data:
    home = game.get('home_team')
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [team for team in teams if team != home][0]
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

new_data = pd.DataFrame(history_data)
history_path = "daily_history.csv"
full_history_df = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()
if not new_data.empty:
    full_history_df = pd.concat([full_history_df, new_data], ignore_index=True)
    full_history_df.to_csv(history_path, index=False)

# === GRID LAYOUT DISPLAY ===
st.markdown('<div class="grid-container">', unsafe_allow_html=True)

# TOP 3 BETS
st.markdown('<div class="grid-item section-box">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🔥 Top 3 Bets</div>', unsafe_allow_html=True)
for ev, matchup, label, odds, model_pct, implied_pct, home_logo, away_logo in sorted(top_bets, reverse=True)[:3]:
    st.write(f"**{matchup}**")
    st.write(f"- **Bet**: {label} @ {odds:+}")
    st.write(f"- **Model**: {model_pct}% | **EV**: {ev}% | **Implied**: {implied_pct}%")
st.markdown('</div>', unsafe_allow_html=True)

# BET TABLE
st.markdown('<div class="grid-item section-box">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📊 Bet Table</div>', unsafe_allow_html=True)
st.dataframe(new_data, use_container_width=True)
csv_buffer = io.StringIO()
new_data.to_csv(csv_buffer, index=False)
st.download_button("📥 Download CSV", csv_buffer.getvalue(), f"nba_bets_{today}.csv")
st.markdown('</div>', unsafe_allow_html=True)

# EV DISTRIBUTION
st.markdown('<div class="grid-item section-box">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📈 EV Distribution</div>', unsafe_allow_html=True)
fig1, ax1 = plt.subplots()
new_data["EV%"].hist(bins=20, ax=ax1, color="#1E88E5")
ax1.set_title("EV% Distribution")
ax1.set_xlabel("EV%")
ax1.set_ylabel("Frequency")
st.pyplot(fig1)
st.markdown("Higher EV% = better potential value.")
st.markdown('</div>', unsafe_allow_html=True)

# EV TREND
st.markdown('<div class="grid-item section-box">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📆 EV Trend Over Time</div>', unsafe_allow_html=True)
if not full_history_df.empty:
    trend = full_history_df.groupby("Date")["EV%"].mean().reset_index()
    fig2, ax2 = plt.subplots()
    ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#FFD700")
    ax2.set_title("Daily Avg EV%")
    ax2.set_ylabel("EV%")
    ax2.set_xlabel("Date")
    ax2.tick_params(axis="x", rotation=45)
    st.pyplot(fig2)
    st.markdown("A rising line indicates stronger daily model performance.")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# === MODEL PERFORMANCE ===
if not full_history_df.empty:
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✅ Model Performance</div>', unsafe_allow_html=True)
    resolved = full_history_df[full_history_df["Result"].isin(["Win", "Loss"])]
    if not resolved.empty:
        win_rate = (resolved["Result"] == "Win").mean()
        st.metric("Hit Rate", f"{win_rate*100:.1f}%")
    else:
        st.info("No resolved results yet.")
    st.markdown('</div>', unsafe_allow_html=True)

