import streamlit as st
import random

def generate_test_cc(bin_prefix=None, exp_month=None, exp_year=None, cvv=None):
    # Wenn BIN angegeben, verwenden; sonst zufällig (Visa-ähnlich)
    if bin_prefix:
        if len(bin_prefix) != 6 or not bin_prefix.isdigit():
            raise ValueError("BIN muss genau 6 Ziffern sein.")
        cc_start = bin_prefix
    else:
        cc_start = '4' + ''.join(str(random.randint(0, 9)) for _ in range(5))
    
    # Restliche Ziffern generieren (insgesamt 16)
    remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(10))
    cc_number = cc_start + remaining_digits
    
    # Luhn-Algorithmus anwenden
    digits = [int(d) for d in cc_number]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    checksum = (10 - sum(digits) % 10) % 10
    cc_number = cc_number[:-1] + str(checksum)
    
    # Monat: Angegeben oder zufällig
    if exp_month:
        month = f"{int(exp_month):02d}"
        if not (1 <= int(month) <= 12):
            raise ValueError("Monat muss zwischen 01 und 12 sein.")
    else:
        month = f"{random.randint(1, 12):02d}"
    
    # Jahr: Angegeben oder zufällig (zukünftig, ab 2026)
    if exp_year:
        year = str(exp_year)
        if not (2026 <= int(year) <= 2030):
            raise ValueError("Jahr sollte ein zukünftiges Jahr sein, z.B. 2026-2030.")
    else:
        year = str(random.randint(2026, 2030))
    
    # CVV: Angegeben oder zufällig
    if cvv:
        cvv_str = str(cvv)
        if len(cvv_str) != 3 or not cvv_str.isdigit():
            raise ValueError("CVV muss genau 3 Ziffern sein.")
    else:
        cvv_str = ''.join(str(random.randint(0, 9)) for _ in range(3))
    
    return {
        'cc_number': cc_number,
        'month': month,
        'year': year,
        'cvv': cvv_str
    }

# Streamlit-App
st.title("🪪 Test-CC-Generator")
st.warning("⚠️ Nur für Testzwecke! Fiktive Daten – nicht für echte Transaktionen verwenden!")

# Eingabefelder
col1, col2 = st.columns(2)

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
