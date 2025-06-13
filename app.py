# app.py

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os

# CONFIG
API_KEY = "3d4eabb1db321b1add71a25189a77697"
st.set_page_config(page_title="NBA Betting Dashboard", layout="wide")

# STYLES
st.markdown("""
<style>
body {
    background-color: #f5f8fc;
}
h1, h2, h3 {
    color: #1E2B5C;
}
.ticker {
    background: #dbe9f4;
    padding: 8px;
    overflow: hidden;
    white-space: nowrap;
    border-radius: 10px;
    margin-bottom: 10px;
}
.ticker span {
    display: inline-block;
    animation: scroll-left 40s linear infinite;
}
.ticker img {
    height: 30px;
    margin: 0 10px;
}
@keyframes scroll-left {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
.dashboard-title {
    font-size: 36px;
    font-weight: bold;
    text-align: center;
    color: #111;
    margin-top: 20px;
    margin-bottom: 30px;
}
.box {
    background-color: #001f3f;
    border-radius: 15px;
    padding: 25px;
    margin: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    color: white;
}
.section-grid {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
}
.section-grid > div {
    flex: 1 1 calc(50% - 20px);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# NBA TEAM LOGOS FOR BANNER
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

# HEADER
st.markdown(f"""
<div class='ticker'><span>{''.join([f'<img src="{logo}" />' for logo in nba_logos])}</span></div>
""", unsafe_allow_html=True)
st.markdown("<div class='dashboard-title'>NBA Betting Insights Dashboard</div>", unsafe_allow_html=True)

# FETCH ODDS
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

today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()
bets = []

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
                    "Implied": implied_pct
                })

df = pd.DataFrame(bets)

# ==== SECTION GRID ====
st.markdown("<div class='section-grid'>", unsafe_allow_html=True)

# BOX 1 - EV Distribution
with st.container():
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("📊 Distribution of EV%")
    if not df.empty and "EV%" in df.columns:
        fig1, ax1 = plt.subplots()
        df["EV%"].hist(ax=ax1, bins=20, color="#FFD700")
        ax1.set_title("EV% Histogram")
        ax1.set_xlabel("Expected Value %")
        ax1.set_ylabel("Number of Bets")
        st.pyplot(fig1)
        st.markdown("💡 Higher EV suggests better model value opportunities.")
    else:
        st.info("No data available for EV% histogram.")
    st.markdown("</div>", unsafe_allow_html=True)

# BOX 2 - Table
with st.container():
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("📋 Full Odds Table")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No odds data to show.")
    st.markdown("</div>", unsafe_allow_html=True)

# BOX 3 - EV Trend (historical)
with st.container():
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("📈 EV Trend Over Time")
    hist_path = "daily_history.csv"
    if os.path.exists(hist_path):
        hist_df = pd.read_csv(hist_path)
        if not hist_df.empty:
            trend = hist_df.groupby("Date")["EV%"].mean().reset_index()
            fig2, ax2 = plt.subplots()
            ax2.plot(trend["Date"], trend["EV%"], marker="o", color="#FF9900")
            ax2.set_title("Average EV% by Date")
            ax2.set_xlabel("Date")
            ax2.set_ylabel("EV%")
            ax2.tick_params(axis="x", rotation=45)
            st.pyplot(fig2)
        else:
            st.info("No historical trend data available.")
    else:
        st.info("History file not found.")
    st.markdown("</div>", unsafe_allow_html=True)

# BOX 4 - Model Summary
with st.container():
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("📌 Summary Stats")
    if not df.empty:
        st.metric("Number of Model Picks", len(df))
        st.metric("Top EV%", f"{df['EV%'].max():.2f}%")
    else:
        st.info("No data for summary.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
# ---------- COMMUNITY BET POSTING ----------

# --- Initialize session state if not already ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_bets" not in st.session_state:
    st.session_state.user_bets = []

def login_section():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in {"user1": "password1", "user2": "password2"} and password == {"user1": "password1", "user2": "password2"}[username]:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Successfully logged in!")
        else:
            st.error("Invalid login credentials.")

def post_bets_section():
    st.subheader(f"Post a Bet ({st.session_state.username})")

    with st.form("bet_form"):
        game = st.text_input("Game", placeholder="e.g. OKC vs IND")
        bet_type = st.selectbox("Bet Type", ["Points", "Rebounds", "Assists", "Parlay", "Other"])
        odds = st.text_input("Odds (e.g. +250 or -110)")
        stake = st.number_input("Stake ($)", min_value=0.0, step=1.0)
        submitted = st.form_submit_button("Submit Bet")
        if submitted:
            st.session_state.user_bets.append({
                "User": st.session_state.username,
                "Game": game,
                "Type": bet_type,
                "Odds": odds,
                "Stake": stake
            })
            st.success("Bet submitted!")

    if st.session_state.user_bets:
        st.markdown("### Your Submitted Bets")
        df_bets = pd.DataFrame(st.session_state.user_bets)
        st.dataframe(df_bets)

# --- Add new tab ---
st.markdown("---")
tabs = st.tabs(["Dashboard", "Post Bets"])
with tabs[1]:
    st.header("📝 Community Bet Posting")
    if not st.session_state.logged_in:
        login_section()
    else:
        post_bets_section()
