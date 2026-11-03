from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import xml.etree.ElementTree as ET
import re

# URIs
ANDROID = "http://schemas.android.com/apk/res/android"
APP = "http://schemas.android.com/apk/res-auto"
TOOLS = "http://schemas.android.com/tools"

@dataclass(frozen=True)
class QName:
    uri: str | None
    local: str

@dataclass(frozen=True)
class XmlElement:
    tag: str
    attributes: Mapping[QName, str]
    children: tuple["XmlElement", ...]
    position: tuple[int, ...]
    text: str

@dataclass(frozen=True)
class XmlDocument:
    path: str
    root: XmlElement

class XmlParseError(Exception):
    pass

def _parse_qname(raw_name: str) -> QName:
    """Convierte el formato '{uri}local' de ElementTree al QName requerido."""
    match = re.match(r"\{(.*)\}(.*)", raw_name)
    if match:
        return QName(uri=match.group(1), local=match.group(2))
    return QName(uri=None, local=raw_name)

def _build_element(node: ET.Element, current_position: tuple[int, ...]) -> XmlElement:
    attributes = {_parse_qname(k): v for k, v in node.attrib.items()}
    
    children = []
    child_index = 0
    for child in node:
        # La especificación exige que solo cuenten los hijos que son elementos, 
        # ignorando comentarios o texto suelto para calcular la ruta posicional
        child_position = current_position + (child_index,)
        children.append(_build_element(child, child_position))
        child_index += 1
        
    text_content = "".join(node.itertext())
    
    return XmlElement(
        tag=_parse_qname(node.tag).local,
        attributes=attributes,
        children=tuple(children),
        position=current_position,
        text=text_content
    )

def parse(path: Path) -> XmlDocument:
    """Parsea el fichero. Lanza XmlParseError si no es válido."""
    try:
        tree = ET.parse(path)
        root = _build_element(tree.getroot(), ())
        return XmlDocument(path=str(path), root=root)
    except ET.ParseError as e:
        raise XmlParseError(str(e))