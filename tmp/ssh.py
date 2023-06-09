import subprocess

def execute_remote_program(hostname, username, password, program_path):
    # Comando SSH con reenvío de X11
    ssh_command = f'ssh -X {username}@{hostname} "cd Documentos/Alejandro/Program-manager/tmp/componente_c; {program_path}"'

    # Ejecutar el comando SSH
    process = subprocess.Popen(ssh_command, shell=True)
    print("kakakakaka")
    process.wait()

# Ingresar los detalles de conexión SSH y la ruta del programa remoto

# Ejecutar el programa remoto a través de SSH
execute_remote_program("158.49.247.194", "robolab","", "ls")
