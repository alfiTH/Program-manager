# Program Manager Web

Program Manager Web is a browser-based control panel for running and monitoring multiple long-lived programs (e.g. robotics components, services, build pipelines) on a remote or local machine. It replaces a wall of SSH terminals with one dashboard: start/stop/build/clean each program, watch its live output, and keep an eye on system resources — all from a single HTTPS page.

## Key Features

- **Multi-terminal management** — create any number of independent terminal instances, each with its own working directory, command, and live output panel (ANSI colors included).
- **Run / Stop / Clean / Build per terminal**
  - **Run**: launches the configured command; supports quick ad-hoc commands typed into the terminal, which are sent to the running process's stdin if it's busy, or launched as a new command if it's idle.
  - **Stop**: terminates the process tree, escalating from `SIGINT` to `SIGTERM` to `SIGKILL`.
  - **Clean**: removes the `build` directory.
  - **Build**: runs `cmake -B build && make -C build -jN`.
  - Both Clean and Build are disabled (visually and server-side) for terminals marked as not buildable.
- **Batch-limited "Build All"** — rebuilds every terminal at once, with configurable **batch size** (max builds running concurrently) and **`-j`** (compiler jobs per build), so a full rebuild doesn't saturate RAM/CPU.
- **Auto-restart** — a terminal can be configured to relaunch its command automatically if the process exits.
- **Startup dependencies** — a terminal can wait for other terminals to be running (with a configurable delay in seconds) before it starts, useful for ordered startup of interdependent components.
- **Real-time resource monitoring** — global CPU/RAM usage plus per-terminal CPU/RAM, and GPU load/VRAM for NVIDIA (via `GPUtil`), AMD, and Intel GPUs (via sysfs), rendered as gauges that fill the available width.
- **VSCodium integration** — open a web-based VSCodium instance scoped to a terminal's working directory directly from the dashboard.
- **Configuration management** — load and save terminal setups (name, directory, command, restart/buildable flags, dependencies) as JSON files, so a whole session can be restored in one click.
- **User authentication** — login system backed by `users.json`, with passwords hashed via `utils/addUser.py`. Optionally, users can instead (or additionally) authenticate with a client TLS certificate issued by the app's own private CA — no password prompt, works in any normal browser (desktop or Android), and can be enforced exclusively with `--cert-only`.
- **Collapsible terminals** — hide/show individual terminals or all of them at once to keep the layout manageable when running many programs.

## Prerequisites

Python dependencies (listed in `requeriments.txt`):
- `flask`
- `flask-socketio`
- `flask-login`
- `psutil`
- `gputil`

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alfiTH/Program-manager.git
   cd Program-manager
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requeriments.txt
   ```

3. **Install VSCodium server** (used for the in-browser code editor):
   ```bash
   mkdir ~/software 2> /dev/null; cd ~/software
   wget https://github.com/VSCodium/vscodium/releases/download/1.109.21026/vscodium-reh-web-linux-x64-1.109.21026.tar.gz
   mkdir vscodium-server
   tar -xzf vscodium-reh-web-linux-x64-1.109.21026.tar.gz -C vscodium-server
   cd -
   ```
   By default the app expects this at `$HOME/software/vscodium-server`; change the `directory` entry in `CONFIG` at the top of `src/ProgramManager.py` if you installed it elsewhere.

## Configuration

### SSL certificates
The application only runs over HTTPS. Generate a certificate/key pair inside `certificates/`:
```bash
cd certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
cd -
```

### Users
Users live in `users.json` with hashed passwords. Add one with:
```bash
python3 src/ProgramManager.py --addUser
```

### Client certificate login (mutual TLS)
As an alternative to passwords, a user can authenticate with a TLS client certificate.
The app acts as its own private Certificate Authority (created automatically on first use,
at `certificates/ca_cert.pem` / `certificates/ca_key.pem`) and only ever trusts certificates
it issued itself — no external authenticator, no third-party account, no browser prompt.
Once the certificate is installed, login is completely transparent: the browser presents it
during the TLS handshake and the dashboard opens directly, with no login form at all.

1. Issue a certificate for an existing user (also creates the CA the first time it's run):
   ```bash
   python3 src/ProgramManager.py --addClientCert
   ```
   This writes a password-protected bundle to `client_certs/<user>-<label>.p12`. Transfer it
   to the user's device over a channel you trust, then delete the copy on the server.
2. Install the `.p12` on the target device:
   - **Desktop**: double-click it (or import it via the browser's/OS's certificate settings)
     and enter the password you set when issuing it.
   - **Android**: Settings → Security → "Install a certificate" (wording varies by
     manufacturer/version), select the `.p12` file, and enter the password.
3. Reload the dashboard — the browser will use the certificate automatically. By default
   (no `--cert-only`), password login still works for anyone without a certificate.

To **enforce** certificate-only access — no password login reachable at all, refused at the
TLS handshake itself, like requiring mutual TLS on a corporate VPN — start the server with:
```bash
python3 src/ProgramManager.py --config etc/config.json --cert-only
```
In this mode, a browser without a valid certificate can't complete the TLS handshake at all
(it will show a generic connection error, not a custom page) — keep this in mind before
enabling it, and make sure every user has a certificate first.

Revoke a lost or compromised certificate (it stops being accepted immediately, without
touching the CA or anyone else's certificate):
```bash
python3 src/ProgramManager.py --revokeClientCert
```

### Terminal configuration files
A configuration file (JSON) describes the terminals to load at startup — see `etc/config.json` for examples. Each entry supports:
```json
{
  "name": "my_component",
  "directory": "$ROBOCOMP/components/my_component",
  "command": "bin/my_component etc/config",
  "restart": false,
  "buildable": true,
  "robocomp": false,
  "depends_on": [{ "name": "other_component", "seconds": 3 }]
}
```
Configurations can also be loaded/saved from the running dashboard via **Load Configuration** / **Save Configuration**.

## Usage

1. **Start the server**:
   ```bash
   python3 src/ProgramManager.py --config etc/config.json
   ```
   Useful flags:
   | Flag | Default | Description |
   |---|---|---|
   | `--config PATH` | — | Terminal configuration file to load at startup |
   | `--port PORT` | `5000` | Port for the web dashboard |
   | `--codium-port PORT` | `8000` | Port for the embedded VSCodium server |
   | `--host HOST` | `localhost` | Bind address (use `0.0.0.0` for remote access) |
   | `--cert-only` | off | Require a valid client certificate for every connection (disables password login) |
   | `--debug` | off | Run Flask in debug mode |
   | `--addUser` | — | Add a new user and exit |
   | `--addClientCert` | — | Issue a client certificate (`.p12`) for an existing user and exit |
   | `--revokeClientCert` | — | Revoke a previously issued client certificate and exit |

2. **Access the dashboard**:
   Open `https://<server_ip>:5000` (or `https://localhost:5000`) in your browser. Since certificates are self-signed, you'll need to accept the browser security warning.

3. **Log in** with a user created via `--addUser`.

## Project Structure

- `src/`
  - `ProgramManager.py` — Flask/Socket.IO application: terminal lifecycle, resource monitoring, config load/save.
  - `templates/` — `index.html` (dashboard) and `login.html`.
  - `utils/` — `addUser.py` (user management), `clientCertAuth.py` (private CA + client certificate issuance/verification), `issueClientCert.py` / `revokeClientCert.py` (client cert CLI), `ansiParser.py` (ANSI-to-HTML), `configLoader.py` (config load/save).
- `etc/` — Sample terminal configuration files.
- `certificates/` — Server SSL certificate/key for HTTPS, plus the app's private CA (`ca_cert.pem` / `ca_key.pem`) used to issue and verify client certificates.
- `client_certs/` — Issued client certificate bundles (`.p12`), pending transfer to their users.
- `client_certs.json` — Registry of issued client certificates (serial, user, label, revoked state).
- `users.json` — Hashed user credentials.
- `requeriments.txt` — Python dependencies.

## License

This project is licensed under the **GNU General Public License v3.0**.

## Author

**Alejandro Torrejón Harto**
- Email: atorrejon@unex.es
- Copyright 2025, The Program Manager Project
