import streamlit as st, random, pandas as pd, time, requests

# --- CONFIG ---
TYPES = {"V":["4"], "M":["51","52","53","54","55"], "A":["34","37"], "D":["6011","65"]}
STRIPE = {"OK":"4242424242424242", "NO":"4000000000000002"}
PAYPAL = {"Si":"4532015112830366", "No":"4032039944505422"}

def luhn(c):d=[*map(int,c)];[setattr(d,i,d[i]*2-9*(d[i]>4))for i in range(len(d)-2,-1,-2)];return c[:-1]+str((10-sum(d)%10)%10)
def gen(t="V",p="Sim",s="OK",b=None,m=None,y=None,c=None):
 if p!="Sim":cc=(STRIPE if p=="Stripe" else PAYPAL).get(s,STRIPE["OK"])
 else:pref=random.choice(TYPES[t]);b=b or pref+"".join(str(random.randint(0,9))for _ in range(6-len(pref)));cc=luhn(b+"0"*(16-len(b)))
 m=f"{int(m):02d}"if m and 1<=int(m)<=12 else f"{random.randint(1,12):02d}"
 y=y if y and 2026<=int(y)<=2030 else str(random.randint(2026,2030))
 cv=c if c and len(str(c))==(4 if t=="A" else 3)else"".join(str(random.randint(0,9))for _ in range(4 if t=="A" else 3))
 return {"T":t,"P":p,"CC":cc,"MM/YY":f"{m}/{y}","CVV":cv}

def chk(card):time.sleep(.2);s=random.choices(["OK","NO"],[7,3])[0];return{"status":s,"msg":"Live"if s=="OK"else"Dead"}

def bin_search(bin_input):
    try:
        resp = requests.get(f"https://binlist.net/json/{bin_input}").json()
        return {
            "BIN": bin_input,
            "Scheme": resp.get("scheme", "N/A"),
            "Type": resp.get("type", "N/A"),
            "Brand": resp.get("brand", "N/A"),
            "Country": resp.get("country", {}).get("name", "N/A"),
            "Bank": resp.get("bank", {}).get("name", "N/A")
        }
    except:
        return {"Error": "BIN-Suche fehlgeschlagen"}

# --- UI ---
st.set_page_config("CC Mini", "wide")
st.title("CC Test + BIN Suche")
c1,c2,c3,c4=st.columns(4)
with c1:p=st.selectbox("Prov",["Sim","Stripe","PayPal"])
with c2:t=st.selectbox("Typ",["V","M","A","D"])
with c3:s=st.selectbox("Szen",STRIPE.keys()if p=="Stripe"else PAYPAL.keys()if p=="PayPal"else["Live"])
with c4:q=st.number_input("Anz",1,50,1)

bin_inp = st.text_input("BIN (6 Ziffern, optional)", "")
m=st.text_input("Monat","");y=st.text_input("Jahr","");cv=st.text_input("CVV","")

if st.button("Generieren"):
 k=[gen(t,p,s,bin_inp or None,m or None,y or None,cv or None)for _ in range(q)]
 st.session_state.k=k;st.success(f"{q} Karten")
 st.dataframe(pd.DataFrame(k),True)

if "k"in st.session_state and st.button("Check",type="primary"):
 st.info("Sim...")
 r=[];b=st.progress(0)
 for i,c in enumerate(st.session_state.k):
  x=chk(c);x.update(c);r.append(x);b.progress((i+1)/q)
 df=pd.DataFrame(r)[["P","T","CC","MM/YY","CVV","status","msg"]]
 st.success("OK");st.dataframe(df,True)
 st.download_button("CSV",df.to_csv(index=False).encode(),"cc.csv","text/csv")

if bin_inp and st.button("BIN suchen"):
    result = bin_search(bin_inp)
    st.json(result)

# --- Sidebar ---
with st.sidebar:
 st.markdown("**Legal testen:**\n- [Stripe Test](https://docs.stripe.com/testing)\n- [PayPal Sandbox](https://developer.paypal.com)")
 st.caption("Mit BIN-Suche via binlist.net")
