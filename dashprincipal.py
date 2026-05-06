import pandas as pd
import plotly.express as px
import os
import dash
from dash import html, Input, Output, dcc, dash_table
from database import obtener_estudiantes
from flask import session

def crear_tablero(server):

    appnotas = dash.Dash(__name__, server=server, url_base_pathname="/dashprincipal/", suppress_callback_exceptions=True)

    _init = obtener_estudiantes()

    appnotas.layout = html.Div([

        html.H1("Tablero Avanzado", style={"textAlign": "center","backgroundColor": "#2D2C5D","color": "white","padding": "20px","borderRadius": "10px"}),

        html.Div([
            html.Label("Seleccionar Carrera"),

            dcc.Dropdown(
                id="filtro_carrera",
                options=[{"label": "Todas", "value": "Todas"}] +
                [{"label": c, "value": c} for c in sorted(_init["Carrera"].unique())],
                value="Todas",
            ),

            html.Br(),

            dcc.RangeSlider(
                id="slider_edad",
                step=1,
                min=_init["Edad"].min(),
                max=_init["Edad"].max(),
                value=[_init["Edad"].min(), _init["Edad"].max()],
            ),

            html.Br(),

            dcc.RangeSlider(
                id="slider_promedio",
                min=0,
                max=5,
                step=0.1,
                value=[0, 5],
            ),

        ]),

        html.Div(id="kpis"),

        dcc.Input(id="busqueda"),

        dcc.Interval(id="intervalo", interval=30000, n_intervals=0),

        dash_table.DataTable(id="tabla"),

        dcc.Graph(id="gran_detallado"),

        dcc.Graph(id="histograma"),
        dcc.Graph(id="dispersion"),
        dcc.Graph(id="pie"),
        dcc.Graph(id="promedio_carrera"),

        dash_table.DataTable(id="ranking"),
        dash_table.DataTable(id="riesgo"),
    ])

    # ---------- TABLA ----------
    @appnotas.callback(
        Output("tabla", "data"),
        Output("tabla", "columns"),
        Output("kpis", "children"),
        Input("filtro_carrera", "value"),
        Input("slider_edad", "value"),
        Input("slider_promedio", "value"),
        Input("busqueda", "value"),
        Input("intervalo", "n_intervals"),   # 🔥 clave
    )
    def actualizar_comp(carrera, rangoedad, rangoprome, busqueda, n):

        dataf = obtener_estudiantes()

        if carrera == "Todas":
            filtro = dataf[
                (dataf["Edad"] >= rangoedad[0]) &
                (dataf["Edad"] <= rangoedad[1]) &
                (dataf["Promedio"] >= rangoprome[0]) &
                (dataf["Promedio"] <= rangoprome[1])
            ]
        else:
            filtro = dataf[
                (dataf["Carrera"] == carrera) &
                (dataf["Edad"] >= rangoedad[0]) &
                (dataf["Edad"] <= rangoedad[1]) &
                (dataf["Promedio"] >= rangoprome[0]) &
                (dataf["Promedio"] <= rangoprome[1])
            ]

        # 🔍 búsqueda segura
        if busqueda:
            filtro = filtro[filtro.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]

        columnas = [{"name": i, "id": i} for i in filtro.columns]

        return filtro.to_dict("records"), columnas, []

    # ---------- GRÁFICOS ----------
    @appnotas.callback(
        Output("histograma", "figure"),
        Output("dispersion", "figure"),
        Output("pie", "figure"),
        Output("promedio_carrera", "figure"),
        Input("filtro_carrera", "value"),
        Input("intervalo", "n_intervals"),   # 🔥 clave
    )
    def actualizar_graficos(carrera, n):

        dataf = obtener_estudiantes()

        if carrera == "Todas" or carrera is None:
            df_carrera = dataf
        else:
            df_carrera = dataf[dataf["Carrera"] == carrera]

        fig_hist = px.histogram(df_carrera, x="Promedio")
        fig_disp = px.scatter(df_carrera, x="Edad", y="Promedio")
        fig_pie = px.pie(df_carrera, names="Desempeño")
        fig_bar = px.bar(dataf, x="Carrera", y="Promedio")

        return fig_hist, fig_disp, fig_pie, fig_bar

    # ---------- RANKING ----------
    @appnotas.callback(
        Output("ranking", "data"),
        Output("ranking", "columns"),
        Input("intervalo", "n_intervals"),
    )
    def actualizar_ranking(n):
        df = obtener_estudiantes()
        top = df.sort_values("Promedio", ascending=False).head(10)
        return top.to_dict("records"), [{"name": i, "id": i} for i in top.columns]

    # ---------- RIESGO ----------
    @appnotas.callback(
        Output("riesgo", "data"),
        Output("riesgo", "columns"),
        Input("intervalo", "n_intervals"),
    )
    def actualizar_riesgo(n):
        df = obtener_estudiantes()
        riesgo = df[df["Promedio"] < 3]
        return riesgo.to_dict("records"), [{"name": i, "id": i} for i in riesgo.columns]

    return appnotas