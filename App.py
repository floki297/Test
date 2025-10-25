import streamlit as st
import random
import pandas as pd
import time
import requests

# ========================================
# KONFIGURATION
# ========================================

CARD_TYPES = {
    "Visa": (["4"], 16),
    "MasterCard": (["51", "52", "53", "54", "55"], 16),
    "American Express": (["34", "37"], 15),
    "Discover": (["6011", "65"], 16)
}

STRIPE_TEST_CARDS = {
    "Erfolgreich": "4242424242424242",
    "Abgelehnt": "4000000000000002",
    "Unzureichend": "4000000000009995"
}

PAYPAL_TEST_CARDS = {
    "Erfolgreich": "4532015112830366",
    "Abgelehnt": "4032039944505422"
}

# ========================================
# HILFSFUNKTIONEN
# ========================================

def luhn_checksum(card_number: str) -> str:
    """Luhn-Algorithmus: Gibt gültige CC mit Prüfziffer zurück."""
    digits = [int(d) for d in card_number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    total = sum(digits)
    checksum = (10 - (total % 10)) % 10
    return card_number[:-1] + str(checksum)


def generate_from_bin(bin_prefix: str, quantity: int = 1):
    """Generiert CCs mit gegebener BIN (6 Ziffern)."""
    if len(bin_prefix) != 6 or not bin_prefix.isdigit():
        raise ValueError("BIN muss genau 6 Ziffern sein.")
    
    cards = []
    for _ in range(quantity):
        middle = "".join(str(random.randint(0, 9)) for _ in range(9))
        temp_number = bin_prefix + middle + "0"
        cc_number = luhn_checksum(temp_number)

        month = f"{random.randint(1, 12):02d}"
        year = str(random.randint(2026, 2030))
        cvv = "".join(str(random.randint(0, 9)) for _ in range(3))

        cards.append({
            "BIN": bin_prefix,
            "CC-Nummer": cc_number,
            "Ablaufdatum": f"{month}/{year}",
            "CVV": cvv
        })
    return cards


def generate_card(
    card_type="Visa",
    provider="Simulation",
    scenario="Erfolgreich",
    bin_prefix=None,
    month=None,
    year=None,
    cvv=None
):
    if provider == "Stripe":
        cc_number = STRIPE_TEST_CARDS.get(scenario, STRIPE_TEST_CARDS["Erfolgreich"])
    elif provider == "PayPal":
        cc_number = PAYPAL_TEST_CARDS.get(scenario, PAYPAL_TEST_CARDS["Erfolgreich"])
    else:
        prefixes, length = CARD_TYPES[card_type]
        prefix = random.choice(prefixes)
        start = bin_prefix or prefix + "".join(str(random.randint(0, 9)) for _ in range(6 - len(prefix)))
        temp = start + "0" * (length - len(start))
        cc_number = luhn_checksum(temp)

    month = f"{int(month):02d}" if month and 1 <= int(month) <= 12 else f"{random.randint(1, 12):02d}"
    year = year if year and 2026 <= int(year) <= 2030 else str(random.randint(2026, 2030))
    cvv_length = 4 if card_type == "American Express" else 3
    cvv = cvv if cvv and len(str(cvv)) == cvv_length else "".join(str(random.randint(0, 9)) for _ in range(cvv_length))

    return {
        "Typ": card_type,
        "Provider": provider,
        "CC-Nummer": cc_number,
        "Ablaufdatum": f"{month}/{year}",
        "CVV": cvv
    }


def simulate_check(card):
    time.sleep(0.3)
    status = random.choices(["live", "dead"], [65, 35])[0]
    message = "Karte aktiv" if status == "live" else "Karte tot"
    return {"status": status, "Nachricht": message}


def search_bin(bin_input):
    if len(bin_input) != 6 or not bin_input.isdigit():
        return {"Fehler": "BIN muss 6 Ziffern sein"}
    try:
        url = f"https://lookup.binlist.net/{bin_input}"
        data = requests.get(url, timeout=5).json()
        return {
            "BIN": bin_input,
            "Scheme": data.get("scheme", "—"),
            "Typ": data.get("type", "—"),
            "Marke": data.get("brand", "—"),
            "Land": data.get("country", {}).get("name", "—"),
            "Bank": data.get("bank", {}).get("name", "—")
        }
    except:
        return {"Fehler": "API nicht erreichbar"}


# ========================================
# STREAMLIT UI
# ========================================

st.set_page_config(page_title="CC Generator + BIN", layout="wide")
st.title("Test-Kreditkarten Generator")
st.caption("Entwickler-Tool – nur für Testzwecke")

# === TABS ===
tab1, tab2, tab3 = st.tabs(["Von BIN generieren", "Normal generieren", "BIN suchen"])

# ========================================
# TAB 1: Von BIN CC erstellen
# ========================================
with tab1:
    st.subheader("CCs von einer BIN generieren")
    bin_input_tab1 = st.text_input("BIN (6 Ziffern)", placeholder="z.B. 411111", key="bin_tab1")
    qty_bin = st.number_input("Anzahl Karten", min_value=1, max_value=100, value=5, key="qty_bin")

    if st.button("Von BIN generieren", type="primary", key="gen_bin"):
        if bin_input_tab1:
            with st.spinner("Generiere Karten..."):
                try:
                    cards = generate_from_bin(bin_input_tab1, qty_bin)
                    st.success(f"{qty_bin} Karten mit BIN {bin_input_tab1} generiert!")
                    df = pd.DataFrame(cards)
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False).encode()
                    st.download_button("CSV herunterladen", csv, f"cc_bin_{bin_input_tab1}.csv", "text/csv")
                except ValueError as e:
                    st.error(str(e))
        else:
            st.warning("Bitte BIN eingeben")

# ========================================
# TAB 2: Normal generieren
# ========================================
with tab2:
    st.subheader("Standard-Generator")
    col1, col2, col3, col4 = st.columns(4)
    with col1: provider = st.selectbox("Provider", ["Simulation", "Stripe", "PayPal"], key="prov2")
    with col2: card_type = st.selectbox("Typ", list(CARD_TYPES.keys()), key="type2")
    with col3:
        if provider == "Stripe":
            scenario = st.selectbox("Szenario", list(STRIPE_TEST_CARDS.keys()), key="scen2")
        elif provider == "PayPal":
            scenario = st.selectbox("Szenario", list(PAYPAL_TEST_CARDS.keys()), key="scen2")
        else:
            scenario = "Live"
    with col4: quantity = st.number_input("Anzahl", 1, 50, 1, key="qty2")

    bin_input = st.text_input("BIN (optional)", placeholder="überschreibt Typ", key="bin_opt")
    col_m, col_y, col_c = st.columns(3)
    with col_m: month_input = st.text_input("Monat", key="m2")
    with col_y: year_input = st.text_input("Jahr", key="y2")
    with col_c: cvv_input = st.text_input("CVV", key="c2")

    if st.button("Generieren", key="gen2"):
        cards = []
        for _ in range(quantity):
            card = generate_card(
                card_type=card_type,
                provider=provider,
                scenario=scenario,
                bin_prefix=bin_input if bin_input else None,
                month=month_input if month_input else None,
                year=year_input if year_input else None,
                cvv=cvv_input if cvv_input else None
            )
            cards.append(card)
        st.session_state.cards = cards
        st.success(f"{quantity} Karten generiert")
        st.dataframe(pd.DataFrame(cards), use_container_width=True)

    if "cards" in st.session_state and st.button("Live-Check simulieren", key="check2"):
        results = []
        progress = st.progress(0)
        for i, card in enumerate(st.session_state.cards):
            check = simulate_check(card)
            results.append({**card, **check})
            progress.progress((i + 1) / len(st.session_state.cards))
        df = pd.DataFrame(results)
        st.dataframe(df[["Provider", "Typ", "CC-Nummer", "Ablaufdatum", "CVV", "status", "Nachricht"]], use_container_width=True)
        st.download_button("CSV", df.to_csv(index=False).encode(), "check_results.csv", "text/csv")

# ========================================
# TAB 3: BIN suchen
# ========================================
with tab3:
    st.subheader("BIN-Informationen")
    bin_search = st.text_input("BIN suchen", placeholder="z.B. 411111", key="bin_search")
    if st.button("Suchen", key="search"):
        if bin_search:
            with st.spinner("Suche..."):
                info = search_bin(bin_search)
                st.json(info)
        else:
            st.warning("BIN eingeben")

# ========================================
# SIDEBAR
# ========================================
with st.sidebar:
    st.header("Info")
    st.markdown("""
    - **Nur Testdaten!**
    - Luhn-Check wird angewendet
    - BIN-Suche: [binlist.net](https://binlist.net)
    """)
    st.markdown("### Echte Tests:")
    st.markdown("""
    - [Stripe](https://docs.stripe.com/testing)  
    - [PayPal Sandbox](https://developer.paypal.com)
    """)
    st.caption("Legal & sicher")
