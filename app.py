from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect('registros_evento.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_inscritos_count():
    with sqlite3.connect('registros_evento.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM registros')
        count = cursor.fetchone()[0]
    return count

def get_inscritos_acompan_count():
    with sqlite3.connect('registros_evento.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM acompanantes')
        count = cursor.fetchone()[0]
    return count

def calcular_cupos_usados():
    return get_inscritos_count() + get_inscritos_acompan_count()

def create_tables():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            dob TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS acompanantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registro_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (registro_id) REFERENCES registros (id)
        )
    ''')
    conn.commit()
    conn.close()

CUPOS_MAXIMOS = 50

@app.route('/', methods=['GET', 'POST'])
def index():
    mensaje = None
    cupos_usados = calcular_cupos_usados()
    cupos_disponibles = CUPOS_MAXIMOS - cupos_usados

    if request.method == 'POST':
        # Datos del formulario principal
        name = request.form.get('name')
        cedula = request.form.get('cedula')
        oficina = request.form.get('oficina')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        

        # Validación básica
        if not name or not email or not cedula or not phone or not oficina:
            error_message = "Todos los campos son obligatorios."
            return render_template('index.html', error_message=error_message, cupos_disponibles=cupos_disponibles)


        if cupos_disponibles > 0:
            try:
                # Guardar datos del registro principal
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO registros (name, cedula, oficina, phone,email) VALUES (?, ?, ?, ? ,?)',
                               (name, cedula, oficina, phone,email))
                registro_id = cursor.lastrowid

                # Guardar acompañantes
                for i in range(1, 4):  # Recorre los acompañantes del 1 al 3
                    acompanante_name = request.form.get(f'acompanante_name{i}')
                    acompanante_cedula = request.form.get(f'acompanante_cedula{i}')
                    if acompanante_name:  # Verificar si el campo tiene un valor
                        cursor.execute('INSERT INTO acompanantes (registro_id, name, cedula) VALUES (?, ?, ?)',
                                       (registro_id, acompanante_name, acompanante_cedula))

                conn.commit()
                conn.close()
                mensaje = "Registro exitoso."
            except Exception as e:
                error_message = f"Error al guardar los datos: {str(e)}"
                return render_template('index.html', error_message=error_message, cupos_disponibles=cupos_disponibles)
        else:
            mensaje = "No hay cupos disponibles."

    return render_template('index.html', cupos_disponibles=cupos_disponibles, mensaje=mensaje)

@app.route('/cupos_disponibles')
def cupos_disponibles():
    cupos_usados = calcular_cupos_usados()
    cupos = CUPOS_MAXIMOS - cupos_usados
    return jsonify({'cupos_disponibles': cupos})

@app.route('/registros')
def registros():
    conn = get_db_connection()
    registros = conn.execute('SELECT * FROM registros').fetchall()
    acompanantes = conn.execute('SELECT * FROM acompanantes').fetchall()
    conn.close()
    return render_template('registros.html', registros=registros, acompanantes=acompanantes)

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)