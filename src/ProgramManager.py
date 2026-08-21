#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# '''Program for visualizing and managing programs '''

import psutil
import subprocess
import threading
import argparse
from time import sleep, time
from collections import defaultdict
import glob
import os
import pwd
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from utils.addUser import load_users
from utils.ansiParser import ansi_to_html
from utils.configLoader import loadConfig, saveConfig, TerminalConfiguration
from utils.clientCertAuth import ensure_ca, identify_client_cert
import GPUtil
import secrets
import ssl
import urllib.parse
import re
import pty
import select
import uuid
import shlex

__author__ = "Alejandro Torrejón Harto"
__copyright__ = "Copyright 2025, The Program Manager Project"
__credits__ = ["Alejandro Torrejón Harto"]
__license__ = "GNU General Public License v3.0"
__version__ = "1.0.0"
__date__ = "27/04/2026"
__maintainer__ = "Alejandro Torrejón Harto"
__email__ = "atorrejon@unex.es"
__status__ = "Stable"



os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"

CONFIG = {
    "directory": "$HOME/software/vscodium-server",
    "bin": "bin/codium-server",
    "token": secrets.token_hex(16) # Generates a random token for this session
}

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
CYAN = "\033[0;36m"
RESET = "\033[0m"

# Flask configuration
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for sessions
app.config["SESSION_COOKIE_SECURE"] = True  # Ensures the cookie is only sent over HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevents access from JavaScript
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"  # Prevents CSRF attacks
socketio = SocketIO(app)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

terminalIsStopping = defaultdict(bool)
terminals: dict[str, subprocess.Popen] = {}
terminalsConfig = defaultdict(TerminalConfiguration)
terminalStartTime: dict[str, float] = {}
terminalStdin: dict[str, int] = {}


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

@app.before_request
def try_client_cert_login():
    """Si el navegador presentó un certificado de cliente válido en el handshake TLS
    (SSL_CLIENT_CERT, expuesto por Werkzeug tras validar la cadena contra nuestra CA),
    inicia sesión automáticamente sin pasar por el formulario de contraseña."""
    if current_user.is_authenticated:
        return
    pem = request.environ.get("SSL_CLIENT_CERT")
    if not pem:
        return
    username = identify_client_cert(pem)
    if username is not None and username in USERS:
        login_user(User(username))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check whether the user exists and the password is correct
        if username in USERS and check_password_hash(USERS[username], password):
            login_user(User(username))
            return redirect(url_for("index"))

        return render_template("login.html", error="Error: Incorrect username or password.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    stop_all()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@socketio.on('connect')
def handle_connect():
    for id, config in terminalsConfig.items():
        socketio.emit("newTerminal", {
            "id": id,
            "name": config.name,
            "buildable": config.buildable
        })
        process = terminals.get(id)
        if process is not None:
            ret = process.poll()
            if ret is None:
                socketio.emit("terminalState", {"id": id, "status": "running"})
            elif ret != 0:
                socketio.emit("terminalState", {"id": id, "status": "error"})
            


######################HAEDER###########

# Standard PCI-SIG vendor IDs (not tied to any specific machine — the same
# ID identifies that vendor's hardware on any Linux system).
AMD_VENDOR_ID = "0x1002"
INTEL_VENDOR_ID = "0x8086"


def _read_sysfs_int(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _iter_drm_cards():
    """Yields (card_name, device_path, vendor_id) for every GPU exposed under
    /sys/class/drm on this machine. Purely discovers whatever hardware is
    present — nothing here is specific to any single computer."""
    for path in sorted(glob.glob("/sys/class/drm/card*")):
        card_name = os.path.basename(path)
        if not re.fullmatch(r"card\d+", card_name):
            continue
        device_path = os.path.join(path, "device")
        try:
            with open(os.path.join(device_path, "vendor")) as f:
                vendor = f.read().strip()
        except OSError:
            continue
        yield card_name, device_path, vendor


def get_nvidia_gpus():
    """Returns usage stats for every NVIDIA GPU detected via GPUtil."""
    gpus = []
    try:
        for index, device in enumerate(GPUtil.getGPUs()):
            gpus.append({
                "id": f"nvidia-{index}",
                "name": device.name,
                "vendor": "NVIDIA",
                "load": round(device.load * 100, 2),
                "vram": round(device.memoryUtil * 100, 2),
                "has_vram": True,
            })
    except Exception:
        pass
    return gpus


def get_amd_gpus():
    """Returns usage stats for every AMD GPU (discrete or integrated) found
    under /sys/class/drm, using the amdgpu driver's sysfs interface."""
    gpus = []
    for card_name, device_path, vendor in _iter_drm_cards():
        if vendor != AMD_VENDOR_ID:
            continue

        load = _read_sysfs_int(os.path.join(device_path, "gpu_busy_percent"))

        vram_used = _read_sysfs_int(os.path.join(device_path, "mem_info_vram_used"))
        vram_total = _read_sysfs_int(os.path.join(device_path, "mem_info_vram_total"))
        has_vram = bool(vram_total)
        vram_pct = round(vram_used / vram_total * 100, 2) if has_vram else 0

        gpus.append({
            "id": f"amd-{card_name}",
            "name": f"AMD GPU ({card_name})",
            "vendor": "AMD",
            "load": load if load is not None else 0,
            "vram": vram_pct,
            "has_vram": has_vram,
        })
    return gpus


def get_intel_gpus():
    """Returns usage stats for every Intel GPU (almost always integrated)
    found under /sys/class/drm. Intel's i915 driver doesn't expose a direct
    busy-percent counter like amdgpu does, so load is estimated from the
    ratio of current to max GT frequency; if the running kernel/driver
    doesn't expose those files (e.g. the newer Xe driver), load falls back
    to 0 rather than the GPU being omitted. Integrated Intel GPUs share
    system RAM, so no VRAM figure is reported."""
    gpus = []
    for card_name, device_path, vendor in _iter_drm_cards():
        if vendor != INTEL_VENDOR_ID:
            continue

        card_path = os.path.dirname(device_path)
        act_freq = _read_sysfs_int(os.path.join(card_path, "gt_act_freq_mhz"))
        max_freq = _read_sysfs_int(os.path.join(card_path, "gt_max_freq_mhz"))
        load = round(act_freq / max_freq * 100, 2) if act_freq is not None and max_freq else 0

        gpus.append({
            "id": f"intel-{card_name}",
            "name": f"Intel GPU ({card_name})",
            "vendor": "Intel",
            "load": load,
            "vram": 0,
            "has_vram": False,
        })
    return gpus


def get_gpus():
    """Returns usage stats for every GPU in the system, across all vendors
    (including integrated ones), so multi-GPU setups are all represented.
    Detection is fully dynamic (PCI vendor IDs + /sys/class/drm), so this
    works unmodified on any machine, not just the one it was written on."""
    return get_nvidia_gpus() + get_amd_gpus() + get_intel_gpus()


def updateGeneralUsage():
    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        gpus = get_gpus()

        socketio.emit("generalUsage", {"cpu": cpu, "ram": ram, "gpus": gpus})
        sleep(0.5)


@socketio.on("runAll")
@login_required
def run_all():
    for id in terminalsConfig.keys():
        run_command({"id": id})

@socketio.on("stopAll")
@login_required
def stop_all():
    for id in terminalsConfig.keys():
        stop_command({"id": id})

@socketio.on("cleanAll")
@login_required
def clean_all():
    for id in terminalsConfig.keys():
        clean_command({"id": id})

@socketio.on("compileAll")
@login_required
def compile_all(data=None):
    try:
        batch_size = max(1, int((data or {}).get("batchSize", 2)))
    except (TypeError, ValueError):
        batch_size = 2
    try:
        jobs = max(1, int((data or {}).get("jobs", 4)))
    except (TypeError, ValueError):
        jobs = 4

    semaphore = threading.Semaphore(batch_size)

    def worker(terminal_id):
        with semaphore:
            _compile_terminal_blocking(terminal_id, jobs)

    for id in terminalsConfig.keys():
        threading.Thread(target=worker, args=(id,)).start()

@socketio.on("createTerminal")
@login_required
def create_terminal():
    id = str(uuid.uuid4())
    terminalsConfig[id] = TerminalConfiguration()
    socketio.emit("newTerminal", {
        "id": id,
        "name": terminalsConfig[id].name,
        "buildable": terminalsConfig[id].buildable
    })

@socketio.on("runCommand")
@login_required
def run_command(data):
    terminal_id = data["id"]
    print(terminal_id)

    expanded_dir = os.path.expandvars(terminalsConfig[terminal_id].directory)
    expanded_cmd = [[os.path.expandvars(tok) for tok in cmd] for cmd in terminalsConfig[terminal_id].command]
    threading.Thread(target=run_command_process, args=(expanded_cmd, expanded_dir, terminal_id), kwargs={"check_dependencies": True}).start()

@socketio.on("stopCommand")
@login_required
def stop_command(data):
    terminal_id = data["id"]
    threading.Thread(target=stop_command_process, args=(terminal_id,)).start()

@socketio.on("cleanCommand")
@login_required
def clean_command(data):
    terminal_id = data["id"]
    if terminalsConfig[terminal_id].buildable:
        expanded_dir = os.path.expandvars(terminalsConfig[terminal_id].directory)
        threading.Thread(target=run_command_process, args=([["rm", "-r", "build"]], expanded_dir, terminal_id)).start()

def _compile_terminal_blocking(terminal_id, jobs=8):
    if not terminalsConfig[terminal_id].buildable:
        return
    expanded_dir = os.path.expandvars(terminalsConfig[terminal_id].directory)
    run_command_process([["cmake", "-B", "build"], ["make", "-C", "build", f"-j{jobs}"]], expanded_dir, terminal_id)

@socketio.on("compileCommand")
@login_required
def compile_command(data):
    terminal_id = data["id"]
    threading.Thread(target=_compile_terminal_blocking, args=(terminal_id,)).start()

@socketio.on("editDirectory")
@login_required
def edit_directory(data):
    # Stored as-is (without expanding $VAR) so that save preserves the original.
    terminalsConfig[data["id"]].directory = data["directory"]

@socketio.on("editCommand")
@login_required
def edit_command(data):
    split_commands = re.split(r'&&|;', data["command"])
    terminalsConfig[data["id"]].command = [cmd.strip().split() for cmd in split_commands if cmd.strip()]

@socketio.on("editRobocomp")
@login_required
def edit_robocomp(data):
    terminalsConfig[data["id"]].robocomp = data["robocomp"]

@socketio.on("editDependsOn")
@login_required
def edit_depends_on(data):
    """Input format: 'nameA:seconds, nameB:seconds'."""
    depends_on = []
    for part in data["dependsOn"].split(","):
        part = part.strip()
        if not part:
            continue
        name, _, seconds = part.rpartition(":")
        name = name.strip()
        if not name:
            continue
        try:
            seconds = float(seconds)
        except ValueError:
            seconds = 0
        depends_on.append({"name": name, "seconds": seconds})
    terminalsConfig[data["id"]].depends_on = tuple(depends_on)

@socketio.on("execQuick")
@login_required
def exec_quick(data):
    terminal_id = data["id"]
    text = data["command"]
    if not text or not text.strip():
        return

    process = terminals.get(terminal_id)
    if process is not None and process.poll() is None:
        # Terminal busy: sent as stdin to the running process (e.g. to
        # answer an input() the program is waiting on).
        fd = terminalStdin.get(terminal_id)
        try:
            os.write(fd, (text + "\n").encode())
        except (OSError, TypeError) as e:
            socketio.emit("output", {"id": terminal_id, "text": ansi_to_html(f"\033[31mError writing to stdin: {e}\033[0m")})
        return

    # Terminal free: launched as a new ad-hoc command, same pipeline as "Run".
    try:
        argv = shlex.split(text)
    except ValueError as e:
        socketio.emit("output", {"id": terminal_id, "text": ansi_to_html(f"\033[31mError parsing command: {e}\033[0m")})
        return
    if not argv:
        return

    expanded_dir = os.path.expandvars(terminalsConfig[terminal_id].directory)
    threading.Thread(target=run_command_process, args=([argv], expanded_dir, terminal_id)).start()

@socketio.on("editName")
@login_required
def edit_name(data):
    terminalsConfig[data["id"]].name = data["name"]

@app.route('/get-editor-url')
def get_url():
    terminal_id = request.args.get('id')
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

@socketio.on("editBuildable")
@login_required
def edit_buildable(data):
    terminalsConfig[data["id"]].buildable = data["buildable"]

@socketio.on("deleteTerminal")
@login_required
def delete_terminal(data):
    terminal_id = data["id"]
    # Stop the process if it's running
    if terminal_id in terminals:
        stop_command_process(terminal_id)
        del terminals[terminal_id]
    # Remove configuration
    if terminal_id in terminalsConfig:
        del terminalsConfig[terminal_id]
    socketio.emit("terminalDeleted", {"id": terminal_id})

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


@app.route('/get-terminal-config')
@login_required
def get_terminal_config():
    terminal_id = request.args.get('id')
    if terminal_id in terminalsConfig:
        config = terminalsConfig[terminal_id]
        command_str = " ".join(" ".join(cmd) for cmd in config.command)
        depends_on_str = ", ".join(f"{dep['name']}:{dep['seconds']}" for dep in config.depends_on)
        return {
            "name": config.name,
            "directory": config.directory,
            "command": command_str,
            "restart": config.restart,
            "buildable": config.buildable,
            "robocomp": config.robocomp,
            "dependsOn": depends_on_str
        }
    return {"error": "Terminal not found"}, 404


# Batching interval in seconds (100ms)
OUTPUT_BATCH_INTERVAL = 0.1
# Maximum lines per batch to avoid huge messages
MAX_LINES_PER_BATCH = 900

def stream_output(master_fd, terminal_id, mutex, is_error=False):
    """Reads a process's output line by line in real time and sends it to the terminal.
    Uses batching to reduce the number of WebSocket emits."""
    buffer = []
    last_flush = time()

    # Set the descriptor to non-blocking mode
    os.set_blocking(master_fd, False)

    try:
        while True:
            # Wait for data (0.1s timeout to allow the time-based flush)
            r, _, _ = select.select([master_fd], [], [], 0.1)

            if r:
                try:
                    raw_bytes = os.read(master_fd, 8192)
                    if not raw_bytes:
                        break

                    # Decode. Important: we do NOT use splitlines here
                    # so we don't lose \r or \n
                    text_chunk = raw_bytes.decode('utf-8', errors='ignore')

                    # Pass the whole chunk to the ANSI parser
                    # ansi_to_html should return the HTML while keeping \r and \n
                    html_piece = ansi_to_html(text_chunk)

                    with mutex:
                        buffer.append(html_piece)

                except (OSError, UnicodeDecodeError):
                    break

            # Batching logic
            now = time()
            if buffer and (now - last_flush >= OUTPUT_BATCH_INTERVAL or len(buffer) >= MAX_LINES_PER_BATCH):
                with mutex:
                    # Send the batch. The frontend should concatenate these strings.
                    socketio.emit("outputBatch", {"id": terminal_id, "lines": buffer})
                    buffer = []
                last_flush = now
    finally:
        # Before closing, send whatever is left in the buffer
        with mutex:
            if buffer:
                socketio.emit("outputBatch", {"id": terminal_id, "lines": buffer})
                buffer = []

            try:
                os.close(master_fd)
            except OSError:
                pass

def find_terminal_id_by_name(name):
    """Resolves a terminal name to its current id. Ids are regenerated on every
    loadConfig, so dependencies must reference terminals by name, not by id.
    If there are duplicate names, the first match is returned."""
    for tid, cfg in terminalsConfig.items():
        if cfg.name == name:
            return tid
    return None

def dependencies_ready(terminal_id):
    """Checks whether all of a terminal's timed dependencies are already satisfied.
    Returns (True, None) if it can start, or (False, reason) if it must wait."""
    for dep in terminalsConfig[terminal_id].depends_on:
        dep_id = find_terminal_id_by_name(dep["name"])
        if dep_id is None:
            return False, f"dependency '{dep['name']}' not found"
        start = terminalStartTime.get(dep_id)
        if start is None:
            return False, f"waiting for '{dep['name']}' to start"
        if time() - start < dep["seconds"]:
            return False, f"waiting for '{dep['name']}' to run {dep['seconds']}s"
    return True, None

def run_command_process(commands:list[list[str]], cwd:str, terminal_id:int, monitoring:bool = True, check_dependencies:bool = False):
    if check_dependencies:
        while True:
            if terminal_id not in terminalsConfig or terminalIsStopping.get(terminal_id, False):
                terminalIsStopping[terminal_id] = False
                return
            ready, _reason = dependencies_ready(terminal_id)
            if ready:
                break
            socketio.emit("terminalState", {"id": terminal_id, "status": "waiting"})
            sleep(0.3)

    for command in commands:
        restart_needed = True
        while restart_needed:
            process = terminals.get(terminal_id)
            masterOut_fd, slaveOut_fd = pty.openpty()
            masterErr_fd, slaveErr_fd = pty.openpty()

            if process is None or process.poll() is not None:
                socketio.emit("output", {"id": terminal_id, "text": ansi_to_html(f"\033[32mRun {' '.join(command)}\033[0m")})
                try:
                    process = subprocess.Popen(command, cwd=cwd, stdin=slaveOut_fd, stdout=slaveOut_fd, stderr=slaveErr_fd, text=True,
                                                env={**os.environ.copy(), "FORCE_COLOR": "true", "TERM": "xterm-256color"},
                                                bufsize=1)
                    terminals[terminal_id] = process
                    terminalStartTime[terminal_id] = time()
                    terminalStdin[terminal_id] = masterOut_fd
                    os.close(slaveOut_fd)
                    os.close(slaveErr_fd)

                except Exception as e:
                    socketio.emit("output", {"id": terminal_id, "text": ansi_to_html(f"\033[31mError: {e}\033[0m")})
                    socketio.emit("terminalState", {"id": terminal_id, "status": "error"})
                    return
                socketio.emit("terminalState", {"id": terminal_id, "status": "running"})

                mutex = threading.Lock() 
                stdout_thread = threading.Thread(target=stream_output, args=(masterOut_fd, terminal_id, mutex, False))
                stderr_thread = threading.Thread(target=stream_output, args=(masterErr_fd, terminal_id, mutex, True))
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
                                # 1. Get current children
                                children = target_process.children(recursive=True)
                                all_processes = [p for p in children if p.name() == 'cc1plus'] if target_process.name() == "make" else [target_process] + children

                                for p in all_processes:
                                    pid = p.pid
                                    current_children_pids.append(pid)

                                    # 2. If it's a new process, store it so it starts being measured
                                    if pid not in tracked_processes:
                                        tracked_processes[pid] = p
                                        # First call with interval=None to initialize
                                        p.cpu_percent(interval=None)

                                    # 3. Add up usage (now gives a real value because the object persists)
                                    try:
                                        total_cpu += tracked_processes[pid].cpu_percent(interval=None)
                                        total_ram += tracked_processes[pid].memory_percent()
                                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                                        pass

                                # 4. Clean up finished processes from the dict to avoid leaking memory
                                pids_to_remove = [pid for pid in tracked_processes if pid not in current_children_pids]
                                for pid in pids_to_remove:
                                    del tracked_processes[pid]

                            except Exception as e:
                                print(f"Error: {e}")

                            # Emit and sleep (the sleep is now global, not per process)
                            socketio.emit("resourceUsage", {"id": terminal_id, "cpu": round(total_cpu, 2), "ram": round(total_ram, 2)})
                            sleep(0.5)
                    
                finally:
                    process.wait()
                    terminalStartTime[terminal_id] = None
                    terminalStdin.pop(terminal_id, None)
                    socketio.emit("resourceUsage", {"id": terminal_id, "cpu": 0, "ram": 0})
                    stdout_thread.join()
                    stderr_thread.join()

                    if process.poll() is None:
                        socketio.emit("terminalState", {"id": terminal_id, "status": "warning"})
                        restart_needed = False
                    elif process.poll() != 0:
                        if terminalsConfig[terminal_id].restart and not terminalIsStopping.get(terminal_id, False):
                            print(f"Terminal {terminal_id} failed with code {process.poll()}. Restarting...")
                            sleep(1)
                        else:
                            socketio.emit("terminalState", {"id": terminal_id, "status": "error"})
                            restart_needed = False
                    else:
                        socketio.emit("terminalState", {"id": terminal_id, "status": "ok"})
                        restart_needed = False
                    terminalIsStopping[terminal_id] = False

            else:
                print(f"Terminal {terminal_id}, yet in use")
                return

           

def stop_command_process(terminal_id):
    # process = terminals.get(terminal_id)
    # trys = 0
    # if process is not None or terminalIsStopping.get(terminal_id, False):
    #     terminalIsStopping[terminal_id] = True
    #     try:
    #         while process.poll() is None:
    #             match trys:
    #                 case 0:
    #                     print("🔹 Trying SIGINT (2): Gracefully interrupt process.😃")
    #                     process.send_signal(2) #SIGINT
    #                 case 1:
    #                     print("🔹 Trying SIGTERM (15): Request a clean termination.🫣")
    #                     process.terminate() #SIGTERM
    #                 case 2:
    #                     print("🔹 Trying SIGKILL (9): Force termination.🤬")
    #                     process.kill() #SIGKILL
    #             trys+=1
    #             sleep(5)
    #     except Exception as e:
    #         print(f"⚠️ Unknown error sending SIGINT: {e}")
    #         return
    # # # Always marked, even without a process yet: allows canceling a
    # # # dependency wait in progress inside run_command_process.
    terminalIsStopping[terminal_id] = True
    process = terminals.get(terminal_id)
    if process is None or process.poll() is not None:
        return
    try:
        # Collect the whole tree: killing only the parent process can leave
        # its children orphaned (e.g. "make -j8" workers).
        parent = psutil.Process(process.pid)
        procs = parent.children(recursive=True) + [parent]
    except psutil.NoSuchProcess:
        return

    for sig, label in (
        (2, "SIGINT (2): Gracefully interrupt process.😃"),
        (15, "SIGTERM (15): Request a clean termination.🫣"),
        (9, "SIGKILL (9): Force termination.🤬"),
    ):
        print(f"🔹 Trying {label}")
        for p in procs:
            try:
                p.send_signal(sig)
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(procs, timeout=5)
        if not alive:
            return
        procs = alive

    print(f"⚠️ Terminal {terminal_id}: PIDs {[p.pid for p in procs]} survived SIGKILL")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configuration management program.")
    parser.add_argument(
        '--addUser', 
        action="store_true",
        help="Flag to add a new user")
    parser.add_argument(
        '--config', 
        type=str, 
        required=False,
        help="Path to the configuration file (CSV or JSON)")
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000,
        required=False,
        help="Port of the server")
    parser.add_argument(
        '--codium-port', 
        type=str, 
        default="8000",
        required=False,
        help="Port of the Codium server")
    parser.add_argument(
        '--host', 
        type=str, 
        default="localhost",
        required=False,
        help="Host of the server (if you want remote access use 0.0.0.0)")
    parser.add_argument(
        '--addClientCert',
        action="store_true",
        help="Flag to issue a client certificate (.p12) for an existing user")
    parser.add_argument(
        '--revokeClientCert',
        action="store_true",
        help="Flag to revoke a previously issued client certificate")
    parser.add_argument(
        '--cert-only',
        action="store_true",
        help="Flag to require a valid client certificate for every connection, disabling password login entirely (mutual TLS)")
    parser.add_argument(
        '--debug',
        action="store_true",
        help="Flag to enable debug mode")
    arg = parser.parse_args()

    if arg.addUser:
        from utils.addUser import add_user
        add_user()
        exit(0)

    if arg.addClientCert:
        from utils.issueClientCert import add_client_cert
        add_client_cert()
        exit(0)

    if arg.revokeClientCert:
        from utils.revokeClientCert import revoke_client_cert_cli
        revoke_client_cert_cli()
        exit(0)

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
    
    # Enable HTTPS (you must have SSL certificates generated)
    print(f"{GREEN}Launch Program Manager on port {RED}{arg.port}{RESET}\n")

    ca_cert_path = ensure_ca()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("certificates/cert.pem", "certificates/key.pem")  # Replace with your certificate files
    context.load_verify_locations(cafile=ca_cert_path)
    if arg.cert_only:
        print(f"{YELLOW}Client-certificate-only mode: password login is disabled, a valid client certificate is required to connect.{RESET}\n")
        context.verify_mode = ssl.CERT_REQUIRED
    else:
        context.verify_mode = ssl.CERT_OPTIONAL

    socketio.run(app, host=arg.host, port=arg.port, debug=arg.debug, ssl_context=context)
