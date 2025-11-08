import re

# Diccionario de colores ANSI a códigos HTML
ANSI_COLORS = {
    '30': 'black', '31': 'red', '32': 'green', '33': 'yellow',
    '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white',
    '40': 'black', '41': 'red', '42': 'green', '43': 'yellow',
    '44': 'blue', '45': 'magenta', '46': 'cyan', '47': 'white',
    '0': 'black',  # Reset color
}

def ansi_to_html(ansi_text):
    # Expresión regular para encontrar los códigos ANSI (e.g. \033[31m)
    ansi_escape = re.compile(r'\033\[(\d+)m')
    
    # Reemplazar los códigos ANSI por el color HTML correspondiente
    def replace(match):
        color_code = match.group(1)
        # Si el color existe en el diccionario, devolver el estilo HTML correspondiente
        if color_code in ANSI_COLORS:
            color = ANSI_COLORS[color_code]
            return f'<span style="color: {color}">'
        # Si es el código de reset (0), se cierra el span
        elif color_code == '0':
            return '</span>'
        return ''

    # Reemplazar en el texto
    html_text = ansi_escape.sub(replace, ansi_text)

    # Escapar cualquier otro texto y devolver el contenido HTML dentro de un <pre> (preservando formato)
    return html_text
