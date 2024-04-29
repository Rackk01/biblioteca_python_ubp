import os
from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
from flask_mysqldb import MySQL
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.secret_key = "Facu"

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sitio'
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto recargar plantillas

# Especifica la ruta del directorio de plantillas
app.template_folder = os.path.abspath('templates')

mysql = MySQL(app)

def fetch_one_as_dict(cursor):
    column_names = [d[0] for d in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(column_names, row))
    else:
        return None

@app.route('/')
def inicio():
    return render_template('sitio/index.html')

@app.route('/img/<imagen>')
def imagenes(imagen):
    return send_from_directory(os.path.join('templates/sitio/img'), imagen)

@app.route("/css/<archivocss>")
def css_link(archivocss):
    return send_from_directory(os.path.join('templates/sitio/css'), archivocss)

@app.route('/libros', methods=['GET'])
def libros():
    conexion = mysql.connection.cursor()
    conexion.execute("SELECT * FROM `libros`")
    libros = conexion.fetchall()
    conexion.close()
    return render_template('sitio/libros.html', libros=libros)

@app.route('/buscar', methods=['GET'])
def buscar_libros():
    query = request.args.get('query', '')
    conexion = mysql.connection.cursor()
    conexion.execute("SELECT * FROM libros WHERE nombre LIKE %s", ('%' + query + '%',))
    libros = conexion.fetchall()
    conexion.close()
    return render_template('sitio/libros.html', libros=libros)

@app.route('/libros', methods=['POST'])
def cargar_libros():
    if not 'login' in session:
        return redirect("/admin/login")
    
    _nombre = request.form['txtNombre']
    _url = request.form['txtURL']
    _archivo = request.files['txtImagen']

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')

    nuevoNombre = None  

    if _archivo.filename != "":
        nuevoNombre = horaActual + "_" + _archivo.filename
        _archivo.save("templates/sitio/img/" + nuevoNombre)

    sql = "INSERT INTO `libros` (`id`, `nombre`, `imagen`, `url`) VALUES (NULL,%s,%s,%s);"
    
    # Define datos basado en si hay un nuevo nombre o no
    if nuevoNombre:
        datos = (_nombre, nuevoNombre, _url)
    else:
        datos = (_nombre, _url)

    conexion = mysql.connection.cursor()
    
    if not nuevoNombre:
        flash("No se seleccionó ningún archivo de imagen.", "error")
        return redirect('/admin/libros')

    conexion.execute(sql, datos)
    mysql.connection.commit()  

    print(_nombre)
    print(_url)
    print(_archivo)

    return redirect('/admin/libros')

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['txtNombre']
        apellido = request.form['txtApellido']
        nombre_usuario = request.form['txtUsuario']
        contraseña = request.form['txtContraseña']
        confirmar_contraseña = request.form['txtConfirmarContraseña']

        # Validación de contraseña
        if contraseña != confirmar_contraseña:
            flash("Las contraseñas no coinciden.", "error")
            return redirect('/registro')

        # Encriptación de la contraseña
        hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())

        # Guardar en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO Usuarios (nombre_usuario, nombre, apellido, contraseña, rol) VALUES (%s, %s, %s, %s, %s)",
                       (nombre_usuario, nombre, apellido, hashed_password, 2))  # 2 es el código para el rol de usuario común
        mysql.connection.commit()
        cursor.close()

        flash("¡Registro exitoso! Por favor inicia sesión.", "success")
        # Redirigir automáticamente a la vista usuarios_comunes si el usuario registrado es un usuario común
        return redirect('/usuarios_comunes')

    return render_template('sitio/registro.html')

@app.route('/admin/')
def admin_index():
    if not 'login' in session:
        return redirect("/admin/login")
    else:
        if 'usuario' in session and session['usuario']['rol'] != 2:
            nombre_usuario = session['usuario']['nombre_usuario']  # Acceder al nombre de usuario específico
            return render_template('admin/index.html', nombre_usuario=nombre_usuario)
        else:
            flash('No tienes permiso para acceder a esta página.', 'error')
            return redirect("/")

@app.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    _usuario = request.form['txtUsuario']
    _password = request.form['txtPassword']

    # Consultar la base de datos para obtener el usuario con el nombre proporcionado
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM Usuarios WHERE nombre_usuario = %s", (_usuario,))
    usuario = fetch_one_as_dict(cursor)
    cursor.close()

    # Verificar si el usuario existe y si la contraseña es correcta
    if usuario and bcrypt.checkpw(_password.encode('utf-8'), usuario['contraseña'].encode('utf-8')):
        session["login"] = True
        session["usuario"] = usuario
        return redirect("/admin")
    else:
        return render_template("admin/login.html", mensaje="Acceso denegado")

@app.route('/admin/cerrar')
def admin_login_cerrar():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin/libros')
def admin_libros():
    if not 'login' in session:
        return redirect("/admin/login")
    
    conexion = mysql.connection.cursor()
    conexion.execute("SELECT * FROM `libros`")
    libros = conexion.fetchall()
    conexion.close()  
    return render_template('admin/libros.html', libros=libros)

@app.route('/admin/libros/guardar', methods=['POST'])
def admin_libros_guardar():

    if not 'login' in session:
        return redirect("/admin/login")
    
    _nombre = request.form['txtNombre']
    _url = request.form['txtURL']
    _archivo = request.files['txtImagen']

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')

    if _archivo.filename != "":
        nuevoNombre = horaActual + "_" + _archivo.filename
        _archivo.save("templates/sitio/img/" + nuevoNombre)

    sql = "INSERT INTO `libros` (`id`, `nombre`, `imagen`, `url`) VALUES (NULL,%s,%s,%s);"
    
    # Define datos basado en si hay un nuevo nombre o no
    if nuevoNombre:
        datos = (_nombre, nuevoNombre, _url)
    else:
        datos = (_nombre, _url)

    conexion = mysql.connection.cursor()
    conexion.execute(sql, datos)
    mysql.connection.commit()

    print(_nombre)
    print(_url)
    print(_archivo)

    return redirect('/admin/libros')

@app.route('/admin/libros/borrar', methods=['POST'])
def admin_libros_borrar():

    if not 'login' in session:
        return redirect("/admin/login")

    _id = request.form['txtID']

    # Consulta SQL para obtener el nombre del archivo de imagen del libro a eliminar
    conexion = mysql.connection.cursor()
    conexion.execute("SELECT imagen FROM `libros` WHERE id=%s", (_id,))
    libro = conexion.fetchall()

    # Verificar si el archivo de imagen existe y eliminarlo
    if os.path.exists("templates/sitio/img/" + str(libro[0][0])):
        os.unlink("templates/sitio/img/" + str(libro[0][0]))
    
    # Eliminar el libro de la base de datos
    conexion.execute("DELETE FROM libros WHERE id=%s", (_id,))
    mysql.connection.commit()  

    conexion.close()  # Cerrar el cursor

    return redirect('/admin/libros')

@app.route('/mis_descargas')
def mis_descargas():
    if 'usuario' not in session:
        flash('Debes iniciar sesión para ver tus descargas.', 'warning')
        return redirect('/admin/login')
    
    # Verificar el rol del usuario
    if 'usuario' in session and session['usuario']['rol'] != 2:  # Solo permitir el acceso a usuarios con rol diferente de 2 (usuario)
        # Obtener el ID del usuario actual desde la sesión
        usuario_id = session['usuario']['id']
        
        # Consultar la base de datos para obtener las descargas del usuario
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT libros.nombre, libros.imagen, libros.url FROM libros \
                        INNER JOIN descargas ON libros.id = descargas.libro_id \
                        WHERE descargas.usuario_id = %s", (usuario_id,))
        descargas = cursor.fetchall()
        cursor.close()
        
        return render_template('/sitio/mis_descargas.html', descargas=descargas)
    else:
        flash('No tienes permiso para acceder a esta página.', 'error')
        return redirect('/')

@app.route('/usuarios_comunes')
def usuarios_comunes():
    # Verificar si el usuario ha iniciado sesión y si su rol es 2
    if 'usuario' in session and session['usuario']['rol'] == 2:
        return render_template('sitio/usuario_comun.html')
    else:
        flash('No tienes permiso para acceder a esta página.', 'error')
        return redirect('/')

if __name__ =='__main__':
    app.run(debug=True)
