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
#punto 5 filtro
final_preferencia = st.sidebar.multiselect(
    label= "PREFERENCIA DECLARADA",
    options= final.preferencia_declarada.unique(),
    default= final.preferencia_declarada.unique()
)
final_FILTRADO = final[
    (final.canal_adquisicion.isin(filtro_canal)) &
    (final.ciudad.isin(filtro_ciudad)) &
    (final.segmento.isin(filtro_segmento)) & 
    (final.preferencia_declarada.isin(final_preferencia))
]

numero_compradores = final_FILTRADO.query("n_pedidos > 0").shape[0]
npedidos = final_FILTRADO.n_pedidos.sum()
ingreso = final_FILTRADO.ingreso_total.sum()
if numero_compradores > 0:
    recompra = final_FILTRADO.query("n_pedidos > 1").shape[0] / numero_compradores
else:
    recompra = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric(label="COMPRADORES", value=numero_compradores, border=True)
col2.metric(label="PEDIDOS", value=npedidos, border=True)
col3.metric(label="INGRESO", value=f"${ingreso:,.0f}", border=True)
col4.metric(label="RECOMPRA", value=f"{recompra:.2%}", border=True)

st.divider()

izquierda, derecha = st.columns(2)

with izquierda:
    df_plot = final_FILTRADO.groupby("segmento", as_index=False).agg(
        n_clientes=("id_cliente", "count")
    )
    fig = pe.bar(data_frame=df_plot, x="segmento", y="n_clientes",
                 color="segmento", text="n_clientes")
    fig.update_layout(xaxis_title="Segmento", yaxis_title="Número de Clientes",
                      showlegend=False)
    st.plotly_chart(fig)

with derecha:
    df_plot2 = final_FILTRADO.groupby("preferencia_declarada", as_index=False).agg(
        ingreso=("ingreso_total", "sum")
    )
    df_plot2 = df_plot2.sort_values("ingreso", ascending=False)
    fig2 = pe.bar(data_frame=df_plot2, x="ingreso", y="preferencia_declarada",
                  orientation="h")
    fig2.update_layout(xaxis_title="Ingreso", yaxis_title="Departamento")
    st.plotly_chart(fig2)
#punto 2
st.divider()
metrica1, metrica2 = st.columns(2)
compradores1 = final_FILTRADO.query("n_pedidos == 1").shape[0]
if numero_compradores != 0:
    porcentaje_respecto_al_total = compradores1 / numero_compradores
else:
    porcentaje_respecto_al_total = 0
metrica1.metric(label="Compradores unica vez",value=compradores1,border=True)
metrica2.metric(label="Porcentaje Compradores unica vez",value=f"{porcentaje_respecto_al_total:.2%}",border=True)

st.write("""Punto 1. La tasa de recompra la sacamos dividiendo los clientes que compraron
dos veces o más entre todos los que compraron al menos una vez. Los clientes con una sola compra
son los que compraron una vez y no volvieron, o sea, la gente a la que le apuntaría la campaña.
Solo con la tasa no alcanza para decidir, porque un porcentaje no dice cuántas personas hay detrás.
Un canal puede tener la tasa más baja pero tener poca gente, y otro puede tener mejor tasa pero
muchos más clientes que solo compraron una vez.""")

#punto 5
st.write("""Punto 5. Probamos los filtros con varias opciones. Con todo seleccionado salen
poco más de mil compradores y alrededor del 33,91% compro una sola vez. Cuando dejamos solo
la preferencia Hogar con los canales Referidos y Orgánico, los números bajan bastante, pero las
tarjetas y las gráficas se siguen actualizando bien. Y si dejamos solo el segmento Sin Compra,
no queda ningún comprador, las tarjetas quedan en cero y en lugar de las gráficas sale el mensaje
de que no hay compradores.""")

#PUNTO 3
st.divider()
st.header("Campaña de recompra por canal")

compradores_sel = final_FILTRADO.query("n_pedidos > 0")
lab_izq, lab_der = st.columns(2)

if compradores_sel.shape[0] > 0:
    compradores_sel["recompra"] = compradores_sel["n_pedidos"] >= 2

    with lab_izq:
        por_canal = compradores_sel.groupby("canal_adquisicion", as_index=False).agg(
            compradores=("id_cliente", "count"),
            recompradores=("recompra", "sum")
        )
        tasa = por_canal["recompradores"] / por_canal["compradores"] * 100
        por_canal["tasa_recompra"] = tasa.round(1)
        por_canal = por_canal.sort_values("tasa_recompra", ascending=False)

        fig_tasa = pe.bar(data_frame=por_canal, x="canal_adquisicion", y="tasa_recompra",
                          text="tasa_recompra", hover_data=["compradores"])
        fig_tasa.update_layout(xaxis_title="Canal", yaxis_title="porcentaje con 2 o más pedidos",
                               title="Tasa de recompra por canal")
        st.plotly_chart(fig_tasa)

    #punto 4
    compradores_sel["una_compra"] = compradores_sel["n_pedidos"] == 1

    with lab_der:
        df_una = compradores_sel.groupby("canal_adquisicion", as_index=False).agg(
            una_compra=("una_compra", "sum")
        )
        df_una = df_una.sort_values("una_compra", ascending=True)

        fig4 = pe.bar(data_frame=df_una, x="una_compra", y="canal_adquisicion",
                      orientation="h", text="una_compra")
        fig4.update_layout(xaxis_title="Clientes con 1 pedido", yaxis_title="Canal",
                           title="Clientes con exactamente un pedido por canal")
        st.plotly_chart(fig4)

    st.write("""Punto 3. Usamos un gráfico de barras porque solo comparamos un dato,
    el porcentaje de recompra, entre cuatro canales. Con barras se ve rápido qué canal tiene
    la tasa más alta y cuál la más baja, y las ordenamos de mayor a menor. Al pasar el mouse
    sobre cada barra aparece cuántos compradores tiene ese canal.""")

    st.write("""Punto 4. No siempre. Si un canal tiene muchos clientes de una sola compra
    puede ser solo porque es un canal grande, con mucha gente. La tasa en cambio, es un
    porcentaje y no depende de cuántos clientes tenga el canal. En nuestros datos sí coinciden
    en Redes sociales, pero también es el canal que más compradores tiene""")
else:
    st.write("No hay compradores")

#punto 6
st.write("""Punto 6: Empezaríamos el piloto en Redes sociales. Es el canal con más
clientes que solo compraron una vez, con 147, y el que tiene la tasa de recompra más baja el 59,6%, mientras que Orgánico tiene el 75,5 %. Es donde hay más gente para
convencer y más espacio para mejorar. Hay que tener en cuenta que los clientes que llegaron hace
poco no han tenido mucho tiempo para volver a comprar, y que los datos no dicen por qué alguien
no volvió. Para saber si el piloto funcionó, miraríamos cuántos de esos clientes hacen su segunda
compra en los 60 días siguientes y lo compararíamos con un grupo al que no le llegue la campaña.""")