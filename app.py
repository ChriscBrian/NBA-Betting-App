# NBA Betting Insights MVP - Streamlit App with Enhanced Layout and Graphics

# 1. DATA INGESTION
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Replace 'YOUR_API_KEY' with your actual Odds API key
API_KEY = "3d4eabb1db321b1add71a25189a77697"

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

# 2. MODEL LAYER - Enhanced Model Probability Estimate

def estimate_model_probability(odds):
    """Estimate win probability using a log-odds based transform."""
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except Exception:
        return 0.50

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

# 3. FRONTEND (Streamlit MVP)
st.set_page_config(page_title="NBA Betting Insights", layout="wide")
st.image("https://media.tenor.com/VbV35bUNRpoAAAAC/basketball-bounce.gif", width=100)

st.markdown("""
    <style>
    .main-title {
        font-size: 3em;
        font-weight: bold;
        color: #1E88E5;
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

# Pull real odds
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()
st.subheader(f"Top Model-Picked Bets Today - {today}")

# Filters
ev_threshold = st.slider("Minimum Expected Value (%)", min_value=-100, max_value=100, value=0, step=1)
all_teams = sorted(list({game['home_team'] for game in odds_data}.union({game['away_team'] for game in odds_data})))
team_filter = st.selectbox("Filter by Team (Optional)", options=["All Teams"] + all_teams)
market_filter = st.radio("Filter by Market Type", options=["All", "h2h", "spreads", "totals"], horizontal=True)

# Load daily history from file
history_path = "daily_history.csv"
full_history_df = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()

# Team Logos
TEAM_LOGOS = {
    "Indiana Pacers": "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png",
    "Oklahoma City Thunder": "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png"
}  # Truncated for brevity

# Track top 3 EV and full bet history
top_bets = []
history_data = []

for game in odds_data:
    home = game['home_team']
    away = game['away_team']
    if team_filter != "All Teams" and team_filter not in (home, away):
        continue
    teams = f"{home} vs {away}"
    home_logo = TEAM_LOGOS.get(home)
    away_logo = TEAM_LOGOS.get(away)

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market_filter != "All" and market["key"] != market_filter:
                continue
            if market["key"] in ["spreads", "totals", "h2h"]:
                for outcome in market.get("outcomes", []):
                    label = outcome.get("name")
                    odds = outcome.get("price")
                    model_prob = estimate_model_probability(odds)
                    ev, model_pct, implied_pct = calc_ev(model_prob, odds)
                    if ev >= ev_threshold:
                        row = {
                            "Date": today,
                            "Matchup": teams,
                            "Bet": label,
                            "Odds": odds,
                            "Model Win%": model_pct,
                            "EV%": ev,
                            "Implied%": implied_pct,
                            "Result": "Pending",
                            "Market": market["key"]
                        }
                        history_data.append(row)
                        top_bets.append((ev, teams, label, odds, model_pct, implied_pct, home_logo, away_logo))

# Append and persist full history
new_data = pd.DataFrame(history_data)
if not new_data.empty:
    full_history_df = pd.concat([full_history_df, new_data], ignore_index=True)
    full_history_df.to_csv(history_path, index=False)

# Sort by EV and show top 3
st.markdown("### 🔥 Top 3 Bets by Expected Value")
for ev, teams, label, odds, model_pct, implied_pct, home_logo, away_logo in sorted(top_bets, reverse=True)[:3]:
    with st.container():
        st.markdown("<div class='bet-card'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if away_logo:
                st.image(away_logo, width=50)
        with col2:
            st.markdown(f"### {teams}")
            st.write(f"**Bet:** {label} @ {odds:+}")
            st.write(f"**Model Win Prob:** {model_pct}% | **EV:** {ev}% | **Implied:** {implied_pct}%")
        with col3:
            if home_logo:
                st.image(home_logo, width=50)
        st.markdown("</div>", unsafe_allow_html=True)

# Full Bet History Table
if not new_data.empty:
    st.markdown("### 📊 Full Bet Insights")
    st.dataframe(new_data, use_container_width=True)
    st.download_button("Download Picks as CSV", data=new_data.to_csv(index=False), file_name=f"nba_bets_{today}.csv", mime="text/csv")

    st.markdown("### 📈 EV Value Distribution")
    fig, ax = plt.subplots()
    new_data["EV%"].hist(bins=20, ax=ax, color="#1E88E5")
    ax.set_title("Distribution of Expected Value (EV%)")
    ax.set_xlabel("EV%")
    ax.set_ylabel("Number of Bets")
    st.pyplot(fig)

# Trend of EV Average Over Time
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

# Hit Rate Calculation
if not full_history_df.empty():
    st.markdown("### ✅ Model Performance")
    resolved = full_history_df[full_history_df["Result"].isin(["Win", "Loss"])]
    if not resolved.empty:
        win_rate = (resolved["Result"] == "Win").mean()
        st.metric("Model Hit Rate", f"{win_rate*100:.1f}% ({(resolved['Result']=='Win').sum()}/{len(resolved)})")

