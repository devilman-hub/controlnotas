from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import mysql.connector
from database import conectar, obtener_usuario, insertar_estudiante, buscar_estudiante, obtener_estudiantes, obtener_carreras
from dashprincipal import crear_tablero
import pandas as pd
import unicodedata

app = Flask(__name__)
app.secret_key = "secreto_123"

#Crear Dashboard.
dash_app = crear_tablero(app)


# ===================== Evitar Caché de Páginas Protegidas. =====================

@app.after_request
def agregar_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"]= "no-cache"
    response.headers["Expires"]= "0"
    return response

# ===================== Proteger Rutas. =====================

@app.before_request
def proteger_rutas():
    
    rutas_protegidas = ["/dashprincipal/"]

    if any(request.path.startswith(ruta) for ruta in rutas_protegidas):
        if "usuario" not in session:
            return redirect("/")

# ===================== LOGIN =====================

@app.route("/",methods=['GET', 'POST'])
def login():
    try:
        
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            usuario = obtener_usuario(username)

            if not usuario:
                return "¡Usuario No Existe!"
            
            if usuario["password"] != password:
                return "Contraseña Incorrecta!"
            
            session['usuario'] = {
                "id": usuario["id"],
                "username": usuario["username"],
                "rol": usuario["rol"]
            }

            return redirect("/dashprincipal/")
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
    return render_template("login.html")

# ======================= CERRAR SESIÓN ========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ======================= REGISTRAR ESTUDIANTE ========================

@app.route("/registro_estudiante", methods=["GET","POST"])
def registro_estudiante():

    if "usuario" not in session:
        return redirect("/")
    
    if request.method == 'POST':
        try:
            nombre = request.form["Nombre"]
            edad = request.form["Edad"]
            carrera = request.form["Carrera"]
            nota_1 = request.form["nota1"]
            nota_2 = request.form["nota2"]
            nota_3 = request.form["nota3"]

            existe = buscar_estudiante(nombre, carrera)
            if existe:
                return render_template("registro_estudiante.html", 
                                       error="El Estudiante ya existe en la Carrera")
            
            promedio = round((nota_1 + nota_2 + nota_3) / 3, 2)
            desempeno = calcular_desempeno(promedio)

            insertar_estudiante(nombre, edad, carrera, nota_1, nota_2, nota_3, promedio, desempeno)

            return redirect("/dashprincipal/")
        
        except Exception as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500
        
    return render_template("registro_estudiante.html")

# ======================= CARGA MASIVA ========================

@app.route("/carga_masiva", methods=["GET","POST"])
def carga_masiva():

    if request.method == "POST":

        archivo = request.files["archivo"]

        df = pd.read_excel(archivo)
        df = df.drop(columns=["id"], errors="ignore")

        df["Nombre"] = df["Nombre"].astype(str).str.strip()
        df["Nombre"] = df["Nombre"].apply(quitar)
        df["Nombre"] = df["Nombre"].str.title()

        df["Carrera"] = df["Carrera"].astype(str).str.strip()
        df["Carrera"] = df["Carrera"].apply(quitar)
        df["Carrera"] = df["Carrera"].str.title()

        rechazados = []

        faltantes = df[df.isnull().any(axis=1)].copy()
        if not faltantes.empty:
            faltantes["Motivo"] = "Datos Faltantes"
            rechazados.append(faltantes)
            df = df.dropna()

        edad_negativa = df[df["Edad"] < 0].copy()
        if not edad_negativa.empty:
            edad_negativa["Motivo"] = "Edad Negativa"
        rechazados.append(edad_negativa)
        df = df[df["Edad"] >= 0]

        # (todo tu código restante queda igual)

    return render_template("carga_masiva.html")

# ======================= DESCARGAR ========================

@app.route("/descargar_rechazados")
def descargar_rechazados():
    return send_file("rechazados.xlsx", as_attachment=True, download_name="rechazados.xlsx")

# ======================= FUNCIONES ========================

def quitar(texto):
    if pd.isna(texto):
        return texto
    
    texto = str(texto)

    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def calcular_desempeno(promedio):

    if promedio >= 4.5:
        desempeno = "Excelente"
    elif promedio >= 4:
        desempeno = "Bueno"
    elif promedio >= 3:
        desempeno = "Regular"
    else:
        desempeno = "Deficiente"

    return desempeno

# ======================= CARRERAS ========================

@app.route("/obtener_carreras")
def ruta_obtener_carreras():
    carreras = obtener_carreras()
    return jsonify(carreras)

# ======================= SERVIDOR ========================

if __name__ == "__main__":
    app.run(debug=True)