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
body { font-family: 'Roboto', sans-serif !important; background-color: var(--bg-dark) !important; color: #ddd !important; margin: 0; padding: 0; }
.banner { position: fixed; top: 35px; left: 0; width: 100%; height: 12px; background-color: var(--bg-light); overflow: hidden; display: flex; align-items: center; z-index: 10000; }
.banner img { height: 12px; margin: 0 4px; animation: scroll 20s linear infinite; }
@keyframes scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
.content-wrapper { padding-top: 60px; padding-left: 16px; padding-right: 16px; }
.section { background: linear-gradient(135deg, var(--accent-start), var(--accent-end)); border-radius: 16px; padding: 24px; margin: 16px 0; color: var(--highlight); box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
.bet-card { background: var(--card-bg-light); border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.2s, box-shadow 0.2s; }
.bet-card:hover { transform: translateY(-4px); box-shadow: 0 6px 16px rgba(0,0,0,0.15); }
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
st.markdown(
    '<div class="banner">' +
    ''.join(f'<img src="{url}" />' for url in NBA_LOGOS) +
    '</div>',
    unsafe_allow_html=True
)

# -----------------------
# --- Header & Wrapper -
# -----------------------
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

# -----------------------
# --- Session State ----
# -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_bets" not in st.session_state:
    st.session_state.user_bets = []
if "credentials" not in st.session_state:
    st.session_state.credentials = {"user1": "password1", "user2": "password2"}

# -----------------------
# --- Sample Fallback --
# -----------------------
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
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "spreads,totals,h2h",
        "oddsFormat": "american"
    }
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return []

raw = fetch_odds()
if not raw:
    st.warning("⚠️ No API data—using sample.")
    raw = SAMPLE_GAME
else:
    st.success(f"✅ Retrieved {len(raw)} games.")

# -----------------------
# --- Build DataFrame --
# -----------------------
rows = []
today = datetime.today().strftime("%Y-%m-%d")

def estimate_prob(o):
    return round(1 / (1 + 10 ** (-o / 400)), 4)

def calc_ev(p, o):
    implied = (100 / (100 + o)) if o > 0 else (abs(o) / (100 + abs(o)))
    ev = (p * (o if o > 0 else 100)) - ((1 - p) * 100)
    return round(ev, 2), round(p * 100, 1), round(implied * 100, 1)

for game in raw:
    home = game.get("home_team")
    away = game.get("away_team")
    if not home or not away:
        continue
    matchup = f"{away} @ {home}"
    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                odds = outcome.get("price")
                if odds is None:
                    continue
                prob = estimate_prob(odds)
                ev, mpct, ipct = calc_ev(prob, odds)
                rows.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Team": outcome.get("name"),
                    "Market": market.get("key"),
                    "Odds": odds,
                    "Model %": mpct,
                    "EV %": ev,
                    "Implied %": ipct
                })

df = pd.DataFrame(rows)

# -----------------------
# --- Login Form -------
# -----------------------
def login_form():
    st.subheader("🔐 Login or Sign Up")
    with st.form("login_form"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        create = st.checkbox("Create new account?")
        go = st.form_submit_button("Submit")
        if go:
            creds = st.session_state.credentials
            if create:
                if user in creds:
                    st.error("That username is already taken.")
                else:
                    creds[user] = pwd
                    st.success("Account created and logged in!")
                    st.session_state.logged_in = True
                    st.session_state.username = user
            else:
                if creds.get(user) == pwd:
                    st.success("Logged in successfully!")
                    st.session_state.logged_in = True
                    st.session_state.username = user
                else:
                    st.error("Invalid credentials.")

# -----------------------
# --- Post Bets Form ---
# -----------------------
def post_bets_section():
    st.subheader(f"📝 Post a Bet — {st.session_state.username}")
    with st.form("bet_form"):
        game = st.text_input("Game", placeholder="e.g. OKC vs IND")
        btype = st.selectbox("Bet Type", ["Points","Rebounds","Assists","Parlay","Other"])
        odds_in = st.text_input("Odds (e.g. +250 or -110)")
        stake = st.number_input("Stake ($)", min_value=0.0, step=1.0)
        submit = st.form_submit_button("Submit Bet")
        if submit:
            st.session_state.user_bets.append({
                "User": st.session_state.username,
                "Game": game,
                "Bet Type": btype,
                "Odds": odds_in,
                "Stake": stake
            })
            st.success("Bet submitted!")
    if st.session_state.user_bets:
        st.markdown("#### Your Session Bets")
        for idx, bet in enumerate(st.session_state.user_bets):
            col1, col2 = st.columns([8, 1])
            col1.write(f"**{bet['Game']}** — {bet['Bet Type']} @ {bet['Odds']} — ${bet['Stake']}")
            if col2.button("Delete", key=f"del_{idx}"):
                st.session_state.user_bets.pop(idx)
                st.experimental_rerun()

# -----------------------
# --- Main Tabs --------
# -----------------------
tab1, tab2 = st.tabs(["📊 Dashboard", "📝 Post Bets"])

with tab1:
    if df.empty:
        st.warning("No bets to display.")
    else:
        st.markdown("<div class='section'><h3>🎛️ Filters</h3></div>", unsafe_allow_html=True)
        ev_cut = st.slider("Minimum EV %", -100, 100, -100)
        df_f = df[df["EV %"] >= ev_cut]
        if df_f.empty:
            st.info("No bets match that filter.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='section'><h3>📈 EV Distribution</h3></div>", unsafe_allow_html=True)
                fig = px.histogram(df_f, x="EV %", nbins=15, template="plotly_dark" if dark_mode else "plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown("<div class='section'><h3>🔥 Top Picks</h3></div>", unsafe_allow_html=True)
                top5 = df_f.sort_values("EV %", ascending=False).head(5)
                for _, r in top5.iterrows():
                    st.markdown(f"<div class='bet-card'><h4>{r['Matchup']}</h4><p><strong>{r['Team']}</strong> | Odds: {r['Odds']} | EV%: {r['EV %']}</p></div>", unsafe_allow_html=True)
            st.markdown("<div class='section'><h3>📥 Full Table</h3></div>", unsafe_allow_html=True)
            st.dataframe(df_f, use_container_width=True)

with tab2:
    if not st.session_state.logged_in:
        login_form()
    else:
        post_bets_section()

st.markdown('</div>', unsafe_allow_html=True)
