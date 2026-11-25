"""Generate the project/part READMEs and the OOBB assembly book from OOMP data."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "components"))
PART_ID = "oobb_holder_motor_pump_submersible_jt_500"


def load_documentation(**kwargs):
    root = Path(kwargs.get("root", ROOT))
    part = yaml.safe_load((root / "parts" / PART_ID / "working.yaml").read_text(encoding="utf-8"))
    return copy.deepcopy(part["documentation"]), part["oobb_details"]


def identify_parts(**kwargs):
    doc = kwargs["doc"]
    parts = copy.deepcopy(doc["parts"])
    for key, part in parts.items():
        part["key"] = key
        part["identity_source"] = "Project printed part" if part["printed"] else "OOMP catalogue identity; public working.yaml checked 2026-11-17"
        if part["printed"]:
            continue
        digest = hashlib.md5(part["id"].encode("utf-8")).hexdigest()
        number, alpha = int(digest[:6], 16), ""
        while number:
            number, digit = divmod(number, 36)
            alpha = "0123456789abcdefghijklmnopqrstuvwxyz"[digit] + alpha
        part.update(md5=digest, md5_6_alpha=alpha or "0", short_url="https://oom.lt/a/" + (alpha or "0"),
                    short_label="oom.lt/a/" + (alpha or "0"), redirect_status="Not verified; code generation does not register a redirect")
    codes = {}
    for part in parts.values():
        if not part["printed"]:
            previous = codes.setdefault(part["md5_6_alpha"], part["id"])
            assert previous == part["id"], "Hardware short-code collision"
    return parts


def write_readmes(**kwargs):
    root = Path(kwargs.get("root", ROOT))
    doc, d = load_documentation(root=root)
    assembly = root / "parts" / PART_ID
    rel = assembly.relative_to(root).as_posix()
    parts = identify_parts(doc=doc)
    browser = doc["book"].get("viewer_url", "")
    viewer_link = f"[Open in browser]({browser})" if browser else f"[Download offline viewer]({rel}/assembly/assembly_instructions.html)"
    hero_link = f"{rel}/README.md"
    root_text = f"""# {doc['title']}

{doc['description']}

Documentation follows [{doc['creator_name']}'s wave-drive assembly book]({doc['credit_url']}) and [OOBB conventions](https://github.com/oomlout/oomlout_oobb_version_5), by [{doc['creator_name']}]({doc['creator_url']}). Pump fit follows the [supplied JT-500 drawing](source_file/pump_dimension_reference.png).

{doc['ai_message']} {doc['physical_status']}

> {doc['notice']}

## Build

| Image | Version and description | Main README | HTML assembly instructions | PDF download |
| --- | --- | --- | --- | --- |
| [![AI-generated CAD render: JT-500 holder]({rel}/assembly/readme/hero_thumb.png)]({hero_link}) | [**{doc['configuration_title']}**]({hero_link})<br>{doc['version_description']} | [Design, parts and assembly]({rel}/README.md) | {viewer_link} | [Download PDF]({rel}/assembly/assembly_instructions.pdf) |

[Print all three pieces]({rel}/3dpr.stl) · [Follow the six illustrated steps]({rel}/README.md#assembly) · [OOBB catalogue](navigation_oobb/README.md)
"""
    (root / "README.md").write_text(root_text, encoding="utf-8")
    hardware = "| Hardware for one holder | Quantity | Catalogue identity | OOMP code |\n| --- | ---: | --- | --- |\n"
    merged_hardware = {}
    for part in parts.values():
        if not part["printed"]:
            if part["id"] in merged_hardware:
                merged_hardware[part["id"]]["quantity"] += part["quantity"]
            else:
                merged_hardware[part["id"]] = copy.deepcopy(part)
    for part in merged_hardware.values():
        hardware += f"| [{part['name']}]({part['catalogue_url']}) | {part['quantity']} | [{part['id']}]({part['catalogue_url']}) | [{part['md5_6_alpha']}]({part['short_url']}) |\n"
    assembly_text = ""
    for i, step in enumerate(doc["steps"], 1):
        assembly_text += f"\n### {i}. {step['title']}\n\n{step['action']}\n\n[![AI-generated CAD: {step['title']}](assembly/readme/step_{i:02d}_thumb.png)](assembly/cards/step_{i:02d}.png)\n"
    preparation = "\n".join("- " + item for item in doc["preparation"])
    installation = "\n".join("- " + item for item in doc["installation"])
    detail = f"""# JT-500 holder - M3 x 16 mm

> {doc['notice']}

## Summary

The retaining base and two-wall clamp capture a JT-500 pump between its rear housing and front face. Four screws enter from the underside and engage nuts loaded into the clamp's side tabs.

{doc['ai_message']} {doc['physical_status']}

![AI-generated CAD render: JT-500 pump in its holder](assembly/readme/hero.png)

[Project](../../README.md) · [Assembly booklet PDF](assembly/assembly_instructions.pdf) · [Download offline HTML](assembly/assembly_instructions.html) · [Jump to assembly](#assembly)

## Details

![Assembled base, clamp and cover](render_studio.png)

Print the [combined STL](3dpr.stl) once. It contains the 6 mm base plate, two-wall clamp and 3 mm cover in their print orientations. The 5 × 5 base measures 74 × 74 mm. [Editable print layout](3dpr.scad) · [Assembled CAD](assembly.scad)

Turn the pump through 180° to choose the outlet side. Each of the two 15.5 mm roof openings can take the outlet or cable. Underneath, the 4 mm wide ledges rest against solid housing between the three inlets. The feet leave 3 mm beneath the fin tips.

![Rear-face sections showing open inlets and contact with both retaining ledges in each orientation](inlet_clearance.png)

The cover captures six M6 nuts on the 15 mm grid. Curved notches in the clamp leave 15 mm diameter clearance around the two M6 base holes at the flush edge.

## Parts

![AI-generated CAD render: printed parts and pump exploded along the assembly axis](render_exploded.png)

{hardware}
The table covers one complete holder and pump. Hose, electrical connections and fasteners for attaching the base to another structure are outside this inventory. Use ordinary hex nuts and measure countersunk screws including the head.

## Assembly

[Download the offline page viewer](assembly/assembly_instructions.html) · [Download the A4 booklet](assembly/assembly_instructions.pdf)

### Preparation

{preparation}
{assembly_text}
### Installation

{installation}

### Regeneration

Run `python action_make_holder.py` to rebuild CAD, run geometry checks, render the views and generate these instructions. The source text, part labels and six-step sequence are explicit dictionaries in `working_oomp_populate.py`, carried through `working_oomp.py` and `working_scad.py`. Run `python working_documentation.py --no-render` to recomposite the book from current, matching renders. [Build and validation notes](../../presentation/README.md).
"""
    (assembly / "README.md").write_text(detail, encoding="utf-8")
    companion = f"# JT-500 holder assembly\n\n> {doc['notice']}\n\n{doc['physical_status']}\n\n[Part README](README.md) · [PDF](assembly/assembly_instructions.pdf) · [Download offline HTML](assembly/assembly_instructions.html)\n\n## Preparation\n\n{preparation}\n{assembly_text}\n## Installation\n\n{installation}\n"
    (assembly / "ASSEMBLY.md").write_text(companion, encoding="utf-8")


def build_hardware(**kwargs):
    output = Path(kwargs["output"])
    screw_length = kwargs.get("screw_length", 16)
    lid_screw_length = kwargs.get("lid_screw_length", 16)
    openscad = kwargs.get("openscad", shutil.which("openscad.com") or shutil.which("openscad"))
    # Nominal display solids, not pocket cutters: threads omitted. The screw
    # has its flush head face at z=0 and tip at z=16, matching the CAD joint.
    sources = {
        "screw": f"$fn=64; difference() {{ union() {{ cylinder(h=1.7,r1=3,r2=1.5); translate([0,0,1.7]) cylinder(h={screw_length}-1.7,r=1.5); }} translate([0,0,-0.01]) cylinder(h=1.21,r=2/sqrt(3),$fn=6); }}",
        "nut": "$fn=64; difference() { cylinder(h=2.5,r=5.5/sqrt(3),$fn=6); translate([0,0,-.01]) cylinder(h=2.52,r=1.5); }",
        "m6nut": "$fn=64; difference() { cylinder(h=5,r=5.77,$fn=6); translate([0,0,-.01]) cylinder(h=5.02,r=3); }",
    }
    sources["m3nut"] = sources["nut"]
    sources["capscrew"] = sources["screw"].replace(f"h={screw_length}-1.7", f"h={lid_screw_length}-1.7")
    paths = {}
    for key, source in sources.items():
        scad = output / "render" / (key + ".scad")
        scad.parent.mkdir(parents=True, exist_ok=True)
        scad.write_text(source)
        target = scad.with_suffix(".stl")
        subprocess.run([openscad, "--backend=Manifold", "-o", str(target), str(scad)], check=True, capture_output=True)
        paths[key] = str(target)
    return paths


def main(**kwargs):
    root = Path(kwargs.get("root", ROOT))
    render = kwargs.get("render", True)
    samples = kwargs.get("samples", 24)
    resolution = kwargs.get("resolution", 1200)
    blender = kwargs.get("blender", shutil.which("blender"))
    doc, dimensions = load_documentation(root=root)
    output = root / "parts" / PART_ID / "assembly"
    output.mkdir(parents=True, exist_ok=True)
    data = copy.deepcopy(doc)
    data["parts"] = identify_parts(doc=doc)
    data["printed_keys"] = [k for k, p in data["parts"].items() if p["printed"]]
    data["physical_item_count"] = sum(p["quantity"] for p in data["parts"].values())
    introduced, quantities = [], {}
    for number, step in enumerate(data["steps"], 1):
        step["number"] = number
        step["loose_parts"] = {}
        for name in step["add"]:
            assert name not in introduced, "Repeated physical item: " + name
            introduced.append(name)
            key = name.split("_")[0]
            step["loose_parts"][key] = step["loose_parts"].get(key, 0) + 1
            quantities[key] = quantities.get(key, 0) + 1
        step["cumulative_instances"] = list(introduced)
    assert quantities == {k: p["quantity"] for k, p in data["parts"].items()}
    data["source_hashes"] = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in [
        "working_oomp_populate.py", "working_scad.py", "working_documentation.py", "components/instructions/render.py",
        "components/presentation/blender_scene.py",
        "source_file/oomlout_logo_unshaded_original.svg",
        f"parts/{PART_ID}/3dpr.stl", f"parts/{PART_ID}/render/mesh_cache/base.stl", f"parts/{PART_ID}/render/mesh_cache/top.stl", f"parts/{PART_ID}/render/mesh_cache/lid.stl", "source_file/pump_reference.stl",
    ]}
    build = json.loads((root / "build_manifest.json").read_text())
    for path, digest in build["source_sha256"].items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == digest, "Rebuild CAD before documenting changed source: " + path
    meshes = {key: str(root / "parts" / PART_ID / "render/mesh_cache" / (key + ".stl")) for key in ["base", "top", "lid"]}
    meshes["pump"] = str(root / "source_file/pump_reference.stl")
    meshes.update(build_hardware(output=output, screw_length=dimensions["screw_length"], lid_screw_length=dimensions["lid_screw_length"]))
    job = {"output": str(output), "meshes": meshes, "data": data, "dimensions": dimensions,
           "samples": samples, "resolution": resolution, "source_hashes": data["source_hashes"]}
    job_path = output / "render/job.json"
    job_path.write_text(json.dumps(job, indent=2))
    if render:
        subprocess.run([blender, "--background", "--factory-startup", "--python-exit-code", "1", "--python",
                        str(root / "components/instructions/render.py"), "--", str(job_path)], cwd=root, check=True)
    rendered = json.loads((output / "render/render_manifest.json").read_text())
    assert rendered["source_hashes"] == data["source_hashes"], "Instruction renders are stale"
    for step, entry in zip(data["steps"], rendered["renders"]):
        assert entry["instances"] == step["cumulative_instances"], "Missing cumulative assembly item"
    for entry in rendered["renders"]:
        path = Path(entry["output"])
        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            white = Image.new("RGBA", rgba.size, "white")
            white.alpha_composite(rgba)
            white.convert("RGB").save(path)
    data["hardware_geometry"] = "Nominal display solids, threads omitted: screw head diameter 6 mm, head depth 1.7 mm, 2 mm hex recess; M3 nut 5.5 mm AF x 2.5 mm; M6 nut 5 mm thick. Not printable replacements."
    from instructions import assembly_booklet, assembly_viewer
    assembly_booklet.publish(output=output, data=data)
    assembly_booklet.review_outputs(output=output, data=data)
    assembly_viewer.publish(output=output, data=data)
    with (output / "parts.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["key", "name", "quantity", "id", "identity_source", "catalogue_url", "md5", "md5_6_alpha", "short_url", "redirect_status"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data["parts"].values())
    readme = output / "readme"
    readme.mkdir(exist_ok=True)
    font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
    with Image.open(output / "render/raw/book_cover.png") as original:
        hero = original.convert("RGB")
        ImageDraw.Draw(hero).text((hero.width / 2, hero.height - 30), doc["notice"], font=font, fill="black", anchor="mm")
        hero.save(readme / "hero.png")
        hero.thumbnail((480, 480))
        hero.save(readme / "hero_thumb.png")
    for number in range(1, len(data["steps"]) + 1):
        with Image.open(output / "cards" / f"step_{number:02d}.png") as image:
            image.thumbnail((480, 480))
            image.save(readme / f"step_{number:02d}_thumb.png")
    write_readmes(root=root)
    validate_links(root=root)
    print("Generated project README, one complete-part README, written assembly, 8-page PDF and offline HTML.")


def validate_links(**kwargs):
    root = Path(kwargs.get("root", ROOT))
    checked = 0
    paths = [root / "README.md"] + list((root / "parts").glob("*/README.md")) + list((root / "parts").glob("*/ASSEMBLY.md"))
    for path in paths:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            target = target.split("#")[0]
            assert (path.parent / target).exists(), f"Broken link in {path}: {target}"
            checked += 1
    return checked


if __name__ == "__main__":
    import sys
    main(render="--no-render" not in sys.argv)
