import streamlit as st
import random
import pandas as pd

# Dictionary mit Karten-Typen und ihren BIN-Prefix-Ranges
CARD_TYPES = {
    "Visa": {"prefixes": ["4"], "length": 16},
    "MasterCard": {"prefixes": ["51", "52", "53", "54", "55", "2221", "2222", "2223", "2224", "2225", "2226", "2227", "2228", "2229", 
                                "223", "224", "225", "226", "227", "228", "229", 
                                "23", "24", "25", "26", "270", "271", "2720"], "length": 16},  # Erweiterte Ranges
    "American Express": {"prefixes": ["34", "37"], "length": 15},
    "Discover": {"prefixes": ["6011", "65", "644", "645", "646", "647", "648", "649", 
                              "622126", "622127", "622128", "622129", "62213", "62214", "62215", "62216", "62217", "62218", "62219", 
                              "6222", "6223", "6224", "6225", "6226", "6227", "6228", "62290", "62291", "622920", "622921", "622922", "622923", "622924", "622925"], "length": 16},
    "Diners Club": {"prefixes": ["300", "301", "302", "303", "304", "305", "36", "38"], "length": 14},  # Oft 14, aber variabel
    "JCB": {"prefixes": ["3528", "3529", "353", "354", "355", "356", "357", "358"], "length": 16}
}

def generate_test_cc(card_type="Visa", bin_prefix=None, exp_month=None, exp_year=None, cvv=None):
    # Wenn BIN angegeben, überschreibe Typ und verwende es
    if bin_prefix:
        if len(bin_prefix) != 6 or not bin_prefix.isdigit():
            raise ValueError("BIN muss genau 6 Ziffern sein.")
        cc_start = bin_prefix
        cc_length = 16  # Default, da benutzerdefinierte BIN
    else:
        # Wähle Typ-spezifische BIN
        if card_type not in CARD_TYPES:
            raise ValueError("Ungültiger Karten-Typ.")
        type_info = CARD_TYPES[card_type]
        prefix = random.choice(type_info["prefixes"])
        # Ergänze zu 6-stelliger BIN
        bin_length = len(prefix)
        cc_start = prefix + ''.join(str(random.randint(0, 9)) for _ in range(6 - bin_length))
        cc_length = type_info["length"]

    # Generiere restliche Ziffern (bis zur Länge -1, da Checksum kommt)
    remaining_length = cc_length - len(cc_start) - 1
    remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(remaining_length + 1))  # +1 für temporären letzten Digit
    cc_number = cc_start + remaining_digits

    # Luhn-Algorithmus
    digits = [int(d) for d in cc_number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    checksum = (10 - sum(digits) % 10) % 10
    cc_number = cc_number[:-1] + str(checksum)

    # Monat
    if exp_month:
        month = f"{int(exp_month):02d}"
        if not (1 <= int(month) <= 12):
            raise ValueError("Monat muss zwischen 01 und 12 sein.")
    else:
        month = f"{random.randint(1, 12):02d}"

    # Jahr (zukünftig)
    if exp_year:
        year = str(exp_year)
        if not (2026 <= int(year) <= 2030):
            raise ValueError("Jahr sollte 2026–2030 sein.")
    else:
        year = str(random.randint(2026, 2030))

    # CVV (3 oder 4 für Amex)
    cvv_length = 4 if card_type == "American Express" else 3
    if cvv:
        cvv_str = str(cvv)
        if len(cvv_str) != cvv_length or not cvv_str.isdigit():
            raise ValueError(f"CVV muss genau {cvv_length} Ziffern sein für {card_type}.")
    else:
        cvv_str = ''.join(str(random.randint(0, 9)) for _ in range(cvv_length))

    return {
        'Typ': card_type,
        'CC-Nummer': cc_number,
        'Monat': month,
        'Jahr': year,
        'CVV': cvv_str,
        'Ablaufdatum': f"{month}/{year}"
    }

# === Streamlit App ===
st.set_page_config(page_title="Test-CC Generator", layout="wide")
st.title("🪪 Erweiterter Test-Kreditkarten Generator")
st.warning("⚠️ Nur für Testzwecke! Fiktive Daten – nicht für echte Transaktionen verwenden!")

# --- Eingaben ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Karten-Typ")
    card_type = st.selectbox("Wähle Typ", options=list(CARD_TYPES.keys()), index=0)

with col2:
    st.subheader("Optionale Vorgaben")
    bin_prefix = st.text_input("BIN (6 Ziffern, überschreibt Typ)", placeholder="z.B. 411111")
    exp_month = st.text_input("Monat (01-12)", placeholder="z.B. 12")
    exp_year = st.text_input("Jahr", placeholder="z.B. 2028")
    cvv_input = st.text_input("CVV (3/4 Ziffern)", placeholder="z.B. 123")

with col3:
    st.subheader("Menge")
    quantity = st.number_input("Anzahl der Karten", min_value=1, max_value=100, value=1, step=1)

# --- Generieren ---
if st.button("Generieren", type="primary"):
    try:
        bin_val = bin_prefix.strip() if bin_prefix.strip() else None
        month_val = exp_month.strip() if exp_month.strip() else None
        year_val = exp_year.strip() if exp_year.strip() else None
        cvv_val = cvv_input.strip() if cvv_input.strip() else None

        results = []
        for _ in range(quantity):
            card = generate_test_cc(card_type, bin_val, month_val, year_val, cvv_val)
            results.append(card)

        df = pd.DataFrame(results)

        st.success(f"{quantity} Testkarte(n) des Typs {card_type} generiert!")
        st.dataframe(df, use_container_width=True)

        # Kopier-Button für alle Nummern
        all_cc = "\n".join(df['CC-Nummer'])
        st.code(all_cc, language="text")

        # CSV Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Als CSV herunterladen",
            data=csv,
            file_name=f"test_cc_{card_type}_{quantity}.csv",
            mime="text/csv"
        )

    except ValueError as e:
        st.error(f"❌ Fehler: {e}")

# --- Sidebar ---
with st.sidebar:
    st.header("Hinweise")
    st.info("""
    - Wähle Typ für automatische BIN.
    - Eigene BIN überschreibt Typ.
    - Amex: 15 Ziffern, CVV 4-stellig.
    - Luhn-Check für Gültigkeit.
    - Nur für Tests!
    """)
    st.markdown("---")
    st.caption("Erweitert mit mehr Typen ❤️")    # Generiere restliche Ziffern (bis zur Länge -1, da Checksum kommt)
    remaining_length = cc_length - len(cc_start) - 1
    remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(remaining_length + 1))  # +1 für temporären letzten Digit
    cc_number = cc_start + remaining_digits

    # Luhn-Algorithmus
    digits = [int(d) for d in cc_number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    checksum = (10 - sum(digits) % 10) % 10
    cc_number = cc_number[:-1] + str(checksum)

    # Monat
    if exp_month:
        month = f"{int(exp_month):02d}"
        if not (1 <= int(month) <= 12):
            raise ValueError("Monat muss zwischen 01 und 12 sein.")
    else:
        month = f"{random.randint(1, 12):02d}"

    # Jahr (zukünftig)
    if exp_year:
        year = str(exp_year)
        if not (2026 <= int(year) <= 2030):
            raise ValueError("Jahr sollte 2026–2030 sein.")
    else:
        year = str(random.randint(2026, 2030))

    # CVV (3 oder 4 für Amex)
    cvv_length = 4 if card_type == "American Express" else 3
    if cvv:
        cvv_str = str(cvv)
        if len(cvv_str) != cvv_length or not cvv_str.isdigit():
            raise ValueError(f"CVV muss genau {cvv_length} Ziffern sein für {card_type}.")
    else:
        cvv_str = ''.join(str(random.randint(0, 9)) for _ in range(cvv_length))

    return {
        'Typ': card_type,
        'CC-Nummer': cc_number,
        'Monat': month,
        'Jahr': year,
        'CVV': cvv_str,
        'Ablaufdatum': f"{month}/{year}"
    }

# === Streamlit App ===
st.set_page_config(page_title="Test-CC Generator", layout="wide")
st.title("🪪 Erweiterter Test-Kreditkarten Generator")
st.warning("⚠️ Nur für Testzwecke! Fiktive Daten – nicht für echte Transaktionen verwenden!")

# --- Eingaben ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Karten-Typ")
    card_type = st.selectbox("Wähle Typ", options=list(CARD_TYPES.keys()), index=0)

with col2:
    st.subheader("Optionale Vorgaben")
    bin_prefix = st.text_input("BIN (6 Ziffern, überschreibt Typ)", placeholder="z.B. 411111")
    exp_month = st.text_input("Monat (01-12)", placeholder="z.B. 12")
    exp_year = st.text_input("Jahr", placeholder="z.B. 2028")
    cvv_input = st.text_input("CVV (3/4 Ziffern)", placeholder="z.B. 123")

with col3:
    st.subheader("Menge")
    quantity = st.number_input("Anzahl der Karten", min_value=1, max_value=100, value=1, step=1)

# --- Generieren ---
if st.button("Generieren", type="primary"):
    try:
        bin_val = bin_prefix.strip() if bin_prefix.strip() else None
        month_val = exp_month.strip() if exp_month.strip() else None
        year_val = exp_year.strip() if exp_year.strip() else None
        cvv_val = cvv_input.strip() if cvv_input.strip() else None

        results = []
        for _ in range(quantity):
            card = generate_test_cc(card_type, bin_val, month_val, year_val, cvv_val)
            results.append(card)

        df = pd.DataFrame(results)

        st.success(f"{quantity} Testkarte(n) des Typs {card_type} generiert!")
        st.dataframe(df, use_container_width=True)

        # Kopier-Button für alle Nummern
        all_cc = "\n".join(df['CC-Nummer'])
        st.code(all_cc, language="text")

        # CSV Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Als CSV herunterladen",
            data=csv,
            file_name=f"test_cc_{card_type}_{quantity}.csv",
            mime="text/csv"
        )

    except ValueError as e:
        st.error(f"❌ Fehler: {e}")

# --- Sidebar ---
with st.sidebar:
    st.header("Hinweise")
    st.info("""
    - Wähle Typ für automatische BIN.
    - Eigene BIN überschreibt Typ.
    - Amex:
with col1:
    st.subheader("Optionale Eingaben")
    bin_prefix = st.text_input("BIN (6 Ziffern, optional)", placeholder="z.B. 411111")
    
with col2:
    exp_month = st.text_input("Monat (01-12, optional)", placeholder="z.B. 05")
    exp_year = st.text_input("Jahr (z.B. 2028, optional)", placeholder="z.B. 2028")
    cvv_input = st.text_input("CVV (3 Ziffern, optional)", placeholder="z.B. 123")

# Generier-Button
if st.button("Generieren", type="primary"):
    try:
        # Leere Felder als None behandeln
        bin_val = bin_prefix.strip() if bin_prefix.strip() else None
        month_val = exp_month.strip() if exp_month.strip() else None
        year_val = exp_year.strip() if exp_year.strip() else None
        cvv_val = cvv_input.strip() if cvv_input.strip() else None
        
        test_data = generate_test_cc(bin_val, month_val, year_val, cvv_val)
        
        st.success("✅ Generierte Testdaten:")
        st.markdown(f"**CC-Nummer:** {test_data['cc_number']}")
        st.markdown(f"**Ablaufdatum:** {test_data['month']}/{test_data['year']}")
        st.markdown(f"**CVV:** {test_data['cvv']}")
        
        # Kopier-Button für CC-Nummer
        st.code(test_data['cc_number'], language="text")
        
    except ValueError as e:
        st.error(f"❌ Fehler: {e}")

# Sidebar mit Infos
with st.sidebar:
    st.header("Hinweise")
    st.info("""
    - Lass Felder leer für Zufallswerte.
    - Die CC-Nummer erfüllt den Luhn-Check (gültig aussehend).
    - Für Hosting: [Streamlit Cloud Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started)
    """)
