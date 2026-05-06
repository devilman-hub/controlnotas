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

# ===================== Proteger Rutas del Dash. =====================

@app.before_request
def proteger_rutas():
    
    rutas_protegidas = ["/dashprincipal"]

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
                return "¡Contraseña Incorrecta!"
            
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

@app.route("/registro_estudiante", methods=["GET","POST"])
def registro_estudiante():

    if "usuario" not in session:
        return redirect("/")
    
    if request.method == 'POST':
        try:
            Nombre = request.form["Nombre"]
            Edad = int(request.form["Edad"])
            Carrera = request.form["Carrera"]
            nota1 = float(request.form["nota1"])
            nota2 = float(request.form["nota2"])
            nota3 = float(request.form["nota3"])

            existe = buscar_estudiante(Nombre, Carrera)
            if existe:
                return render_template("registro_estudiante.html", 
                                       error="El Estudiante ya existe en la Carrera")
            

            Promedio = round((nota1 + nota2 + nota3) / 3, 2)
            Desempeño = calcular_desempeño(Promedio)

            insertar_estudiante(Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño)

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


        #----- Leer Archivo. -----
        df = pd.read_excel(archivo)
        df = df.drop(columns=["id"], errors="ignore")


        #----- Limpiar Nombres. -----
        df["Nombre"] = df["Nombre"].astype(str).str.strip()
        df["Nombre"] = df["Nombre"].apply(quitar_acento)
        df["Nombre"] = df["Nombre"].str.title()

        df["Carrera"] = df["Carrera"].astype(str).str.strip()
        df["Carrera"] = df["Carrera"].apply(quitar_acento)
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
            ~(
                (df["nota1"] >= 0) & (df["nota1"] <= 5) &
                (df["nota2"] >= 0) & (df["nota2"] <= 5) &
                (df["nota3"] >= 0) & (df["nota3"] <= 5) 
            )

        ].copy()

        if not notas_invalidas.empty:
            notas_invalidas["Motivo"] = "Notas Inválidas"
            rechazados.append(notas_invalidas)
            
        df = df[
                (df["nota1"] >= 0) & (df["nota1"] <= 5) &
                (df["nota2"] >= 0) & (df["nota2"] <= 5) &
                (df["nota3"] >= 0) & (df["nota3"] <= 5) 
                
                
                ]
            

            #----- Datos Duplicados del Archivo. -----
            
        duplicados = df[df.duplicated(subset=["Nombre", "Carrera"], keep="first")].copy()
        
        if not duplicados.empty:
            duplicados["Motivo"] = "Datos Duplicados"
            rechazados.append(duplicados)
            
        df = df.drop_duplicates(subset=["Nombre", "Carrera"])


            #----- Estudiantes que ya Existen en la BD. -----
            
        existentes = obtener_estudiantes()[["Nombre", "Carrera"]]
        mascara = df.apply(
            lambda r: ((existentes["Nombre"] == r["Nombre"]) &
                       (existentes["Carrera"] == r["Carrera"])).any(), axis=1
            )
        
        ya_existentes = df[mascara].copy()
        if not ya_existentes.empty:
            ya_existentes["Motivo"] = "Estudiante ya existe"
            rechazados.append(ya_existentes)

            df = df[~mascara]


            #----- Calcular el Promedio y Desempeño. -----

            df["Promedio"] = ((df["nota1"] + df["nota2"] + df["nota3"]) / 3).round(2)
            df = df[df["Promedio"] <= 5]

            df["Desempeño"] = df["Promedio"].apply(calcular_desempeño)



            #----- Insertar Datos. -----

            conexion = conectar()
            cursor = conexion.cursor()

            query = """INSERT INTO estudiantes (Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

            existentes = obtener_estudiantes()[["Nombre", "Carrera"]]
            df = df[~df.apply(lambda r: ((existentes["Nombre"] == r["Nombre"]) & (existentes["Carrera"] == r["Carrera"])).any(), axis=1)]

            for _, row in df.iterrows():
                cursor.execute(query, (

                    row["Nombre"],
                    row["Edad"],
                    row["Carrera"],
                    row["nota1"],
                    row["nota2"],
                    row["nota3"],
                    row["Promedio"],
                    row["Desempeño"],
                ))
                
            conexion.commit()
            conexion.close()


            #----- Contar por Categoría. -----

            total_insertados = len(df)
            total_faltantes = len(faltantes) if not faltantes.empty else 0
            total_edad = len(edad_negativa) if not edad_negativa.empty else 0
            total_notas = len(notas_invalidas) if not notas_invalidas.empty else 0
            total_duplicados = len(duplicados) if not duplicados.empty else 0
            total_existentes = len(ya_existentes) if not ya_existentes.empty else 0
            total_rechazados = total_faltantes + total_edad + total_notas + total_duplicados + total_existentes


            #----- Generar Archivo de Rechazados. -----

            if rechazados:
                df_rechazados = pd.concat(rechazados, ignore_index = True)
                ruta = "rechazados.xlsx"
                df_rechazados.to_excel(ruta, index = False)
                hay_rechazados = True

            else:
                hay_rechazados = False

            return render_template("carga_masiva.html",
                                   insertados = total_insertados,
                                   hay_rechazados = hay_rechazados,
                                   resumen = [
                                       {"categoria": "Insertados", "cantidad": total_insertados},
                                       {"categoria": "Rechazados", "cantidad": total_rechazados},
                                       {"categoria": "Duplicados", "cantidad": total_duplicados},

                                   ])
        
        return render_template("carga_masiva.html")
    

    #----- Descargar el Archivo de los Rechazados. -----

@app.route("/descargar_rechazados")
def descargar_rechazados():
    return send_file("rechazados.xlsx", as_attachment= True, download_name="rechazados.xlsx")
    

    #----- Función para quitar Acentos. -----

def quitar_acento(texto):
        if pd.isna(texto):
            return texto
        
        texto = str(texto)

        return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


    #----- Clasificar Desempeño. -----

def calcular_desempeño(promedio):
        if promedio >= 4.5:
            desempeno = "Excelente"
        elif promedio >= 4.0:
            desempeno = "Bueno"
        elif promedio >= 3.0:
            desempeno = "Regular"
        else:
            desempeno = "Deficiente"

        return desempeno
    
    
    #----- Obtener todas las Carreras. -----

@app.route("/obtener_carreras")
def obtener_carreras_api():
        carreras = obtener_carreras()
        return jsonify(carreras)
    

# ======================= SERVIDOR. ========================

if __name__ == "__main__":
    app.run(debug=True)