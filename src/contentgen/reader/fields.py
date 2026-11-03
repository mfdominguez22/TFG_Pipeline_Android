from dataclasses import dataclass
from contentgen.model.project import (
    Field, FieldKey, Family, TextValue, TextOrigin, PreviewText, PreviewKind,
    Hint, Container, OverwriteMark, OverwriteLevel, Attr, AttrState, AttrSource, Reason
)
from contentgen.xmlio.parser import XmlDocument, XmlElement, QName, ANDROID, APP, TOOLS
from contentgen.reader.strings import StringIndex
from contentgen.reader.styles import StyleIndex, resolve_attribute
from contentgen.reader.classes import is_field_container

@dataclass(frozen=True)
class ReaderEnv:
    """Contexto necesario para procesar un layout"""
    namespace: str
    strings: StringIndex
    styles: StyleIndex

def _parse_text_origin(raw_value: str | None, strings: StringIndex) -> TextValue:
    """Clasificar el origen del texto y obtener su valor de ser posible"""
    if raw_value is None:
        return TextValue(origin=TextOrigin.ABSENT, key=None, value=None)
    
    raw_value = raw_value.strip()
    
    if raw_value.startswith("@{") or raw_value.startswith("@={"):
        return TextValue(origin=TextOrigin.DATA_BINDING, key=None, value=None)
    
    if raw_value.startswith("@android:string/"):
        return TextValue(origin=TextOrigin.FRAMEWORK_RESOURCE, key=None, value=None)
    
    if raw_value.startswith("@string/"):
        key = raw_value.removeprefix("@string/")
        resolved_value = strings[key].value if key in strings else None
        return TextValue(origin=TextOrigin.STRING_RESOURCE, key=key, value=resolved_value)
    
    return TextValue(origin=TextOrigin.LITERAL, key=None, value=raw_value)

def _parse_preview_text(element: XmlElement) -> PreviewText | None:
    """Unifica tools:text y tools:sample/*."""
    tools_text = element.attributes.get(QName(TOOLS, "text"))
    if not tools_text:
        return None
        
    if tools_text.startswith("@tools:sample/"):
        return PreviewText(kind=PreviewKind.SAMPLE, value=tools_text)
    return PreviewText(kind=PreviewKind.TEXT, value=tools_text)

def _resolve_max_lines(element: XmlElement, styles: StyleIndex) -> Attr[int]:
    """
    Normaliza maxLines, lines y singleLine en un unico valor.
    Prioriza el menor valor y maneja los estados UNRESOLVED.
    """
    max_lines_attr = resolve_attribute(element, QName(ANDROID, "maxLines"), styles)
    lines_attr = resolve_attribute(element, QName(ANDROID, "lines"), styles)
    single_line_attr = resolve_attribute(element, QName(ANDROID, "singleLine"), styles)
    
    declared_values = []
    has_unresolved = False
    source = AttrSource.ELEMENT
    
    for attr, is_single in [(max_lines_attr, False), (lines_attr, False), (single_line_attr, True)]:
        if attr.state == AttrState.PRESENT and attr.value is not None:
            if is_single:
                if attr.value.lower() == "true":
                    declared_values.append((1, attr.source))
            else:
                try:
                    declared_values.append((int(attr.value), attr.source))
                except ValueError:
                    pass
        elif attr.state == AttrState.UNRESOLVED:
            has_unresolved = True

    if declared_values:
        # Devuelve el menor conservando su fuente original
        min_val, min_source = min(declared_values, key=lambda x: x[0])
        return Attr(state=AttrState.PRESENT, value=min_val, source=min_source)
    
    if has_unresolved:
        return Attr(state=AttrState.UNRESOLVED)
        
    return Attr(state=AttrState.ABSENT)

def build_field(
    element: XmlElement, 
    family: Family, 
    doc: XmlDocument, 
    env: ReaderEnv,
    parent_element: XmlElement | None
) -> Field:
    """
    Construye el objeto Field a partir de un XmlElement
    """
    # 1. Identidad
    raw_id = element.attributes.get(QName(ANDROID, "id"), "")
    resource_name = f"{env.namespace}:id/{raw_id.split('/')[-1]}" if raw_id else ""
    key = FieldKey(layout_path=doc.path, resource_name=resource_name)
    
    # 2. Estructura y contenedor (TextInputLayout)
    container_info = None
    hint_value = element.attributes.get(QName(ANDROID, "hint"))
    hint_from_container = False
    
    if parent_element:
        parent_id_raw = parent_element.attributes.get(QName(ANDROID, "id"), "")
        parent_res_name = f"{env.namespace}:id/{parent_id_raw.split('/')[-1]}" if parent_id_raw else None
        container_info = Container(element_class=parent_element.tag, resource_name=parent_res_name)
        
        # Herencia de TextInputLayout
        if is_field_container(parent_element.tag):
            parent_hint = parent_element.attributes.get(QName(ANDROID, "hint"))
            if parent_hint and not hint_value:
                hint_value = parent_hint
                hint_from_container = True

    hint_obj = Hint(value=hint_value, from_container=hint_from_container) if hint_value else None

    # 3. Textos y SemÃ¡ntica
    text_val = _parse_text_origin(element.attributes.get(QName(ANDROID, "text")), env.strings)
    preview_text = _parse_preview_text(element)
    content_desc = element.attributes.get(QName(ANDROID, "contentDescription"))
    
    # Input Type (se descompone la lista separada por |)
    input_type_attr = resolve_attribute(element, QName(ANDROID, "inputType"), env.styles)
    it_val = tuple(input_type_attr.value.split("|")) if input_type_attr.value else None
    input_type = Attr(state=input_type_attr.state, value=it_val, source=input_type_attr.source)

    # Autofill (se descompone la lista separada por comas)
    autofill_raw = element.attributes.get(QName(ANDROID, "autofillHints"))
    autofill_hints = tuple(autofill_raw.split(",")) if autofill_raw else ()
    important_for_autofill = element.attributes.get(QName(ANDROID, "importantForAutofill"))

    # 4. Restricciones de longitud y presentaciÃ³n (con resoluciÃ³n de estilos)
    max_length_attr = resolve_attribute(element, QName(ANDROID, "maxLength"), env.styles)
    ml_val = int(max_length_attr.value) if max_length_attr.value and max_length_attr.value.isdigit() else None
    max_length = Attr(state=max_length_attr.state, value=ml_val, source=max_length_attr.source)

    ellipsize = resolve_attribute(element, QName(ANDROID, "ellipsize"), env.styles)
    
    all_caps_attr = resolve_attribute(element, QName(ANDROID, "textAllCaps"), env.styles, is_text_all_caps=True)
    ac_val = all_caps_attr.value.lower() == "true" if all_caps_attr.value else None
    all_caps = Attr(state=all_caps_attr.state, value=ac_val, source=all_caps_attr.source)

    # 5. Editabilidad
    # Editable si pertenece a la familia, salvo inputType="none" o enabled="false"
    is_enabled = element.attributes.get(QName(ANDROID, "enabled"), "true").lower() != "false"
    is_editable = (
        family == Family.EDITABLE 
        and (not it_val or "none" not in it_val) 
        and is_enabled
    )

    # 6. Marca de sobrescritura inicial (SerÃ¡ enriquecida luego por overwrite.py)
    # Si hay data binding o preview text, ya sabemos que el layout da pistas fuertes
    reasons = []
    level = OverwriteLevel.NOT_ANALYZED
    
    if text_val.origin == TextOrigin.DATA_BINDING:
        level = OverwriteLevel.CERTAIN
        reasons.append(Reason.DATA_BINDING)
    elif preview_text:
        level = OverwriteLevel.PROBABLE
        reasons.append(Reason.PREVIEW_TEXT)

    overwrite_mark = OverwriteMark(level=level, reasons=tuple(reasons))

    return Field(
        key=key,
        position=element.position,
        element_class=element.tag,
        family=family,
        text=text_val,
        preview_text=preview_text,
        hint=hint_obj,
        content_description=content_desc,
        input_type=input_type,
        autofill_hints=autofill_hints,
        important_for_autofill=important_for_autofill,
        max_length=max_length,
        max_lines=_resolve_max_lines(element, env.styles),
        ellipsize=ellipsize,
        all_caps=all_caps,
        labels=(), # Se asignan posteriormente en labels.py porque requieren analizar a los hermanos
        editable=is_editable,
        container=container_info,
        visibility=element.attributes.get(QName(ANDROID, "visibility")),
        overwrite=overwrite_mark
    )
