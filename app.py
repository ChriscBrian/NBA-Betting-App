import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# Set your Odds API key
API_KEY = "3d4eabb1db321b1add71a25189a77697"

# Page config
st.set_page_config(page_title="NBA Betting Insights", layout="wide")
st.title("🏀 NBA Betting Insights")

# Fetch odds from The Odds API
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

# Model logic
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

# DEBUG: Show number of games and raw JSON
st.write("API games returned:", len(odds_data))
st.json(odds_data)

if not odds_data:
    st.warning("No betting data available.")
else:
    # Filter and build rows
    rows = []
    today = datetime.today().strftime("%Y-%m-%d")

    for game in odds_data:
        home = game.get("home_team")
        teams = game.get("teams", [])
        if not teams or len(teams) < 2:
            continue
        away = [team for team in teams if team != home]
        if not away:
            continue
        away = away[0]
        matchup = f"{away} @ {home}"

        for bookmaker in game.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    label = outcome.get("name")
                    odds = outcome.get("price")
                    prob_model = estimate_model_probability(odds)
                    ev, model_pct, implied_pct = calc_ev(prob_model, odds)
                    
                    # TEMP: Append everything (skip EV filtering)
                    rows.append({
                        "Date": today,
                        "Matchup": matchup,
                        "Bet": label,
                        "Odds": odds,
                        "Model Win%": model_pct,
                        "EV%": ev,
                        "Implied%": implied_pct,
                        "Market": market["key"]
                    })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No valid bets passed filter logic.")
    else:
        st.dataframe(df)
