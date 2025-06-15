import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# === API SETUP ===
API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your Odds API key

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

# === PAGE CONFIG ===
st.set_page_config(page_title="NBA Betting Insights Dashboard", layout="wide")

# === STYLES ===
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
h1 {
    font-family: 'Helvetica Neue', sans-serif;
}
.banner {
    background-color: #e0e7ff;
    padding: 10px 0;
    overflow: hidden;
    white-space: nowrap;
    margin-bottom: 15px;
}
.banner img {
    height: 35px;
    margin: 0 10px;
    animation: scroll-left 12s linear infinite;
}
@keyframes scroll-left {
    0%   { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
.section {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.section-title {
    font-size: 20px;
    font-weight: 700;
    color: #1E88E5;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# === TEAM LOGOS ===
logos = [
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

st.markdown(f"<div class='banner'>{''.join([f'<img src=\"{logo}\" />' for logo in logos])}</div>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

# === FETCH DATA ===
odds_data = fetch_odds()
today = datetime.today().strftime("%Y-%m-%d")

ev_cutoff = st.slider("Minimum Expected Value (%)", -100, 100, 0)

# === PROCESS DATA ===
bets = []
for game in odds_data:
    home = game.get("home_team")
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [team for team in teams if team != home][0]
    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                odds = outcome.get("price")
                label = outcome.get("name")
                model_prob = estimate_model_probability(odds)
                ev, model_pct, implied_pct = calc_ev(model_prob, odds)
                if ev >= ev_cutoff:
                    bets.append({
                        "Date": today,
                        "Matchup": f"{away} @ {home}",
                        "Bet": label,
                        "Odds": odds,
                        "Model Prob": model_pct,
                        "EV%": ev,
                        "Implied Prob": implied_pct,
                        "Market": market.get("key")
                    })

df = pd.DataFrame(bets)

# === DISPLAY SECTIONS ===
if not df.empty:
    with st.container():
        st.markdown("<div class='section'><div class='section-title'>📋 Bet Table</div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download CSV", df.to_csv(index=False), f"nba_bets_{today}.csv")
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='section'><div class='section-title'>📊 EV Distribution</div>", unsafe_allow_html=True)
        if "EV%" in df.columns:
            fig, ax = plt.subplots()
            df["EV%"].hist(bins=20, ax=ax, color="#1E88E5")
            ax.set_title("Distribution of Expected Value (EV%)")
            ax.set_xlabel("EV%")
            ax.set_ylabel("Count")
            st.pyplot(fig)
        else:
            st.info("EV% data not available.")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("No betting data available.")
