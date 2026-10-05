import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# Nome del file di persistenza dati
DB_FILE = "bilancio_db.json"

# --- FUNZIONI DI GESTIONE DATI (CARICAMENTO E SALVATAGGIO) ---
def carica_dati():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "budget_manuale": 0.0,
        "tipi_pagamento": ["Cibo", "Trasporti", "Stipendio", "Svago", "Bollette"],
        "metodi_pagamento": ["Contanti", "Carta di Credito", "Bonifico", "PayPal"],
        "transazioni": [] # Lista di dizionari: {id, data, nome, tipo, metodo, importo, categoria}
    }

def salva_dati(dati):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)

# Inizializzazione dello stato Streamlit
if "db" not in st.session_state:
    st.session_state.db = carica_dati()

db = st.session_state.db

# Configurazione della pagina
st.set_page_config(page_title="Gestione Bilancio", page_icon="💰", layout="centered")
st.title("💰 Gestore Bilancio Personale")

# --- CALCOLO DEL BILANCIO ---
totale_entrate = sum(t['importo'] for t in db['transazioni'] if t['categoria'] == 'Entrata')
totale_spese = sum(t['importo'] for t in db['transazioni'] if t['categoria'] == 'Spesa')
bilancio_effettivo = db['budget_manuale'] + totale_entrate - totale_spese

# KPI Bilancio
st.metric(
    label="Bilancio Attuale (Euro)",
    value=f"€ {bilancio_effettivo:,.2f}",
    delta=f"Budget Iniziale: € {db['budget_manuale']:,.2f}"
)

st.markdown("---")

# --- NAVIGAZIONE SCHEDE ---
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

    # --- SEZIONE SPESE ---
    with col_spesa:
        st.subheader("🔴 Aggiungi Spesa")
        
        # Ultime 5 spese
        spese = [t for t in db['transazioni'] if t['categoria'] == 'Spesa']
        st.caption("📋 Ultime 5 spese inserite:")
        if spese:
            df_spese = pd.DataFrame(spese[-5:][::-1])[['nome', 'tipo', 'metodo', 'importo']]
            df_spese['importo'] = df_spese['importo'].apply(lambda x: f"€ {x:.2f}")
            st.table(df_spese)
        else:
            st.info("Nessuna spesa registrata.")

        # Form inserimento Spesa
        with st.form("form_spesa", clear_on_submit=True):
            nome_s = st.text_input("Nome Spesa")
            tipo_s = st.selectbox("Tipo Pagamento (Categoria)", db['tipi_pagamento'], key="t_s")
            metodo_s = st.selectbox("Metodo di Pagamento", db['metodi_pagamento'], key="m_s")
            importo_s = st.number_input("Importo (€)", min_value=0.01, step=0.50, key="i_s")
            submit_s = st.form_submit_button("Salva Spesa")

            if submit_s:
                if nome_s.strip():
                    nuova_transazione = {
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "nome": nome_s,
                        "tipo": tipo_s,
                        "metodo": metodo_s,
                        "importo": importo_s,
                        "categoria": "Spesa"
                    }
                    db['transazioni'].append(nuova_transazione)
                    salva_dati(db)
                    st.success(f"Spesa '{nome_s}' salvata!")
                    st.rerun()
                else:
                    st.error("Inserisci un nome valido!")

    # --- SEZIONE ENTRATE ---
    with col_entrata:
        st.subheader("🟢 Aggiungi Entrata")
        
        # Ultime 5 entrate
        entrate = [t for t in db['transazioni'] if t['categoria'] == 'Entrata']
        st.caption("📋 Ultime 5 entrate inserite:")
        if entrate:
            df_entrate = pd.DataFrame(entrate[-5:][::-1])[['nome', 'tipo', 'metodo', 'importo']]
            df_entrate['importo'] = df_entrate['importo'].apply(lambda x: f"€ {x:.2f}")
            st.table(df_entrate)
        else:
            st.info("Nessuna entrata registrata.")

        # Form inserimento Entrata
        with st.form("form_entrata", clear_on_submit=True):
            nome_e = st.text_input("Nome Entrata")
            tipo_e = st.selectbox("Tipo Pagamento (Categoria)", db['tipi_pagamento'], key="t_e")
            metodo_e = st.selectbox("Metodo di Pagamento", db['metodi_pagamento'], key="m_e")
            importo_e = st.number_input("Importo (€)", min_value=0.01, step=0.50, key="i_e")
            submit_e = st.form_submit_button("Salva Entrata")

            if submit_e:
                if nome_e.strip():
                    nuova_transazione = {
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "nome": nome_e,
                        "tipo": tipo_e,
                        "metodo": metodo_e,
                        "importo": importo_e,
                        "categoria": "Entrata"
                    }
                    db['transazioni'].append(nuova_transazione)
                    salva_dati(db)
                    st.success(f"Entrata '{nome_e}' salvata!")
                    st.rerun()
                else:
                    st.error("Inserisci un nome valido!")

# ----------------------------------------------------
# TAB 2: VISTE E REPORT MENSILI
# ----------------------------------------------------
with tab2:
    st.header("📊 Resoconto e Statistiche")
    
    # Calcolo data limite (ultimi 30 giorni)
    limite_mese = datetime.now() - timedelta(days=30)

    # Conversione in DataFrame per facilitare i filtri
    if db['transazioni']:
        df_all = pd.DataFrame(db['transazioni'])
        df_all['datetime'] = pd.to_datetime(df_all['data'])
        
        # Filtro per ultimi 30 giorni
        df_ultimo_mese = df_all[df_all['datetime'] >= limite_mese]

        # 1. Spese Ultimo Mese
        st.subheader("🔴 Spese Ultimo Mese (Ultimi 30 giorni)")
        spese_mese = df_ultimo_mese[df_ultimo_mese['categoria'] == 'Spesa']
        totale_spese_mese = spese_mese['importo'].sum() if not spese_mese.empty else 0.0
        
        st.metric("Totale Spese Ultimo Mese", f"€ {totale_spese_mese:,.2f}")
        if not spese_mese.empty:
            st.dataframe(spese_mese[['data', 'nome', 'tipo', 'metodo', 'importo']], use_container_width=True)
        else:
            st.info("Nessuna spesa negli ultimi 30 giorni.")

        st.markdown("---")

        # 2. Entrate Ultimo Mese
        st.subheader("🟢 Entrate Ultimo Mese (Ultimi 30 giorni)")
        entrate_mese = df_ultimo_mese[df_ultimo_mese['categoria'] == 'Entrata']
        totale_entrate_mese = entrate_mese['importo'].sum() if not entrate_mese.empty else 0.0
        
        st.metric("Totale Entrate Ultimo Mese", f"€ {totale_entrate_mese:,.2f}")
        if not entrate_mese.empty:
            st.dataframe(entrate_mese[['data', 'nome', 'tipo', 'metodo', 'importo']], use_container_width=True)
        else:
            st.info("Nessuna entrata negli ultimi 30 giorni.")

        st.markdown("---")

        # 3. Mostra Tutto
        st.subheader("📑 Mostra Tutto (Storico Completo)")
        st.dataframe(df_all[['data', 'categoria', 'nome', 'tipo', 'metodo', 'importo']], use_container_width=True)
    else:
        st.info("Nessuna transazione presente nel database.")

# ----------------------------------------------------
# TAB 3: MODIFICA BUDGET MANUALE
# ----------------------------------------------------
with tab3:
    st.header("⚙️ Modifica Budget Manuale")
    st.write("Imposta o correggi manualmente il saldo base del tuo conto.")
    
    nuovo_budget = st.number_input(
        "Nuovo Budget Iniziale (€)", 
        value=float(db['budget_manuale']), 
        step=10.0
    )
    
    if st.button("Aggiorna Budget"):
        db['budget_manuale'] = nuovo_budget
        salva_dati(db)
        st.success("Budget aggiornato con successo!")
        st.rerun()

# ----------------------------------------------------
# TAB 4: MODIFICA LISTE TIPO/METODO DI PAGAMENTO
# ----------------------------------------------------
with tab4:
    st.header("🏷️ Personalizza Liste")

    col_tipo, col_metodo = st.columns(2)

    # Gestione Tipi di Pagamento
    with col_tipo:
        st.subheader("Tipo Pagamento")
        st.write("Currenti:", db['tipi_pagamento'])
        
        nuovo_tipo = st.text_input("Aggiungi Tipo (es. Ristorante)")
        if st.button("Aggiungi Tipo"):
            if nuovo_tipo.strip() and nuovo_tipo not in db['tipi_pagamento']:
                db['tipi_pagamento'].append(nuovo_tipo.strip())
                salva_dati(db)
                st.success(f"Aggiunto '{nuovo_tipo}'")
                st.rerun()

        tipo_da_rimuovere = st.selectbox("Rimuovi Tipo", ["-- Seleziona --"] + db['tipi_pagamento'])
        if st.button("Rimuovi Tipo"):
            if tipo_da_rimuovere != "-- Seleziona --":
                db['tipi_pagamento'].remove(tipo_da_rimuovere)
                salva_dati(db)
                st.success(f"Rimosso '{tipo_da_rimuovere}'")
                st.rerun()

    # Gestione Metodi di Pagamento
    with col_metodo:
        st.subheader("Metodo di Pagamento")
        st.write("Currenti:", db['metodi_pagamento'])
        
        nuovo_metodo = st.text_input("Aggiungi Metodo (es. Satispay)")
        if st.button("Aggiungi Metodo"):
            if nuovo_metodo.strip() and nuovo_metodo not in db['metodi_pagamento']:
                db['metodi_pagamento'].append(nuovo_metodo.strip())
                salva_dati(db)
                st.success(f"Aggiunto '{nuovo_metodo}'")
                st.rerun()

        metodo_da_rimuovere = st.selectbox("Rimuovi Metodo", ["-- Seleziona --"] + db['metodi_pagamento'])
        if st.button("Rimuovi Metodo"):
            if metodo_da_rimuovere != "-- Seleziona --":
                db['metodi_pagamento'].remove(metodo_da_rimuovere)
                salva_dati(db)
                st.success(f"Rimosso '{metodo_da_rimuovere}'")
                st.rerun()
