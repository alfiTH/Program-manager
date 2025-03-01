# #!/usr/bin/python3
# # -*- coding: utf-8 -*-
# '''Programa de visualización y manejo de programas '''

import psutil
import subprocess
import threading
import time
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from utils.addUser import load_users
import GPUtil


__author__ = "Alejandro Torrejón Harto"
__copyright__ = "Copyright 2025, The Program Manager Project"
__credits__ = ["Alejandro Torrejón Harto"]
__license__ = "GNU General Public License v3.0"
__version__ = "0.0.5"
__date__ = "01/03/2025"
__maintainer__ = "Alejandro Torrejón Harto"
__email__ = "atorrejon@unex.es"
__status__ = "Prototype"

# def loadconfig(filename):
#     if filename.endswith('.csv'):
#         return pandas.read_csv(filename, delimiter=";")
#     elif filename.endswith('.json'):
#         return pandas.read_json(filename)
#     else:
#         raise ValueError("Unsupported config file format")



os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

# Configuración de Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave secreta para sesiones
app.config["SESSION_COOKIE_SECURE"] = True  # Asegura que la cookie solo se envíe por HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Evita accesos desde JavaScript
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"  # Previene ataques CSRF
socketio = SocketIO(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Base de datos simulada de usuarios
USERS = load_users()

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in USERS:
        return User(user_id)
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Verificar si el usuario existe y si la contraseña es correcta
        if username in USERS and check_password_hash(USERS[username], password):
            login_user(User(username))
            return redirect(url_for("index"))
        
        return "Error: Nombre de usuario o contraseña incorrectos."
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

def updateGeneralUsage():
    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        gpuDevice:GPUtil.GPUtil.GPU = GPUtil.getGPUs()[0]
        gpu = gpuDevice.load * 100
        vram = gpuDevice.memoryUtil * 100 #todo check

        socketio.emit("generalUsage", {"cpu": cpu, "gpu": gpu, "ram": ram, "vram": vram})
        time.sleep(0.5)

@socketio.on("runCommand")
@login_required
def run_command(data):
    terminal_id = data["id"]
    threading.Thread(target=run_command_process, args=("echo hola", terminal_id)).start()  # Replace with your real command

@socketio.on("cleanCommand")
@login_required
def clean_command(data):
    terminal_id = data["id"]
    threading.Thread(target=run_command_process, args=("rm -r build", terminal_id)).start()  # Example clean command

@socketio.on("compileCommand")
@login_required
def compile_command(data):
    terminal_id = data["id"]
    threading.Thread(target=run_command_process, args=("cmake -B build && make -C build -j8", terminal_id)).start()  # Example compile command

def run_command_process(command, terminal_id):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    error_detected = False

    for line in process.stdout:
        socketio.emit("output", {"id": terminal_id, "text": line})
    for line in process.stderr:
        error_detected = True
        socketio.emit("output", {"id": terminal_id, "text": line})

    status = "error" if error_detected else "ok"
    socketio.emit("finished", {"id": terminal_id, "status": status})

if __name__ == "__main__":
    threading.Thread(target=updateGeneralUsage, daemon=True).start()
    
    # Habilitar HTTPS (debes tener certificados SSL generados)
    context = ("certificates/cert.pem", "certificates/key.pem")  # Reemplaza con tus archivos de certificado
    socketio.run(app, debug=True, ssl_context=context)
