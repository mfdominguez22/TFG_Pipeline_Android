from dataclasses import dataclass
from typing import Iterable, Mapping
from contentgen.model.project import Attr, AttrState, AttrSource
from contentgen.xmlio.parser import XmlDocument, XmlElement, QName, ANDROID, APP

# Tipos internos definidos en el diseÃ±o de la herramienta (Â§5.3.3)
@dataclass(frozen=True)
class StyleInfo:
    name: str
    parent: str | None
    items: Mapping[QName, str]
    has_text_appearance: bool

StyleIndex = Mapping[str, StyleInfo]

def _get_attr(element: XmlElement, uri: str | None, local: str) -> str | None:
    """FunciÃ³n auxiliar para obtener un atributo XML de forma segura."""
    return element.attributes.get(QName(uri, local))

def _parse_item_name(name_str: str) -> QName:
    """
    Convierte el nombre del atributo declarado en <item name="..."> a un QName formal.
    En Android, los atributos del framework llevan el prefijo 'android:'.
    """
    if name_str.startswith("android:"):
        return QName(ANDROID, name_str.removeprefix("android:"))
    if name_str.startswith("app:"):
        return QName(APP, name_str.removeprefix("app:"))
    return QName(None, name_str)

def read_styles(docs: Iterable[XmlDocument]) -> StyleIndex:
    """
    Recorre los documentos de valores y construye el Ã­ndice de estilos del proyecto.
    """
    index: dict[str, StyleInfo] = {}

    for doc in docs:
        if doc.root.tag != "resources":
            continue

        for child in doc.root.children:
            if child.tag == "style":
                name = _get_attr(child, None, "name")
                if not name:
                    continue
                
                parent = _get_attr(child, None, "parent")
                items = {}
                has_ta = False

                for item in child.children:
                    if item.tag == "item":
                        item_name = _get_attr(item, None, "name")
                        if item_name:
                            qname = _parse_item_name(item_name)
                            items[qname] = item.text
                            if qname == QName(ANDROID, "textAppearance"):
                                has_ta = True

                index[name] = StyleInfo(name, parent, items, has_ta)

    return index

def resolve_attribute(
    element: XmlElement,
    attr_qname: QName,
    style_index: StyleIndex,
    is_text_all_caps: bool = False
) -> Attr[str]:
    """
    Resuelve el estado de un atributo siguiendo la cadena de estilos.
    """
    # 1. ComprobaciÃ³n en el propio elemento (Prioridad absoluta)
    if attr_qname in element.attributes:
        return Attr(state=AttrState.PRESENT, value=element.attributes[attr_qname], source=AttrSource.ELEMENT)

    # Regla especial para textAllCaps: Si el elemento declara textAppearance, 
    # y textAllCaps no estaba en el elemento, queda UNRESOLVED
    element_has_ta = QName(ANDROID, "textAppearance") in element.attributes
    if is_text_all_caps and element_has_ta:
        return Attr(state=AttrState.UNRESOLVED)

    # 2. BÃºsqueda en el estilo declarado
    style_attr = _get_attr(element, None, "style")
    
    if not style_attr:
        return Attr(state=AttrState.ABSENT)

    if style_attr.startswith("?"):
        return Attr(state=AttrState.UNRESOLVED)

    current_style_name = style_attr.removeprefix("@style/")

    while current_style_name:
        if current_style_name not in style_index:
            return Attr(state=AttrState.UNRESOLVED)

        style_info = style_index[current_style_name]

        if attr_qname in style_info.items:
            return Attr(state=AttrState.PRESENT, value=style_info.items[attr_qname], source=AttrSource.STYLE)

        if is_text_all_caps and style_info.has_text_appearance:
            return Attr(state=AttrState.UNRESOLVED)

        if style_info.parent:
            current_style_name = style_info.parent
        else:
            last_dot = current_style_name.rfind(".")
            if last_dot != -1:
                implicit_parent = current_style_name[:last_dot]
                if implicit_parent in style_index:
                    current_style_name = implicit_parent
                else:
                    current_style_name = None
            else:
                current_style_name = None

    return Attr(state=AttrState.ABSENT)
