# nba_betting_insights/app.py

import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="NBA Betting Insights", layout="wide")

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # 🔐 Replace with your actual key

# ---------- STYLES ----------
st.markdown("""
<style>
body {
    background-color: #f4f6fa;
}
.section {
    background: linear-gradient(to right, #001f3f, #003366);
    border-radius: 20px;
    padding: 20px;
    margin: 20px 0;
    color: white;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}
.section h3 {
    color: #FFDF00;
    margin-bottom: 10px;
}
.banner {
    background-color: #e8f0ff;
    padding: 5px 0;
    overflow: hidden;
    white-space: nowrap;
}
.banner img {
    height: 30px;
    margin: 0 10px;
    vertical-align: middle;
    animation: scroll 60s linear infinite;
}
@keyframes scroll {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
</style>
""", unsafe_allow_html=True)

# ---------- LOGO BANNER ----------
NBA_LOGOS = [
    "https://loodibee.com/wp-content/uploads/nba-atlanta-hawks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    # ... (all the rest of your logos) ...
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
st.markdown(f"""
<div class="banner">
  {''.join([f'<img src="{logo}">' for logo in NBA_LOGOS])}
</div>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align:center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

# ---------- SESSION STATE SETUP ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_bets" not in st.session_state:
    st.session_state.user_bets = []
if "credentials" not in st.session_state:
    # two test accounts; users can also sign up in-session
    st.session_state.credentials = {"user1": "password1", "user2": "password2"}

# ---------- SAMPLE FALLBACK DATA ----------
SAMPLE_GAME = [{
    "home_team": "Lakers",
    "teams": ["Lakers", "Warriors"],
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

# ---------- FETCH ODDS (WITH CACHE) ----------
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
        st.error(f"API error: {e}")
        return []

# ---------- PULL RAW DATA & DEBUG ----------
raw_data = fetch_odds()
st.write("🔍 Raw API data preview:", raw_data[:2])  # show first two entries

if not raw_data:
    st.warning("⚠️ Odds API returned no games. Switching to sample data.")
    raw_data = SAMPLE_GAME
else:
    st.success(f"✅ Retrieved {len(raw_data)} games from the API.")

# ---------- UTILS: MODEL PROB & EV CALC ----------
def estimate_model_probability(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except:
        return 0.5

def calc_ev(prob_model, odds):
    implied_prob = (100 / (100 + odds)) if odds > 0 else (abs(odds) / (100 + abs(odds)))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

# ---------- BUILD BETS LIST ----------
bets = []
today = datetime.today().strftime("%Y-%m-%d")

for game in raw_data:
    home = game.get("home_team")
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [t for t in teams if t != home][0]
    matchup = f"{away} @ {home}"
    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                name = outcome.get("name")
                price = outcome.get("price")
                if price is None:
                    continue
                prob = estimate_model_probability(price)
                ev, model_pct, implied_pct = calc_ev(prob, price)
                bets.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Team": name,
                    "Market": market["key"],
                    "Odds": price,
                    "Model Prob (%)": model_pct,
                    "EV (%)": ev,
                    "Implied (%)": implied_pct
                })

# ---------- FALLBACK IF PARSE YIELDS NOTHING ----------
if not bets:
    st.warning("⚠️ No bets parsed from API data. Rebuilding from sample data.")
    bets = []
    for game in SAMPLE_GAME:
        home = game["home_team"]
        away = [t for t in game["teams"] if t != home][0]
        matchup = f"{away} @ {home}"
        for m in game["bookmakers"][0]["markets"]:
            for o in m["outcomes"]:
                prob = estimate_model_probability(o["price"])
                ev, m_pct, i_pct = calc_ev(prob, o["price"])
                bets.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Team": o["name"],
                    "Market": m["key"],
                    "Odds": o["price"],
                    "Model Prob (%)": m_pct,
                    "EV (%)": ev,
                    "Implied (%)": i_pct
                })

df = pd.DataFrame(bets)
st.write("📊 Parsed bets DataFrame:", df)

# ---------- LOGIN / SIGN-UP TAB ----------
def login_section():
    st.subheader("🔐 Login or Sign Up")
    with st.form("login_form"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        create = st.checkbox("Create new account?")
        ok = st.form_submit_button("Submit")

        if ok:
            creds = st.session_state.credentials
            if create:
                if user in creds:
                    st.error("Username already exists.")
                else:
                    creds[user] = pwd
                    st.success("Account created & logged in!")
                    st.session_state.logged_in = True
                    st.session_state.username = user
            else:
                if user in creds and creds[user] == pwd:
                    st.success("Successfully logged in!")
                    st.session_state.logged_in = True
                    st.session_state.username = user
                else:
                    st.error("Invalid credentials.")

# ---------- POST BETS TAB ----------
def post_bets_section():
    st.subheader(f"📝 Post a Bet — {st.session_state.username}")
    with st.form("bet_form"):
        game = st.text_input("Game", placeholder="e.g. OKC vs IND")
        btype = st.selectbox("Bet Type", ["Points", "Rebounds", "Assists", "Parlay", "Other"])
        odds = st.text_input("Odds (e.g. +250 or -110)")
        stake = st.number_input("Stake ($)", min_value=0.0, step=1.0)
        go = st.form_submit_button("Submit Bet")
        if go:
            st.session_state.user_bets.append({
                "User": st.session_state.username,
                "Game": game,
                "Bet Type": btype,
                "Odds": odds,
                "Stake": stake
            })
            st.success("Bet submitted!")

    if st.session_state.user_bets:
        st.markdown("#### Your Session Bets")
        st.dataframe(pd.DataFrame(st.session_state.user_bets))

# ---------- MAIN TABS ----------
tab1, tab2 = st.tabs(["📊 Dashboard", "📝 Post Bets"])

with tab1:
    if df.empty:
        st.warning("No betting data available.")
    else:
        st.markdown("<div class='section'><h3>🎛️ Filters</h3>", unsafe_allow_html=True)
        ev_cut = st.slider("Minimum EV (%)", -100, 100, -100)
        df_filt = df[df["EV (%)"] >= ev_cut]
        st.markdown("</div>", unsafe_allow_html=True)

        if df_filt.empty:
            st.info("No bets matched your EV filter.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='section'><h3>📈 EV Distribution</h3>", unsafe_allow_html=True)
                fig, ax = plt.subplots()
                df_filt["EV (%)"].hist(ax=ax, bins=10)
                ax.set_xlabel("EV (%)")
                ax.set_ylabel("Frequency")
                st.pyplot(fig)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='section'><h3>🔥 Top Picks</h3>", unsafe_allow_html=True)
                top5 = df_filt.sort_values("EV (%)", ascending=False).head(5)
                st.dataframe(top5[["Matchup", "Team", "Odds", "EV (%)"]], use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section'><h3>📥 Full Table</h3>", unsafe_allow_html=True)
            st.dataframe(df_filt, use_container_width=True)
            st.download_button("Download CSV", df_filt.to_csv(index=False), "bets.csv")
            st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    if not st.session_state.logged_in:
        login_section()
    else:
        post_bets_section()
