# NBA Betting Insights Dashboard

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

# --- CONFIG ---
API_KEY = "3d4eabb1db321b1add71a25189a77697"
st.set_page_config(page_title="NBA Betting Insights Dashboard", layout="wide")

# --- STYLES ---
st.markdown("""
    <style>
    body {
        background-color: #f5f8ff;
    }
    .title {
        font-size: 3em;
        font-weight: 700;
        text-align: center;
        color: #212529;
    }
    .section {
        background: linear-gradient(to right, #001f3f, #FFDF00);
        border-radius: 10px;
        padding: 10px 25px;
        color: white;
        font-size: 20px;
        font-weight: bold;
        margin: 10px 0;
    }
    .logo-banner {
        display: flex;
        overflow-x: auto;
        white-space: nowrap;
        background-color: #dee2e6;
        padding: 10px;
        border-radius: 5px;
    }
    .logo-banner img {
        height: 40px;
        margin-right: 15px;
        animation: scroll 20s linear infinite;
    }
    @keyframes scroll {
        0% {transform: translateX(100%);}
        100% {transform: translateX(-100%);}
    }
    .highlight {
        font-weight: bold;
        color: #1E88E5;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='logo-banner'>" +
    "".join([f"<img src='https://loodibee.com/wp-content/uploads/nba-{team}-logo.png'>" for team in [
        "atlanta-hawks", "boston-celtics", "brooklyn-nets", "charlotte-hornets", "chicago-bulls",
        "cleveland-cavaliers", "dallas-mavericks", "denver-nuggets", "detroit-pistons", "golden-state-warriors",
        "houston-rockets", "indiana-pacers", "la-clippers", "los-angeles-lakers", "memphis-grizzlies",
        "miami-heat", "milwaukee-bucks", "minnesota-timberwolves", "new-orleans-pelicans", "new-york-knicks",
        "oklahoma-city-thunder", "orlando-magic", "philadelphia-76ers", "phoenix-suns", "portland-trail-blazers",
        "sacramento-kings", "san-antonio-spurs", "toronto-raptors", "utah-jazz", "washington-wizards"
    ]]) +
    "</div>", unsafe_allow_html=True)

st.markdown("<div class='title'>🏀 NBA Betting Insights</div>", unsafe_allow_html=True)

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
        res = requests.get(url, params=params)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return []

def calc_model_prob(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except:
        return 0.5

def calc_ev(prob, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob * (odds if odds > 0 else 100)) - ((1 - prob) * 100)
    return round(ev, 2), round(prob * 100, 1), round(implied_prob * 100, 1)

# --- DATA ---
odds_data = fetch_odds()
today = datetime.today().strftime("%Y-%m-%d")
rows = []

for game in odds_data:
    home = game["home_team"]
    away = game["away_team"]
    matchup = f"{away} @ {home}"
    for book in game.get("bookmakers", []):
        book_title = book["title"]
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                label = outcome["name"]
                odds = outcome["price"]
                model_prob = calc_model_prob(odds)
                ev, model_pct, implied_pct = calc_ev(model_prob, odds)
                rows.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Market": market["key"],
                    "Bet": label,
                    "Odds": odds,
                    "Model Win%": model_pct,
                    "Implied%": implied_pct,
                    "EV%": ev,
                    "Book": book_title
                })

df = pd.DataFrame(rows)

# --- FILTER ---
st.sidebar.markdown("### Filters")
ev_cutoff = st.sidebar.slider("Minimum Expected Value (EV%)", -100, 100, 0)
filtered = df[df["EV%"] >= ev_cutoff] if not df.empty else pd.DataFrame()

# --- OUTPUT ---
if not filtered.empty:
    st.markdown("<div class='section'>🔥 Top Value Bets</div>", unsafe_allow_html=True)
    top = filtered.sort_values("EV%", ascending=False).head(5)
    for _, row in top.iterrows():
        st.markdown(f"""
        **{row['Matchup']}**  
        📊 *{row['Market']}* | 🏷️ *{row['Bet']}* @ {row['Odds']}  
        💥 EV%: **{row['EV%']}%** | Model: {row['Model Win%']}% | Implied: {row['Implied%']}% | Book: {row['Book']}
        """)
    st.markdown("---")

    st.markdown("<div class='section'>📋 Bet Table</div>", unsafe_allow_html=True)
    st.dataframe(filtered)

    st.markdown("<div class='section'>📈 EV Distribution</div>", unsafe_allow_html=True)
    fig, ax1 = plt.subplots()
    filtered["EV%"].hist(bins=20, ax=ax1, color="#1E88E5")
    ax1.set_title("Distribution of EV%")
    ax1.set_xlabel("EV%")
    ax1.set_ylabel("Number of Bets")
    st.pyplot(fig)
else:
    st.warning("No betting data available.")
