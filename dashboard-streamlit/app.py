# app.py — FarmTech Solutions (Fase 3)
# Dashboard com diagnóstico de caminho, upload de CSV, gráficos e sugestões de irrigação

import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

# ======= CONFIG INICIAL =======
st.set_page_config(page_title='FarmTech Dashboard', layout='wide')
st.title('🌱 FarmTech Solutions — Dashboard Fase 3')

# ======= DIAGNÓSTICO + UPLOAD (garante que o CSV seja encontrado) =======
BASE = Path(__file__).resolve().parents[1]      # ...\FarmTech-Fase3
DATA_DIR = BASE / 'dados'                        # ...\FarmTech-Fase3\dados
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = DATA_DIR / 'sensores_fase2.csv'      # nome esperado

st.caption(f"📂 Procurando em: {DATA_PATH}")
st.caption(f"📁 Conteúdo da pasta dados: {[p.name for p in DATA_DIR.glob('*')]}")

# Se não existir, permite enviar o arquivo e salva no lugar certo
if not DATA_PATH.exists():
    up = st.file_uploader("Envie aqui o seu **sensores_fase2.csv**", type=['csv'])
    if up is not None:
        DATA_PATH.write_bytes(up.read())
        st.success("✅ Arquivo salvo em /dados! Clique em **R** (Rerun) no canto direito.")
        st.stop()
    st.error('❌ Arquivo não encontrado. Coloque **sensores_fase2.csv** em **/dados** e recarregue.')
    st.stop()

# ======= LEITURA ROBUSTA DO CSV (; ou ,) =======
def read_csv_flex(path: Path) -> pd.DataFrame:
    # 1) tenta com ; (formato BR)
    try:
        df_try = pd.read_csv(path, sep=';', encoding='utf-8', engine='python')
        if df_try.shape[1] > 1:
            return df_try
    except Exception:
        pass
    # 2) fallback com vírgula
    return pd.read_csv(path, sep=',', encoding='utf-8', engine='python')

df = read_csv_flex(DATA_PATH)

# ======= NORMALIZA NOMES DE COLUNAS =======
colmap = {
    'data_coleta': 'DATA_COLETA', 'hora_coleta': 'HORA_COLETA',
    'umidade_solo': 'UMIDADE_SOLO', 'ph_solo': 'PH_SOLO',
    'nitrogenio_n': 'NITROGENIO_N', 'fosforo_p': 'FOSFORO_P',
    'potassio_k': 'POTASSIO_K', 'chuva_mm': 'CHUVA_MM', 'temp_c': 'TEMP_C',
    'status_irrigacao': 'STATUS_IRRIGACAO'
}
df.columns = [colmap.get(c.lower(), c.upper()) for c in df.columns]

# Converte data (se existir)
if 'DATA_COLETA' in df.columns:
    df['DATA_COLETA'] = pd.to_datetime(df['DATA_COLETA'], errors='coerce')

# ======= FILTROS LATERAIS =======
st.sidebar.header('Filtros')
if 'DATA_COLETA' in df.columns and df['DATA_COLETA'].notna().any():
    dmin, dmax = df['DATA_COLETA'].min(), df['DATA_COLETA'].max()
    intervalo = st.sidebar.date_input('Período', [dmin.date(), dmax.date()])
    if isinstance(intervalo, list) and len(intervalo) == 2:
        df = df[
            (df['DATA_COLETA'] >= pd.to_datetime(intervalo[0])) &
            (df['DATA_COLETA'] <= pd.to_datetime(intervalo[1]))
        ]

vars_all = [c for c in ['UMIDADE_SOLO','PH_SOLO','FOSFORO_P','POTASSIO_K','NITROGENIO_N','CHUVA_MM','TEMP_C'] if c in df.columns]
vars_default = [c for c in ['UMIDADE_SOLO','PH_SOLO','FOSFORO_P','POTASSIO_K'] if c in df.columns]
vars_to_show = st.sidebar.multiselect('Variáveis para gráfico', vars_all, default=vars_default if vars_default else vars_all)

# ======= KPIs =======
c1, c2, c3, c4 = st.columns(4)
if 'UMIDADE_SOLO' in df: c1.metric('Umidade média (%)', f"{df['UMIDADE_SOLO'].mean():.1f}")
if 'PH_SOLO' in df:      c2.metric('pH médio', f"{df['PH_SOLO'].mean():.2f}")
if 'TEMP_C' in df:       c3.metric('Temp. média (°C)', f"{df['TEMP_C'].mean():.1f}")
if 'CHUVA_MM' in df:     c4.metric('Chuva média (mm)', f"{df['CHUVA_MM'].mean():.1f}")

# ======= GRÁFICOS DE LINHA =======
if 'DATA_COLETA' in df.columns and len(vars_to_show) > 0:
    df_line = df.sort_values('DATA_COLETA')
    for v in vars_to_show:
        if v in df_line.columns:
            st.plotly_chart(
                px.line(df_line, x='DATA_COLETA', y=v, title=f'{v} ao longo do tempo'),
                use_container_width=True
            )

# ======= DISTRIBUIÇÃO DE STATUS (se existir) =======
if 'STATUS_IRRIGACAO' in df.columns:
    st.subheader('Distribuição do Status de Irrigação')
    dist = df['STATUS_IRRIGACAO'].value_counts().reset_index()
    dist.columns = ['STATUS_IRRIGACAO', 'QTD']
    st.plotly_chart(px.bar(dist, x='STATUS_IRRIGACAO', y='QTD'), use_container_width=True)

# ======= REGRAS SIMPLES DE RECOMENDAÇÃO =======
st.subheader('Sugestão de Irrigação (regras simples)')
UMID_OK, UMID_BAIXA, TEMP_ALTA, CHUVA_LIMIAR = 40, 30, 32, 3

def sugere(r):
    chuva = r.get('CHUVA_MM', 0) or 0
    umid  = r.get('UMIDADE_SOLO', 0) or 0
    temp  = r.get('TEMP_C', 0) or 0
    if chuva >= CHUVA_LIMIAR: return 'NAO_IRRIGAR'
    if umid >= UMID_OK:       return 'NAO_IRRIGAR'
    if temp >= TEMP_ALTA and umid < UMID_BAIXA: return 'IRRIGAR_FORTE'
    if UMID_BAIXA <= umid < UMID_OK:            return 'IRRIGAR_LEVE'
    return 'IRRIGAR'

if all(c in df.columns for c in ['UMIDADE_SOLO','CHUVA_MM','TEMP_C']):
    df['SUGESTAO'] = df.apply(sugere, axis=1)
    cols = [c for c in ['DATA_COLETA','UMIDADE_SOLO','PH_SOLO','CHUVA_MM','TEMP_C','SUGESTAO'] if c in df.columns]
    st.dataframe(df[cols].head(50), use_container_width=True)
else:
    st.info('ℹ️ Para sugestões, garanta as colunas: **UMIDADE_SOLO**, **CHUVA_MM**, **TEMP_C**.')
