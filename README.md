# Program Manager Web

Program Manager Web is a powerful tool designed to manage and monitor programs remotely via a web interface. It allows users to control multiple terminal processes, monitor system resources in real-time, and integrates with VSCode (Codium) for a seamless development experience.

## Description

This project provides a centralized dashboard to run, stop, clean, and compile various programs. It features a real-time terminal output display with ANSI color support, making it easy to track the status and logs of your applications. Additionally, it offers detailed resource monitoring, including CPU, RAM, GPU, and VRAM usage, ensuring you have full visibility into your system's performance.

## Key Features

-   **Web-Based Control Panel**: Manage your programs from any browser.
-   **Real-Time Resource Monitoring**: Visualize CPU, RAM, GPU, and VRAM usage with dynamic progress bars.
-   **Multi-Terminal Management**: Create and control multiple terminal instances independently.
    -   **Run**: Execute commands.
    -   **Stop**: Terminate processes (supports SIGINT, SIGTERM, SIGKILL).
    -   **Clean & Build**: Pre-configured buttons for cleaning and compiling projects (e.g., using `make` and `cmake`).
-   **Live Terminal Output**: Stream process logs in real-time with full ANSI color support.
-   **VSCode (Codium) Integration**: Open a web-based VSCode instance for the project directory directly from the interface.
-   **User Authentication**: Secure access with a login system backed by `users.json`.
-   **Configuration Management**: Save and load terminal configurations (names, directories, commands) to easily restore setups.

## Prerequisites

Required Python libraries (listed in `requeriments.txt`):
-   `flask`
-   `flask-socketio`
-   `flask-login`
-   `psutil`
-   `gputil`

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/alfiTH/Program-manager.git
    cd Program-manager-web
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requeriments.txt
    #Codium download
    mkdir ~/software 2> /dev/null; cd ~/software && wget https://github.com/VSCodium/vscodium/releases/download/1.109.21026/vscodium-reh-web-linux-x64-1.109.21026.tar.gz && mkdir vscodium-server && tar -xzf vscodium-reh-web-linux-x64-1.109.21026.tar.gz -C vscodium-server && cd -
    ```

## Configuration

### SSL Certificates
The application runs over HTTPS. You need to generate SSL certificates in the `certificates` directory.
1.  Navigate to the `certificates` folder:
    ```bash
    cd certificates
    ```
2.  Generate `cert.pem` and `key.pem`.
    ```bash
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    ```
### Users
Users are managed via the `users.json` file. Ensure this file exists and contains valid user credentials. You can use the `utils/addUser.py` script to add new users securely.
```bash
python3 src/utils/addUser.py
```
## Usage

1.  **Start the Server**:
    Run the main script from the project root:
    ```bash
    python3 src/ProgramManager.py --config etc/config.json
    ```

2.  **Access the Application**:
    Open your web browser and navigate to:
    
    ```https://<server_ip>:5000 ``` or ```https://localhost:5000```

    (Note: Since it uses self-signed certificates, you may need to acknowledge a security warning in your browser).

3.  **Login**:
    Enter your username and password to access the dashboard.

## Project Structure

-   `src/`: Contains the source code of the application.
    -   `ProgramManager.py`: Main entry point and Flask application.
    -   `templates/`: HTML templates for the web interface.
    -   `utils/`: Utility scripts for user management, ANSI parsing, and configuration loading.
-   `certificates/`: Stores SSL certificates for secure HTTPS connection.
-   `users.json`: Stores user credentials.
-   `requeriments.txt`: List of Python dependencies.

## License

This project is licensed under the **GNU General Public License v3.0**.

## Author

**Alejandro Torrejón Harto**
-   Email: atorrejon@unex.es
-   Copyright 2025, The Program Manager Project