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
def  obtener_usuarios(username):
     #Conectar a la Base de Datos.
        conn = conectar()
        cursor = conn.cursor(dictionary = True)
        #Buscar el Usuario en la Base de Datos.
        cursor.execute("SELECT * FROM usuarios WHERE username = %s",(username,))
        usuario = cursor.fetchone()
        conn.close()
        return usuario

#Obtener los Estudiantes.
def obtener_estudiantes():
     conn = conectar()
     query = "SELECT * FROM estudiantes"
     df = pd.read_sql(query, conn)
     conn.close()

     return df

#Función Nueva ---- Verificar si el Estudiante ya existe en el Sistema.

def estudiante_existe(nombre, carrera):

    conn = conectar()
    cursor = conn.cursor()

    query = """
    SELECT COUNT(*) 
    FROM estudiantes
    WHERE Nombre = %s AND Carrera = %s
    """

    cursor.execute(query, (nombre, carrera))
    resultado = cursor.fetchone()[0]

    conn.close()

    return resultado > 0


#Registrar Estudiante.

def insertar_estudiante(nombre, edad, carrera, nota1, nota2, nota3, promedio, desempeno):
    
     conn = conectar()
     cursor = conn.cursor()

     query = """INSERT INTO estudiantes (Nombre, Edad, Carrera, nota1, nota2, nota3, Promedio, Desempeño) values (%s, %s, %s, %s, %s, %s, %s, %s)"""
     
     cursor.execute(query,(nombre, edad, carrera, nota1, nota2, nota3, promedio, desempeno))
     
     conn.commit()
     conn.close()


if __name__ == "__main__":
    conn = conectar()
    print("¡Conexión Exitosa!")
    conn.close()