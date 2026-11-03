import json
from pathlib import Path
from dataclasses import asdict
from contentgen.reader.stage import run_reader_stage

def main():
    # 1. Definir las rutas apuntando a nuestro proyecto de prueba
    project_root = Path("tests/fixtures/android/test_app")
    res_dir = project_root / "app" / "src" / "main" / "res"
    
    layout_paths = list((res_dir / "layout").glob("*.xml"))
    values_paths = list((res_dir / "values").glob("*.xml"))

    print(f"Buscando en {project_root}...")
    print(f"Layouts encontrados: {len(layout_paths)}")
    print(f"Ficheros de values encontrados: {len(values_paths)}\n")

    # 2. Ejecutar la etapa del Lector
    try:
        project_model = run_reader_stage(
            project_root=project_root,
            layout_paths=layout_paths,
            values_paths=values_paths,
            module="app" # Le indicamos explícitamente el módulo
        )
        
        # 3. Convertir las dataclasses inmutables a un diccionario nativo y mostrarlo
        model_dict = asdict(project_model)
        
        # Para que sea legible, convertimos los Enums a su valor string
        def default_serializer(obj):
            if hasattr(obj, 'value'):
                return obj.value
            return str(obj)

        print("=== EXTRACCIÓN EXITOSA ===")
        print(json.dumps(model_dict, indent=2, default=default_serializer, ensure_ascii=False))

    except Exception as e:
        print(f"ERROR DURANTE LA EJECUCIÓN:\n{e}")

if __name__ == "__main__":
    main()