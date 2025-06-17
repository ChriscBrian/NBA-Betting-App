# nba_betting_insights/app.py

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# -----------------------
# --- Page & Theme -----
# -----------------------
st.set_page_config(page_title="NBA Betting Insights", layout="wide")

# Sidebar theme toggle
theme = st.sidebar.radio("Select Theme", ["Light", "Dark"])
dark_mode = theme == "Dark"

# CSS overrides for themes and banner animation & bet cards
css = f"""
<style>
/* BODY & TEXT */
body {{
    background-color: {'#1e1e1e' if dark_mode else '#f4f6fa'};
    color: {'#ddd' if dark_mode else '#333'};
}}
/* SECTION BOXES */
.section {{
    background: linear-gradient(to right, {'#000' if dark_mode else '#001f3f'}, {'#222' if dark_mode else '#003366'});
    color: #FFDF00;
}}
/* BANNER SCROLL */
.banner {{
    background-color: {'#111' if dark_mode else '#e8f0ff'};
    padding: 5px 0; overflow:hidden; white-space:nowrap;
}}
.banner img {{
    height: 30px; margin:0 10px; vertical-align:middle;
    animation: scroll 20s linear infinite;
}}
@keyframes scroll {{
  0% {{ transform: translateX(100%); }}
  100% {{ transform: translateX(-100%); }}
}}
/* BET CARD */
.bet-card {{
    background: {'#333' if dark_mode else '#fff'};
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    color: {'#eee' if dark_mode else '#111'};
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# -----------------------
# --- Constants & State-
# -----------------------
API_KEY = "3d4eabb1db321b1add71a25189a77697"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_bets" not in st.session_state:
    st.session_state.user_bets = []
if "credentials" not in st.session_state:
    st.session_state.credentials = {"user1": "password1", "user2": "password2"}

SAMPLE_GAME = [{
    "home_team": "Lakers",
    "away_team": "Warriors",
    "bookmakers": [{
        "markets": [{
            "key": "spreads",
            "outcomes": [
                {"name":"Lakers","price":-110},
                {"name":"Warriors","price":100}
            ]
        }]
    }]
}]

# -----------------------
# --- Fetch & Parse ----
# -----------------------
@st.cache_data
def fetch_odds():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {"apiKey": API_KEY, "regions":"us", "markets":"spreads,totals,h2h", "oddsFormat":"american"}
    try:
        res = requests.get(url, params=params); res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return []

raw = fetch_odds()
if not raw:
    st.warning("API returned nothing. Using sample data.")
    raw = SAMPLE_GAME
else:
    st.success(f"Retrieved {len(raw)} games.")

def estimate_prob(o): return round(1/(1+10**(-o/400)),4)
def calc_ev(p,o):
    imp = (100/(100+o)) if o>0 else (abs(o)/(100+abs(o)))
    ev = p*(o if o>0 else 100) - (1-p)*100
    return round(ev,2), round(p*100,1), round(imp*100,1)

rows=[]
today = datetime.today().strftime("%Y-%m-%d")
for g in raw:
    h,a = g.get("home_team"), g.get("away_team")
    if not h or not a: continue
    m = f"{a} @ {h}"
    for b in g["bookmakers"]:
        for mk in b["markets"]:
            for o in mk["outcomes"]:
                price = o.get("price")
                if price is None: continue
                p = estimate_prob(price)
                ev,mp,ip = calc_ev(p,price)
                rows.append({
                    "Date":today, "Matchup":m, "Team":o["name"],
                    "Market":mk["key"], "Odds":price,
                    "Model %":mp, "EV %":ev, "Imp %":ip
                })
df = pd.DataFrame(rows)

# -----------------------
# --- Login & Betting ---
# -----------------------
def login_form():
    st.subheader("🔐 Login or Sign Up")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        c = st.checkbox("Create account?")
        ok= st.form_submit_button("Go")
        if ok:
            creds = st.session_state.credentials
            if c:
                if u in creds: st.error("Exists!")
                else:
                    creds[u]=p; st.success("Created & logged in")
                    st.session_state.logged_in=True; st.session_state.username=u
            else:
                if u in creds and creds[u]==p:
                    st.success("Welcome back!")
                    st.session_state.logged_in=True; st.session_state.username=u
                else: st.error("Invalid")

def bets_form():
    st.subheader(f"📝 Post a Bet — {st.session_state.username}")
    with st.form("bet"):
        g  = st.text_input("Game",placeholder="e.g. OKC vs IND")
        bt = st.selectbox("Bet Type",["Points","Rebounds","Assists","Parlay","Other"])
        od = st.text_input("Odds (e.g. +250 or -110)")
        stak = st.number_input("Stake $",0.0, step=1.0)
        s = st.form_submit_button("Submit")
        if s:
            st.session_state.user_bets.append({"Game":g,"Type":bt,"Odds":od,"Stake":stak})
            st.success("Bet added!")
    # render as cards with delete
    for i,bet in enumerate(st.session_state.user_bets):
        c1,c2=st.columns([8,1])
        c1.markdown(f"""
          <div class="bet-card">
            <h4>{bet['Game']}</h4>
            <p><strong>{bet['Type']}</strong> | Odds: {bet['Odds']} | Stake: ${bet['Stake']}</p>
          </div>
        """,unsafe_allow_html=True)
        if c2.button("✕",key=f"del{i}"):
            st.session_state.user_bets.pop(i); st.experimental_rerun()

# -----------------------
# --- Main Tabs --------
# -----------------------
tab1, tab2 = st.tabs(["📊 Dashboard","📝 Post Bets"])

with tab1:
    if df.empty:
        st.warning("No bets to show.")
    else:
        # Filters
        st.markdown("<div class='section'><h3>🎛 Filters</h3></div>",unsafe_allow_html=True)
        ev_min = st.slider("Minimum EV %", -100, 100, -100)
        df2 = df[df["EV %"]>=ev_min]

        # Interactive EV histogram
        fig = px.histogram(df2, x="EV %", nbins=15, title="EV% Distribution",
                           template="plotly_dark" if dark_mode else "plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # Top picks as cards
        st.markdown("<div class='section'><h3>🔥 Top Picks</h3></div>",unsafe_allow_html=True)
        top5 = df2.sort_values("EV %", ascending=False).head(5)
        for _,r in top5.iterrows():
            st.markdown(f"""
              <div class="bet-card">
                <h4>{r['Matchup']}</h4>
                <p><strong>{r['Team']}</strong> | {r['Market']} | Odds: {r['Odds']} | EV%: {r['EV %']}</p>
              </div>
            """,unsafe_allow_html=True)

        # Full interactive table
        st.markdown("<div class='section'><h3>📥 Full Table</h3></div>",unsafe_allow_html=True)
        st.dataframe(df2, use_container_width=True)

with tab2:
    if not st.session_state.logged_in:
        login_form()
    else:
        bets_form()
