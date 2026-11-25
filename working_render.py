"""Repeatable Blender studio renders for the M3x16 holder."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main(**kwargs):
    root = Path(kwargs.get("root", Path(__file__).resolve().parent)).resolve()
    blender = kwargs.get("blender", shutil.which("blender"))
    samples = kwargs.get("samples", 40)
    resolution = kwargs.get("resolution", 1100)
    render = kwargs.get("render", True)

    import working_verify
    if not blender:
        raise RuntimeError("Install Blender or pass blender=path_to_executable")
    records = working_verify.discover(root=root)
    base = records[0]
    holders = records
    assembly = records[0]
    work = root / "presentation"
    for folder in [work / "scenes", work / "qa"]:
        folder.mkdir(parents=True, exist_ok=True)
    job = {
        "root": str(root),
        "base": str(base["folder"] / "render/mesh_cache/base.stl"),
        "base_folder": str(base["folder"]),
        "lid": str(base["folder"] / "render/mesh_cache/lid.stl"),
        "pump": str(root / "source_file/pump_reference.stl"),
        "scene_file": str(work / "scenes/jt500_holder.blend"),
        "samples": samples,
        "resolution": resolution,
        "holders": [],
        "source_hashes": {},
        "palette": {"primary": "00B1B7", "secondary": "121212", "marker": "FEC601"},
        "style_source": "C:/gh/oomlout_oobb_version_5/RENDER_STYLE.md",
    }
    for record in holders:
        d = record["details"]
        job["holders"].append({
            "details": d,
            "mesh": str(record["folder"] / "render/mesh_cache/top.stl"),
            "top_folder": str(record["folder"]),
            "assembly_folder": str(assembly["folder"]),
        })
    for path in [Path(job["base"]), Path(job["pump"]), Path(job["lid"])] + [Path(r["mesh"]) for r in job["holders"]]:
        job["source_hashes"][path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    job_path = work / "render_job.json"
    job_path.write_text(json.dumps(job, indent=2) + "\n")
    if render:
        subprocess.run([blender, "--background", "--factory-startup", "--python-exit-code", "1",
                        "--python", str(root / "components/presentation/blender_scene.py"),
                        "--", str(job_path)], check=True, cwd=root)
    render_inlet_sections(folder=base["folder"], pump=job["pump"], details=base["details"])
    write_notes(root=root, job=job)
    validate_outputs(root=root, job=job)


def render_inlet_sections(**kwargs):
    """Draw the inlet and support footprints directly from the production meshes."""
    folder = Path(kwargs["folder"])
    details = kwargs["details"]
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, PathPatch
    from matplotlib.path import Path as PlotPath
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient
    from shapely.ops import unary_union
    import trimesh

    def section_loops(mesh, z):
        section = mesh.section([0, 0, 1], [0, 0, z])
        loops = [Polygon(line[:, :2]) for line in section.discrete]
        return sorted(loops, key=lambda loop: loop.area, reverse=True)

    def fill(axis, shape, colour):
        for polygon in getattr(shape, "geoms", [shape]):
            polygon = orient(polygon)
            rings = [polygon.exterior, *polygon.interiors]
            path = PlotPath.make_compound_path(*(PlotPath(ring.coords) for ring in rings))
            axis.add_patch(PathPatch(path, facecolor=colour, linewidth=0))

    datum = details["depth"] + details["base_foot_height"]
    base = trimesh.load_mesh(folder / "render/mesh_cache/base.stl")
    base.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    base.apply_translation([0, -details["pump_offset_y"], datum])
    exterior, *holes = section_loops(base, datum - .1)
    plate = exterior.difference(unary_union(holes))
    pump = trimesh.load_mesh(kwargs["pump"])
    pump.apply_transform(trimesh.transformations.rotation_matrix(math.radians(details["pump_rotation_z"]), [0, 0, 1]))
    figure, axes = plt.subplots(1, 2, figsize=(7.4, 4.15))
    for axis, title in zip(axes, ["Outlet toward the flush edge", "Outlet toward the base centre"]):
        face, *inlets = section_loops(pump, .1)
        fill(axis, plate, "#dedede")
        fill(axis, face, "#fafafa")
        fill(axis, plate.intersection(face.difference(unary_union(inlets))), "#e6aa49")
        for inlet in inlets:
            fill(axis, inlet, "#13918f")
        axis.plot(*face.exterior.xy, color="#42474a", linewidth=1.3)
        axis.set(xlim=(-22, 22), ylim=(-23, 23), aspect="equal", title=title)
        axis.axis("off")
        pump.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1]))
    figure.suptitle("Pump rear face on the retaining base", fontsize=15)
    legend = [Patch(color=c, label=label) for c, label in [
        ("#13918f", "Open inlet"), ("#e6aa49", "Supported housing"), ("#dedede", "Base plate")]]
    figure.legend(handles=legend, loc="lower center", ncol=3, frameon=False)
    figure.tight_layout(rect=[0, .09, 1, .97])
    figure.savefig(folder / "inlet_clearance.png", dpi=160)
    plt.close(figure)


def write_notes(**kwargs):
    root = Path(kwargs.get("root", Path(__file__).resolve().parent))
    import working_documentation
    working_documentation.write_readmes(root=root)


def validate_outputs(**kwargs):
    root = Path(kwargs.get("root", Path(__file__).resolve().parent))
    job = kwargs["job"]

    from PIL import Image
    manifest = json.loads((root / "presentation/qa/render_manifest.json").read_text())
    if manifest["source_hashes"] != job["source_hashes"]:
        raise ValueError("Presentation meshes are stale; rerun with render=True")
    if len(manifest["renders"]) != 6:
        raise ValueError("Expected six holder presentation views")
    for entry in manifest["renders"]:
        with Image.open(entry["output"]) as img:
            img.verify()
    if not Path(manifest["scene_file"]).is_file():
        raise ValueError("Editable Blender study was not saved")
    (root / "presentation/qa/presentation_validation.json").write_text(json.dumps({
        "status": "passed", "renders": 6,
        "editable_scene": manifest["scene_file"], "mesh_hashes_match": True,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
