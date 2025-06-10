# NBA Betting Insights MVP - Streamlit App with Enhanced Layout, Graphics, and Ticker Banner

# 1. DATA INGESTION
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

# Replace 'YOUR_API_KEY' with your actual Odds API key
API_KEY = "3d4eabb1db321b1add71a25189a77697"

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

@st.cache_data(show_spinner=False)
def fetch_scores():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/scores/"
    params = {"apiKey": API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

# 2. MODEL LAYER - Enhanced Model Probability Estimate

def estimate_model_probability(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except Exception:
        return 0.50

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

# 3. FRONTEND (Streamlit MVP)
st.set_page_config(page_title="NBA Betting Insights", layout="wide")
st.markdown("""
    <style>
    .main-title {
        font-size: 3em;
        font-weight: bold;
        color: #1E88E5;
        padding-bottom: 10px;
    }
    .bet-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .ticker {
        background-color: #000;
        color: white;
        padding: 8px;
        overflow: hidden;
        white-space: nowrap;
        box-shadow: inset 0 -1px 0 #ccc;
    }
    .ticker span {
        display: inline-block;
        padding-right: 3rem;
        animation: scroll-left 20s linear infinite;
    }
    @keyframes scroll-left {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    </style>
""", unsafe_allow_html=True)

# Add ticker banner with NBA teams
nba_teams = [
    "Hawks", "Celtics", "Nets", "Hornets", "Bulls", "Cavaliers", "Mavericks",
    "Nuggets", "Pistons", "Warriors", "Rockets", "Pacers", "Clippers", "Lakers",
    "Grizzlies", "Heat", "Bucks", "Timberwolves", "Pelicans", "Knicks", "Thunder",
    "Magic", "76ers", "Suns", "Trail Blazers", "Kings", "Spurs", "Raptors", "Jazz", "Wizards"
]
st.markdown(f"""
    <div class='ticker'><span>{' | '.join(nba_teams)}</span></div>
""", unsafe_allow_html=True)

st.image("https://media.tenor.com/VbV35bUNRpoAAAAC/basketball-bounce.gif", width=100)
st.markdown("<div class='main-title'>NBA Betting Insights</div>", unsafe_allow_html=True)

# REMAINDER OF YOUR CODE UNCHANGED...
# (To maintain space, we have truncated below this line)
# Make sure to keep all logic for odds display, EV calcs, charts, and bet history intact.
