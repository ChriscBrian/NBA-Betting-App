# NBA Dashboard Style Layout
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

API_KEY = "3d4eabb1db321b1add71a25189a77697"

st.set_page_config(page_title="NBA Betting Dashboard", layout="wide")

# === STYLING ===
st.markdown("""
<style>
body {
    background-color: #f0f4f8;
}
.box {
    background: linear-gradient(135deg, #001f3f 90%, #FFD700 10%);
    border-radius: 15px;
    padding: 25px;
    color: white;
    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    margin: 15px;
}
h2, h3 {
    color: #FFD700;
}
.ticker {
    overflow: hidden;
    white-space: nowrap;
    background: #e0eafc;
    padding: 8px;
    margin-bottom: 20px;
    border-radius: 10px;
}
.ticker img {
    height: 32px;
    margin: 0 12px;
    vertical-align: middle;
    animation: scroll 40s linear infinite;
}
@keyframes scroll {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-200%); }
}
</style>
""", unsafe_allow_html=True)

# === NBA LOGO TICKER ===
logos = [
    "atlanta-hawks", "boston-celtics", "brooklyn-nets", "charlotte-hornets", "chicago-bulls",
    "cleveland-cavaliers", "dallas-mavericks", "denver-nuggets", "detroit-pistons", "golden-state-warriors",
    "houston-rockets", "indiana-pacers", "la-clippers", "la-lakers", "memphis-grizzlies", "miami-heat",
    "milwaukee-bucks", "minnesota-timberwolves", "new-orleans-pelicans", "new-york-knicks",
    "oklahoma-city-thunder", "orlando-magic", "philadelphia-76ers", "phoenix-suns",
    "portland-trail-blazers", "sacramento-kings", "san-antonio-spurs", "toronto-raptors", "utah-jazz", "washington-wizards"
]
img_html = "".join([f'<img src="https://loodibee.com/wp-content/uploads/nba-{team}-logo.png">' for team in logos])
st.markdown(f"<div class='ticker'>{img_html}</div>", unsafe_allow_html=True)

# === HEADER ===
st.markdown("<h1 style='text-align: center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)
today = datetime.today().strftime("%Y-%m-%d")

# === FETCH ODDS ===
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
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()
    except:
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

# === DATA LOGIC ===
data = fetch_odds()
top_bets = []
rows = []

for game in data:
    home = game.get('home_team')
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [t for t in teams if t != home][0]
    matchup = f"{away} @ {home}"
    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                team = outcome["name"]
                odds = outcome.get("price")
                prob = estimate_model_probability(odds)
                ev, prob_pct, implied = calc_ev(prob, odds)
                rows.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Bet": team,
                    "Odds": odds,
                    "Model Win%": prob_pct,
                    "EV%": ev,
                    "Implied%": implied,
                    "Market": market["key"]
                })

df = pd.DataFrame(rows)
history_path = "daily_history.csv"
full_history = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()
if not df.empty:
    full_history = pd.concat([full_history, df], ignore_index=True)
    full_history.to_csv(history_path, index=False)

# === DASHBOARD GRID ===
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("📊 Distribution of EV%")
    fig1, ax1 = plt.subplots()
    df["EV%"].hist(ax=ax1, bins=20, color="#FFD700")
    ax1.set_title("EV% Histogram")
    ax1.set_xlabel("Expected Value %")
    ax1.set_ylabel("Number of Bets")
    st.pyplot(fig1)
    st.markdown("💡 Higher EV suggests better model value opportunities.")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("📈 EV Trend")
    if not full_history.empty:
        trend = full_history.groupby("Date")["EV%"].mean().reset_index()
        fig2, ax2 = plt.subplots()
        ax2.plot(trend["Date"], trend["EV%"], marker='o', color="#FFD700")
        ax2.set_title("Average EV% Over Time")
        ax2.set_ylabel("EV%")
        ax2.set_xlabel("Date")
        ax2.tick_params(axis="x", rotation=45)
        st.pyplot(fig2)
        st.markdown("📅 Track model performance over time.")
    st.markdown("</div>", unsafe_allow_html=True)

with col1:
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("🏀 Top Bets Today")
    for _, row in df.sort_values("EV%", ascending=False).head(3).iterrows():
        st.markdown(f"**{row['Matchup']} - {row['Bet']} @ {row['Odds']}**")
        st.write(f"EV: {row['EV%']}% | Model: {row['Model Win%']}% | Implied: {row['Implied%']}%")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("📄 Full Bet Table")
    st.dataframe(df.head(10), use_container_width=True)
    st.download_button("Download CSV", df.to_csv(index=False), f"bets_{today}.csv")
    st.markdown("</div>", unsafe_allow_html=True)

