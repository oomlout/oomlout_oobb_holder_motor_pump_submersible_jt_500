"""Exercise the offline instruction viewer and render README previews in Edge."""
import json
from pathlib import Path


def main(**kwargs):
    root = Path(kwargs.get("root", Path(__file__).resolve().parents[2]))
    from playwright.sync_api import sync_playwright
    import markdown

    folder = root / "parts/oobb_holder_motor_pump_submersible_jt_500/assembly"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1200, "height": 850}, offline=True, has_touch=True)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((folder / "assembly_instructions.html").as_uri())
        sheet = page.locator("#page")
        selector = page.locator("#jump")
        sheet.evaluate("img => img.decode()")
        assert selector.input_value() == "page-03"
        assert "Steps 1-4" in sheet.get_attribute("alt")
        assert page.locator(".print-page").count() == 8
        page.screenshot(path=str(folder / "viewer_desktop.png"))
        page.keyboard.press("ArrowRight")
        assert "Steps 5-6" in sheet.get_attribute("alt")
        sheet.evaluate("img => img.decode()")
        page.screenshot(path=str(folder / "viewer_cover.png"))
        selector.select_option("page-07")
        assert page.locator('#links a[href^="https://oom.lt/a/"]').count() == 4
        page.locator("#fullscreen").click()
        assert page.evaluate("!!document.fullscreenElement")
        page.locator("#fullscreen").click()
        page.keyboard.press("End")
        assert page.locator("#next").is_disabled()
        page.keyboard.press("Home")
        assert page.locator("#previous").is_disabled()
        page.emulate_media(media="print")
        assert not page.locator("nav").is_visible()
        assert page.locator(".print-page").first.is_visible()
        page.emulate_media(media="screen")
        page.set_viewport_size({"width": 390, "height": 844})
        selector.select_option("page-03")
        sheet.evaluate("img => img.decode()")
        bounds = sheet.bounding_box()
        assert abs(bounds["width"] / bounds["height"] - 297 / 210) < .01
        page.screenshot(path=str(folder / "viewer_mobile.png"))
        page.locator("#zoom").click()
        assert page.locator("#viewer").evaluate("v => v.scrollWidth > v.clientWidth")
        page.locator("#zoom").click()
        page.mouse.move(270, 325)
        page.mouse.down()
        page.mouse.move(90, 325)
        page.mouse.up()
        assert selector.input_value() == "page-04"
        for label, source in [("project", root / "README.md"), ("assembly", folder.parent / "README.md")]:
            body = markdown.markdown(source.read_text(encoding="utf-8"), extensions=["tables"])
            html = '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><base href="' + source.parent.as_uri() + '/"><style>body{max-width:980px;margin:30px auto;padding:0 20px;font:16px/1.5 Arial}img{max-width:100%;height:auto}table{border-collapse:collapse;display:block;overflow:auto}th,td{border:1px solid #ddd;padding:8px}a{color:#0969da}</style></head><body>' + body + '</body></html>'
            preview = folder / (label + "_readme_preview.html")
            preview.write_text(html, encoding="utf-8")
            page.set_viewport_size({"width": 1200, "height": 900})
            page.goto(preview.as_uri())
            page.wait_for_function("[...document.images].every(img=>img.complete && img.naturalWidth>0)")
            page.screenshot(path=str(folder / (label + "_readme_desktop.png")), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(folder / (label + "_readme_mobile.png")), full_page=True)
        browser.close()
    assert not errors, errors
    report = {"status": "passed", "browser": "Edge Chromium headless", "offline": True,
              "checks": ["start at steps 1-4", "page navigation", "A4 landscape print", "zoom and pan", "hardware links", "fullscreen",
                         "endpoints", "pointer swipe", "390px mobile layout", "README images at desktop/mobile"],
              "page_errors": errors}
    (folder / "browser_validation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == "__main__":
    main()
