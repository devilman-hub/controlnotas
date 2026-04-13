import pandas as pd
import plotly.express as px
import os
import dash
from dash import html, Input, Output, dcc, dash_table
from database import obtenerestudiantes
from flask import session

#Ruta para Cargar desde la Base de Datos.
def creartablero(server):

   # Cargar Datos Iniciales.
   dataf = obtenerestudiantes()

   #Correción para la Ñ.
   dataf.columns = dataf.columns.str.replace("ñ", "n")

   #Iniciar App.
   appnotas = dash.Dash(__name__,
                        server=server,
                        url_base_pathname="/dashprincipal/",
                        suppress_callback_exceptions=True)

   appnotas.layout = html.Div([

      html.H1("Tablero Avanzado",
              style={"textAlign": "center",
                     "backgroundColor": "#1E1BD2",
                     "color": "white",
                     "padding": "20px"}),

      html.Div([

         html.Label("Seleccionar Carrera"),

         dcc.Dropdown(
            id="filtro_carrera",
            options=[{"label": ca, "value": ca} for ca in sorted(dataf["Carrera"].unique())],
            value=dataf["Carrera"].unique()[0] if len(dataf) > 0 else None
         ),

         html.Br(),

         html.Label("Rango de Edad"),

         dcc.RangeSlider(
            id="slider_edad",
            min=dataf["Edad"].min(),
            max=dataf["Edad"].max(),
            step=1,
            value=[dataf["Edad"].min(), dataf["Edad"].max()],
            tooltip={"placement": "bottom", "always_visible": True}
         ),

         html.Br(),

         html.Label("Rango Promedio"),

         dcc.RangeSlider(
            id="slider_promedio",
            min=0,
            max=5,
            step=1,
            value=[0, 5],
            tooltip={"placement": "bottom", "always_visible": True},
         )

      ], style={"width": "80%", "margin": "auto"}),

      html.Br(),

      html.Div(id="kpis",
               style={"display": "flex",
                      "justifyContent": "space-around"}),

      html.Br(),
      #Crear una Tabla.
      dcc.Loading(

         dash_table.DataTable(
            id="tabla",
            page_size=8,
            filter_action="native",
            sort_action="native",
            row_selectable="multi",
            selected_rows=[],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center"}
         ),

         type="circle"
      ),

      html.Br(),

      dcc.Input(
         id="busqueda",
         type="text",
         placeholder="Buscar Estudiante..."
      ),

      html.Br(),

      dcc.Interval(
         id="intervalo",
         interval=10000,
         n_intervals=0
      ),

      dcc.Loading(
         dcc.Graph(id="gra_detallado"),
         type="default"
      ),

      html.Br(),

      dcc.Tabs([

         dcc.Tab(label="Histograma",
                 children=[dcc.Graph(id="histograma")]),

         dcc.Tab(label="Dispersion",
                 children=[dcc.Graph(id="dispersion")]),

         dcc.Tab(label="Desempeño",
                 children=[dcc.Graph(id="pie")]),

         dcc.Tab(label="Promedio por Carrera",
                 children=[dcc.Graph(id="barras")]),

         
         dcc.Tab(label="Rango de Edad",
                children=[dcc.Graph(id="rangoedad")]),

      ])

   ])


#Actualización de la Tabla y los Gráficos en General.
   @appnotas.callback(
      Output("tabla", "data"),
      Output("tabla", "columns"),
      Output("kpis", "children"),
      Output("histograma", "figure"),
      Output("dispersion", "figure"),
      Output("pie", "figure"),
      Output("barras", "figure"),

      Input("filtro_carrera", "value"),
      Input("slider_edad", "value"),
      Input("slider_promedio", "value"),
      Input("busqueda", "value"),
      Input("intervalo", "n_intervals")
   )

   def actualizar_comp(carrera, rangoedad, rangoprome, busqueda, n_intervals):

      dataf = obtenerestudiantes()
      dataf.columns = dataf.columns.str.replace("ñ", "n")

      filtro = dataf[
         (dataf["Carrera"] == carrera) &
         (dataf["Edad"] >= rangoedad[0]) &
         (dataf["Edad"] <= rangoedad[1]) &
         (dataf["Promedio"] >= rangoprome[0]) &
         (dataf["Promedio"] <= rangoprome[1])
      ]

      #Aplicar la Búsqueda.
      if busqueda:

         filtro = filtro[
            filtro.apply(
               lambda row: busqueda.lower() in str(row).lower(),
               axis=1)
         ]

      #Si el Filtro queda vacío para evitar Errores.
      if filtro.empty:

         fig = px.scatter(title="Sin Datos")

         return [], [], [], fig, fig, fig, fig

      promedio = round(filtro["Promedio"].mean(), 2)
      total = len(filtro)
      maximo = round(filtro["Promedio"].max(), 2)

      kpis = [

         html.Div(
            [html.H4("Promedio"), html.H2(promedio)],
            style={"backgroundColor": "#3498db",
                   "color": "white",
                   "padding": "15px",
                   "borderRadius": "10px"}
         ),

         html.Div(
            [html.H4("Total estudiantes"), html.H2(total)],
            style={"backgroundColor": "#3498db",
                   "color": "white",
                   "padding": "15px",
                   "borderRadius": "10px"}
         ),

         html.Div(
            [html.H4("Máximo"), html.H2(maximo)],
            style={"backgroundColor": "#3498db",
                   "color": "white",
                   "padding": "15px",
                   "borderRadius": "10px"}
         )
      ]

      #=============== Diagnóstica. ===============

      #Rangos de Edad. 
      filtro["RangoEdad"] = pd.cut(filtro["Edad"],
      bins = [0, 18, 25, 40, 100],
      labels = ["Adolescente", "Joven", "Adulto", "Mayor"])
      
      
      #Gráficos Originales Mejorados.

      edadbar = px.bar(filtro.groupby("RangoEdad").size().reset_index(name = "Cantidad"),
                       x = "Rangoedad",
                       y = "Cantidad",
                       title = "Cantidad de Estudiante por Rango de Edad" 
                       )

      histo = px.histogram(
         filtro,
         x="Promedio",
         nbins=10,
         title="Distribución de Promedios"
      )

      dispersion = px.scatter(
         filtro,
         x="Edad",
         y="Promedio",
         color="Desempeno",
         trendline="ols",
         title="Edad Vs. Promedio"
      )

      pie = px.pie(
         filtro,
         names="Desempeno",
         title="Distribución por Desempeño"
      )

      promedios = dataf.groupby("Carrera")["Promedio"].mean().reset_index()

      barras = px.bar(
         promedios,
         x="Carrera",
         y="Promedio",
         color="Carrera",
         title="Promedio General por Carrera"
      )

      return (
         filtro.to_dict("records"),
         [{"name": i, "id": i} for i in filtro.columns],
         kpis,
         histo,
         dispersion,
         pie,
         barras
      )

   @appnotas.callback(
      Output("gra_detallado", "figure"),
      Input("tabla", "derived_virtual_data"),
      Input("tabla", "derived_virtual_selected_rows")
   )

   def actualizartab(rows, selected_rows):

      if rows is None:
         return px.scatter(title="Sin Datos")

      dff = pd.DataFrame(rows)

      if selected_rows:
         dff = dff.iloc[selected_rows]

      fig = px.scatter(
         dff,
         x="Edad",
         y="Promedio",
         color="Desempeno",
         size="Promedio",
         title="Analisis Detallado (Seleccione Filas de la Tabla)",
         trendline="ols"
      )

      return fig

   return appnotas