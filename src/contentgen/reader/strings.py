import re
from typing import Iterable, Mapping
from contentgen.model.project import StringEntry, Placeholder, PlaceholderType
from contentgen.xmlio.parser import XmlDocument, XmlElement

# Tipo interno definido en el diseño de la herramienta (§5.3.3)
StringIndex = Mapping[str, StringEntry]

# Expresión regular para detectar huecos de formato (ej. %s, %1$d, %.2f)
_PLACEHOLDER_RE = re.compile(r'%(\d+\$)?[\-\+#0, ]*\d*(?:\.\d+)?([a-zA-Z])')

def _parse_placeholder_type(conversion_char: str) -> PlaceholderType:
    """Mapea el carácter de conversión de C/Java al tipo simplificado del TFG."""
    if conversion_char in ('d', 'i', 'o', 'x', 'X'):
        return PlaceholderType.INTEGER
    if conversion_char in ('f', 'e', 'E', 'g', 'G', 'a', 'A'):
        return PlaceholderType.DECIMAL
    return PlaceholderType.TEXT

def _clean_android_string(raw_text: str) -> str:
    """
    Aplica las reglas de limpieza exactas de la especificación (§6):
    1. Tratamiento de espacios y comillas dobles.
    2. Decodificación de escapes de Android.
    3. Eliminación de etiquetas de marcado HTML/XML.
    """
    if not raw_text:
        return ""

    # 1. Tratamiento de espacios y comillas
    # Si el texto está envuelto en comillas dobles, se respetan los espacios y se quitan las comillas.
    # Si no, se colapsan los espacios múltiples y se hace un trim a los extremos.
    match_quotes = re.match(r'^"(.*)"$', raw_text.strip(), flags=re.DOTALL)
    if match_quotes:
        processed_text = match_quotes.group(1)
    else:
        # Colapsar secuencias de espacios/saltos de línea a un solo espacio
        processed_text = re.sub(r'\s+', ' ', raw_text).strip()

    # 2. Decodificación de secuencias de escape
    escapes = {
        r"\'": "'",
        r'\"': '"',
        r"\n": "\n",
        r"\t": "\t",
        r"\@": "@",
        r"\?": "?",
        r"\\": "\\"
    }
    for esc, repl in escapes.items():
        processed_text = processed_text.replace(esc, repl)
        
    # Decodificar unicode \uXXXX
    processed_text = re.sub(
        r'\\u([0-9a-fA-F]{4})',
        lambda m: chr(int(m.group(1), 16)),
        processed_text
    )

    # 3. Eliminar etiquetas de marcado (<b>, <i>, <u>, <xliff:g>) conservando su texto interior
    processed_text = re.sub(r'<[^>]+>', '', processed_text)

    return processed_text

def _extract_placeholders(text: str) -> tuple[Placeholder, ...]:
    """Extrae la posición y el tipo de los huecos de formato en el texto resultante."""
    placeholders = []
    for match in _PLACEHOLDER_RE.finditer(text):
        pos = match.start()
        conversion = match.group(2)
        placeholders.append(Placeholder(
            position=pos,
            type=_parse_placeholder_type(conversion)
        ))
    return tuple(placeholders)

def read_strings(docs: Iterable[XmlDocument]) -> StringIndex:
    """
    Recibe los documentos XML de la carpeta de valores y devuelve un índice
    con las entradas de texto simples.
    """
    string_index = {}

    for doc in docs:
        if doc.root.tag != "resources":
            continue

        for child in doc.root.children:
            if child.tag == "string":
                # La clave es el atributo 'name' (sin namespace)
                # Ojo: la búsqueda de atributos asume QName(uri=None, local='name')
                key = next((v for k, v in child.attributes.items() if k.local == "name" and k.uri is None), None)
                if not key:
                    continue

                # El atributo translatable es true por defecto
                translatable_str = next((v for k, v in child.attributes.items() if k.local == "translatable"), "true")
                translatable = translatable_str.lower() != "false"

                # Procesar el valor según la especificación
                raw_text = child.text
                value = _clean_android_string(raw_text)
                
                placeholders = _extract_placeholders(value)

                string_index[key] = StringEntry(
                    key=key,
                    value=value,
                    translatable=translatable,
                    placeholders=placeholders
                )

    return string_index