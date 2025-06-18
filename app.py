# nba_betting_insights/app.py

import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------
# --- Page & Theme -----
# -----------------------
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# Theme toggle
theme = st.sidebar.radio("Select Theme", ["Light", "Dark"])
dark_mode = theme == "Dark"

# -----------------------
# --- API Key ----------
# -----------------------
API_KEY = os.getenv("ODDS_API_KEY", "3d4eabb1db321b1add71a25189a77697")

# -----------------------
# --- Global CSS -------
# -----------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
/* hide default menu */
#MainMenu, footer, header {visibility: hidden;}
:root {
  --bg-light: #f4f6fa;
  --bg-dark:  #1e1e1e;
  --accent-start: #001f3f;
  --accent-end:   #003366;
  --highlight:    #FFDF00;
  --card-bg-light: #fff;
}
body {
  font-family: 'Roboto', sans-serif !important;
  background-color: var(--bg-dark) !important;
  color: #ddd !important;
  margin: 0; padding: 0;
}
/* tiny banner */
.banner {
  position: fixed;
  top: 35px;
  left: 0;
  width: 100%;
  height: 12px;
  background-color: var(--bg-light);
  overflow: hidden;
  display: flex;
  align-items: center;
  z-index: 10000;
}
.banner img {
  height: 12px;
  margin: 0 4px;
  animation: scroll 20s linear infinite;
}
@keyframes scroll {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
/* content below banner */
.content-wrapper {
  padding-top: 60px;
  padding-left: 16px;
  padding-right: 16px;
}
.section {
  background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
  border-radius: 16px;
  padding: 24px;
  margin: 16px 0;
  color: var(--highlight);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}
.bet-card {
  background: var(--card-bg-light);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}
.bet-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# --- Banner Logos -----
# -----------------------
NBA_LOGOS = [
    "https://loodibee.com/wp-content/uploads/nba-atlanta-hawks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    # ... all 30 logos ...
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
st.markdown(f'<div class="banner">{"".join(f"<img src=\"{u}\"/>" for u in NBA_LOGOS)}</div>', unsafe_allow_html=True)

# -----------------------
# --- Main Content -----
# -----------------------
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

# Session state
if "logged_in" not in st.session_state: st.session_state.logged_in=False
if "username" not in st.session_state: st.session_state.username=""
if "user_bets" not in st.session_state: st.session_state.user_bets=[]
if "credentials" not in st.session_state: st.session_state.credentials={"user1":"password1","user2":"password2"}

# Fallback sample
SAMPLE_GAME=[{"home_team":"Lakers","away_team":"Warriors","bookmakers":[{"markets":[{"key":"spreads","outcomes":[{"name":"Lakers","price":-110},{"name":"Warriors","price":100}]}]}]}]

# Fetch odds
@st.cache_data(show_spinner=False)
def fetch_odds():
    url="https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params={"apiKey":API_KEY,"regions":"us","markets":"spreads,totals,h2h","oddsFormat":"american"}
    try:
        r=requests.get(url,params=params);r.raise_for_status();return r.json()
    except Exception as e:
        st.error(f"API error: {e}");return []

raw=fetch_odds()
if not raw:raw=SAMPLE_GAME;st.warning("Using sample data.")
else:st.success(f"Retrieved {len(raw)} games.")

# Compute probabilities & EV
rows=[];today=datetime.today().strftime("%Y-%m-%d")
def estimate_prob(o):return round(1/(1+10**(-o/400)),4)
def calc_ev(p,o):imp=(100/(100+o)) if o>0 else (abs(o)/(100+abs(o)));ev=p*(o if o>0 else 100)-(1-p)*100;return round(ev,2),round(p*100,1),round(imp*100,1)
for g in raw:
    h,a=g.get("home_team"),g.get("away_team");
    if not h or not a: continue
    m=f"{a} @ {h}"
    for b in g.get("bookmakers",[]):
        for mk in b.get("markets",[]):
            for o in mk.get("outcomes",[]):
                price=o.get("price");
                if price is None: continue
                p=estimate_prob(price);ev,mp,ip=calc_ev(p,price)
                rows.append({"Date":today,"Matchup":m,"Team":o["name"],"Market":mk["key"],"Odds":price,"Model %":mp,"EV %":ev})

import pandas as pd

df=pd.DataFrame(rows)

# Login form
```
