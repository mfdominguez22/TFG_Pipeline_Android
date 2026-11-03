from dataclasses import replace
from contentgen.model.project import Field, OverwriteLevel, Reason
from contentgen.reader.code_analysis import CodeEvidence

def mark_overwrite(fields: tuple[Field, ...], evidence: CodeEvidence) -> tuple[Field, ...]:
    """
    Combina la marca inicial con la evidencia del codigo.
    """
    updated_fields = []
    
    for field in fields:
        has_code_assignment = evidence.assignments.get(field.key.resource_name, False)
        
        current_mark = field.overwrite
        new_level = current_mark.level
        new_reasons = list(current_mark.reasons)
        
        if has_code_assignment:
            # Si el nivel no era ya CERTAIN subir a PROBABLE
            if new_level != OverwriteLevel.CERTAIN:
                new_level = OverwriteLevel.PROBABLE
            if Reason.CODE_ASSIGNMENT not in new_reasons:
                new_reasons.append(Reason.CODE_ASSIGNMENT)
        else:
            # Si no hay asignacion, y el nivel era NOT_ANALYZED,
            # significa que ejecutamos el anÃ¡lisis y no encontramos nada.
            if new_level == OverwriteLevel.NOT_ANALYZED and isinstance(evidence.assignments, dict):
                # Ojo: como en esta versiÃ³n usamos NoCodeAnalysis, no hay asignaciones pero el 
                # nivel general se mantiene segÃºn lo que pida la implementaciÃ³n futura.
                pass

        updated_mark = replace(current_mark, level=new_level, reasons=tuple(new_reasons))
        updated_fields.append(replace(field, overwrite=updated_mark))
        
    return tuple(updated_fields)
