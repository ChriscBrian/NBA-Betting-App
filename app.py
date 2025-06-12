import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual key

st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# === STYLES ===
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
.section {
    background: linear-gradient(to right, #001f3f, #001f3f);
    border-radius: 15px;
    padding: 25px;
    margin: 15px;
    color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.section h3 {
    margin-bottom: 10px;
    color: #FFDF00;
}
.banner {
    background-color: #e0e8f0;
    padding: 10px;
    border-radius: 10px;
    overflow: hidden;
    white-space: nowrap;
}
.banner img {
    height: 30px;
    margin: 0 8px;
    animation: slide 60s linear infinite;
}
@keyframes slide {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>
""", unsafe_allow_html=True)

# === BANNER ===
logos = [
    "https://loodibee.com/wp-content/uploads/nba-golden-state-warriors-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-los-angeles-lakers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-miami-heat-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-chicago-bulls-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-milwaukee-bucks-logo.png"
]
st.markdown(
    f"<div class='banner'>{''.join([f'<img src=\"{logo}\" />' for logo in logos])}</div>",
    unsafe_allow_html=True
)

st.markdown("<h1 style='text-align: center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError("Empty data from API")
        return data
    except Exception as e:
        st.warning(f"⚠️ Live data fetch failed. Using mock data instead.\n\nError: {e}")
        return [
            {
                "home_team": "Golden State Warriors",
                "teams": ["Golden State Warriors", "Los Angeles Lakers"],
                "bookmakers": [
                    {
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Golden State Warriors", "price": -130},
                                    {"name": "Los Angeles Lakers", "price": 110}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

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

if not odds_data:
    st.warning("No betting data available.")
else:
    bets = []
    for game in odds_data:
        home = game.get("home_team")
        teams = game.get("teams", [])
        if not teams or home not in teams or len(teams) != 2:
            continue
        away = [t for t in teams if t != home][0]
        matchup = f"{away} @ {home}"

        for bookmaker in game.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") not in ["h2h", "spreads", "totals"]:
                    continue
                for outcome in market.get("outcomes", []):
                    team = outcome.get("name")
                    odds = outcome.get("price")
                    prob = estimate_model_probability(odds)
                    ev, model_pct, implied_pct = calc_ev(prob, odds)
                    bets.append({
                        "Date": today,
                        "Matchup": matchup,
                        "Team": team,
                        "Market": market["key"],
                        "Odds": odds,
                        "Model Prob": model_pct,
                        "EV%": ev,
                        "Implied%": implied_pct
                    })

        df = pd.DataFrame(bets)

    # Filter options
    st.markdown("<div class='section'><h3>⚙️ Filter Settings</h3>", unsafe_allow_html=True)
    ev_cutoff = st.slider("Minimum Expected Value (%)", min_value=-100, max_value=100, value=-100)
    df = df[df["EV%"] >= ev_cutoff]
    st.markdown("</div>", unsafe_allow_html=True)

    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<div class='section'><h3>📊 Distribution of EV%</h3>", unsafe_allow_html=True)
            fig, ax = plt.subplots()
            df["EV%"].hist(ax=ax, bins=15, color="#FFDF00")
            ax.set_title("Expected Value Histogram")
            ax.set_xlabel("EV%")
            ax.set_ylabel("Frequency")
            st.pyplot(fig)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='section'><h3>📈 Top Picks</h3>", unsafe_allow_html=True)
            top_bets = df.sort_values("EV%", ascending=False).head(5)
            st.dataframe(top_bets[["Matchup", "Team", "Market", "Odds", "EV%"]], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section'><h3>📥 Full Data</h3>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "nba_model_bets.csv")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("No valid bets passed filter logic. Try lowering the EV threshold.")
    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<div class='section'><h3>📊 Distribution of EV%</h3>", unsafe_allow_html=True)
            fig, ax = plt.subplots()
            df["EV%"].hist(ax=ax, bins=15, color="#FFDF00")
            ax.set_title("Expected Value Histogram")
            ax.set_xlabel("EV%")
            ax.set_ylabel("Frequency")
            st.pyplot(fig)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='section'><h3>📈 Top Picks</h3>", unsafe_allow_html=True)
            top_bets = df.sort_values("EV%", ascending=False).head(5)
            st.dataframe(top_bets[["Matchup", "Team", "Market", "Odds", "EV%"]], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section'><h3>📥 Full Data</h3>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "nba_model_bets.csv")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No valid bets passed filter logic.")
