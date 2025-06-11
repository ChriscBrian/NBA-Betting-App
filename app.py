# NBA Betting Insights MVP - Streamlit App with Team Banner

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual API key

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

st.set_page_config(page_title="NBA Betting Insights", layout="wide")
# --- NBA Team Logo Banner with Light Blue Background ---
st.markdown("""
    <style>
    .ticker {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 1000;
        background-color: rgba(173, 216, 230, 0.6); /* Light blue with transparency */
        overflow: hidden;
        white-space: nowrap;
        padding: 5px 0;
    }
    .ticker span {
        display: inline-block;
        padding-left: 100%;
        animation: scroll-left 60s linear infinite;
    }
    .ticker img {
        height: 30px;
        margin: 0 12px;
        vertical-align: middle;
    }
    @keyframes scroll-left {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    </style>
""", unsafe_allow_html=True)

logos = [
    "atlanta-hawks", "boston-celtics", "brooklyn-nets", "charlotte-hornets", "chicago-bulls",
    "cleveland-cavaliers", "dallas-mavericks", "denver-nuggets", "detroit-pistons", "golden-state-warriors",
    "houston-rockets", "indiana-pacers", "la-clippers", "la-lakers", "memphis-grizzlies", "miami-heat",
    "milwaukee-bucks", "minnesota-timberwolves", "new-orleans-pelicans", "new-york-knicks",
    "oklahoma-city-thunder", "orlando-magic", "philadelphia-76ers", "phoenix-suns", "portland-trail-blazers",
    "sacramento-kings", "san-antonio-spurs", "toronto-raptors", "utah-jazz", "washington-wizards"
]
logo_imgs = ''.join([f'<img src="https://loodibee.com/wp-content/uploads/nba-{team}-logo.png"/>' for team in logos])
st.markdown(f"<div class='ticker'><span>{logo_imgs}</span></div>", unsafe_allow_html=True)
st.image("https://media.tenor.com/VbV35bUNRpoAAAAC/basketball-bounce.gif", width=100)

# --- Transparent Floating NBA Logo Banner ---
st.markdown("""
    <style>
    .ticker {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 1000;
        background-color: transparent;
        overflow: hidden;
        white-space: nowrap;
        padding: 5px 0;
    }
    .ticker span {
        display: inline-block;
        padding-left: 100%;
        animation: scroll-left 60s linear infinite;
    }
    .ticker img {
        height: 30px;
        margin: 0 12px;
        vertical-align: middle;
    }
    @keyframes scroll-left {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    </style>
""", unsafe_allow_html=True)

logos = [
    "atlanta-hawks", "boston-celtics", "brooklyn-nets", "charlotte-hornets", "chicago-bulls",
    "cleveland-cavaliers", "dallas-mavericks", "denver-nuggets", "detroit-pistons", "golden-state-warriors",
    "houston-rockets", "indiana-pacers", "la-clippers", "la-lakers", "memphis-grizzlies", "miami-heat",
    "milwaukee-bucks", "minnesota-timberwolves", "new-orleans-pelicans", "new-york-knicks",
    "oklahoma-city-thunder", "orlando-magic", "philadelphia-76ers", "phoenix-suns", "portland-trail-blazers",
    "sacramento-kings", "san-antonio-spurs", "toronto-raptors", "utah-jazz", "washington-wizards"
]
logo_imgs = ''.join([f'<img src="https://loodibee.com/wp-content/uploads/nba-{team}-logo.png"/>' for team in logos])
st.markdown(f"<div class='ticker'><span>{logo_imgs}</span></div>", unsafe_allow_html=True)

# --- App Styling ---
st.markdown("""
    <style>
    .main-title {
        font-size: 3em;
        font-weight: bold;
        color: #1E88E5;
        padding-top: 60px;
        padding-bottom: 10px;
    }
    .bet-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>NBA Betting Insights</div>", unsafe_allow_html=True)

# Odds + Setup
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()
st.subheader(f"🏀 Top Model-Picked Bets Today - {today}")

ev_threshold = st.slider("Minimum Expected Value (%)", min_value=-100, max_value=100, value=0, step=1)
all_teams = sorted(list({game['home_team'] for game in odds_data}.union({game['away_team'] for game in odds_data})))
team_filter = st.selectbox("Filter by Team (Optional)", options=["All Teams"] + all_teams)
market_filter = st.radio("Filter by Market Type", options=["All", "h2h", "spreads", "totals"], horizontal=True)

# Load bet history
history_path = "daily_history.csv"
full_history_df = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()

TEAM_LOGOS = {
    "Indiana Pacers": "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png",
    "Oklahoma City Thunder": "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png"
}

top_bets = []
history_data = []

for game in odds_data:
    home = game['home_team']
    away = game['away_team']
    if team_filter != "All Teams" and team_filter not in (home, away):
        continue
    matchup = f"{home} vs {away}"
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

# Save
new_data = pd.DataFrame(history_data)
if not new_data.empty:
    full_history_df = pd.concat([full_history_df, new_data], ignore_index=True)
    full_history_df.to_csv(history_path, index=False)

# Display Top 3
st.markdown("### 🔥 Top 3 Bets by Expected Value")
for ev, matchup, label, odds, model_pct, implied_pct, home_logo, away_logo in sorted(top_bets, reverse=True)[:3]:
    with st.container():
        st.markdown("<div class='bet-card'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if away_logo:
                st.image(away_logo, width=50)
        with col2:
            st.markdown(f"### {matchup}")
            st.write(f"**Bet:** {label} @ {odds:+}")
            st.write(f"**Model Win Prob:** {model_pct}% | **EV:** {ev}% | **Implied:** {implied_pct}%")
        with col3:
            if home_logo:
                st.image(home_logo, width=50)
        st.markdown("</div>", unsafe_allow_html=True)

# Full Bet Table
if not new_data.empty:
    st.markdown("### 📊 Full Bet Insights")
    st.dataframe(new_data, use_container_width=True)

    csv_buffer = io.StringIO()
    new_data.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download Picks as CSV",
        data=csv_buffer.getvalue(),
        file_name=f"nba_bets_{today}.csv",
        mime="text/csv"
    )

    st.markdown("### 📈 EV Value Distribution")
    fig, ax = plt.subplots()
    new_data["EV%"].hist(bins=20, ax=ax, color="#1E88E5")
    ax.set_title("Distribution of Expected Value (EV%)")
    ax.set_xlabel("EV%")
    ax.set_ylabel("Number of Bets")
    st.pyplot(fig)

if not full_history_df.empty:
    trend = full_history_df.groupby("Date")["EV%"].mean().reset_index()
    st.markdown("### 📆 EV Trend Over Time")
    fig2, ax2 = plt.subplots()
    ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#EF6C00")
    ax2.set_title("Average Expected Value by Day")
    ax2.set_ylabel("Average EV%")
    ax2.set_xlabel("Date")
    ax2.tick_params(axis="x", rotation=45)
    st.pyplot(fig2)

    st.markdown("### ✅ Model Performance")
    resolved = full_history_df[full_history_df["Result"].isin(["Win", "Loss"])]
    if not resolved.empty:
        win_rate = (resolved["Result"] == "Win").mean()
        st.metric("Model Hit Rate", f"{win_rate*100:.1f}% ({(resolved['Result']=='Win').sum()}/{len(resolved)})")
