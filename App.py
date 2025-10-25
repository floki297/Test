import streamlit as st
import random
import pandas as pd
import time

# === Karten-Typen ===
CARD_TYPES = {
    "Visa": {"prefixes": ["4"], "length": 16},
    "MasterCard": {"prefixes": ["51", "52", "53", "54", "55", "2221", "2222", "2223", "2224", "2225", "2226", "2227", "2228", "2229", 
                                "223", "224", "225", "226", "227", "228", "229", 
                                "23", "24", "25", "26", "270", "271", "2720"], "length": 16},
    "American Express": {"prefixes": ["34", "37"], "length": 15},
    "Discover": {"prefixes": ["6011", "65", "644", "645", "646", "647", "648", "649"], "length": 16},
    "Diners Club": {"prefixes": ["300", "301", "302", "303", "304", "305", "36", "38"], "length": 14},
    "JCB": {"prefixes": ["3528", "3529", "353", "354", "355", "356", "357", "358"], "length": 16}
}

def generate_test_cc(card_type="Visa", bin_prefix=None, exp_month=None, exp_year=None, cvv=None):
    if bin_prefix:
        if len(bin_prefix) != 6 or not bin_prefix.isdigit():
            raise ValueError("BIN muss genau 6 Ziffern sein.")
        cc_start = bin_prefix
        cc_length = 16
    else:
        type_info = CARD_TYPES[card_type]
        prefix = random.choice(type_info["prefixes"])
        bin_length = len(prefix)
        cc_start = prefix + ''.join(str(random.randint(0, 9)) for _ in range(6 - bin_length))
        cc_length = type_info["length"]

    remaining_length = cc_length - len(cc_start) - 1
    remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(remaining_length + 1))
    cc_number = cc_start + remaining_digits

    # Luhn
    digits = [int(d) for d in cc_number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    checksum = (10 - sum(digits) % 10) % 10
    cc_number = cc_number[:-1] + str(checksum)

    # Monat / Jahr
    month = f"{int(exp_month):02d}" if exp_month and 1 <= int(exp_month) <= 12 else f"{random.randint(1, 12):02d}"
    year = str(exp_year) if exp_year and 2026 <= int(exp_year) <= 2030 else str(random.randint(2026, 2030))
    cvv_length = 4 if card_type == "American Express" else 3
    cvv_str = str(cvv) if cvv and len(str(cvv)) == cvv_length else ''.join(str(random.randint(0, 9)) for _ in range(cvv_length))

    return {
        'Typ': card_type,
        'CC-Nummer': cc_number,
        'Monat': month,
        'Jahr': year,
        'CVV': cvv_str,
        'Ablaufdatum': f"{month}/{year}"
    }

# === SIMULIERTER LIVE-CHECK ===
def simulate_live_check(card_data):
    time.sleep(0.5)  # Simuliere Netzwerkverzögerung
    status_options = [
        ("live", 60),
        ("dead", 30),
        ("insufficient_funds", 5),
        ("declined", 5)
    ]
    statuses, weights = zip(*status_options)
    status = random.choices(statuses, weights=weights, k=1)[0]

    response = {
        "status": status,
        "message": {
            "live": "Karte ist aktiv und zahlungsfähig",
            "dead": "Karte ist gesperrt oder abgelaufen",
            "insufficient_funds": "Nicht genügend Guthaben",
            "declined": "Zahlung abgelehnt (z.B. falscher CVV)"
        }[status],
        "gateway": random.choice(["Stripe", "PayPal", "Adyen", "MockGateway"])
    }
    return response

# === Streamlit App ===
st.set_page_config(page_title="CC Test + Live-Check", layout="wide")
st.title("Test-Kreditkarten Generator + Live-Check (SIMULIERT)")
st.warning("Nur für Testzwecke! Keine echte Prüfung – alles lokal simuliert!")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Karten-Typ")
    card_type = st.selectbox("Typ", options=list(CARD_TYPES.keys()))

with col2:
    st.subheader("Optionale Vorgaben")
    bin_prefix = st.text_input("BIN (6)", placeholder="411111")
    exp_month = st.text_input("Monat", placeholder="12")
    exp_year = st.text_input("Jahr", placeholder="2028")
    cvv_input = st.text_input("CVV", placeholder="123")

with col3:
    st.subheader("Menge")
    quantity = st.number_input("Anzahl", min_value=1, max_value=50, value=1)

# --- Generieren ---
if st.button("Generieren", type="secondary"):
    try:
        bin_val = bin_prefix.strip() if bin_prefix.strip() else None
        month_val = exp_month.strip() if exp_month.strip() else None
        year_val = exp_year.strip() if exp_year.strip() else None
        cvv_val = cvv_input.strip() if cvv_input.strip() else None

        cards = [generate_test_cc(card_type, bin_val, month_val, year_val, cvv_val) for _ in range(quantity)]
        st.session_state.cards = cards
        st.success(f"{quantity} Karten generiert!")
        st.dataframe(pd.DataFrame(cards), use_container_width=True)

    except ValueError as e:
        st.error(f"Fehler: {e}")

# --- Live-Check (nur wenn Karten generiert) ---
if 'cards' in st.session_state and st.button("Live-Check simulieren", type="primary"):
    st.info("Simuliere Anfragen an Zahlungsgateway... (keine echte Verbindung)")
    progress_bar = st.progress(0)
    results = []

    for i, card in enumerate(st.session_state.cards):
        result = simulate_live_check(card)
        result.update(card)
        results.append(result)
        progress_bar.progress((i + 1) / len(st.session_state.cards))

    df = pd.DataFrame(results)
    df = df[['Typ', 'CC-Nummer', 'Ablaufdatum', 'CVV', 'status', 'message', 'gateway']]
    st.success("Live-Check abgeschlossen!")
    st.dataframe(df, use_container_width=True)

    # CSV Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Ergebnisse als CSV", data=csv, file_name="live_check_results.csv", mime="text/csv")

# --- Sidebar ---
with st.sidebar:
    st.header("Simulation")
    st.info("""
    - **Keine echte API-Anfrage**
    - Zufällige, aber realistische Antworten
    - Ideal für UI-Tests, Demos, Debugging
    """)
    st.markdown("---")
    st.caption("Entwickler-Tool | Kein Carding")
