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
/* Hide default Streamlit header/footer/menu */
#MainMenu {visibility: hidden;} 
footer {visibility: hidden;} 
header {visibility: hidden;}

:root {
  --bg-light: #f4f6fa;
  --bg-dark:  #1e1e1e;
  --text-light: #111;
  --text-dark:  #ddd;
  --accent-start: #001f3f;
  --accent-end:   #003366;
  --highlight:    #FFDF00;
  --card-bg-light: #fff;
  --card-bg-dark:  #2a2a2a;
}
body {
  font-family: 'Roboto', sans-serif !important;
  background-color: var(--bg-dark) !important;
  color: var(--text-dark) !important;
  margin: 0; padding: 0;
}

/* Banner at top */
.banner {
  position: fixed;
  top: 50px; /* below Streamlit cloud bar */
  left: 0;
  width: 100%;
  height: 50px; /* reduced height */
  background-color: var(--bg-light);
  overflow: hidden;
  display: flex;
  align-items: center;
  z-index: 10000;
}
.banner img {
  height: 40px; /* smaller icons */
  margin: 0 16px;
  animation: scroll 20s linear infinite;
}
@keyframes scroll {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}

/* Push content below banner */
.content-wrapper {
  padding-top: 110px; /* banner height + offset */
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
  transition: box-shadow 0.3s;
}
.section:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
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
    # ... include all 30 logos ...
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
html_banner = '<div class="banner">' + ''.join(f'<img src="{url}" />' for url in NBA_LOGOS) + '</div>'
st.markdown(html_banner, unsafe_allow_html=True)

# -----------------------
# --- Main Content -----
# -----------------------
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

# Remaining app code unchanged...
# (login forms, betting logic, data fetching, etc.)
