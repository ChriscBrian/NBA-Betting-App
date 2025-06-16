# nba_betting_insights/app.py

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os

# === CONFIG ===
st.set_page_config(page_title="NBA Betting Insights", layout="wide")
API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual Odds API key

# === STYLES ===
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
.section {
    background: #001f3f;
    border-radius: 15px;
    padding: 25px;
    margin: 25px 0;
    color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.section h3 {
    color: #FFDF00;
}
.banner {
    width: 100%;
    overflow: hidden;
    white-space: nowrap;
    margin-bottom: 20px;
}
.logo-strip {
    display: inline-block;
    animation: scroll-left 20s linear infinite;
}
.logo-strip img {
    height: 40px;
    margin: 0 15px;
}
@keyframes scroll-left {
    0% { transform: translateX(100%) }
    100% { transform: translateX(-100%) }
}
</style>
""", unsafe_allow_html=True)

# === NBA TEAM LOGOS FOR BANNER ===
NBA_LOGOS = [
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
    "https://loodibee.com/wp-content/uploads/nba-los-angeles-lakers-logo.png",
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

# === BANNER ===
banner_html = '<div class="banner"><div class="logo-strip">'
for logo_url in NBA_LOGOS:
    banner_html += f'<img src="{logo_url}" alt="Team Logo">'
banner_html += '</div></div>'
st.markdown(banner_html, unsafe_allow_html=True)

st.title("🏀 NBA Betting Insights")

# === HELPERS ===
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

# === MAIN LOGIC ===
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()
ev_threshold = st.slider("Filter by minimum EV%", -100, 100, 0)

rows = []
for game in odds_data:
    home = game.get("home_team")
    away = next((t for t in game.get("teams", []) if t != home), None)
    if not away: continue
    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                label = outcome.get("name")
                odds = outcome.get("price")
                prob_model = estimate_model_probability(odds)
                ev, prob_pct, implied_pct = calc_ev(prob_model, odds)
                if ev >= ev_threshold:
                    rows.append({
                        "Date": today,
                        "Matchup": f"{away} @ {home}",
                        "Bet": label,
                        "Odds": odds,
                        "Model Win%": prob_pct,
                        "EV%": ev,
                        "Implied%": implied_pct,
                        "Market": market["key"]
                    })

new_data = pd.DataFrame(rows)
if not new_data.empty:
    st.markdown('<div class="section"><h3>📊 Bet Table</h3>', unsafe_allow_html=True)
    st.dataframe(new_data, use_container_width=True)
    st.download_button("Download CSV", new_data.to_csv(index=False), file_name=f"bets_{today}.csv")
    st.markdown('</div>', unsafe_allow_html=True)

    # CHARTS SECTION
    st.markdown('<div class="section"><h3>📈 EV Charts</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if "EV%" in new_data.columns:
            fig, ax = plt.subplots()
            new_data["EV%"].hist(bins=20, ax=ax, color="#1E88E5")
            ax.set_title("EV% Distribution")
            st.pyplot(fig)
    with col2:
        if "Date" in new_data.columns and "EV%" in new_data.columns:
            trend = new_data.groupby("Date")["EV%"].mean().reset_index()
            if not trend.empty:
                fig2, ax2 = plt.subplots()
                ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#EF6C00")
                ax2.set_title("Average EV% by Day")
                ax2.tick_params(axis="x", rotation=45)
                st.pyplot(fig2)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("No betting data available.")
