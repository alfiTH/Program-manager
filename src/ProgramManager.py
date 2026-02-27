# #!/usr/bin/python3
# # -*- coding: utf-8 -*-
# '''Programa de visualización y manejo de programas '''

import psutil
import subprocess
import threading
import argparse
from time import sleep, time
from collections import defaultdict
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from utils.addUser import load_users
from utils.ansiParser import ansi_to_html
from utils.configLoader import loadConfig, saveConfig, TerminalConfiguration
import GPUtil
import secrets
import urllib.parse
import re

__author__ = "Alejandro Torrejón Harto"
__copyright__ = "Copyright 2025, The Program Manager Project"
__credits__ = ["Alejandro Torrejón Harto"]
__license__ = "GNU General Public License v3.0"
__version__ = "0.0.5"
__date__ = "01/03/2025"
__maintainer__ = "Alejandro Torrejón Harto"
__email__ = "atorrejon@unex.es"
__status__ = "Prototype"



os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

CONFIG = {
    "directory": "$HOME/software/vscodium-server",
    "bin": "bin/codium-server",
    "token": secrets.token_hex(16) # Genera un token aleatorio para esta sesión
}

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
CYAN = "\033[0;36m"
RESET = "\033[0m"

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

terminals: dict[int, subprocess.Popen] = {}
terminalsConfig = defaultdict(TerminalConfiguration)


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
    stop_all_processes()
    return redirect(url_for("login"))

def stop_all_processes():
    print("Deteniendo todos los procesos...")
    for id in range(len(terminals)):
        threading.Thread(target=stop_command_process, args=(id,)).start()

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@socketio.on('connect')
def handle_connect():
    for id in range(len(terminalsConfig)):
        socketio.emit("newTerminal", {"id":id, "name":terminalsConfig[id].name, "restart":terminalsConfig[id].restart})
        process = terminals.get(id)
        if process is not None:
            ret = process.poll()
            if ret is None:
                socketio.emit("terminalState", {"id": id, "status": "running"})
            elif ret != 0:
                socketio.emit("terminalState", {"id": id, "status": "error"})
            


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


@socketio.on("runAll")
@login_required
def run_all():
    for id in range(len(terminalsConfig)):
        run_command({"id": id})  # Replace with your real command

@socketio.on("stopAll")
@login_required
def stop_all():
    for id in range(len(terminalsConfig)):
        stop_command({"id": id})

@socketio.on("cleanAll")
@login_required
def clean_all():
    for id in range(len(terminalsConfig)):
        clean_command({"id": id})

@socketio.on("compileAll")
@login_required
def compile_all():
    for id in range(len(terminalsConfig)):
        compile_command({"id": id})

@socketio.on("runCommand")
@login_required
def run_command(data):
    terminal_id = data["id"]
    threading.Thread(target=run_command_process, args=(terminalsConfig[terminal_id].command, terminalsConfig[terminal_id].directory, terminal_id)).start()  # Replace with your real command

@socketio.on("stopCommand")
@login_required
def stop_command(data):
    terminal_id = data["id"]
    threading.Thread(target=stop_command_process, args=(terminal_id,)).start()  # Replace with your real command

@socketio.on("cleanCommand")
@login_required
def clean_command(data):
    terminal_id = data["id"]
    threading.Thread(target=run_command_process, args=([["rm", "-r", "build"]], terminalsConfig[terminal_id].directory, terminal_id)).start()  # Example clean command

@socketio.on("compileCommand")
@login_required
def compile_command(data):
    terminal_id = data["id"]
    threading.Thread(target=run_command_process, args=([["cmake", "-B", "build"],[ "make", "-C", "build", "-j8"]], terminalsConfig[terminal_id].directory, terminal_id)).start()  # Example compile command

@socketio.on("editDirectory")
@login_required
def edit_directory(data):
    terminalsConfig[data["id"]].directory = os.path.expandvars(data["directory"])

@socketio.on("editCommand")
@login_required
def edit_command(data):
    raw_command = os.path.expandvars(data["command"])
    split_commands = re.split(r'&&|;', raw_command)
    terminalsConfig[data["id"]].command = [cmd.strip().split() for cmd in split_commands if cmd.strip()]

@socketio.on("editName")
@login_required
def edit_name(data):
    terminalsConfig[data["id"]].name = data["name"]

@app.route('/get-editor-url')
def get_url():
    terminal_id = int(request.args.get('id'))
    server_ip = request.host.split(':')[0]

    raw_directory = terminalsConfig[terminal_id].directory

    decoded_directory = urllib.parse.unquote(raw_directory)
    final_directory = os.path.expandvars(decoded_directory)

    url = f"http://{server_ip}:{arg.codium_port}?tkn={CONFIG['token']}&folder={final_directory}"

    return {"url": url}

@socketio.on("editRestart")
@login_required
def edit_restart(data):
    terminalsConfig[data["id"]].restart = data["restart"]

@socketio.on("loadConfig")
@login_required
def load_config(data):
    global terminalsConfig
    terminalsConfig = loadConfig(data["directory"])
    handle_connect()
    socketio.emit("configLoaded", {"status": "success"})

@socketio.on("saveConfig")
@login_required
def save_config(data):
    saveConfig(data["directory"], terminalsConfig)


# Intervalo de batching en segundos (100ms)
OUTPUT_BATCH_INTERVAL = 0.1
# Máximo de líneas por batch para evitar mensajes enormes
MAX_LINES_PER_BATCH = 900

def stream_output(pipe, terminal_id, mutex, is_error=False):
    """Lee la salida de un proceso línea por línea en tiempo real y la envía a la terminal.
    Usa batching para reducir el número de emits WebSocket."""
    buffer = []
    last_flush = time()
    
    for line in iter(pipe.readline, ''):
        html_line = ansi_to_html(line.strip())
        with mutex:
            buffer.append(html_line)
        
        now = time()
        if now - last_flush >= OUTPUT_BATCH_INTERVAL or len(buffer) >= MAX_LINES_PER_BATCH:
            with mutex:
                if buffer:
                    socketio.emit("outputBatch", {"id": terminal_id, "lines": buffer})
                    buffer = []
            last_flush = now
    
    # Flush remaining lines
    with mutex:
        if buffer:
            socketio.emit("outputBatch", {"id": terminal_id, "lines": buffer})
    pipe.close()

def run_command_process(commands:list[list[str]], cwd:str, terminal_id:int, monitoring:bool = True):
    for command in commands:
        restart_needed = True
        while restart_needed:
            process = terminals.get(terminal_id)

            if process is None or process.poll() is not None:
                socketio.emit("output", {"id": terminal_id, "text": ansi_to_html(f"\033[32mRun {' '.join(command)}\033[0m")})
                try:
                    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    terminals[terminal_id] = process
                except Exception as e:
                    socketio.emit("output", {"id": terminal_id, "text": ansi_to_html(f"\033[31mError: {e}\033[0m")})
                    socketio.emit("terminalState", {"id": terminal_id, "status": "error"})
                    return
                socketio.emit("terminalState", {"id": terminal_id, "status": "running"})

                mutex = threading.Lock() 
                stdout_thread = threading.Thread(target=stream_output, args=(process.stdout, terminal_id, mutex, False))
                stderr_thread = threading.Thread(target=stream_output, args=(process.stderr, terminal_id, mutex, True))
                stdout_thread.start()
                stderr_thread.start()

                try:
                    if monitoring:
                        target_process = psutil.Process(process.pid)
                        tracked_processes = {} 
                        while process.poll() is None:
                            total_cpu = 0
                            total_ram = 0
                            current_children_pids = []

                            try:
                                # 1. Obtener hijos actuales
                                children = target_process.children(recursive=True)
                                all_processes = [p for p in children if p.name() == 'cc1plus'] if target_process.name() == "make" else [target_process] + children

                                for p in all_processes:
                                    pid = p.pid
                                    current_children_pids.append(pid)
                                    
                                    # 2. Si es un proceso nuevo, lo guardamos para que empiece a medir
                                    if pid not in tracked_processes:
                                        tracked_processes[pid] = p
                                        # La primera vez llamamos con interval=None para inicializar
                                        p.cpu_percent(interval=None) 
                                    
                                    # 3. Sumamos el uso (ahora sí dará un valor real porque el objeto persiste)
                                    try:
                                        total_cpu += tracked_processes[pid].cpu_percent(interval=None)
                                        total_ram += tracked_processes[pid].memory_percent()
                                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                                        pass

                                # 4. Limpiar procesos que ya terminaron del diccionario para no fugar memoria
                                pids_to_remove = [pid for pid in tracked_processes if pid not in current_children_pids]
                                for pid in pids_to_remove:
                                    del tracked_processes[pid]

                            except Exception as e:
                                print(f"Error: {e}")

                            # Emitir y dormir (el sleep ahora es global, no por cada proceso)
                            socketio.emit("resourceUsage", {"id": terminal_id, "cpu": round(total_cpu, 2), "ram": round(total_ram, 2)})
                            sleep(0.5)
                    
                finally:
                    process.wait()
                    socketio.emit("resourceUsage", {"id": terminal_id, "cpu": 0, "ram": 0})
                    stdout_thread.join()
                    stderr_thread.join()

                    if process.poll() is None:
                        socketio.emit("terminalState", {"id": terminal_id, "status": "warning"})
                        return
                    elif process.poll() != 0:
                        if terminalsConfig[terminal_id].restart:
                            print(f"Terminal {terminal_id} failed with code {process.poll()}. Restarting...")
                            sleep(1)
                        else:
                            socketio.emit("terminalState", {"id": terminal_id, "status": "error"})
                            return
                    else:
                        socketio.emit("terminalState", {"id": terminal_id, "status": "ok"})
                        restart_needed = False

            else:
                print(f"Terminal {terminal_id}, yet in use")
                return

           

def stop_command_process(terminal_id):
    process = terminals.get(terminal_id)
    trys = 0
    if process is not None:
        try:
            while process.poll() is None:
                match trys:
                    case 0:
                        print("🔹 Intentando SIGINT (2): Interrumpir de forma amigable.😃")
                        process.send_signal(2) #SIGINT
                    case 1:
                        print("🔹 Intentando SIGTERM (15): Solicitar una terminación limpia.🫣")
                        process.terminate() #SIGTERM
                    case 2:
                        print("🔹 Intentando SIGKILL (9): Forzar la terminación.🤬")
                        process.kill() #SIGKILL
                trys+=1
                sleep(5)
        except Exception as e:
            print(f"⚠️ Error desconocido al enviar SIGINT: {e}")
            return



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Programa de gestión de configuraciones.")
    parser.add_argument(
        '--config', 
        type=str, 
        required=False,
        help="Ruta del archivo de configuración (CSV o JSON)")
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000,
        required=False,
        help="Puerto del servidor")
    parser.add_argument(
        '--codium-port', 
        type=str, 
        default="8000",
        required=False,
        help="Puerto del servidor")
    parser.add_argument(
        '--host', 
        type=str, 
        default="0.0.0.0",
        required=False,
        help="Host del servidor")
    arg = parser.parse_args()

    configPath = arg.config
    if configPath is not None:
        terminalsConfig = loadConfig(arg.config)

    # print(terminalsConfig)
    threading.Thread(target=updateGeneralUsage, daemon=True).start()
    subprocess.Popen(args=[
                        CONFIG["bin"],
                        "--host", arg.host,
                        "--port", arg.codium_port,
                        "--connection-token", CONFIG["token"]],
                    cwd=os.path.expandvars(CONFIG["directory"]),
                    stdout=subprocess.DEVNULL)

    print(f"\n{GREEN}Launch Codium on port {RED}{arg.codium_port}{GREEN} with token {RED}{CONFIG['token']}{RESET}")
    # Habilitar HTTPS (debes tener certificados SSL generados)
    print(f"{GREEN}Launch Program Manager on port {RED}{arg.port}{RESET}\n")
    context = ("certificates/cert.pem", "certificates/key.pem")  # Reemplaza con tus archivos de certificado
    socketio.run(app, host=arg.host, port=arg.port, debug=False, ssl_context=context)
