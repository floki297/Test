import streamlit as st
import random, pandas as pd, time

# --- KONFIG ---
CARD_TYPES = {
    "Visa": (["4"], 16), "MasterCard": (["51","52","53","54","55"], 16),
    "American Express": (["34","37"], 15), "Discover": (["6011","65"], 16),
    "Diners Club": (["30","36","38"], 14), "JCB": (["3528","3529"], 16)
}
STRIPE_CARDS = {"Erfolgreich": "4242424242424242", "Abgelehnt": "4000000000000002", "Unzureichend": "4000000000009995"}
PAYPAL_CARDS = {"Erfolgreich": "4532015112830366", "Abgelehnt": "4032039944505422"}

def luhn(cc): 
    d = [int(x) for x in cc]; 
    for i in range(len(d)-2, -1, -2): d[i] = d[i]*2 if d[i] <= 4 else d[i]*2-9
    return cc[:-1] + str((10 - sum(d)%10)%10)

def gen_card(typ="Visa", prov="Sim", scen="Erfolgreich", bin=None, mon=None, jahr=None, cvv=None):
    if prov in ["Stripe","PayPal"]:
        cc = (STRIPE_CARDS if prov=="Stripe" else PAYPAL_CARDS).get(scen, STRIPE_CARDS["Erfolgreich"])
    else:
        pref, length = CARD_TYPES[typ]
        start = bin or random.choice(pref) + "".join(str(random.randint(0,9)) for _ in range(6-len(random.choice(pref))))
        cc = start + "".join(str(random.randint(0,9)) for _ in range(length - len(start) - 1)) + "0"
        cc = luhn(cc)
    mon = f"{int(mon):02d}" if mon and 1<=int(mon)<=12 else f"{random.randint(1,12):02d}"
    jahr = jahr if jahr and 2026<=int(jahr)<=2030 else str(random.randint(2026,2030))
    cvv_len = 4 if typ=="American Express" else 3
    cvv = cvv if cvv and len(str(cvv))==cvv_len else "".join(str(random.randint(0,9)) for _ in range(cvv_len))
    return {"Typ":typ, "Provider":prov, "CC":cc, "MM/YY":f"{mon}/{jahr}", "CVV":cvv}

def sim_check(card):
    time.sleep(0.3)
    opts = {"Stripe": [("succeeded",60),("card_declined",40)],
            "PayPal": [("approved",70),("declined",30)],
            "Sim": [("live",60),("dead",40)]}[card["Provider"]]
    status = random.choices([s for s,_ in opts], [w for _,w in opts])[0]
    return {"status":status, "msg": {"succeeded":"OK","approved":"OK","live":"Live","card_declined":"Abgelehnt","declined":"Abgelehnt","dead":"Tot"}[status]}

# --- UI ---
st.set_page_config("CC Test Tool", layout="wide")
st.title("Test-CC Generator + Sim-Check")
st.caption("Nur für Entwicklung! Keine echte Prüfung.")

c1, c2, c3, c4 = st.columns(4)
with c1: prov = st.selectbox("Provider", ["Simulation","Stripe","PayPal"])
with c2: typ = st.selectbox("Typ", list(CARD_TYPES))
with c3: 
    if prov!="Simulation": scen = st.selectbox("Szenario", STRIPE_CARDS.keys() if prov=="Stripe" else PAYPAL_CARDS.keys())
    else: scen = "Live"
with c4: qty = st.number_input("Anzahl",1,50,1)

mon = st.text_input("Monat (01-12)", "")
jahr = st.text_input("Jahr", "")
cvv = st.text_input("CVV", "")

if st.button("Generieren"):
    cards = [gen_card(typ, prov, scen, None, mon or None, jahr or None, cvv or None) for _ in range(qty)]
    st.session_state.cards = cards
    st.success(f"{qty} Karten generiert")
    st.dataframe(pd.DataFrame(cards), use_container_width=True)

if "cards" in st.session_state and st.button("Check simulieren", type="primary"):
    st.info("Simuliere API...")
    res = []
    bar = st.progress(0)
    for i, c in enumerate(st.session_state.cards):
        chk = sim_check(c); chk.update(c); res.append(chk)
        bar.progress((i+1)/len(c))
    df = pd.DataFrame(res)[["Provider","Typ","CC","MM/YY","CVV","status","msg"]]
    st.success("Fertig!")
    st.dataframe(df, use_container_width=True)
    st.download_button("CSV", df.to_csv(index=False).encode(), "cc_check.csv", "text/csv")

# --- Sidebar ---
with st.sidebar:
    st.header("Legal testen")
    st.markdown("""
    **Stripe:** [docs.stripe.com/testing](https://docs.stripe.com/testing)  
    **PayPal:** [developer.paypal.com](https://developer.paypal.com)  
    → Nutze **deine** Test-Keys in Sandbox!
    """)
    st.caption("Kompakt & sicher")
