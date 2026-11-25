"""Cumulative assembly scenes using production holder meshes and nominal hardware."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "components"))
from presentation.blender_scene import material, load_mesh, make_scene


def main(**kwargs):
    job_path = Path(kwargs["job_path"])
    job = json.loads(job_path.read_text())
    output = Path(job["output"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    job["device"] = "CPU"
    for backend in ["OPTIX", "CUDA"]:
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            if any(d.type == backend for d in prefs.devices):
                for device in prefs.devices:
                    device.use = device.type == backend
                job["device"] = "GPU"
                break
        except (TypeError, RuntimeError):
            continue
    mats = {
        "base": material(name="Base black", swatch="121212"),
        "top": material(name="Clamp teal", swatch="00B1B7"),
        "pump": material(name="Pump grey", swatch="707A7E"),
        "nut": material(name="Nut steel", swatch="A5ABB2", roughness=.28),
        "screw": material(name="Screw black steel", swatch="303439", roughness=.28),
    }
    mats.update(lid=mats["base"], m3nut=mats["nut"], m6nut=mats["nut"], capscrew=mats["screw"])
    for key in ["nut", "screw"]:
        mats[key].node_tree.nodes.get("Principled BSDF").inputs["Metallic"].default_value = .7
    material(name="Warm white background", swatch="F7F6F2")
    meshes = {key: load_mesh(path=path, mat=mats[key], name=key) for key, path in job["meshes"].items()}
    d = job["dimensions"]
    z = d["depth"] + d["base_foot_height"]
    shift = d["pump_offset_y"]
    lid_z = z + d["pump_body_length"] + d["axial_clearance"] + d["top_depth"]
    transforms = {
        "base": Matrix.Translation((0, 0, z)) @ Matrix.Rotation(math.pi, 4, "X"),
        "top": Matrix.Translation((0, shift - (d["top_height"] * 15 - 1) / 2, z)) @ Matrix.Rotation(-math.pi / 2, 4, "X"),
        "pump": Matrix.Translation((0, shift, z)),
        "lid": Matrix.Translation((0, shift, lid_z)),
    }
    for i, (x, y) in enumerate([(x, y) for x in [-d["mount_x"], d["mount_x"]] for y in [-d["mount_y"], d["mount_y"]]], 1):
        transforms[f"nut_{i}"] = Matrix.Translation((x, y + shift, z + d["nut_height_from_foot"]))
        transforms[f"screw_{i}"] = Matrix.Translation((x, y + shift, z - d["depth"]))
    m3_positions = [entry["pos"] for entry in d["attachment_nuts"] if entry["radius_name"] == "m3"] + d["lid_mount_positions"]
    m6_positions = [entry["pos"] for entry in d["attachment_nuts"] if entry["radius_name"] == "m6"]
    for key, positions, depth in [("m3nut", m3_positions, 3), ("m6nut", m6_positions, 5.5)]:
        for i, (x, y) in enumerate(positions, 1):
            nut_z = z + d["pump_body_length"] + d["axial_clearance"] + d["lid_nut_bottom"] + .5 if key == "m3nut" else lid_z - depth
            transforms[f"{key}_{i}"] = Matrix.Translation((x, y + shift, nut_z))
    for i, (x, y) in enumerate(d["lid_mount_positions"], 1):
        transforms[f"capscrew_{i}"] = Matrix.Translation((x, y + shift, lid_z + d["lid_depth"])) @ Matrix.Rotation(math.pi, 4, "X")
    orientation = Matrix.Rotation(math.radians(d["pump_rotation_z"]), 4, "Z")
    transforms["pump"] = transforms["pump"] @ orientation
    seen, results = [], []
    for step in job["data"]["steps"]:
        seen.extend(step["add"])
        items = []
        for name in seen:
            delta = [v * job["data"]["style"]["explosion_scale"] for v in step["move"].get(name, [0, 0, 0])]
            items.append((name, meshes[name.split("_")[0]], Matrix.Translation(delta) @ transforms[name]))
        results.append(make_scene(name=step["key"], items=items, job=job,
                                 output=output / "render/raw" / (step["key"] + ".png"),
                                 direction=step.get("eye", job["data"]["style"]["eye"]),
                                 captions=False, show_floor=False))
    all_items = [(name, meshes[name.split("_")[0]], transforms[name]) for name in seen]
    results.append(make_scene(name="book_cover", items=all_items, job=job,
                             output=output / "render/raw/book_cover.png", captions=False, show_floor=False,
                             direction=job["data"]["style"]["eye"]))
    for key, mesh in meshes.items():
        transform = transforms.get(key, Matrix.Identity(4))
        results.append(make_scene(name="part_" + key, items=[(key, mesh, transform)], job=job,
                                 output=output / "render/raw" / ("part_" + key + ".png"),
                                 captions=False, show_floor=False, direction=[1, -1, .9]))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "render/assembly.blend"))
    (output / "render/render_manifest.json").write_text(json.dumps({
        "source_hashes": job["source_hashes"], "renders": results,
        "cumulative_instances": seen, "device": job["device"],
    }, indent=2))


if __name__ == "__main__":
    main(job_path=sys.argv[sys.argv.index("--") + 1])
