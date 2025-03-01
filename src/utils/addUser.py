from werkzeug.security import generate_password_hash
import json
from getpass import getpass

# Guardar usuarios en un archivo
def save_users(users, user_file="users.json"):
    with open(user_file, "w") as file:
        json.dump(users, file, indent=4)

# Cargar usuarios desde un archivo
def load_users(user_file="users.json"):
    try:
        with open(user_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

if __name__ == "__main__":
    print("Presiona CTRL+C para salir.\n")
    
    users = load_users()
    
    while True:
        try:
            username = input("Introduce el nombre de usuario a agregar: ").strip()
            if not username:
                print("❌ El nombre de usuario no puede estar vacío.")
                continue
            if username in users:
                print("⚠️ El usuario ya existe. Intenta con otro.")
                continue

            password = getpass("Introduce la contraseña: ").strip()
            if not password:
                print("❌ La contraseña no puede estar vacía.")
                continue

            users[username] = generate_password_hash(password)
            save_users(users)

            print(f"✅ Usuario '{username}' agregado correctamente.\n")

        except KeyboardInterrupt:
            print("\nSaliendo...")
            break
