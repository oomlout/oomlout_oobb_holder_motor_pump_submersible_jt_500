"""Write the single-build OOBB taxonomy entry beside its printable mesh."""
from pathlib import Path
import os
import shutil

import yaml


def publish(**kwargs):
    folder = Path(kwargs["folder"]).resolve()
    root = folder.parents[1]
    part = yaml.safe_load((folder / "working.yaml").read_text(encoding="utf-8"))
    nav = root / "navigation_oobb"
    levels = [part.get(f"taxonomy_{index}") for index in range(1, 21)]
    leaf = nav.joinpath(*(value for value in levels if value))
    if leaf == nav:
        raise ValueError("Missing OOMP taxonomy for the printable holder")
    leaf.mkdir(parents=True, exist_ok=True)
    mesh = folder / "3dpr.stl"
    copy = leaf / mesh.name
    shutil.copyfile(mesh, copy)
    if copy.read_bytes() != mesh.read_bytes():
        raise ValueError("Navigation STL differs from the production STL")
    name = part["documentation"]["title"]
    main = Path(os.path.relpath(folder / "README.md", leaf)).as_posix()
    (leaf / "oomp_id.txt").write_text(part["id"] + "\n", encoding="utf-8")
    (leaf / "README.md").write_text(
        f"# [{name}]({main})\n\n"
        f"[Print the complete holder](3dpr.stl) · [Illustrated assembly]({main}#assembly)\n",
        encoding="utf-8",
    )
    for parent in leaf.parents:
        if parent == root:
            break
        entry = Path(os.path.relpath(leaf / "README.md", parent)).as_posix()
        (parent / "README.md").write_text(f"# OOBB holders\n\n[{name}]({entry})\n", encoding="utf-8")
