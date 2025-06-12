# NBA Betting Insights Dashboard – Full Streamlit App

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your real Odds API key

# === PAGE CONFIG ===
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# === STYLES ===
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
.ticker-container {
    width: 100%;
    overflow: hidden;
    background: #e6f0ff;
    padding: 5px 0;
    border-bottom: 1px solid #ccc;
}
.ticker {
    display: flex;
    animation: scroll 40s linear infinite;
}
.ticker img {
    height: 30px;
    margin: 0 20px;
}
@keyframes scroll {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
.box-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 30px;
    justify-content: center;
}
.box {
    background: linear-gradient(145deg, #002244, #FFD700);
    border-radius: 20px;
    padding: 30px;
    width: 45%;
    min-width: 300px;
    color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.box h4 {
    margin-top: 0;
}
</style>
""", unsafe_allow_html=True)

# === NBA LOGO BANNER ===
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
<div class="ticker-container">
    <div class="ticker">{''.join([f'<img src="{logo}" />' for logo in nba_logos])}</div>
</div>
""", unsafe_allow_html=True)

# === TITLE ===
st.markdown("<h1 style='text-align:center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

# === FUNCTIONS ===
@st.cache_data
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

# === DATA ===
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()
history_path = "daily_history.csv"
history_df = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()

# === BET CALCULATIONS ===
bet_rows = []
for game in odds_data:
    home = game.get("home_team")
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [t for t in teams if t != home][0]
    matchup = f"{away} @ {home}"

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                label = outcome["name"]
                odds = outcome["price"]
                prob = estimate_model_probability(odds)
                ev, prob_pct, implied = calc_ev(prob, odds)
                bet_rows.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Team": label,
                    "Odds": odds,
                    "Model Prob": prob_pct,
                    "EV%": ev,
                    "Implied": implied,
                    "Market": market["key"]
                })

bets_df = pd.DataFrame(bet_rows)
if not bets_df.empty:
    history_df = pd.concat([history_df, bets_df], ignore_index=True)
    history_df.to_csv(history_path, index=False)

# === GRID DISPLAY ===
if not bets_df.empty:
    st.markdown("<div class='box-grid'>", unsafe_allow_html=True)

    # Box 1: EV% Distribution
    with st.container():
        st.markdown("<div class='box'><h4>📊 Distribution of EV%</h4>", unsafe_allow_html=True)
        fig1, ax1 = plt.subplots()
        bets_df["EV%"].hist(ax=ax1, bins=20, color="#FFD700")
        ax1.set_xlabel("EV%")
        ax1.set_ylabel("Number of Bets")
        st.pyplot(fig1)
        st.markdown("</div>", unsafe_allow_html=True)

    # Box 2: Trend Over Time
    with st.container():
        st.markdown("<div class='box'><h4>📈 EV Trend Over Time</h4>", unsafe_allow_html=True)
        if not history_df.empty:
            trend = history_df.groupby("Date")["EV%"].mean().reset_index()
            fig2, ax2 = plt.subplots()
            ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#FFDD00")
            ax2.set_ylabel("EV%")
            ax2.set_xlabel("Date")
            ax2.tick_params(axis="x", rotation=45)
            st.pyplot(fig2)
        else:
            st.write("No trend data.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Box 3: Download
    with st.container():
        st.markdown("<div class='box'><h4>📥 Download Bets</h4>", unsafe_allow_html=True)
        csv = bets_df.to_csv(index=False)
        st.download_button("Download CSV", csv, file_name=f"nba_bets_{today}.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)

    # Box 4: Top Bet Table
    with st.container():
        st.markdown("<div class='box'><h4>✅ Model Picks Table</h4>", unsafe_allow_html=True)
        st.dataframe(bets_df[["Matchup", "Team", "Odds", "Model Prob", "EV%", "Implied", "Market"]], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No betting data available.")
