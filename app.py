from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import mysql.connector
from database import conectar, obtener_usuario, insertar_estudiante
from dashprincipal import crear_tablero
import pandas as pd
import unicodedata

app = Flask(__name__)

app.secret_key = "secreto_123"

# Crear Dashboard.
dash_app = crear_tablero(app)

# ===================== Evitar Caché =====================

@app.after_request
def agregar_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"]= "no-cache"
    response.headers["Expires"]= "0"
    return response

# ===================== Proteger rutas =====================

@app.before_request
def proteger_rutas():
    
    rutas_protegidas = ["/dashprincipal"]

    if any(request.path.startswith(ruta) for ruta in rutas_protegidas):
        if "username" not in session:
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

        return redirect("/dashprincipal")
    
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

@app.route("registro_estudiante", methods=["GET","POST"])
def registro_estudiante():

    if "usuario" not in session:
        return redirect("/")
    
    if request.method == 'POST':
        try:
            nombre = request.form["nombre"]
            edad = request.form["edad"]
            carrera = request.form["carrera"]
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

            return redirect("/dashprincipal")
        
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

        #----- Leer Archivo Excel. -----

        df = pd.read_excel(archivo)
        df = df.drop(columns=["id"], errors="ignore")

        #----- Limpiar Nombre y Carrera. -----

        df["Nombre"] = df["Nombre"].astype(str).str.strip()
        df["Nombre"] = df["Nombre"].apply(quitar)
        df["Nombre"] = df["Nombre"].str.title()


        df["Carrera"] = df["Carrera"].astype(str).str.strip()
        df["Carrera"] = df["Carrera"].apply(quitar)
        df["Carrera"] = df["Carrera"].str.title()

        rechazados = []


        #----- Datos Faltantes. -----

        faltantes = df[df.isnull().any(axis=1)].copy()
        if not faltantes.empty:

            faltantes["Motivo"] = "Datos Faltantes"
            rechazados.append(faltantes)
            df = df.dropna()


        #----- Edad Negativa. -----

        edad_negativa = df[df["Edad"] < 0].copy()
        if not edad_negativa.empty:
            edad_negativa["Motivo"] = "Edad Negativa"
        rechazados.append(edad_negativa)
        df = df[df["Edad"] >= 0]


        #----- Notas Inválidas. -----

        notas_invalidas = df[
            (

            (df["Nota1"] >= 0) & (df["Nota1"] <= 5) &
            (df["Nota2"] >= 0) & (df["Nota2"] <= 5) &
            (df["Nota3"] >= 0) & (df["Nota3"] <= 5) 

            )
            
            ].copy()
        
        if not notas_invalidas.empty:
            notas_invalidas["Motivo"] = "Notas Inválidas"
            rechazados.append(notas_invalidas)

            df = df[
     
            (df["Nota1"] >= 0) & (df["Nota1"] <= 5) &
            (df["Nota2"] >= 0) & (df["Nota2"] <= 5) &
            (df["Nota3"] >= 0) & (df["Nota3"] <= 5) 

            ]

            #----- Datos Duplicados del Archivo. -----

            duplicados = df[df.duplicated(subset=["Nombre", "Carrera"], keep = "first")].copy()
            if not duplicados.empty:
                duplicados["Motivo"] = "Dato Duplicado"
                rechazados.append(duplicados)

            df = df.drop_duplicates(subset=["Nombre", "Carrera"])


            #----- Estudiantes que existen en la Base de Datos. -----

            existentes = obtener_estudiantes()[["Nombre", "Carrera"]]
            mascara = df.apply(
            lambda r: ((existentes["Nombre"] == r["Nombre"]) &
                       (existentes["Carrera"] == r["Carrera"])).any(), axis=1)
            
            ya_existen = df[mascara].copy()
            if not ya_existen.empty:
                ya_existen["Motivo"] = "El Estudiante ya existe en la Base de Datos."
                rechazados.append(ya_existen)
                df = df[~mascara]


            #----- Calcular el Promedio y Desempeño. -----

            df["Promedio"] = ((df["Nota1"] + df["Nota2"] + df["Nota3"]) / 3).round(2)
            df = df[df["Promedio"] <= 5]


            #


        

    





# ======================= DASHBOARD ========================

@app.route("/dashprincipal")
def dashprinci():
    
    if "username" not in session:
        return redirect("/")

    return render_template("dashprinci.html", usuario=session["username"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ======================= VALIDAR DUPLICADOS ========================

def estudiante_existe(nombre, carrera):

    conn = conectar()
    cursor = conn.cursor()

    query = """
    SELECT COUNT(*)
    FROM estudiantes
    WHERE Nombre = %s AND Carrera = %s
    """

    cursor.execute(query,(nombre,carrera))

    resultado = cursor.fetchone()[0]

    conn.close()

    return resultado > 0

# ======================= REGISTRO MANUAL ========================

@app.route("/registro_estudiante", methods=["GET","POST"])
def registroestudiante():

    if "username" not in session:
        return redirect("/")

    if request.method == "POST":

        nombre = request.form["nombre"]
        edad = int(request.form["edad"])
        carrera = request.form["carrera"]

        nota1 = float(request.form["nota1"])
        nota2 = float(request.form["nota2"])
        nota3 = float(request.form["nota3"])

        promedio = round((nota1 + nota2 + nota3)/3,2)

        desempeno = calculardesempeno(promedio)

        # Validar duplicados

        if estudiante_existe(nombre,carrera):

            flash("El estudiante ya está registrado")

        else:

            insertar_estudiante(nombre,edad,carrera,nota1,nota2,nota3,promedio,desempeno)

            flash(f"Estudiante {nombre} registrado correctamente")

        return redirect("/dashprincipal")

    return render_template("registro_estudiante.html")

# ======================= QUITAR ACENTOS ========================

def quitar(texto):

    if pd.isna(texto):
        return texto

    texto = str(texto)

    return ''.join(
        c for c in unicodedata.normalize('NFD',texto)
        if unicodedata.category(c) != 'Mn'
    )

# ======================= CALCULAR DESEMPEÑO ========================

def calculardesempeno(promedio):

    if promedio >= 5:
        return "Excelente"
    elif promedio >= 4.5:
        return "Bueno"
    elif promedio >= 4:
        return "Regular"
    else:
        return "Bajo"

# ======================= CARGA MASIVA ========================


        for index, fila in df.iterrows():

            nombre = fila["Nombre"]
            edad = fila["Edad"]
            carrera = fila["Carrera"]

            n1 = fila["Nota1"]
            n2 = fila["Nota2"]
            n3 = fila["Nota3"]

            # Validar datos faltantes

            if pd.isna(nombre) or pd.isna(edad) or pd.isna(carrera):

                fila["Motivo"] = "Datos faltantes"
                rechazados.append(fila)
                rechazados_count += 1
                continue

            # Edad negativa

            if edad < 0:

                fila["Motivo"] = "Edad negativa"
                rechazados.append(fila)
                rechazados_count += 1
                continue

            # Notas inválidas

            if n1 < 0 or n1 > 5 or n2 < 0 or n2 > 5 or n3 < 0 or n3 > 5:

                fila["Motivo"] = "Notas inválidas"
                rechazados.append(fila)
                rechazados_count += 1
                continue

            # Validar duplicados

            if estudiante_existe(nombre,carrera):

                fila["Motivo"] = "Estudiante duplicado"
                rechazados.append(fila)
                duplicados += 1
                continue

            promedio = round((n1+n2+n3)/3,2)

            desempeno = calculardesempeno(promedio)

            insertar_estudiante(nombre,edad,carrera,n1,n2,n3,promedio,desempeno)

            insertados += 1

        # Generar Excel de rechazados

        if len(rechazados) > 0:

            df_rechazados = pd.DataFrame(rechazados)

            df_rechazados.to_excel("rechazados.xlsx",index=False)

        flash(f"""
        Resultado del cargue masivo

        Insertados: {insertados}
        Rechazados: {rechazados_count}
        Duplicados: {duplicados}
        """)

        return render_template("carga_masiva.html")

    return render_template("carga_masiva.html")

# ======================= RANKING TOP 10 ========================

@app.route("/ranking")

def ranking():

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT Nombre, Carrera, Promedio
    FROM estudiantes
    ORDER BY Promedio DESC
    LIMIT 10
    """

    cursor.execute(query)

    ranking = cursor.fetchall()

    conn.close()

    return render_template("ranking.html", ranking=ranking)

# ======================= ALERTA ESTUDIANTES EN RIESGO ========================

@app.route("/riesgo")

def estudiantes_riesgo():

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT Nombre, Carrera, Promedio
    FROM estudiantes
    WHERE Promedio < 3
    """

    cursor.execute(query)

    riesgo = cursor.fetchall()

    conn.close()

    return render_template("riesgo.html", riesgo=riesgo)

# ======================= MAIN ========================

if __name__ == "__main__":
    app.run(debug=True)