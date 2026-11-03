from pathlib import Path
from typing import Iterable
from contentgen.model.project import ProjectModel, Counts, LayoutInfo
from contentgen.xmlio.parser import parse, XmlParseError
from contentgen.reader.strings import read_strings
from contentgen.reader.styles import read_styles
from contentgen.reader.layouts import scan_layout
from contentgen.reader.fields import build_field, ReaderEnv
from contentgen.reader.labels import attach_labels
from contentgen.reader.code_analysis import ANALYZERS
from contentgen.reader.overwrite import mark_overwrite
from contentgen.reader.project import locate

def run_reader_stage(
    project_root: Path,
    layout_paths: Iterable[Path],
    values_paths: Iterable[Path],
    code_analysis_config: str = "none",
    module: str | None = None,
) -> ProjectModel:
    
    """Ejecuta el pipeline completo del Lector de proyecto."""
    project_info = locate(project_root, module)
    namespace = project_info.namespace
    malformed_files: list[str] = []

    value_docs = []
    for path in values_paths:
        try:
            value_docs.append(parse(path))
        except XmlParseError:
            malformed_files.append(str(path))

    string_index = read_strings(value_docs)
    style_index = read_styles(value_docs)
    env = ReaderEnv(namespace=namespace, strings=string_index, styles=style_index)

    all_fields = []
    layout_infos = []
    counts = {
        "text_elements": 0,
        "without_id": 0,
        "attrs_resolved": 0,
        "alt_layouts_skipped": 0,
    }

    for path in layout_paths:
        try:
            doc = parse(path)
            scan_result = scan_layout(doc)

            layout_infos.append(
                LayoutInfo(
                    path=str(path),
                    includes=scan_result.includes,
                    view_stubs=scan_result.view_stubs,
                )
            )

            counts["text_elements"] += scan_result.text_elements_count
            counts["without_id"] += scan_result.text_elements_without_id_count

            fields_in_layout = []
            for candidate in scan_result.candidates:
                node, parent, family = candidate
                field = build_field(node, family=family, doc=doc, env=env, parent_element=parent)
                fields_in_layout.append(field)

            fields_in_layout = attach_labels(tuple(fields_in_layout), doc, env)
            all_fields.extend(fields_in_layout)

        except XmlParseError:
            malformed_files.append(str(path))

    analyzer = ANALYZERS.get(code_analysis_config, ANALYZERS["none"])
    evidence = analyzer.analyze({}, tuple(all_fields))
    final_fields = mark_overwrite(tuple(all_fields), evidence)

    if not layout_infos:
        raise RuntimeError(
            f"Postcondición fallida: No se ha analizado ningún layout válido. "
            f"Ficheros mal formados: {len(malformed_files)}"
        )

    if not final_fields:
        raise RuntimeError("Postcondición fallida: Se han analizado layouts pero no se ha registrado ningún campo.")

    model_counts = Counts(
        text_elements=counts["text_elements"],
        text_elements_without_id=counts["without_id"],
        attributes_resolved_from_styles=counts["attrs_resolved"],
        alternative_layouts_not_analyzed=counts["alt_layouts_skipped"],
        malformed_files=tuple(malformed_files),
    )

    return ProjectModel(
        schema_version="1.0",
        reader_version="1.1",
        namespace=namespace,
        code_analysis=code_analysis_config,
        layouts=tuple(layout_infos),
        fields=tuple(final_fields),
        strings=tuple(string_index.values()),
        counts=model_counts,
    )