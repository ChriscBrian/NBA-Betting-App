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

.banner {
  position: fixed;
  top: 50px; /* push below cloud bar */
  left: 0;
  width: 100%;
  height: 100px;
  background-color: var(--bg-light);
  overflow: hidden;
  display: flex;
  align-items: center;
  z-index: 10000;
}
.banner img {
  height: 100px;
  margin: 0 32px;
  animation: scroll 30s linear infinite;
}
@keyframes scroll {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}

.content-wrapper {
  padding-top: 170px; /* height + offset */
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

# -----------------------
# --- Session State ----
# -----------------------
if "logged_in" not in st.session_state:     st.session_state.logged_in = False
if "username" not in st.session_state:      st.session_state.username = ""
if "user_bets" not in st.session_state:     st.session_state.user_bets = []
if "credentials" not in st.session_state:
    st.session_state.credentials = {"user1": "password1", "user2": "password2"}

# Sample fallback game
SAMPLE_GAME = [{
    "home_team": "Lakers",
    "away_team": "Warriors",
    "bookmakers": [{
        "markets": [{
            "key": "spreads",
            "outcomes": [
                {"name": "Lakers", "price": -110},
                {"name": "Warriors", "price": 100}
            ]
        }]
    }]
}]

# -----------------------
# --- Fetch Odds -------
# -----------------------
@st.cache_data(show_spinner=False)
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"apiKey": API_KEY, "regions": "us", "markets": "spreads,totals,h2h", "oddsFormat": "american"}
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Odds API error: {e}")
        return []

raw = fetch_odds()
if not raw:
    st.warning("⚠️ API returned no games; using sample data.")
    raw = SAMPLE_GAME
else:
    st.success(f"✅ Retrieved {len(raw)} games.")

# Compute probabilities & EV
rows = []
today = datetime.today().strftime("%Y-%m-%d")
def estimate_prob(o): return round(1/(1+10**(-o/400)),4)
def calc_ev(p,o): imp=(100/(100+o)) if o>0 else (abs(o)/(100+abs(o))); ev=p*(o if o>0 else 100)-(1-p)*100; return round(ev,2), round(p*100,1), round(imp*100,1)
for g in raw:
    h,a=g.get("home_team"),g.get("away_team");
    if not h or not a: continue
    m=f"{a} @ {h}"
    for b in g.get("bookmakers",[]):
        for mk in b.get("markets",[]):
            for o in mk.get("outcomes",[]):
                price=o.get("price");
                if price is None: continue
                p=estimate_prob(price);
                ev,mp,ip=calc_ev(p,price)
                rows.append({"Date":today,"Matchup":m,"Team":o["name"],"Market":mk["key"],"Odds":price,"Model %":mp,"EV %":ev,"Imp %":ip})

df=pd.DataFrame(rows)

# Login form
def login_form():
    st.subheader("🔐 Login or Sign Up")
    with st.form("login"):
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        c=st.checkbox("Create account?")
        go=st.form_submit_button("Go")
        if go:
            creds=st.session_state.credentials
            if c:
                if u in creds: st.error("Username taken.")
                else: creds[u]=p; st.success("Created & logged in!"); st.session_state.logged_in=True; st.session_state.username=u
            else:
                if creds.get(u)==p: st.success("Logged in!"); st.session_state.logged_in=True; st.session_state.username=u
                else: st.error("Invalid credentials.")

# Bets form & delete
def bets_form():
    st.subheader(f"📝 Post a Bet — {st.session_state.username}")
    with st.form("bet"):
        g=st.text_input("Game", placeholder="e.g. OKC vs IND")
        bt=st.selectbox("Bet Type",["Points","Rebounds","Assists","Parlay","Other"])
        od=st.text_input("Odds (e.g. +250 or -110)")
        stak=st.number_input("Stake ($)",0.0,step=1.0)
        s=st.form_submit_button("Submit")
        if s: st.session_state.user_bets.append({"Game":g,"Type":bt,"Odds":od,"Stake":stak}); st.success("Bet added!")
    for i,bet in enumerate(st.session_state.user_bets):
        c1,c2=st.columns([8,1])
        c1.markdown(f"<div class='bet-card'><h4>{bet['Game']}</h4><p><strong>{bet['Type']}</strong> | Odds: {bet['Odds']} | Stake: ${bet['Stake']}</p></div>",unsafe_allow_html=True)
        if c2.button("✕", key=f"del_{i}"): st.session_state.user_bets.pop(i); st.experimental_rerun()

# Main tabs
tab1,tab2=st.tabs(["📊 Dashboard","📝 Post Bets"])
with tab1:
    if df.empty: st.warning("No bets to show.")
    else:
        st.markdown("<div class='section'><h3>🎛 Filters</h3></div>",unsafe_allow_html=True)
        ev_min=st.slider("Minimum EV %",-100,100,-100)
        df2=df[df["EV %"]>=ev_min]
        fig=px.histogram(df2,x="EV %",nbins=15,title="EV% Distribution",template="plotly_dark" if dark_mode else "plotly_white")
        st.plotly_chart(fig,use_container_width=True)
        st.markdown("<div class='section'><h3>🔥 Top Picks</h3></div>",unsafe_allow_html=True)
        for _,r in df2.sort_values("EV %",ascending=False).head(5).iterrows():
            st.markdown(f"<div class='bet-card'><h4>{r['Matchup']}</h4><p><strong>{r['Team']}</strong> | {r['Market']} | Odds: {r['Odds']} | EV%: {r['EV %']}</p></div>",unsafe_allow_html=True)
        st.markdown("<div class='section'><h3>📥 Full Table</h3></div>",unsafe_allow_html=True)
        st.dataframe(df2,use_container_width=True)
with tab2:
    if not st.session_state.logged_in: login_form()
    else: bets_form()

st.markdown('</div>',unsafe_allow_html=True)
