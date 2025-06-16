import requests
import pandas as pd
import streamlit as st
from datetime import datetime

API_KEY = "3d4eabb1db321b1add71a25189a77697"

st.set_page_config(page_title="NBA Betting Insights", layout="wide")
st.title("🏀 NBA Betting Insights")

@st.cache_data(show_spinner=False)
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
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

# Fetch data
odds_data = fetch_odds()
today = datetime.today().strftime("%Y-%m-%d")
st.write("Games available from API:", len(odds_data))

bet_rows = []

for game in odds_data:
    home = game.get("home_team")
    away = game.get("away_team", "Unknown")
    matchup = f"{away} @ {home}"

    for book in game.get("bookmakers", []):
        book_name = book["title"]
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                label = outcome.get("name")
                odds = outcome.get("price")
                prob_model = estimate_model_probability(odds)
                ev, model_pct, implied_pct = calc_ev(prob_model, odds)

                bet_rows.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Market": market["key"],
                    "Bet": label,
                    "Odds": odds,
                    "Model Win%": model_pct,
                    "Implied%": implied_pct,
                    "EV%": ev,
                    "Book": book_name
                })

df = pd.DataFrame(bet_rows)

if df.empty:
    st.warning("No valid odds found.")
else:
    st.markdown("### 📊 All Available Bets")
    st.dataframe(df, use_container_width=True)
