# #!/usr/bin/python3
# # -*- coding: utf-8 -*-
# '''Programa de visualización y manejo de programas '''

import psutil
import subprocess
import threading
from time import sleep
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

terminals: dict[int,subprocess.Popen] = {}

# Base de datos simulada de usuarios
USERS = load_users()




############################BASIC FLASK###########################3
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


######################HAEDER###########3

def updateGeneralUsage():
    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        gpuDevice:GPUtil.GPUtil.GPU = GPUtil.getGPUs()[0]
        gpu = gpuDevice.load * 100
        vram = gpuDevice.memoryUtil * 100 #todo check

        socketio.emit("generalUsage", {"cpu": cpu, "gpu": gpu, "ram": ram, "vram": vram})
        sleep(0.5)





@socketio.on("runCommand")
@login_required
def run_command(data):
    terminal_id = data["id"]
    threading.Thread(target=run_command_process, args=(f"python3 tmp/hola/src/hola.py", terminal_id)).start()  # Replace with your real command

@socketio.on("stopCommand")
@login_required
def stop_command(data):
    terminal_id = data["id"]
    threading.Thread(target=stop_command_process, args=(terminal_id,)).start()  # Replace with your real command

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


def stream_output(pipe, terminal_id, mutex, is_error=False):
    """Lee la salida de un proceso línea por línea en tiempo real y la envía a la terminal."""
    for line in iter(pipe.readline, ''):
        with mutex:  # Bloquea para evitar mezclas de salida
            socketio.emit("output", {"id": terminal_id, "text": line.strip()})
    pipe.close()


def run_command_process(command, terminal_id):
    process = terminals.get(terminal_id)

    if process is None or process.poll() is not None:
        
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        mutex = threading.Lock() 
        stdout_thread = threading.Thread(target=stream_output, args=(process.stdout, terminal_id, mutex, False))
        stderr_thread = threading.Thread(target=stream_output, args=(process.stderr, terminal_id, mutex, True))

        stdout_thread.start()
        stderr_thread.start()

        terminals[terminal_id] = process

        try:
            psProcess = psutil.Process(process.pid).children()[0]
            while process.poll() is None:
            
                socketio.emit("resourceUsage", {"id": terminal_id, 
                                                "cpu": round(psProcess.cpu_percent(interval=2), 5) , 
                                                "ram":round(psProcess.memory_percent(), 5)})
        except IndexError:
            print(f"Error: No child process found for terminal {terminal_id}")
            return
        except FileNotFoundError:
            pass
        except psutil.NoSuchProcess:
            pass

        socketio.emit("resourceUsage", {"id": terminal_id, "cpu": 0 , "ram":0})

        process.wait()
        stdout_thread.join()
        stderr_thread.join()
    else:
        print(f"Terminal {terminal_id}, yet in use")

def stop_command_process(terminal_id):
    process = terminals.get(terminal_id)
    trys = 0
    if process is not None:
        try:
            psProcess = psutil.Process(process.pid).children()[0]
        except IndexError:
            print(f"Error: No child process found for terminal {terminal_id}")
            return
        
        try:
            while psProcess.is_running():
                match trys:
                    case 0:
                        print("🔹 Intentando SIGINT (2): Interrumpir de forma amigable.😃")
                        psProcess.send_signal(2) #SIGINT
                    case 1:
                        print("🔹 Intentando SIGTERM (15): Solicitar una terminación limpia.🫣")
                        psProcess.send_signal(15) #SIGTERM
                    case 2:
                        print("🔹 Intentando SIGKILL (9): Forzar la terminación.🤬")
                        psProcess.send_signal(9) #SIGKILL
                trys+=1
                sleep(5)

        except psutil.NoSuchProcess:
            print(f"⚠️ Proceso {terminal_id} ya ha terminado o no existe.")
            return
        except psutil.AccessDenied:
            print(f"⚠️ Acceso denegado al proceso {terminal_id}.")
            return
        except Exception as e:
            print(f"⚠️ Error desconocido al enviar SIGINT: {e}")
            return



if __name__ == "__main__":
    threading.Thread(target=updateGeneralUsage, daemon=True).start()
    
    # Habilitar HTTPS (debes tener certificados SSL generados)
    context = ("certificates/cert.pem", "certificates/key.pem")  # Reemplaza con tus archivos de certificado
    socketio.run(app, debug=True, ssl_context=context)
