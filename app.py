# 1. DATA INGESTION
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

# Replace with your actual API key
API_KEY = "3d4eabb1db321b1add71a25189a77697"

st.set_page_config(page_title="NBA Betting Insights Dashboard", layout="wide")

# === STYLES + BANNER ===
st.markdown("""
<style>
body {
    background-color: #f5f7fb;
}
.banner {
    background-color: #e8f0ff;
    padding: 6px 0;
    overflow: hidden;
    white-space: nowrap;
}
.banner span {
    display: inline-block;
    padding-left: 100%;
    animation: scroll-left 12s linear infinite;
}
.banner img {
    height: 32px;
    margin: 0 10px;
    vertical-align: middle;
}
@keyframes scroll-left {
    0% { transform: translateX(0); }
    100% { transform: translateX(-100%); }
}
.section {
    background: #fff;
    border-radius: 15px;
    padding: 25px;
    margin: 25px 0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.section-header {
    font-size: 20px;
    font-weight: bold;
    color: #333;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# === BANNER IMAGES ===
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
<div class='banner'>
    <span>{''.join([f'<img src="{logo}" />' for logo in nba_logos])}</span>
</div>
""", unsafe_allow_html=True)

# === HEADER ===
st.markdown("<h1 style='text-align:center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

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

# === PROCESS DATA ===
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()
ev_cutoff = st.slider("Minimum Expected Value (%)", -100, 100, 0)

rows = []
for game in odds_data:
    home = game.get("home_team")
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [team for team in teams if team != home][0]
    matchup = f"{away} @ {home}"

    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                odds = outcome.get("price")
                team = outcome.get("name")
                model_prob = estimate_model_probability(odds)
                ev, prob_pct, implied_pct = calc_ev(model_prob, odds)
                if ev >= ev_cutoff:
                    rows.append({
                        "Date": today,
                        "Matchup": matchup,
                        "Team": team,
                        "Market": market["key"],
                        "Odds": odds,
                        "Model Prob %": prob_pct,
                        "Implied %": implied_pct,
                        "EV%": ev
                    })

new_data = pd.DataFrame(rows)

# === DISPLAY TABLE ===
if not new_data.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📊 Bet Table</div>", unsafe_allow_html=True)
    st.dataframe(new_data, use_container_width=True)
    csv_data = io.StringIO()
    new_data.to_csv(csv_data, index=False)
    st.download_button("📥 Download CSV", csv_data.getvalue(), "nba_bets.csv", "text/csv")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No betting data available.")

# === CHARTS ===
if not new_data.empty and "EV%" in new_data.columns:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📈 EV Distribution</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        fig, ax1 = plt.subplots()
        new_data["EV%"].hist(bins=20, ax=ax1, color="#1E88E5")
        ax1.set_title("EV% Distribution")
        ax1.set_xlabel("EV%")
        ax1.set_ylabel("Count")
        st.pyplot(fig)
        st.markdown("🔹 **How to read**: Higher EV% implies better model-derived value.")

    with col2:
        if "Date" in new_data.columns:
            trend = new_data.groupby("Date")["EV%"].mean().reset_index()
            fig2, ax2 = plt.subplots()
            ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#EF6C00")
            ax2.set_title("Average EV% by Date")
            ax2.set_ylabel("EV%")
            ax2.set_xlabel("Date")
            ax2.tick_params(axis="x", rotation=45)
            st.pyplot(fig2)
            st.markdown("📈 **How to read**: A rising trend indicates improving model performance.")
    st.markdown("</div>", unsafe_allow_html=True)

