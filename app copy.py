import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as pe

st.title("KORA-CLIENTES")
st.subheader("Elaborado con datos de clientes agosto 2025 – septiembre 2026")

pedidos = pd.read_csv("KORA_pedidos.csv", parse_dates=["fecha_pedido"])
clientes = pd.read_csv("KORA_clientes.csv", parse_dates=["fecha_registro"])

compradores_df = pedidos.groupby("id_cliente").agg(
    n_pedidos=("id_pedido", "count"),
    ingreso_total=("ingreso_neto_cop", "sum"),
    fecha_ultimo_pedido=("fecha_pedido", "max")
)
compradores_df["recencia"] = (pd.Timestamp.today() - compradores_df["fecha_ultimo_pedido"]).dt.days

def segmento(n_pedidos, tiempo):
    segmento = ""
    if n_pedidos == 0:
        segmento = "Sin Compra"
    elif n_pedidos == 1 and tiempo <= 90:
        segmento = "Primerizo"
    elif n_pedidos == 2 and tiempo <= 90:
        segmento = "En Desarrollo"
    elif n_pedidos >= 3 and tiempo <= 90:
        segmento = "Fiel"
    elif n_pedidos >= 1 and tiempo > 90:
        segmento = "En Pausa"
    return segmento

final = clientes.merge(compradores_df, how="left", on="id_cliente")
final["n_pedidos"] = final["n_pedidos"].fillna(0).astype(int)
final["ingreso_total"] = final["ingreso_total"].fillna(0)
final["segmento"] = final.apply(lambda fila: segmento(fila["n_pedidos"], fila["recencia"]), axis=1)

st.sidebar.header("FILTROS")
filtro_canal = st.sidebar.multiselect(
    label="CANALES",
    options=final.canal_adquisicion.unique(),
    default=final.canal_adquisicion.unique()
)
filtro_ciudad = st.sidebar.multiselect(
    label="CIUDAD",
    options=final.ciudad.unique(),
    default=final.ciudad.unique()
)
filtro_segmento = st.sidebar.multiselect(
    label="SEGMENTO",
    options=final.segmento.unique(),
    default=final.segmento.unique()
)

final_FILTRADO = final[
    (final.canal_adquisicion.isin(filtro_canal)) &
    (final.ciudad.isin(filtro_ciudad)) &
    (final.segmento.isin(filtro_segmento))
]

numero_compradores = final_FILTRADO.query("n_pedidos > 0").shape[0]
npedidos = final_FILTRADO.n_pedidos.sum()
ingreso = final_FILTRADO.ingreso_total.sum()
recompra = final_FILTRADO.query("n_pedidos > 1").shape[0] / numero_compradores if numero_compradores > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="COMPRADORES", value=numero_compradores, border=True)
col2.metric(label="PEDIDOS", value=npedidos, border=True)
col3.metric(label="INGRESO", value=f"${ingreso:,.0f}", border=True)
col4.metric(label="RECOMPRA", value=f"{recompra:.2%}", border=True)

st.divider()

izquierda, derecha = st.columns(2)

