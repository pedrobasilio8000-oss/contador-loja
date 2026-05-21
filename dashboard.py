import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(
    page_title="Contador de Visitantes",
    page_icon="🏪",
    layout="wide"
)

st.title("🏪 Dashboard - Contador de Visitantes")

ID_PLANILHA = "1W_7Won4bMFdtFxm6gVsPcbO-9mcuXqutD9KdTmJrXD8"

@st.cache_data(ttl=30)
def carregar_dados():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(ID_PLANILHA).sheet1
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)
    return df

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao conectar ao Google Sheets: {e}")
    st.stop()

if df.empty:
    st.warning("Nenhum dado encontrado na planilha!")
    st.stop()

df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")
df["Hora_dt"] = pd.to_datetime(df["Hora"], format="%H:%M:%S")
df["Hora_int"] = df["Hora_dt"].dt.hour

st.sidebar.header("Filtros")
datas = df["Data"].dt.date.unique()
data_selecionada = st.sidebar.selectbox(
    "Selecione a data:",
    sorted(datas, reverse=True),
    format_func=lambda x: x.strftime("%d/%m/%Y")
)

if st.sidebar.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.rerun()

df_filtrado = df[df["Data"].dt.date == data_selecionada]
total_passagens = len(df_filtrado)
total_visitantes = total_passagens // 2

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Passagens", total_passagens)
col2.metric("Visitantes Estimados", total_visitantes)
col3.metric("Horário de Pico",
    f"{df_filtrado.groupby('Hora_int').size().idxmax()}h" if not df_filtrado.empty else "-")
col4.metric("Turno com Mais Movimento",
    df_filtrado["Turno"].value_counts().idxmax() if not df_filtrado.empty else "-")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Visitantes por Hora")
    por_hora = df_filtrado.groupby("Hora_int").size().reset_index(name="Passagens")
    por_hora["Visitantes"] = por_hora["Passagens"] // 2
    fig1 = px.bar(por_hora, x="Hora_int", y="Visitantes",
                  labels={"Hora_int": "Hora do Dia", "Visitantes": "Visitantes"},
                  color="Visitantes", color_continuous_scale="blues")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.subheader("Visitantes por Turno")
    por_turno = df_filtrado.groupby("Turno").size().reset_index(name="Passagens")
    por_turno["Visitantes"] = por_turno["Passagens"] // 2
    fig2 = px.pie(por_turno, values="Visitantes", names="Turno",
                  color_discrete_sequence=px.colors.sequential.Blues_r)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Visitantes por Dia da Semana")
por_dia = df.groupby("Dia da Semana").size().reset_index(name="Passagens")
por_dia["Visitantes"] = por_dia["Passagens"] // 2
ordem = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
por_dia["Dia da Semana"] = pd.Categorical(por_dia["Dia da Semana"], categories=ordem, ordered=True)
por_dia = por_dia.sort_values("Dia da Semana")
fig3 = px.bar(por_dia, x="Dia da Semana", y="Visitantes",
              color="Visitantes", color_continuous_scale="blues")
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Registro Detalhado")
df_show = df_filtrado[["Data", "Hora", "Dia da Semana", "Turno", "ID Visitante"]].copy()
df_show["Data"] = df_show["Data"].dt.strftime("%d/%m/%Y")
st.dataframe(df_show, use_container_width=True)

st.caption(f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Dados atualizados a cada 30 segundos")