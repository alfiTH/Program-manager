#!/usr/bin/python3
import tkinter as tk

def on_button_click():
    label.config(text="¡Hola, mundo!")


print("hola")
# Crear la ventana principal
window = tk.Tk()
window.title("Interfaz gráfica")
window.geometry("300x200")

# Crear un etiqueta
label = tk.Label(window, text="Presiona el botón para saludar")
label.pack(pady=20)

# Crear un botón
button = tk.Button(window, text="Saludar", command=on_button_click)
button.pack()
print("El botón arrancado")
# Ejecutar el bucle principal de la interfaz gráfica
window.mainloop()