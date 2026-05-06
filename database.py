import mysql.connector
import pandas as pd

def conectar():
    conexion = mysql.connector.connect(
        host="localhost",
        user = "root",
        password = "",
        database = "notas"
    )

    return conexion

#Obtener Usuarios.
def  obtener_usuario(username):
     #Conectar a la Base de Datos.
        conexion = conectar()
        cursor = conexion.cursor(dictionary = True)

        #Buscar el Usuario en la Base de Datos.
        cursor.execute("SELECT * FROM usuarios WHERE username = %s",(username,))
        usuario = cursor.fetchone()

        conexion.close()

        return usuario


#Obtener los Estudiantes.
def obtener_estudiantes():
     conexion = conectar()
     query = "SELECT * FROM estudiantes"

     df = pd.read_sql(query, conexion)
     conexion.close()

     return df


#Buscar Estudiante por Nombre y Carrera.
def buscar_estudiante(nombre, carrera):
     conexion = conectar()
     cursor = conexion.cursor(dictionary=True)

     cursor.execute("SELECT * FROM estudiantes WHERE Nombre = %s AND Carrera = %s", (nombre, carrera))
     estudiante = cursor.fetchone()

     conexion.close()

     return estudiante



#Registrar Estudiante.

def insertar_estudiante(Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño):
     conexion = conectar()
     cursor = conexion.cursor()

     query = """INSERT INTO estudiantes (Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
     
     cursor.execute(query, (Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño))
     conexion.commit()
     
     conexion.close()


#Registrar Estudiante.
def insertar_estudiante(Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño):
    
     conexion = conectar()
     cursor = conexion.cursor()

     query = """INSERT INTO estudiantes (Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
     
     cursor.execute(query,(Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño))

     conexion.commit()
     
     conexion.close()


#Obtener todas las Carreras.

def obtener_carreras():
     conexion = conectar()
     cursor = conexion.cursor(dictionary=True)

     cursor.execute('SELECT Carrera FROM estudiantes GROUP BY Carrera')
     carreras = cursor.fetchall()

     conexion.close()

     return carreras


if __name__ == "__main__":
    conn = conectar()
    print("¡Conexión Exitosa!")
    conn.close()