# NBA Betting Insights Dashboard
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import os
from datetime import datetime

# --- CONFIG ---
API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual key
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
.section {
    background: linear-gradient(135deg, #001f3f, #003366);
    border-radius: 18px;
    padding: 25px;
    margin: 25px 0;
    color: white;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.section h3 {
    color: #FFDF00;
    margin-bottom: 10px;
}
.section-title {
    font-size: 22px;
    font-weight: 700;
}
.banner {
    background-color: #e0e7ff;
    padding: 8px 0;
    margin-bottom: 10px;
    border-radius: 10px;
    overflow: hidden;
    white-space: nowrap;
}
.banner span {
    display: inline-block;
    padding: 0 1.5rem;
    animation: scroll-left 20s linear infinite;
}
.banner img {
    height: 30px;
    margin: 0 10px;
    vertical-align: middle;
}
@keyframes scroll-left {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>
""", unsafe_allow_html=True)

# --- NBA TEAM LOGOS FOR BANNER ---
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
<div class='banner'><span>{''.join([f'<img src="{logo}" />' for logo in nba_logos])}</span></div>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("## 🏀 NBA Betting Insights Dashboard")

# --- API CALL ---
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
        return 0.5

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

# --- DATA PREP ---
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()

ev_cutoff = st.slider("Minimum Expected Value (%)", -100, 100, 0)
history_path = "daily_history.csv"
full_history_df = pd.read_csv(history_path) if os.path.exists(history_path) else pd.DataFrame()

top_bets = []
history_data = []

for game in odds_data:
    home = game.get('home_team')
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [team for team in teams if team != home][0]
    matchup = f"{away} @ {home}"
    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            for outcome in market.get("outcomes", []):
                team = outcome["name"]
                odds = outcome.get("price", 0)
                prob = estimate_model_probability(odds)
                ev, prob_pct, implied = calc_ev(prob, odds)
                if ev >= ev_cutoff:
                    row = {
                        "Date": today,
                        "Matchup": matchup,
                        "Bet": team,
                        "Odds": odds,
                        "Model Win%": prob_pct,
                        "EV%": ev,
                        "Implied%": implied,
                        "Result": "Pending",
                        "Market": market["key"]
                    }
                    history_data.append(row)
                    top_bets.append((ev, matchup, team, odds, prob_pct, implied))

new_data = pd.DataFrame(history_data)
if not new_data.empty:
    full_history_df = pd.concat([full_history_df, new_data], ignore_index=True)
    full_history_df.to_csv(history_path, index=False)

# === DISPLAY SECTIONS ===
if not new_data.empty:
    st.markdown("<div class='section'><h3>📊 Bet Table</h3>", unsafe_allow_html=True)
    st.dataframe(new_data, use_container_width=True)
    csv = new_data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, "nba_bets.csv", key="download")
    st.markdown("</div>", unsafe_allow_html=True)

    # Charts Section
    st.markdown("<div class='section'><h3>📈 EV Distribution</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        try:
            fig, ax1 = plt.subplots()
            new_data["EV%"].hist(bins=20, ax=ax1, color="#1E88E5")
            ax1.set_title("Distribution of EV%")
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Could not generate EV histogram: {e}")
    with col2:
        if "Date" in new_data.columns and not new_data["Date"].isnull().all():
            try:
                trend = new_data.groupby("Date")["EV%"].mean().reset_index()
                if not trend.empty:
                    fig2, ax2 = plt.subplots()
                    ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#EF6C00")
                    ax2.set_title("Average EV% by Date")
                    ax2.set_ylabel("EV%")
                    ax2.set_xlabel("Date")
                    ax2.tick_params(axis="x", rotation=45)
                    st.pyplot(fig2)
                else:
                    st.info("No trend data to display.")
            except Exception as e:
                st.warning(f"Error generating EV trend chart: {e}")
        else:
            st.info("No valid date data to display EV trend.")
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.warning("No betting data available.")

