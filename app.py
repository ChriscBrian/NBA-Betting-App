# NBA Betting Insights MVP with Transparent Floating Team Logo Banner

import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import os
import io

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

def estimate_model_probability(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except Exception:
        return 0.50

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

st.set_page_config(page_title="NBA Betting Insights", layout="wide")
st.image("https://media.tenor.com/VbV35bUNRpoAAAAC/basketball-bounce.gif", width=100)

# Transparent Banner with Team Logos
st.markdown("""
<style>
.ticker-container {
    width: 100%;
    overflow: hidden;
    white-space: nowrap;
    position: fixed;
    top: 0;
    z-index: 1000;
    background-color: rgba(255,255,255,0);
}
.ticker-content {
    display: inline-block;
    padding-left: 100%;
    animation: scroll-left 60s linear infinite;
}
.ticker-content img {
    height: 32px;
    margin: 0 12px;
    vertical-align: middle;
}
@keyframes scroll-left {
    0% { transform: translateX(0); }
    100% { transform: translateX(-100%); }
}
.main-title {
    font-size: 3em;
    font-weight: bold;
    color: #1E88E5;
    padding-top: 60px;
    padding-bottom: 10px;
}
.bet-card {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
</style>
<div class="ticker-container">
  <div class="ticker-content">
    <img src="https://loodibee.com/wp-content/uploads/nba-atlanta-hawks-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-brooklyn-nets-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-charlotte-hornets-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-chicago-bulls-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-cleveland-cavaliers-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-dallas-mavericks-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-denver-nuggets-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-detroit-pistons-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-golden-state-warriors-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-houston-rockets-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-la-clippers-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-la-lakers-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-miami-heat-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-milwaukee-bucks-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-minnesota-timberwolves-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-new-orleans-pelicans-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-new-york-knicks-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-orlando-magic-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-philadelphia-76ers-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-phoenix-suns-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-portland-trail-blazers-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-sacramento-kings-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-san-antonio-spurs-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-toronto-raptors-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-utah-jazz-logo.png"/>
    <img src="https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"/>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>NBA Betting Insights</div>", unsafe_allow_html=True)

# The rest of your original logic from “Pull real odds” through performance display should follow here exactly as it was.
