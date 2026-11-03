from dataclasses import dataclass
from contentgen.xmlio.parser import XmlDocument, XmlElement, QName, ANDROID
from contentgen.reader.classes import resolve_element_class, get_family
from contentgen.model.project import Family

@dataclass(frozen=True)
class LayoutScan:
    """Resultado de recorrer un layout"""
    candidates: tuple[tuple[XmlElement, XmlElement | None, Family], ...]
    includes: tuple[str, ...]
    view_stubs: int
    text_elements_count: int
    text_elements_without_id_count: int

def _is_custom_text_element(element: XmlElement) -> bool:
    """
    Heurística para clases desconocidas (§4.4).
    Detecta si una vista personalizada declara atributos típicos de un campo de texto.
    """
    has_text = QName(ANDROID, "text") in element.attributes
    has_hint = QName(ANDROID, "hint") in element.attributes
    has_input_type = QName(ANDROID, "inputType") in element.attributes
    return has_text or has_hint or has_input_type

def scan_layout(doc: XmlDocument) -> LayoutScan:
    """
    Recorre el documento XML identificando elementos estructurales y 
    filtrando los nodos que cumplen los criterios para ser campos.
    """
    candidates = []
    includes = []
    view_stubs = 0
    text_elements = 0
    without_id = 0

    def traverse(node: XmlElement, parent: XmlElement | None):
        nonlocal view_stubs, text_elements, without_id

        if node.tag == "include":
            layout_ref = node.attributes.get(QName(None, "layout"))
            if layout_ref:
                includes.append(layout_ref)
            return

        if node.tag == "ViewStub":
            view_stubs += 1
            return

        effective_parent = parent if node.tag == "merge" else node

        resolved_class = resolve_element_class(node.tag, node.attributes.get(QName(None, "class")))
        family = get_family(resolved_class)

        is_text_element = False
        if family is not None:
            is_text_element = True
        elif _is_custom_text_element(node):
            is_text_element = True

        if is_text_element:
            text_elements += 1
            if QName(ANDROID, "id") in node.attributes:
                candidates.append((node, parent, family or Family.UNKNOWN))
            else:
                without_id += 1

        for child in node.children:
            traverse(child, effective_parent)

    traverse(doc.root, None)

    return LayoutScan(
        candidates=tuple(candidates),
        includes=tuple(includes),
        view_stubs=view_stubs,
        text_elements_count=text_elements,
        text_elements_without_id_count=without_id
    )