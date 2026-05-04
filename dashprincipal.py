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


#----- Inicializar la App. -----
  
appnotas = dash.Dash(__name__, server=server, routes_pathname_prefix="/dashprincipal/", requests_pathname_prefix="/dashprincipal/",suppress_callback_exceptions=True
)

#----- Cargar Datos Iniciales. -----

_init = obtener_estudiantes()


#----- Renderizar del Dashboard. -----

appnotas.layout = html.Div([

   html.H1("Tablero Avanzado", style={"textAlign": "center", 
                                       "backgroundColor": "#1E1BD2", 
                                       "color": "white", 
                                       "padding": "20px",
                                       "borderRadius": "10px"}),


]),


#----- Función para Crear el Tablero (Contenedor de Filtros). -----


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
   marks={i: str(i) for i in range(_init["edad"].min(), _init["edad"].max() + 1, 5)},
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

],  style={"width": "80%", "margin": "auto", "backgroundColor": "#f0f0f0", "padding": "20px", "borderRadius": "10px"}),

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

dcc.Interval(
   id="intervalo",
   interval=30000,
   n_intervals=0
),

html.Br(),

dcc.Interval(
   id="intervalo_kpis",
   interval=30000,
   n_intervals=0
   
)


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
            {
               "if": {"row_index": "odd"},
               "backgroundColor": "#f9f9f9"
            }
         ], type="circle"
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
dash_table.DataTable(
  id="ranking",
  page_size=10,
  style_table={"overflowX": "auto"},
  style_cell={"textAlign": "center", "padding": "10px"},
  style_header={
    "backgroundColor": "#1E1BD2",
    "color": "white",
    "fontWeight": "bold"
  },

),

html.Br(),

#----- Tabla con Estudiantes en Riesgo. -----

html.H3("Estudiantes en Riesgo", style={"textAlign": "center", "marginTop": "40px"}),
dash_table.DataTable(
  id="riesgo",
   page_size=10,
   style_table={"overflowX": "auto"},
   style_cell={"textAlign": "center", "padding": "10px"},
   style_header={
     "backgroundColor": "#1E1BD2",
     "color": "white",
     "fontWeight": "bold"
   },

),

#----- Botón para Cerrar Sesión. -----


html.A("Cerrar Sesión",
            href="/cerrar_sesion",
            style={
                "position": "absolute",
                "right": "20px",
                "top": "40px",
                "backgroundColor": "#000000",
                "color": "white",
                "padding": "10px 20px",
                "borderRadius": "5px",
                "textDecoration": "none",
                "fontWeight": "bold"
            }
        ), 


#----- Botón para Registrar Nuevo Estudiante. -----

html.A("Registrar Estudiante",
            href="/opciones_registro",
            style={
                "position": "absolute",
                "left": "20px",
                "top": "40px",
                "backgroundColor": "#000000",
                "color": "white",
                "padding": "10px 20px",
                "borderRadius": "5px",
                "textDecoration": "none",
                "fontWeight": "bold"
            }
        ), 

    ], style={"fontFamily": "Times New Roman"})


#----- Callback y función para Actualizar la Tabla y los Gráficos. -----

@appnotas.callback(
   Output("gran_detallado", "figure"),
   Input("tabla", "derived_virtual_data"),
   Input("tabla", "derived_virtual_selected_rows"),
   Input("intervalo", "n_intervals"),

)


def actualizartab(rows, selected_rows, n_intervals):

   if not rows:
      return px.scatter(title="Sin Datos")
   
   if selected_rows:
      dff = dff.iloc[selected_rows]  

   fig = px.scatter(dff, x="Edad", y="Promedio", color="Desempeño", size="Promedio", title="Análisis Detallado (Seleccione Filas de la Tabla)", trendline="ols")

   return fig


#----- Callback y función para Actualizar el Dropdown de Carreras. -----

@appnotas.callback(
   Output("filtro_carrera", "options"),
   Input("intervalo", "n_intervals"),
)

def actualizar_carreras(n_intervals):
   dataf = obtener_estudiantes()
   carreras = sorted(dataf["Carrera"].unique())
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
   min_e = int(dataf["Edad"].min())
   max_e = int(dataf["Edad"].max())
   marks = {i: str(i) for i in range(min_e, max_e + 1, 5)}
   return min_e, max_e, [min_e, max_e], marks

#----- Callback y función para Actualizar el Dropdown de Promedios. -----

@appnotas.callback(
   Output("tabla", "data"),
   Output("tabla", "columns"),
   Output("kpis", "children"),
   Input("filtro_carrera", "value"),
   Input("slider_edad", "value"),
   Input("slider_promedio", "value"),
   Input("busqueda", "value"),
   Input("intervalo", "n_intervals")

)

def actualizar_comp(carrera, rangoedad, rangoprome, busqueda, n_intervals):

   if rangoedad is None or rangoprome is None:
      return [], [], []

dataf = obtener_estudiantes()

#----- Filtro de Datos. -----

if carrera == "Todas":
   filtro = dataf[
      (dataf["Edad"] >= rangoedad[0]) &
      (dataf["Edad"] <= rangoedad[1]) &
      (dataf["Promedio"] >= rangoprome[0]) &
      (dataf["Promedio"] <= rangoprome[1])


else: 
filtro = dataf[
   (dataf["Carrera"] == carrera) &
   (dataf["Edad"] >= rangoedad[0]) &
   (dataf["Edad"] <= rangoedad[1]) &
   (dataf["Promedio"] >= rangoprome[0]) &
   (dataf["Promedio"] <= rangoprome[1])
   
   ]

   #----- Filtro de Búsqueda. -----

   if busqueda:
      filtro = filtro[filtro.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]
   ]


#----- Cálculo de Métricas. -----

if not filtro.empty:
   promedio_val = round(filtro["Promedio"].mean(), 2)
   total_val = len(filtro)
   maximo_val = round(filtro["Promedio"].max(), 2)
else:
   promedio_val = total_val = maximo_val = 0

   #----- Creación de Componentes de KPIs. -----

   estilo_kpi = {"backgroundColor": "#3498db", "color": "white", "padding": "15px", "borderRadius": "10px"}

   kpis_html = [
      html.Div([html.H4("Promedio"), html.H2(promedio_val)], style=estilo_kpi),
      html.Div([html.H4("Total estudiantes"), html.H2(total_val)], style=estilo_kpi),
      html.Div([html.H4("Máximo"), html.H2(maximo_val)], style=estilo_kpi),

   ]
   
   columnas = [{"name": i, "id": i} for i in filtro.columns]
   
   return filtro.to_dict("records"), columnas, kpis_html


#----- Callback y función para Actualizar los Gráficos. -----

@appnotas.callback(
        Output("histograma", "figure"),
        Output("dispersion", "figure"),
        Output("pie", "figure"),
        Output("promedio_carrera", "figure"),
        Input("filtro_carrera", "value"),
        Input("intervalo", "n_intervals"),
    )

def actualizar_graficos(carrera, n_intervals):
        
        if carrera is None:
            carrera = "Todas"
        
        dataf = obtener_estudiantes()

        if carrera == "Todas":
            df_carrera = dataf
        else:
            df_carrera = dataf[dataf["carrera"] == carrera]
        
        fig_hist = px.histogram(df_carrera, x="promedio", title="Distribución de Promedios", color_discrete_sequence=['#4251A7'])
        fig_disp = px.scatter(df_carrera, x="edad", y="promedio", title="Edad vs Promedio", color="desempeno")  
        fig_pie = px.pie(df_carrera, names="desempeno", title="Proporción por Desempeño")
        fig_prom_car = px.bar(dataf, x="carrera", y="promedio", title="Promedio por Carrera", color="carrera")  

        return fig_hist, fig_disp, fig_pie, fig_prom_car


#----- Callback y Función para Actualizar el Ranking de Estudiantes. -----

@appnotas.callback(
    Output("ranking", "data"),
    Output("ranking", "columns"),
    Input("filtro_carrera", "n_intervals"),

)

def actualizar_ranking(n_intervals):
      dataf = obtener_estudiantes()
      top10 = dataf.sort_values(by="promedio", ascending=False).head(10)

      columnas = [{"name": i, "id": i} for i in top10.columns]

      return top10.to_dict("records"), columnas

#----- Callback y función para Actualizar Tabla de Estudiantes en Riesgo. -----

@appnotas.callback(
    Output("riesgo", "data"),
    Output("riesgo", "columns"),
    Input("filtro_carrera", "n_intervals"),
    
)

def actualizar_riesgo(n_intervals):
      dataf = obtener_estudiantes()

      riesgo = dataf[dataf["promedio"] < 3.0][["nombre", "carrera", "promedio"]] \
      .sort_values(by="promedio", ascending=True).head(10) \
      .reset_index(drop=True)

      riesgo.index += 1
      riesgo.insert(0, "posicion", riesgo.index)

      columnas = [{"name": i.capitalize(), "id": i} for i in riesgo.columns]
      
      return riesgo.to_dict("records"), columnas


#----- Exportar todo el Dashboard. -----

return appnotas 