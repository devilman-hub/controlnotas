from grpc import server
import pandas as pd
import plotly.express as px
import os
import dash
from dash import html, Input, Output, dcc, dash_table
from database import obtener_estudiantes
from flask import session

#----- Ruta para Cargar desde la Base de Datos. -----

def crear_tablero(server):

    #----- Cargar Datos Iniciales. -----
    dataf = obtener_estudiantes()

    #----- Inicializar la App. -----

    #Correción para la Ñ.
    dataf.columns = dataf.columns.str.replace("ñ", "n")

    dataf.columns = dataf.columns.str.lower()

    #Iniciar App.
    appnotas = dash.Dash(__name__, server=server, url_base_pathname="/dashprincipal/", suppress_callback_exceptions=True)

    #----- Cargar Datos Iniciales. -----
    _init = dataf

    #----- Renderizar del Dashboard. -----

    appnotas.layout = html.Div([

        html.H1("Tablero Avanzado", style={"textAlign": "center", 
                                        "backgroundColor": "#1E1BD2", 
                                        "color": "white", 
                                        "padding": "20px",
                                        "borderRadius": "10px"}),

        html.Div([
            html.Label("Seleccionar Carrera", style={"fontSize": "18px", "fontWeight": "bold"}),

            #----- Filtro por Carrera. -----
            dcc.Dropdown(
                id="filtro_carrera",
                options=[{"label": "Todas", "value": "Todas"}] +
                [{"label": c, "value": c} for c in sorted(_init["carrera"].unique())],
                value="Todas",
            ),

            html.Br(),

            html.Label("Rango de Edad", style={"fontSize": "18px", "fontWeight": "bold"}),

            #----- Filtro por Rango de Edad. -----
            dcc.RangeSlider(
                id="slider_edad",
                step=1,
                min=_init["edad"].min(),
                max=_init["edad"].max(),
                value=[_init["edad"].min(), _init["edad"].max()],
                marks={i: str(i) for i in range(int(_init["edad"].min()), int(_init["edad"].max()) + 1, 5)},
                tooltip={"placement": "bottom", "always_visible": True}
            ),

            html.Br(),

            html.Label("Rango Promedio", style={"fontSize": "18px", "fontWeight": "bold"}),

            dcc.RangeSlider(
                id="slider_promedio",
                min=0,
                max=5,
                step=0.1,
                value=[0, 5],
                tooltip={"placement": "bottom", "always_visible": True},
            ),

        ], style={"width": "80%", "margin": "auto", "backgroundColor": "#f0f0f0", "padding": "20px", "borderRadius": "10px"}),

        html.Br(),

        #----- Contenedor para KPIs. -----
        html.Div(id="kpis", style={"display": "flex", "justifyContent": "space-around"}),

        html.Br(),

        #----- Barra de Búsqueda. -----
        dcc.Input(
            id="busqueda",
            type="text",
            placeholder="Buscar Estudiante...",
            style={
                "width": "100%",
                "padding": "10px",
                "fontSize": "16px", 
                "borderRadius": "5px",
                "border": "1px solid #ccc"}
        ),

        html.Br(),

        dcc.Interval(id="intervalo", interval=30000, n_intervals=0),
        dcc.Interval(id="intervalo_kpis", interval=30000, n_intervals=0),

        html.Br(),

        #----- Tabla con los Estudiantes. -----
        dcc.Loading(
            children=[
                dash_table.DataTable(
                    id="tabla",
                    page_size=8,
                    filter_action="native",
                    sort_action="native",
                    row_selectable="multi",
                    selected_rows=[],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "center", "padding": "10px"},
                    style_header={
                        "backgroundColor": "#1E1BD2",
                        "color": "white",
                        "fontWeight": "bold"
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#f9f9f9"}
                    ],
                ),

                html.Br(),

                dcc.Graph(id="gra_detallado"),

                #----- Gráficos Detallados. -----
                dcc.Tabs([
                    dcc.Tab(label="Histograma Promedios", children=[dcc.Graph(id="histograma")]),
                    dcc.Tab(label="Dispersión Edad Vs. Nota", children=[dcc.Graph(id="dispersion")]),
                    dcc.Tab(label="Desempeño Por Carrera", children=[dcc.Graph(id="pie")]),
                    dcc.Tab(label="Histograma Promedios", children=[dcc.Graph(id="promedio_carrera")])
                ]),

                #----- Tabla de los Mejores 10 Estudiantes. -----
                html.H3("Top 10 Estudiantes", style={"textAlign": "center", "marginTop": "40px"}),
                dash_table.DataTable(id="ranking", page_size=10),

                html.Br(),

                #----- Tabla con Estudiantes en Riesgo. -----
                html.H3("Estudiantes en Riesgo", style={"textAlign": "center", "marginTop": "40px"}),
                dash_table.DataTable(id="riesgo", page_size=10),
            ]
        ),

        #----- Botón para Cerrar Sesión. -----
        html.A("Cerrar Sesión", href="/cerrar_sesion"),

        #----- Botón para Registrar Nuevo Estudiante. -----
        html.A("Registrar Estudiante", href="/opciones_registro"),

    ], style={"fontFamily": "Times New Roman"})


    #----- Callback y función para Actualizar la Tabla y los Gráficos. -----

    @appnotas.callback(
        Output("gra_detallado", "figure"),
        Input("tabla", "derived_virtual_data"),
        Input("tabla", "derived_virtual_selected_rows"),
        Input("intervalo", "n_intervals"),
    )
    def actualizartab(rows, selected_rows, n_intervals):

        if not rows:
            return px.scatter(title="Sin Datos")

        dff = pd.DataFrame(rows)

        if selected_rows:
            dff = dff.iloc[selected_rows]

        fig = px.scatter(dff, x="edad", y="promedio")

        return fig


    #----- Callback y función para Actualizar el Dropdown de Carreras. -----

    @appnotas.callback(
        Output("filtro_carrera", "options"),
        Input("intervalo", "n_intervals"),
    )
    def actualizar_carreras(n_intervals):
        dataf = obtener_estudiantes()
        carreras = sorted(dataf["carrera"].unique())
        return [{"label": "Todas", "value": "Todas"}] + [{"label": c, "value": c} for c in carreras]


    #----- Callback y función para Actualizar el Dropdown de Edades. -----

    @appnotas.callback(
        Output("slider_edad", "min"),
        Output("slider_edad", "max"),
        Output("slider_edad", "value"),
        Output("slider_edad", "marks"),
        Input("intervalo", "n_intervals"),
    )
    def actualizar_edades(n_intervals):
        dataf = obtener_estudiantes()
        min_e = int(dataf["edad"].min())
        max_e = int(dataf["edad"].max())
        marks = {i: str(i) for i in range(min_e, max_e + 1, 5)}
        return min_e, max_e, [min_e, max_e], marks


    #----- Exportar todo el Dashboard. -----
    return appnotas