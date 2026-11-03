from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar('T')


class Family(Enum):
    READ_ONLY = "READ_ONLY"
    EDITABLE = "EDITABLE"
    CONTROL = "CONTROL"
    UNKNOWN = "UNKNOWN"


class AttrState(Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    UNRESOLVED = "UNRESOLVED"


class AttrSource(Enum):
    ELEMENT = "ELEMENT"
    STYLE = "STYLE"


class TextOrigin(Enum):
    LITERAL = "LITERAL"
    STRING_RESOURCE = "STRING_RESOURCE"
    FRAMEWORK_RESOURCE = "FRAMEWORK_RESOURCE"
    DATA_BINDING = "DATA_BINDING"
    ABSENT = "ABSENT"


class PreviewKind(Enum):
    TEXT = "TEXT"
    SAMPLE = "SAMPLE"


class LabelKind(Enum):
    DECLARED = "DECLARED"
    CONSTRAINT = "CONSTRAINT"
    ADJACENT = "ADJACENT"


class OverwriteLevel(Enum):
    CERTAIN = "CERTAIN"
    PROBABLE = "PROBABLE"
    NOT_DETECTED = "NOT_DETECTED"
    NOT_ANALYZED = "NOT_ANALYZED"


class Reason(Enum):
    DATA_BINDING = "DATA_BINDING"
    PREVIEW_TEXT = "PREVIEW_TEXT"
    CODE_ASSIGNMENT = "CODE_ASSIGNMENT"


class PlaceholderType(Enum):
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    TEXT = "TEXT"


@dataclass(frozen=True)
class Attr(Generic[T]):
    state: AttrState
    value: T | None = None
    source: AttrSource | None = None


@dataclass(frozen=True)
class FieldKey:
    layout_path: str
    resource_name: str


@dataclass(frozen=True)
class TextValue:
    origin: TextOrigin
    key: str | None
    value: str | None


@dataclass(frozen=True)
class Placeholder:
    position: int
    type: PlaceholderType


@dataclass(frozen=True)
class StringEntry:
    key: str
    value: str
    translatable: bool
    placeholders: tuple[Placeholder, ...]


@dataclass(frozen=True)
class PreviewText:
    kind: PreviewKind
    value: str


@dataclass(frozen=True)
class Hint:
    value: str
    from_container: bool


@dataclass(frozen=True)
class LabelRef:
    kind: LabelKind
    resource_name: str | None
    text: str | None


@dataclass(frozen=True)
class Container:
    element_class: str
    resource_name: str | None


@dataclass(frozen=True)
class OverwriteMark:
    level: OverwriteLevel
    reasons: tuple[Reason, ...]


@dataclass(frozen=True)
class Field:
    key: FieldKey
    position: tuple[int, ...]
    element_class: str
    family: Family
    text: TextValue
    preview_text: PreviewText | None
    hint: Hint | None
    content_description: str | None
    input_type: Attr[tuple[str, ...]]
    autofill_hints: tuple[str, ...]
    important_for_autofill: str | None
    max_length: Attr[int]
    max_lines: Attr[int]
    ellipsize: Attr[str]
    all_caps: Attr[bool]
    labels: tuple[LabelRef, ...]
    editable: bool
    container: Container | None
    visibility: str | None
    overwrite: OverwriteMark


@dataclass(frozen=True)
class LayoutInfo:
    path: str
    includes: tuple[str, ...]
    view_stubs: int


@dataclass(frozen=True)
class Counts:
    text_elements: int
    text_elements_without_id: int
    attributes_resolved_from_styles: int
    alternative_layouts_not_analyzed: int
    malformed_files: tuple[str, ...]


@dataclass(frozen=True)
class ProjectModel:
    schema_version: str
    reader_version: str
    namespace: str
    code_analysis: str
    layouts: tuple[LayoutInfo, ...]
    fields: tuple[Field, ...]
    strings: tuple[StringEntry, ...]
    counts: Counts