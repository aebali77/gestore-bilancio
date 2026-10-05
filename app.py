import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta

# --- CONNESSIONE A SUPABASE ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- FUNZIONI DATI SUPABASE ---
def carica_impostazioni():
    res = supabase.table("impostazioni").select("*").execute()
    dati = {row['chiave']: row['valore'] for row in res.data}
    return {
        "budget_manuale": float(dati.get("budget_manuale", 0.0)),
        "tipi_pagamento": dati.get("tipi_pagamento", ["Cibo", "Trasporti", "Stipendio", "Svago", "Bollette"]),
        "metodi_pagamento": dati.get("metodi_pagamento", ["Contanti", "Carta di Credito", "Bonifico", "PayPal"])
    }

def salva_impostazione(chiave, valore):
    supabase.table("impostazioni").upsert({"chiave": chiave, "valore": valore}).execute()

def carica_transazioni():
    res = supabase.table("transazioni").select("*").order("data", desc=False).execute()
    return res.data

def salva_transazione(nome, tipo, metodo, importo, categoria):
    nuova = {
        "nome": nome,
        "tipo": tipo,
        "metodo": metodo,
        "importo": importo,
        "categoria": categoria,
        "data": datetime.now().isoformat()
    }
    supabase.table("transazioni").insert(nuova).execute()

# Configurazione Pagina
st.set_page_config(page_title="Gestione Bilancio", page_icon="💰", layout="centered")
st.title("💰 Gestore Bilancio Personale")

# Caricamento dati
impostazioni = carica_impostazioni()
transazioni = carica_transazioni()

# --- CALCOLO BILANCIO ---
totale_entrate = sum(float(t['importo']) for t in transazioni if t['categoria'] == 'Entrata')
totale_spese = sum(float(t['importo']) for t in transazioni if t['categoria'] == 'Spesa')
bilancio_effettivo = impostazioni['budget_manuale'] + totale_entrate - totale_spese

st.metric(
    label="Bilancio Attuale (Euro)",
    value=f"€ {bilancio_effettivo:,.2f}",
    delta=f"Budget Iniziale: € {impostazioni['budget_manuale']:,.2f}"
)

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Aggiungi Transazione", 
    "📊 Analisi Mese & Storico", 
    "⚙️ Modifica Budget", 
    "🏷️ Gestione Liste"
])

# ----------------------------------------------------
# TAB 1: AGGIUNGI SPESA / ENTRATA
# ----------------------------------------------------
with tab1:
    col_spesa, col_entrata = st.columns(2)

    # --- SPESE ---
    with col_spesa:
        st.subheader("🔴 Aggiungi Spesa")
        spese = [t for t in transazioni if t['categoria'] == 'Spesa']
        st.caption("📋 Ultime 5 spese inserite:")
        if spese:
            df_spese = pd.DataFrame(spese[-5:][::-1])[['nome', 'tipo', 'metodo', 'importo']]
            df_spese['importo'] = df_spese['importo'].apply(lambda x: f"€ {float(x):.2f}")
            st.table(df_spese)
        else:
            st.info("Nessuna spesa registrata.")

        with st.form("form_spesa", clear_on_submit=True):
            nome_s = st.text_input("Nome Spesa")
            tipo_s = st.selectbox("Tipo Pagamento", impostazioni['tipi_pagamento'], key="t_s")
            metodo_s = st.selectbox("Metodo di Pagamento", impostazioni['metodi_pagamento'], key="m_s")
            importo_s = st.number_input("Importo (€)", min_value=0.01, step=0.50, key="i_s")
            submit_s = st.form_submit_button("Salva Spesa")

            if submit_s:
                if nome_s.strip():
                    salva_transazione(nome_s, tipo_s, metodo_s, importo_s, "Spesa")
                    st.success(f"Spesa '{nome_s}' salvata!")
                    st.rerun()
                else:
                    st.error("Inserisci un nome valido!")

    # --- ENTRATE ---
    with col_entrata:
        st.subheader("🟢 Aggiungi Entrata")
        entrate = [t for t in transazioni if t['categoria'] == 'Entrata']
        st.caption("📋 Ultime 5 entrate inserite:")
        if entrate:
            df_entrate = pd.DataFrame(entrate[-5:][::-1])[['nome', 'tipo', 'metodo', 'importo']]
            df_entrate['importo'] = df_entrate['importo'].apply(lambda x: f"€ {float(x):.2f}")
            st.table(df_entrate)
        else:
            st.info("Nessuna entrata registrata.")

        with st.form("form_entrata", clear_on_submit=True):
            nome_e = st.text_input("Nome Entrata")
            tipo_e = st.selectbox("Tipo Pagamento", impostazioni['tipi_pagamento'], key="t_e")
            metodo_e = st.selectbox("Metodo di Pagamento", impostazioni['metodi_pagamento'], key="m_e")
            importo_e = st.number_input("Importo (€)", min_value=0.01, step=0.50, key="i_e")
            submit_e = st.form_submit_button("Salva Entrata")

            if submit_e:
                if nome_e.strip():
                    salva_transazione(nome_e, tipo_e, metodo_e, importo_e, "Entrata")
                    st.success(f"Entrata '{nome_e}' salvata!")
                    st.rerun()
                else:
                    st.error("Inserisci un nome valido!")

# ----------------------------------------------------
# TAB 2: VISTE E REPORT MENSILI
# ----------------------------------------------------
with tab2:
    st.header("📊 Resoconto e Statistiche")
    limite_mese = datetime.now() - timedelta(days=30)

    if transazioni:
        df_all = pd.DataFrame(transazioni)
        df_all['datetime'] = pd.to_datetime(df_all['data'])
        df_all['importo'] = df_all['importo'].astype(float)
        
        df_ultimo_mese = df_all[df_all['datetime'].dt.tz_localize(None) >= limite_mese]

        # Spese Ultimo Mese
        st.subheader("🔴 Spese Ultimo Mese")
        spese_mese = df_ultimo_mese[df_ultimo_mese['categoria'] == 'Spesa']
        totale_spese_mese = spese_mese['importo'].sum() if not spese_mese.empty else 0.0
        st.metric("Totale Spese Ultimo Mese", f"€ {totale_spese_mese:,.2f}")
        if not spese_mese.empty:
            st.dataframe(spese_mese[['data', 'nome', 'tipo', 'metodo', 'importo']], use_container_width=True)

        st.markdown("---")

        # Entrate Ultimo Mese
        st.subheader("🟢 Entrate Ultimo Mese")
        entrate_mese = df_ultimo_mese[df_ultimo_mese['categoria'] == 'Entrata']
        totale_entrate_mese = entrate_mese['importo'].sum() if not entrate_mese.empty else 0.0
        st.metric("Totale Entrate Ultimo Mese", f"€ {totale_entrate_mese:,.2f}")
        if not entrate_mese.empty:
            st.dataframe(entrate_mese[['data', 'nome', 'tipo', 'metodo', 'importo']], use_container_width=True)

        st.markdown("---")

        # Mostra Tutto
        st.subheader("📑 Mostra Tutto")
        st.dataframe(df_all[['data', 'categoria', 'nome', 'tipo', 'metodo', 'importo']], use_container_width=True)
    else:
        st.info("Nessuna transazione nel database.")

# ----------------------------------------------------
# TAB 3: MODIFICA BUDGET MANUALE
# ----------------------------------------------------
with tab3:
    st.header("⚙️ Modifica Budget Manuale")
    nuovo_budget = st.number_input("Nuovo Budget Iniziale (€)", value=impostazioni['budget_manuale'], step=10.0)
    if st.button("Aggiorna Budget"):
        salva_impostazione("budget_manuale", nuovo_budget)
        st.success("Budget aggiornato con successo!")
        st.rerun()

# ----------------------------------------------------
# TAB 4: MODIFICA LISTE
# ----------------------------------------------------
with tab4:
    st.header("🏷️️ Personalizza Liste")
    col_t, col_m = st.columns(2)

    with col_t:
        st.subheader("Tipi di Pagamento")
        st.write("Attuali:", impostazioni['tipi_pagamento'])
        n_tipo = st.text_input("Aggiungi Tipo")
        if st.button("Aggiungi Tipo"):
            if n_tipo.strip() and n_tipo not in impostazioni['tipi_pagamento']:
                nuova_lista = impostazioni['tipi_pagamento'] + [n_tipo.strip()]
                salva_impostazione("tipi_pagamento", nuova_lista)
                st.rerun()

    with col_m:
        st.subheader("Metodi di Pagamento")
        st.write("Attuali:", impostazioni['metodi_pagamento'])
        n_metodo = st.text_input("Aggiungi Metodo")
        if st.button("Aggiungi Metodo"):
            if n_metodo.strip() and n_metodo not in impostazioni['metodi_pagamento']:
                nuova_lista = impostazioni['metodi_pagamento'] + [n_metodo.strip()]
                salva_impostazione("metodi_pagamento", nuova_lista)
                st.rerun()
