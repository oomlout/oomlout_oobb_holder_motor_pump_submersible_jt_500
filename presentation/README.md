# Rebuild the JT-500 holder

Run `python action_make_holder.py` from the project root in the OOBB/OOMP Python environment with OpenSCAD and Blender on PATH. The build exports the combined print, runs the geometry tests, renders the assembly from the exported meshes, then produces the illustrated book and offline viewer.

- [Print and assemble the holder](../parts/oobb_holder_motor_pump_submersible_jt_500/README.md#assembly)
- [Edit dimensions, hardware and assembly steps](../working_oomp_populate.py)
- [Inspect the editable Blender scenes](scenes/jt500_holder.blend)
- [Review the mesh measurements](../verification.json) and [test results](qa/test_run.txt)

The clearance checks cover both pump orientations. They sweep all three rear inlet openings across ±3 mm of play and measure support from each tongue at nine positions per orientation. Physical fit, flow and printed strength still need a bench test.

Run `python working_documentation.py --no-render` to compose the instructions again from matching renders. Run `python components/instructions/validate_browser.py` to check the offline viewer and README layouts at desktop and phone widths.
