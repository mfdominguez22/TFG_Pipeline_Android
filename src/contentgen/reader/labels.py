from dataclasses import replace
from contentgen.model.project import Field, LabelRef, LabelKind
from contentgen.xmlio.parser import XmlDocument, XmlElement, QName, APP, ANDROID
from contentgen.reader.fields import ReaderEnv

def _get_element_at(root: XmlElement, pos: tuple[int, ...]) -> XmlElement:
    """Navega el arbol DOM usando la ruta positional del campo"""
    current = root
    for idx in pos:
        current = current.children[idx]
    return current

def _extract_id_base(raw_id: str | None) -> str | None:
    """Extrae el nombre ignorando el prefijo """
    if not raw_id:
        return None
    return raw_id.split('/')[-1]

def attach_labels(fields: tuple[Field, ...], doc: XmlDocument, env: ReaderEnv) -> tuple[Field, ...]:
    """Asocia etiquetas declaradas y adyacentes a cada campo."""
    
    fields_by_res = {f.key.resource_name: f for f in fields if f.key.resource_name}
    fields_by_pos = {f.position: f for f in fields}
    
    updated_fields = []
    
    for field in fields:
        labels: list[LabelRef] = []
        node = _get_element_at(doc.root, field.position)
        field_id_base = _extract_id_base(field.key.resource_name)
        
        # 1. DECLARED (android:labelFor)
        # Revisamos si algÃºn otro campo apunta explÃ­citamente a nuestro ID
        if field_id_base:
            for other_field in fields:
                if other_field == field:
                    continue
                other_node = _get_element_at(doc.root, other_field.position)
                label_for_attr = other_node.attributes.get(QName(ANDROID, "labelFor"))
                if label_for_attr and _extract_id_base(label_for_attr) == field_id_base:
                    labels.append(LabelRef(
                        kind=LabelKind.DECLARED,
                        resource_name=other_field.key.resource_name,
                        text=other_field.text.value
                    ))
        
        # 2. CONSTRAINT (Atributos de posicionamiento relativo)
        constraint_attrs = [
            QName(APP, "layout_constraintStart_toEndOf"),
            QName(APP, "layout_constraintLeft_toRightOf"),
            QName(APP, "layout_constraintTop_toBottomOf")
        ]
        for attr in constraint_attrs:
            target_id_raw = node.attributes.get(attr)
            if target_id_raw:
                target_id_base = _extract_id_base(target_id_raw)
                target_res = f"{env.namespace}:id/{target_id_base}"
                target_field = fields_by_res.get(target_res)
                # Solo cuenta si el elemento al que apuntamos es un campo de texto registrado
                if target_field:
                    labels.append(LabelRef(
                        kind=LabelKind.CONSTRAINT,
                        resource_name=target_field.key.resource_name,
                        text=target_field.text.value
                    ))
                    break # La especificaciÃ³n pide tomar solo el primero vÃ¡lido en ese orden
                    
        # 3. ADJACENT (Hermanos inmediatos en el mismo contenedor)
        if len(field.position) > 0:
            parent_pos = field.position[:-1]
            my_idx = field.position[-1]
            
            # Revisar el hermano anterior y el posterior
            for adj_idx in (my_idx - 1, my_idx + 1):
                if adj_idx >= 0:
                    adj_pos = parent_pos + (adj_idx,)
                    adj_field = fields_by_pos.get(adj_pos)
                    if adj_field:
                        labels.append(LabelRef(
                            kind=LabelKind.ADJACENT,
                            resource_name=adj_field.key.resource_name,
                            text=adj_field.text.value
                        ))
                        
        updated_fields.append(replace(field, labels=tuple(labels)))
        
    return tuple(updated_fields)
