import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="NBA Betting Insights", layout="wide")

API_KEY = "3d4eabb1db321b1add71a25189a77697"  # 🔐 Replace with your actual API key

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

# ---------- LOGOS ----------
NBA_LOGOS = [
    "https://loodibee.com/wp-content/uploads/nba-atlanta-hawks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-brooklyn-nets-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-charlotte-hornets-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-chicago-bulls-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-cleveland-cavaliers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-dallas-mavericks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-denver-nuggets-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-detroit-pistons-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-golden-state-warriors-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-houston-rockets-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-indiana-pacers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-la-clippers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-la-lakers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-memphis-grizzlies-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-miami-heat-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-milwaukee-bucks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-minnesota-timberwolves-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-new-orleans-pelicans-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-new-york-knicks-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-oklahoma-city-thunder-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-orlando-magic-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-philadelphia-76ers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-phoenix-suns-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-portland-trail-blazers-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-sacramento-kings-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-san-antonio-spurs-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-toronto-raptors-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-utah-jazz-logo.png",
    "https://loodibee.com/wp-content/uploads/nba-washington-wizards-logo.png"
]
st.markdown(f"""
<div class="banner">
  {''.join([f'<img src="{logo}">' for logo in NBA_LOGOS])}
</div>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align:center;'>NBA Betting Insights Dashboard</h1>", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_bets" not in st.session_state:
    st.session_state.user_bets = []
if "credentials" not in st.session_state:
    st.session_state.credentials = {
        "user1": "password1",
        "user2": "password2"
    }

# ---------- API FETCH ----------
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

raw_data = fetch_odds()
if not raw_data:
    st.warning("Odds API returned no data. Showing sample fallback.")
    raw_data = [{
        "home_team": "Lakers",
        "teams": ["Lakers", "Warriors"],
        "bookmakers": [{
            "markets": [{
                "key": "spreads",
                "outcomes": [{"name": "Lakers", "price": -110}, {"name": "Warriors", "price": 100}]
            }]
        }]
    }]
else:
    st.success(f"✅ Retrieved {len(raw_data)} games.")

# ---------- MATH UTILS ----------
def estimate_model_probability(odds):
    try:
        return round(1 / (1 + 10 ** (-odds / 400)), 4)
    except:
        return 0.5

def calc_ev(prob_model, odds):
    implied_prob = 100 / (100 + odds) if odds > 0 else abs(odds) / (100 + abs(odds))
    ev = (prob_model * (odds if odds > 0 else 100)) - ((1 - prob_model) * 100)
    return round(ev, 2), round(prob_model * 100, 1), round(implied_prob * 100, 1)

# ---------- BUILD BETS DATAFRAME ----------
bets = []
today = datetime.today().strftime("%Y-%m-%d")

for game in raw_data:
    home = game.get("home_team")
    teams = game.get("teams", [])
    if not teams or home not in teams or len(teams) != 2:
        continue
    away = [team for team in teams if team != home][0]
    matchup = f"{away} @ {home}"
    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                team = outcome.get("name")
                odds = outcome.get("price")
                if odds is None:
                    continue
                model_prob = estimate_model_probability(odds)
                ev, model_pct, implied_pct = calc_ev(model_prob, odds)
                bets.append({
                    "Date": today,
                    "Matchup": matchup,
                    "Team": team,
                    "Market": market["key"],
                    "Odds": odds,
                    "Model Prob": model_pct,
                    "EV%": ev,
                    "Implied": implied_pct
                })

df = pd.DataFrame(bets)
st.write("📊 Sample of Data:", df.head())

# ---------- LOGIN ----------
def login_section():
    st.subheader("Login or Sign Up")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        new_user = st.checkbox("Create new account?")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if new_user:
                if username in st.session_state.credentials:
                    st.error("Username already taken.")
                else:
                    st.session_state.credentials[username] = password
                    st.success("Account created. You are now logged in.")
                    st.session_state.logged_in = True
                    st.session_state.username = username
            else:
                if (
                    username in st.session_state.credentials and
                    st.session_state.credentials[username] == password
                ):
                    st.success("Logged in successfully!")
                    st.session_state.logged_in = True
                    st.session_state.username = username
                else:
                    st.error("Invalid credentials.")

# ---------- POST BETS ----------
def post_bets_section():
    st.subheader(f"Post a Bet ({st.session_state.username})")
    with st.form("bet_form"):
        game = st.text_input("Game", placeholder="e.g. OKC vs IND")
        bet_type = st.selectbox("Bet Type", ["Points", "Rebounds", "Assists", "Parlay", "Other"])
        odds = st.text_input("Odds (e.g. +250 or -110)")
        stake = st.number_input("Stake ($)", min_value=0.0, step=1.0)
        submit_bet = st.form_submit_button("Submit Bet")
        if submit_bet:
            st.session_state.user_bets.append({
                "User": st.session_state.username,
                "Game": game,
                "Type": bet_type,
                "Odds": odds,
                "Stake": stake
            })
            st.success("Bet submitted!")

    if st.session_state.user_bets:
        st.markdown("### Your Bets")
        st.dataframe(pd.DataFrame(st.session_state.user_bets))

# ---------- TABS ----------
tab1, tab2 = st.tabs(["📊 Dashboard", "📝 Post Bets"])

with tab1:
    if df.empty:
        st.warning("No betting data available.")
    else:
        st.markdown("<div class='section'><h3>⚙️ Filter Settings</h3>", unsafe_allow_html=True)
        ev_cutoff = st.slider("Minimum Expected Value (%)", -100, 100, -100)
        df = df[df["EV%"] >= ev_cutoff]
        st.markdown("</div>", unsafe_allow_html=True)

        if df.empty:
            st.info("No bets matched the filters or EV threshold.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("<div class='section'><h3>📊 EV% Histogram</h3>", unsafe_allow_html=True)
                fig, ax = plt.subplots()
                df["EV%"].hist(ax=ax, bins=15, color="#FFDF00")
                ax.set_title("Expected Value Histogram")
                ax.set_xlabel("EV%")
                ax.set_ylabel("Frequency")
                st.pyplot(fig)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='section'><h3>📈 Top Picks</h3>", unsafe_allow_html=True)
                top_bets = df.sort_values("EV%", ascending=False).head(5)
                st.dataframe(top_bets[["Matchup", "Team", "Market", "Odds", "EV%"]], use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section'><h3>📥 Full Data</h3>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
            st.download_button("Download CSV", df.to_csv(index=False), "nba_model_bets.csv")
            st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    if not st.session_state.logged_in:
        login_section()
    else:
        post_bets_section()
