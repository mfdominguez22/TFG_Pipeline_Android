import re
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class ProjectInfo:
    """Informacion basica del modulo analizado, definida en el disenio interno (§5.3.3)."""
    root: Path
    module: str
    namespace: str
    res_dir: Path

def locate(project_root: Path, module: str | None) -> ProjectInfo:
    """
    Localiza el modulo de aplicacion y extrae su espacio de nombres.
    Si no se especifica modulo, asume 'app' por convencion.
    """
    module_name = module or "app"
    module_dir = project_root / module_name
    
    if not module_dir.exists():
        raise RuntimeError(f"No se encuentra el directorio del modulo: {module_dir}")

    namespace = None
    
    # Buscar en ficheros de Gradle
    for build_file in ("build.gradle", "build.gradle.kts"):
        build_path = module_dir / build_file
        if build_path.exists():
            content = build_path.read_text(encoding="utf-8")
            # Busca 'namespace "com.ejemplo"' o 'namespace = "com.ejemplo"'
            match = re.search(r'''namespace\s*=?\s*['"]([^'"]+)['"]''', content)
            if match:
                namespace = match.group(1)
                break
                
    # 2. Cai­da de seguridad al AndroidManifest.xml
    if not namespace:
        manifest_path = module_dir / "src" / "main" / "AndroidManifest.xml"
        if manifest_path.exists():
            content = manifest_path.read_text(encoding="utf-8")
            match = re.search(r'''package\s*=\s*['"]([^'"]+)['"]''', content)
            if match:
                namespace = match.group(1)

    if not namespace:
        # Se detiene con error si no puede encontrarlo en ninguno de los dos sitios
        raise RuntimeError(f"No se pudo extraer el espacio de nombres del modulo {module_name}")

    return ProjectInfo(
        root=project_root,
        module=module_name,
        namespace=namespace,
        res_dir=module_dir / "src" / "main" / "res"
    )
