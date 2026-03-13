import re

def ansi_to_html(ansi_text):
    # Diccionarios de mapeo extendidos
    COLORS = {
        '30': 'black', '31': 'red', '32': 'green', '33': 'yellow', '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white',
        '90': 'gray', '91': 'lightred', '92': 'lightgreen', '93': 'lightyellow', '94': 'lightblue', '95': 'lightmagenta', '96': 'lightcyan', '97': 'white'
    }
    BG_COLORS = {
        '40': 'black', '41': 'red', '42': 'green', '43': 'yellow', '44': 'blue', '45': 'magenta', '46': 'cyan', '47': 'white',
        '100': 'gray', '101': 'lightred', '102': 'lightgreen', '103': 'lightyellow', '104': 'lightblue', '105': 'lightmagenta', '106': 'lightcyan', '107': 'white'
    }
    STYLES = {
        '1': 'font-weight: bold;',
        '3': 'font-style: italic;',
        '4': 'text-decoration: underline;',
        '9': 'text-decoration: line-through;'
    }

# 1. Limpiar Hipervínculos (OSC 8) y comandos de sistema (OSC)
    # Esta regex es más precisa: busca desde \033] hasta el final de la secuencia OSC (\x07 o \033\)
    # sin llevarse por delante los corchetes de los colores [\
    ansi_text = re.sub(r'\x1b\][0-9;]*;.*?(\x07|\x1b\\)', '', ansi_text)

    # 2. Limpiar secuencias de control de terminal que NO son color (CSI)
    # Borra movimientos de cursor, limpiezas de pantalla, etc. (Terminan en A, B, C, D, H, J, K...)
    # Pero EXCLUIMOS la 'm', que es la de los colores.
    ansi_text = re.sub(r'\x1b\[[0-9;?]*[A-LN-Z]', '', ansi_text)

    # Regex que captura secuencias complejas como \033[1;36;42m
    ansi_escape = re.compile(r'\x1b\[([\d;]*)m')
    
    parts = ansi_escape.split(ansi_text)
    result = []
    stack_count = 0

    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Texto normal: escapamos caracteres HTML básicos para seguridad
            result.append(part.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        else:
            # Es un código de control
            codes = part.split(';') if part else ['0']
            
            # Si hay un '0' o está vacío, cerramos todo lo abierto
            if '0' in codes or not codes:
                result.append('</span>' * stack_count)
                stack_count = 0
                continue

            # Construimos el estilo para esta secuencia
            current_styles = []
            for code in codes:
                if code in STYLES:
                    current_styles.append(STYLES[code])
                elif code in COLORS:
                    current_styles.append(f"color: {COLORS[code]};")
                elif code in BG_COLORS:
                    current_styles.append(f"background-color: {BG_COLORS[code]};")

            if current_styles:
                result.append(f'<span style="{" ".join(current_styles)}">')
                stack_count += 1

    # Limpieza final de etiquetas
    result.append('</span>' * stack_count)
    return "".join(result)