"""Build the M3x16 holder, then run measured-geometry checks."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def discover(**kwargs):
    root = Path(kwargs.get('root', Path(__file__).resolve().parent))
    import yaml
    records = []
    for path in sorted((root / 'parts').glob('*/working.yaml')):
        part = yaml.safe_load(path.read_text())
        details = part.get('oobb_details', {})
        if details.get('oobb_type') == 'holder_motor_pump_submersible_jt_500':
            records.append({'folder': path.parent, 'details': details})
    return records


def main(**kwargs):
    regenerate = kwargs.get('regenerate', True)
    openscad = kwargs.get('openscad', shutil.which('openscad.com') or shutil.which('openscad'))
    root = Path(kwargs.get('root', Path(__file__).resolve().parent)).resolve()
    render_previews = kwargs.get('render_previews', True)

    import working
    if Path.cwd().resolve() != root:
        raise RuntimeError('Run this build from the project directory')
    if not openscad:
        raise RuntimeError('OpenSCAD executable not found')
    if regenerate:
        working.run(run_oomp_populate=True, run_oomp=True, run_scad=True,
                    run_action=False, modes=['true', '3dpr'], save_type='none', navigation=False)
    manifest = {'source_sha256': {}, 'parts': []}
    for source in ['working_scad.py', 'working_oomp_populate.py', 'source_file/pump_reference.stl']:
        manifest['source_sha256'][source] = hashlib.sha256((root / source).read_bytes()).hexdigest()
    for record in discover(root=root):
        folder, d = record['folder'], record['details']
        if d['piece'] == 'all':
            subprocess.run([openscad, '--backend=Manifold', '--export-format', 'binstl',
                            '-o', str(folder / '3dpr.stl'), str(folder / '3dpr.scad')], check=True)
            manifest['parts'].append({
                'folder': folder.relative_to(root).as_posix(),
                'piece': d['piece'], 'screw_length_mm': d['screw_length'],
                'sha256': hashlib.sha256((folder / '3dpr.stl').read_bytes()).hexdigest(),
            })
            make_piece_cache(folder=folder, details=d)
            import working_navigation
            working_navigation.publish(folder=folder)
            import working_scad
            import opsc
            assembly = {'components': [], 'components_objects': [], 'components_string': []}
            assembled = dict(d, piece='assembly', prepare_print=False)
            working_scad.get_holder_motor_pump_submersible_jt_500(assembly, **assembled)
            opsc.opsc_make_object(str(folder / 'assembly.scad'), assembly['components'], mode='true')
        if render_previews:
            subprocess.run([openscad, '--backend=Manifold', '--render', '--imgsize=800,800',
                            '--autocenter', '--viewall', '--projection=o', '--camera=0,0,40,65,0,35,240',
                            '-o', str(folder / 'preview.png'), str(folder / '3dpr.scad')], check=True)
    (root / 'build_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    result = subprocess.run(['python', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                            cwd=root, capture_output=True, text=True)
    qa = root / 'presentation/qa'
    qa.mkdir(parents=True, exist_ok=True)
    (qa / 'test_run.txt').write_text(result.stdout + result.stderr)
    print(result.stderr)
    result.check_returncode()
    print('Built and checked the M3x16 holder and base.')


def make_piece_cache(**kwargs):
    """Derive internal render/test meshes from the single public print file."""
    folder = Path(kwargs['folder'])
    details = kwargs['details']
    import trimesh
    import numpy as np
    import working_scad

    layout = trimesh.load_mesh(folder / '3dpr.stl')
    pieces = sorted(layout.split(), key=lambda mesh: mesh.extents[2])
    if len(pieces) != 3:
        raise ValueError('The print file must contain one base, one clamp and one lid')
    cache = folder / 'render/mesh_cache'
    cache.mkdir(parents=True, exist_ok=True)
    offsets = working_scad.get_jt500_print_offsets(**details)
    for key, mesh in zip(['lid', 'base', 'top'], pieces):
        mesh.apply_translation(-np.array(offsets[key]))
        mesh.export(cache / (key + '.stl'))


if __name__ == '__main__':
    main()
