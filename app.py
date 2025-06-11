# 1. DATA INGESTION
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

# Replace 'your api key' with actual key
API_KEY = "3d4eabb1db321b1add71a25189a77697"

st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# === STYLES AND BANNER ===
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
.section {
    background: white;
    border-radius: 15px;
    padding: 25px;
    margin-bottom: 25px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.section-header {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 15px;
    color: #003366;
}
.ticker {
    width: 100%;
    overflow: hidden;
    background: rgba(173, 216, 230, 0.3); /* light blue tint */
    padding: 8px 0;
    margin-bottom: 10px;
}
.ticker span {
    display: inline-block;
    white-space: nowrap;
    animation: scroll-left 60s linear infinite;
}
.ticker img {
    height: 32px;
    margin: 0 10px;
    vertical-align: middle;
}
@keyframes scroll-left {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
</style>
""", unsafe_allow_html=True)

# TEAM LOGOS (all 30 teams)
team_logos = [
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

# Render banner
st.markdown(f"""
<div class="ticker"><span>{''.join([f'<img src="{logo}" />' for logo in team_logos])}</span></div>
""", unsafe_allow_html=True)

# === HEADER ===
st.image("https://loodibee.com/wp-content/uploads/nba-logo.png", width=90)
st.markdown("<h1 style='color:#1E88E5;'>NBA Betting Insights</h1>", unsafe_allow_html=True)

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

# === DATA ===
today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()

# === FILTERS ===
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>📌 Filters</div>", unsafe_allow_html=True)

ev_threshold = st.slider("Minimum Expected Value (%)", -100, 100, 0)
all_teams = sorted({team for game in odds_data for team in [game.get("home_team"), *game.get("teams", [])] if team})
team_filter = st.selectbox("Filter by Team (Optional)", options=["All Teams"] + all_teams)
market_filter = st.radio("Filter by Market Type", options=["All", "h2h", "spreads", "totals"], horizontal=True)

st.markdown("</div>", unsafe_allow_html=True)

# === BET TABLE GENERATION ===
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

# === TOP BETS ===
if not new_data.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🔥 Top 3 Bets</div>", unsafe_allow_html=True)
    for ev, matchup, label, odds, model_pct, implied_pct, home_logo, away_logo in sorted(top_bets, reverse=True)[:3]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if away_logo:
                st.image(away_logo, width=50)
        with col2:
            st.subheader(matchup)
            st.write(f"**Bet:** {label} @ {odds:+}")
            st.write(f"**Model Prob:** {model_pct}% | **EV:** {ev}% | **Implied:** {implied_pct}%")
        with col3:
            if home_logo:
                st.image(home_logo, width=50)
    st.markdown("</div>", unsafe_allow_html=True)

# === TABLE ===
if not new_data.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📊 Full Bet Table</div>", unsafe_allow_html=True)
    st.dataframe(new_data, use_container_width=True)
    st.download_button("📥 Download CSV", new_data.to_csv(index=False), f"nba_bets_{today}.csv")
    st.markdown("</div>", unsafe_allow_html=True)

# === CHARTS ===
if not new_data.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📈 Charts</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots()
        new_data["EV%"].hist(bins=20, ax=ax, color="#1E88E5")
        ax.set_title("Distribution of EV%")
        ax.set_xlabel("EV%")
        ax.set_ylabel("Bets")
        st.pyplot(fig)
        st.markdown("**How to read**: Higher EV% implies more favorable model value.")
    with col2:
        if not full_history_df.empty:
            trend = full_history_df.groupby("Date")["EV%"].mean().reset_index()
            fig2, ax2 = plt.subplots()
            ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#EF6C00")
            ax2.set_title("Average EV% by Date")
            ax2.set_ylabel("EV%")
            ax2.set_xlabel("Date")
            ax2.tick_params(axis="x", rotation=45)
            st.pyplot(fig2)
            st.markdown("**How to read**: A rising trend implies improving model performance.")
    st.markdown("</div>", unsafe_allow_html=True)

# === PERFORMANCE ===
if not full_history_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>✅ Model Performance</div>", unsafe_allow_html=True)
    resolved = full_history_df[full_history_df["Result"].isin(["Win", "Loss"])]
    if not resolved.empty:
        win_rate = (resolved["Result"] == "Win").mean()
        st.metric("Model Hit Rate", f"{win_rate*100:.1f}%")
    else:
        st.info("No resolved bets yet.")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No valid betting data available to display.")
