#!/usr/bin/env python3
"""
Sincroniza los writeups de HTB desde el repositorio externo a la estructura de MkDocs.

Uso:
    python sync_writeups.py [--repo-url URL] [--work-dir DIR]

El script clona (o actualiza) el repositorio de writeups y copia los archivos
a la carpeta docs/ para que MkDocs los sirva.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/egz-dev/HTB.git"
WORK_DIR = Path(".sync_cache")
DOCS_DIR = Path("docs")

# Mapeo de carpetas del repo origen a docs/
FOLDER_MAP = {
    "machines": "writeups",
    "documentación": "guias",
}


def run(cmd: list[str], cwd: Path | None = None) -> None:
    """Ejecuta un comando y aborta si falla."""
    print(f"  → {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ Error: {result.stderr.strip()}")
        sys.exit(1)


def get_default_branch(work_dir: Path) -> str:
    """Detecta la rama por defecto del repositorio clonado."""
    result = subprocess.run(
        ["git", "remote", "show", "origin"],
        cwd=work_dir, capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("HEAD branch:"):
            return stripped.split(":")[1].strip()
    return "main"  # fallback


def clone_or_pull(repo_url: str, work_dir: Path) -> None:
    """Clona el repositorio si no existe, o hace pull si ya está clonado."""
    if (work_dir / ".git").exists():
        print(f"[*] Actualizando repositorio en {work_dir}...")
        run(["git", "fetch", "origin"], cwd=work_dir)
        branch = get_default_branch(work_dir)
        run(["git", "reset", "--hard", f"origin/{branch}"], cwd=work_dir)
    else:
        print(f"[*] Clonando {repo_url} en {work_dir}...")
        work_dir.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", repo_url, str(work_dir)])


def copy_content(src_dir: Path, dst_dir: Path, label: str) -> list[str]:
    """
    Copia el contenido de src_dir a dst_dir.
    Retorna la lista de rutas relativas copiadas (sin extensión).
    """
    if not src_dir.exists():
        print(f"  ⚠ Carpeta '{src_dir}' no encontrada, saltando...")
        return []

    # Limpiar destino
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    entries: list[str] = []
    for item in sorted(src_dir.iterdir()):
        dest = dst_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
            # Buscar un .md principal dentro
            for md_file in sorted(dest.rglob("*.md")):
                rel = md_file.relative_to(DOCS_DIR)
                entries.append(str(rel.with_suffix("")))
                break  # solo el primer .md por carpeta
        elif item.suffix == ".md":
            shutil.copy2(item, dest)
            rel = dest.relative_to(DOCS_DIR)
            entries.append(str(rel.with_suffix("")))

    print(f"  ✓ {label}: {len(entries)} elementos copiados")
    return entries


def generate_nav(writeup_entries: list[str], guia_entries: list[str]) -> str:
    """Genera la sección 'nav' del mkdocs.yml con las entradas descubiertas."""
    lines = [
        "nav:",
        '  - Inicio: index.md',
    ]

    if writeup_entries:
        lines.append("  - Writeups:")
        lines.append("      - writeups/index.md")
        for entry in writeup_entries:
            name = entry.split("/")[-1].replace("-", " ").replace("_", " ").title()
            lines.append(f"      - {name}: {entry}.md")
    else:
        lines.append("  - Writeups: writeups/index.md")

    if guia_entries:
        lines.append("  - Guías:")
        lines.append("      - guias/index.md")
        for entry in guia_entries:
            name = entry.split("/")[-1].replace("-", " ").replace("_", " ").title()
            lines.append(f"      - {name}: {entry}.md")
    else:
        lines.append("  - Guías: guias/index.md")

    return "\n".join(lines) + "\n"


def update_mkdocs_nav(writeup_entries: list[str], guia_entries: list[str]) -> None:
    """Actualiza la sección nav en mkdocs.yml con las entradas generadas."""
    mkdocs_path = Path("mkdocs.yml")
    content = mkdocs_path.read_text()

    # Encontrar y reemplazar la sección 'nav:'
    nav_start_marker = "# --nav-auto-start--"
    nav_end_marker = "# --nav-auto-end--"

    if nav_start_marker in content and nav_end_marker in content:
        # Reemplazar entre marcadores
        before = content.split(nav_start_marker)[0]
        after = content.split(nav_end_marker)[1]
        new_nav = generate_nav(writeup_entries, guia_entries)
        new_content = before + nav_start_marker + "\n" + new_nav + nav_end_marker + after
        mkdocs_path.write_text(new_content)
        print("[*] Nav de mkdocs.yml actualizada")
    else:
        print("[*] No se encontraron marcadores # --nav-auto-start--/--nav-auto-end-- en mkdocs.yml")
        print("    La nav se deja como está (usa la configuración estática)")


def create_index(dst_dir: Path, title: str, entries: list[str]) -> None:
    """Crea un index.md en dst_dir con enlaces a las entradas."""
    index_path = dst_dir / "index.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"# {title}", ""]
    if entries:
        for entry in entries:
            name = entry.split("/")[-1].replace("-", " ").replace("_", " ").title()
            lines.append(f"- [{name}]({entry.split('/', 1)[1] if '/' in entry else entry}.md)")
    else:
        lines.append("_No hay entradas todavía._")

    index_path.write_text("\n".join(lines) + "\n")
    print(f"  ✓ index.md creado en {dst_dir}")


def main():
    parser = argparse.ArgumentParser(description="Sincroniza writeups HTB → MkDocs")
    parser.add_argument("--repo-url", default=REPO_URL, help="URL del repositorio de writeups")
    parser.add_argument("--work-dir", default=str(WORK_DIR), help="Directorio de trabajo para el clon")
    args = parser.parse_args()

    repo_url: str = args.repo_url
    work_dir = Path(args.work_dir)

    print("=" * 50)
    print("  Sincronización de Writeups HTB → MkDocs")
    print("=" * 50)

    # 1. Clonar o actualizar
    clone_or_pull(repo_url, work_dir)

    # 2. Copiar contenido
    all_writeup_entries: list[str] = []
    all_guia_entries: list[str] = []

    for src_folder, dst_folder in FOLDER_MAP.items():
        src = work_dir / src_folder
        dst = DOCS_DIR / dst_folder
        entries = copy_content(src, dst, dst_folder)

        if dst_folder == "writeups":
            all_writeup_entries = entries
        elif dst_folder == "guias":
            all_guia_entries = entries

    # 3. Copiar assets si existen
    assets_src = work_dir / "assets"
    assets_dst = DOCS_DIR / "assets"
    if assets_src.exists():
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)
        print(f"  ✓ assets copiados a {assets_dst}")
    else:
        print("  ⚠ Carpeta 'assets' no encontrada, saltando...")

    # 4. Crear índices
    create_index(DOCS_DIR / "writeups", "Writeups - Máquinas HTB", all_writeup_entries)
    create_index(DOCS_DIR / "guias", "Guías Prácticas", all_guia_entries)

    # 5. Actualizar nav
    update_mkdocs_nav(all_writeup_entries, all_guia_entries)

    print()
    print("[✓] Sincronización completada.")
    print(f"    Writeups: {len(all_writeup_entries)}")
    print(f"    Guías:    {len(all_guia_entries)}")


if __name__ == "__main__":
    main()
