import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import altair as alt
from datetime import datetime
import os

# --- CONFIG ---
API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace this
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# --- STYLES ---
st.markdown("""
<style>
body, .stApp {
    background-color: black;
    color: #39FF14;
}
h1, h2, h3, h4, h5 {
    color: #39FF14;
}
.section {
    background-color: #000000;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    color: #39FF14;
}
.card {
    background-color: #111111;
    border: 1px solid #39FF14;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 10px;
}
a {
    color: #1E90FF;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER + MARQUEE BANNER ---
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center;">
    <div style="overflow:hidden; white-space:nowrap; width:85%;">
        <marquee scrollamount="7">
            {''.join([f'<img src="https://loodibee.com/wp-content/uploads/nba-{team}-logo.png" height="40" style="margin-right:15px;">' for team in [
                'atlanta-hawks', 'boston-celtics', 'brooklyn-nets', 'charlotte-hornets',
                'chicago-bulls', 'cleveland-cavaliers', 'dallas-mavericks', 'denver-nuggets',
                'detroit-pistons', 'golden-state-warriors', 'houston-rockets', 'indiana-pacers',
                'los-angeles-clippers', 'los-angeles-lakers', 'memphis-grizzlies', 'miami-heat',
                'milwaukee-bucks', 'minnesota-timberwolves', 'new-orleans-pelicans', 'new-york-knicks',
                'oklahoma-city-thunder', 'orlando-magic', 'philadelphia-76ers', 'phoenix-suns',
                'portland-trail-blazers', 'sacramento-kings', 'san-antonio-spurs', 'toronto-raptors',
                'utah-jazz', 'washington-wizards'
            ]])}
        </marquee>
    </div>
    <div style="width:15%; text-align:right;">
        <img src="parlayplaytrophy.jpg" height="60">
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<h1>NBA Betting Insights</h1>", unsafe_allow_html=True)

# --- Sportsbook Links ---
st.markdown("""
<p>
🔗 <a href="https://www.fanduel.com" target="_blank">FanDuel</a> |
<a href="https://www.draftkings.com" target="_blank">DraftKings</a> |
<a href="https://www.betmgm.com" target="_blank">BetMGM</a> |
<a href="https://www.betrivers.com" target="_blank">BetRivers</a> |
<a href="https://www.betonline.ag" target="_blank">BetOnline.ag</a>
</p>
""", unsafe_allow_html=True)

# --- API FUNCTIONS ---
@st.cache_data
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "spreads,totals,h2h,player_points",
        "oddsFormat": "american"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return []

@st.cache_data
def fetch_live_scores():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/scores"
    params = {
        "apiKey": API_KEY,
        "daysFrom": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
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

# --- DATA FETCH ---
odds_data = fetch_odds()
today = datetime.today().strftime("%Y-%m-%d")

# --- FILTERS ---
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.subheader("🎯 Filters")
ev_threshold = st.slider("Minimum Expected Value (EV%)", -100, 100, 0)
teams_available = sorted({t for g in odds_data for t in g.get("teams", [])})
team_filter = st.selectbox("Filter by Team (Optional)", ["All Teams"] + teams_available)
market_filter = st.radio("Filter by Market", options=["All", "h2h", "spreads", "totals", "player_points"], horizontal=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- PROCESS DATA ---
rows = []
for game in odds_data:
    home = game.get("home_team")
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [t for t in teams if t != home][0]
    if team_filter != "All Teams" and team_filter not in (home, away):
        continue
    matchup = f"{away} @ {home}"
    for bookmaker in game.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market_filter != "All" and market["key"] != market_filter:
                continue
            for outcome in market.get("outcomes", []):
                label = outcome.get("name")
                odds_val = outcome.get("price")
                model_prob = estimate_model_probability(odds_val)
                ev, model_pct, implied_pct = calc_ev(model_prob, odds_val)
                if ev >= ev_threshold:
                    rows.append({
                        "Date": today,
                        "Matchup": matchup,
                        "Market": market["key"],
                        "Bet": label,
                        "Odds": odds_val,
                        "Model Win%": model_pct,
                        "Implied%": implied_pct,
                        "EV%": ev,
                        "Bookmaker": bookmaker["title"]
                    })

bets_df = pd.DataFrame(rows)

# --- TOP BETS ---
if not bets_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("🔥 Top Bets Today")
    top_bets = bets_df.sort_values("EV%", ascending=False).head(3)
    for _, row in top_bets.iterrows():
        st.markdown(f"""
        <div class='card'>
            <strong>{row['Matchup']}</strong><br>
            Bet: {row['Bet']} ({row['Market']})<br>
            Odds: {row['Odds']} | EV%: {row['EV%']} | Model Win%: {row['Model Win%']}% | Implied%: {row['Implied%']}%<br>
            <em>Bookmaker: {row['Bookmaker']}</em>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- DATA TABLE ---
if not bets_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("📋 All Bets")
    st.dataframe(bets_df, use_container_width=True)
    st.download_button("📥 Download Bets", bets_df.to_csv(index=False), f"bets_{today}.csv")
    st.markdown("</div>", unsafe_allow_html=True)

# --- CHART ---
if not bets_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("📈 EV Distribution")
    chart = alt.Chart(bets_df).mark_bar().encode(
        alt.X("EV%:Q", bin=alt.Bin(maxbins=20)),
        y='count():Q',
        tooltip=["EV%"]
    ).properties(width=600, height=300).interactive()
    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- LIVE SCORES ---
live_scores = fetch_live_scores()
if live_scores:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("🏀 Live Scores")
    for game in live_scores:
        if game["completed"]: continue
        st.write(f"**{game['home_team']} vs {game['away_team']}** - {game['scores'][0]['name']}: {game['scores'][0]['score']} | {game['scores'][1]['name']}: {game['scores'][1]['score']}")
    st.markdown("</div>", unsafe_allow_html=True)

# --- NO BETS ---
if bets_df.empty:
    st.info("No bets matched the filters or EV threshold.")
