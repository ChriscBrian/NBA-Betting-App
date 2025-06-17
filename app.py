import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import altair as alt
from datetime import datetime
import os

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # Replace with your actual key
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# --- STYLES ---
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
.section {
    background: #001f3f;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 25px;
    color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.section h3 {
    color: #FFDF00;
}
.card {
    background: linear-gradient(135deg, #00274d, #003366);
    border: 1px solid #FFDF00;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# --- BANNER ---
st.markdown("""
<div style="overflow:hidden; white-space:nowrap; background-color:rgba(255,255,255,0.1); padding:10px 0;">
    <marquee behavior="scroll" direction="left" scrollamount="8">
        <img src="https://loodibee.com/wp-content/uploads/nba-logo.png" height="40">
        <img src="https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png" height="40">
        <img src="https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png" height="40">
        <img src="https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png" height="40">
        <img src="https://loodibee.com/wp-content/uploads/nba-los-angeles-lakers-logo.png" height="40">
        <img src="https://loodibee.com/wp-content/uploads/nba-miami-heat-logo.png" height="40">
        <img src="https://loodibee.com/wp-content/uploads/nba-golden-state-warriors-logo.png" height="40">
        <img src="https://loodibee.com/wp-content/uploads/nba-chicago-bulls-logo.png" height="40">
    </marquee>
</div>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color:#1E88E5;'>NBA Betting Insights</h1>", unsafe_allow_html=True)

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

today = datetime.today().strftime("%Y-%m-%d")
odds_data = fetch_odds()

# === FILTERS ===
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 🎯 Filters")
ev_threshold = st.slider("Minimum Expected Value (EV%)", -100, 100, 0)
team_filter = st.selectbox("Filter by Team (Optional)", options=["All Teams"] + sorted({t for g in odds_data for t in g.get("teams", [])}))
market_filter = st.radio("Filter by Market", options=["All", "h2h", "spreads", "totals"], horizontal=True)
st.markdown("</div>", unsafe_allow_html=True)

# === DATA PROCESSING ===
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

# === HISTORY ===
history_path = "daily_history.csv"
if os.path.exists(history_path):
    history_df = pd.read_csv(history_path)
else:
    history_df = pd.DataFrame()
if not bets_df.empty:
    history_df = pd.concat([history_df, bets_df], ignore_index=True)
    history_df.to_csv(history_path, index=False)

# === TOP BET CARDS ===
if not bets_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("### 🔥 Today's Best Bets")
    top3 = bets_df.sort_values("EV%", ascending=False).head(3)
    for _, row in top3.iterrows():
        st.markdown(f"""
        <div class='card'>
            <h4>{row['Matchup']}</h4>
            <p><strong>Bet:</strong> {row['Bet']} ({row['Market']})</p>
            <p><strong>Odds:</strong> {row['Odds']} | <strong>EV%:</strong> {row['EV%']} | <strong>Model Win%:</strong> {row['Model Win%']}% | <strong>Implied%:</strong> {row['Implied%']}%</p>
            <p><em>Bookmaker: {row['Bookmaker']}</em></p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# === FULL TABLE ===
if not bets_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("### 📋 All Bets")
    st.dataframe(bets_df, use_container_width=True)
    st.download_button("📥 Download Today's Bets", bets_df.to_csv(index=False), f"bets_{today}.csv")
    st.markdown("</div>", unsafe_allow_html=True)

# === CHARTS ===
if not bets_df.empty:
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.markdown("### 📈 EV Distribution")

    chart = alt.Chart(bets_df).mark_bar().encode(
        alt.X("EV%:Q", bin=alt.Bin(maxbins=20)),
        y='count():Q',
        tooltip=["EV%"]
    ).properties(
        width=600,
        height=300
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("No bets matched the filters or EV threshold.")
