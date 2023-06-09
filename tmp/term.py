
comando = "componente_c/src/Contador hola"
import subprocess

# Comando a ejecutar en el primer proceso
comando1 = comando

# Comando a ejecutar en el segundo proceso
comando2 = "pwd;while true; do read -r linea; echo $linea; done"

# Crear el primer proceso y redirigir su salida a una tubería
proceso1 = subprocess.Popen(comando1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(proceso1.stdout.fileno, )

# Crear el segundo proceso y redirigir su entrada desde la tubería del primer proceso
proceso2 = subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', comando2])
proceso2.stdin = proceso1.stdin

# Esperar a que el primer proceso termine
proceso1.wait()
