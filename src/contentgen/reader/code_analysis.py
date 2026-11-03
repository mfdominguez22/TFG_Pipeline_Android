from typing import Protocol, Mapping
from dataclasses import dataclass
from contentgen.model.project import Field

# alias temporal para ProjectInfo
ProjectInfo = dict

@dataclass(frozen=True)
class CodeEvidence:
    """Para cada clave de campo, un booleano que indica si hay asignacion en codigo."""
    assignments: Mapping[str, bool]

class CodeAnalyzer(Protocol):
    def analyze(self, project: ProjectInfo, fields: tuple[Field, ...]) -> CodeEvidence:
        ...

class NoCodeAnalysis:
    """por defecto que no leer el codigo"""
    def analyze(self, project: ProjectInfo, fields: tuple[Field, ...]) -> CodeEvidence:
        return CodeEvidence(assignments={})

# analizadores
ANALYZERS = {
    "none": NoCodeAnalysis()
}
