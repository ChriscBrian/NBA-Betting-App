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
    # … all your other logos …
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
st.markdown(f"""
<div class="banner">
  {''.join(f'<img src=\"{logo}\">' for logo in NBA_LOGOS)}
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
    st.session_state.credentials = {"user1": "password1", "user2": "password2"}

# ---------- SAMPLE FALLBACK GAME ----------
SAMPLE_GAME = [{
    "home_team": "Lakers",
    "away_team": "Warriors",
    "bookmakers": [{
        "markets": [{
            "key": "spreads",
            "outcomes": [
                {"name": "Lakers", "price": -110},
                {"name": "Warriors", "price": +100}
            ]
        }]
    }]
}]

# ---------- FETCH ODDS ----------
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
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Odds API error: {e}")
        return []

raw_data = fetch_odds()
if not raw_data:
    st.warning("⚠️ API returned no games — using a sample fallback.")
    raw_data = SAMPLE_GAME
else:
    st.success(f"✅ Retrieved {len(raw_data)} games.")

# ---------- MODEL PROBABILITY & EV FUNCTIONS ----------
def estimate_model_probability(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except:
        return 0.5

def calc_ev(prob_model, odds):
    implied = (100 / (100 + odds)) if odds > 0 else (abs(odds) / (100 + abs(odds)))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied * 100, 1)

# ---------- BUILD BETS DATAFRAME ----------
bets = []
today = datetime.today().strftime("%Y-%m-%d")

for game in raw_data:
    home = game.get("home_team")
    away = game.get("away_team")
    if not home or not away:
        continue
    matchup = f"{away} @ {home}"

    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                name  = outcome.get("name")
                price = outcome.get("price")
                if price is None:
                    continue

                prob     = estimate_model_probability(price)
                ev, mpct, ipct = calc_ev(prob, price)

                bets.append({
                    "Date":       today,
                    "Matchup":    matchup,
                    "Team":       name,
                    "Market":     market["key"],
                    "Odds":       price,
                    "Model %":    mpct,
                    "EV %":       ev,
                    "Implied %":  ipct
                })

df = pd.DataFrame(bets)

# ---------- LOGIN / SIGN-UP FORM ----------
def login_section():
    st.subheader("🔐 Login or Sign Up")
    with st.form("login_form"):
        user   = st.text_input("Username")
        pwd    = st.text_input("Password", type="password")
        create = st.checkbox("Create new account?")
        go     = st.form_submit_button("Submit")

        if go:
            creds = st.session_state.credentials
            if create:
                if user in creds:
                    st.error("That username is already taken.")
                else:
                    creds[user] = pwd
                    st.success("Account created and logged in!")
                    st.session_state.logged_in  = True
                    st.session_state.username   = user
            else:
                if user in creds and creds[user] == pwd:
                    st.success("Logged in successfully!")
                    st.session_state.logged_in  = True
                    st.session_state.username   = user
                else:
                    st.error("Invalid credentials.")

# ---------- POST BETS FORM ----------
def post_bets_section():
    st.subheader(f"📝 Post a Bet — {st.session_state.username}")
    with st.form("bet_form"):
        game    = st.text_input("Game", placeholder="e.g. OKC vs IND")
        btype   = st.selectbox("Bet Type", ["Points","Rebounds","Assists","Parlay","Other"])
        odds_in = st.text_input("Odds (e.g. +250 or -110)")
        stake   = st.number_input("Stake ($)", min_value=0.0, step=1.0)
        submit  = st.form_submit_button("Submit Bet")

        if submit:
            st.session_state.user_bets.append({
                "User":    st.session_state.username,
                "Game":    game,
                "Bet Type":btype,
                "Odds":    odds_in,
                "Stake":   stake
            })
            st.success("Bet submitted!")

    if st.session_state.user_bets:
        st.markdown("#### Your Session Bets")
        st.dataframe(pd.DataFrame(st.session_state.user_bets))

# ---------- MAIN TABS ----------
tab1, tab2 = st.tabs(["📊 Dashboard", "📝 Post Bets"])

with tab1:
    if df.empty:
        st.warning("No bets to display.")
    else:
        st.markdown("<div class='section'><h3>🎛️ Filters</h3>", unsafe_allow_html=True)
        ev_cut = st.slider("Minimum EV %", -100, 100, -100)
        df_f   = df[df["EV %"] >= ev_cut]
        st.markdown("</div>", unsafe_allow_html=True)

        if df_f.empty:
            st.info("No bets match that filter.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='section'><h3>📈 EV Distribution</h3>", unsafe_allow_html=True)
                fig, ax = plt.subplots()
                df_f["EV %"].hist(ax=ax, bins=15)
                ax.set_xlabel("EV %")
                ax.set_ylabel("Frequency")
                st.pyplot(fig)
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='section'><h3>🔥 Top Picks</h3>", unsafe_allow_html=True)
                top5 = df_f.sort_values("EV %", ascending=False).head(5)
                st.dataframe(top5[["Matchup","Team","Odds","EV %"]], use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section'><h3>📥 Full Table</h3>", unsafe_allow_html=True)
            st.dataframe(df_f, use_container_width=True)
            st.download_button("Download CSV", df_f.to_csv(index=False), "bets.csv")
            st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    if not st.session_state.logged_in:
        login_section()
    else:
        post_bets_section()
