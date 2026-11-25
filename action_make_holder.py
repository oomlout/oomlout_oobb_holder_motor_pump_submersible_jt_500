"""Build the M3x16 holder, run tests and refresh Blender presentation."""


def main(**kwargs):
    render = kwargs.get("render", True)
    samples = kwargs.get("samples", 40)
    resolution = kwargs.get("resolution", 1100)

    import working_verify
    import working_render
    import working_documentation
    working_verify.main()
    working_render.main(render=render, samples=samples, resolution=resolution)
    working_documentation.main(render=render, samples=samples, resolution=resolution)


if __name__ == "__main__":
    main()
