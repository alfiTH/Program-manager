from getpass import getpass

from utils.addUser import load_users
from utils.clientCertAuth import issue_client_cert


def add_client_cert():
    print("Presiona CTRL+C para salir.\n")

    users = load_users()

    while True:
        try:
            username = input("Usuario existente al que emitir el certificado: ").strip()
            if username not in users:
                print("❌ Ese usuario no existe. Créalo antes con --addUser.")
                continue

            label = input("Etiqueta para este certificado (p.ej. 'portatil', 'movil') [default]: ").strip() or "default"

            password = getpass("Contraseña para proteger el archivo .p12 (la pedirá el navegador al importarlo): ")
            if not password:
                print("❌ La contraseña no puede estar vacía: protege la clave privada dentro del .p12.")
                continue
            confirm = getpass("Repite la contraseña: ")
            if password != confirm:
                print("❌ Las contraseñas no coinciden.")
                continue

            path = issue_client_cert(username, label, password)
            print(f"✅ Certificado generado en '{path}'.")
            print("   Transfiérelo por un canal seguro al dispositivo del usuario, instálalo")
            print("   en el navegador/sistema y borra la copia de este servidor.\n")

        except KeyboardInterrupt:
            print("\nSaliendo...")
            break


if __name__ == "__main__":
    add_client_cert()
