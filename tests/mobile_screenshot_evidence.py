#!/usr/bin/env python3
"""Capture mapped 390px mobile stage evidence for the 13 repaired demos.
Run after build with the local static preview at http://127.0.0.1:8873/.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "design/evidence"
SHOTS = EVIDENCE / "g3-screenshots"
REPORT = EVIDENCE / "g3-regression.json"
MANIFEST = EVIDENCE / "g3-mobile-screenshots.json"
URL = os.environ.get("LAB_TEST_URL", "http://127.0.0.1:8873/")
TARGETS = (6, 15, 20, 21, 22, 23, 26, 28, 34, 42, 51, 53, 54)


def click(demo, selector: str) -> None:
    target = demo.locator(selector)
    if target.count() and target.is_visible():
        target.evaluate("(e) => e.click()")


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    entries: dict[str, dict] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
        )
        page = browser.new_page(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            color_scheme="dark",
        )
        page.goto(URL, wait_until="domcontentloaded", timeout=20000)
        page.emulate_media(reduced_motion="no-preference")
        page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")

        for number in TARGETS:
            demo_id = f"demo-{number:02d}"
            demo = page.locator(f"#{demo_id}")
            if demo.count() != 1:
                raise AssertionError(f"expected one #{demo_id}, found {demo.count()}")
            demo.scroll_into_view_if_needed()
            page.wait_for_timeout(500)

            # Scope the stage to this section: a global #stage-N selector once
            # produced a mislabeled #54 mobile screenshot, so ownership is asserted.
            stage = demo.locator(".stage")
            if stage.count() != 1:
                raise AssertionError(f"#{demo_id} must contain exactly one .stage")
            stage_owner = stage.evaluate('(e) => e.closest(".demo")?.id || ""')
            stage_id = stage.get_attribute("id") or ""
            if stage_owner != demo_id or stage_id != f"stage-{number:02d}":
                raise AssertionError(
                    f"stage ownership mismatch: demo={demo_id}, owner={stage_owner}, id={stage_id}"
                )
            stage.scroll_into_view_if_needed()
            page.wait_for_function(
                "id => { const e=document.getElementById(id); if(!e) return false; "
                "const r=e.getBoundingClientRect(); return r.height>0 && r.top>=0 && r.bottom<=innerHeight; }",
                arg=stage_id,
                timeout=6000,
            )
            page.wait_for_timeout(150)

            if number in (22, 23, 26):
                try:
                    page.wait_for_function(
                        "id => { const e=document.getElementById(id); "
                        "return !e || ['ready','error'].includes(e.dataset.libState || ''); }",
                        arg=demo_id,
                        timeout=15000,
                    )
                except Exception:
                    pass  # A visible library fallback is valid evidence too.
            if number == 6:
                demo.locator("#reveal-scroll").evaluate(
                    '(e) => { e.scrollTop = 0; e.dispatchEvent(new Event("scroll")); }'
                )
            elif number == 15:
                canvas = demo.locator("#px-canvas")
                if canvas.count():
                    box = canvas.bounding_box()
                    if box:
                        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        page.wait_for_timeout(220)
            elif number == 20:
                click(demo, "#motion-run")
                page.wait_for_timeout(900)
            elif number == 21:
                controls = demo.locator(".lab-equivalent-controls button")
                if controls.count() >= 3:
                    controls.nth(0).evaluate("(e) => e.click()")
                    controls.nth(2).evaluate("(e) => e.click()")
            elif number == 22:
                if demo.locator("#p5-style").count():
                    demo.locator("#p5-style").select_option("ring")
                    demo.locator("#p5-lag").fill("20")
                    demo.locator("#p5-count").fill("240")
                    demo.locator("#p5-trail").fill("75")
                    demo.locator("#p5-liquid").fill("80")
                    click(demo, "#p5-generate")
                    page.wait_for_timeout(500)
            elif number == 23:
                if demo.locator("#ec-style").count():
                    demo.locator("#ec-style").select_option("area")
                    click(demo, "#ec-reset")
                    page.wait_for_timeout(300)
            elif number == 26:
                click(demo, "#embla-next")
                page.wait_for_timeout(180)
                click(demo, "#embla-prev")
            elif number == 34:
                click(demo, '[data-tw-action="primary"]')
                click(demo, '[data-tw-action="secondary"]')
                if demo.locator("#tw-class-input").count():
                    demo.locator("#tw-class-input").fill("bg-sky-100 p-6 rounded-lg text-slate-900")
                    page.wait_for_timeout(500)
            elif number == 42:
                click(demo, "#vt-toggle")
                page.wait_for_timeout(500)
                if "vt-list" in (demo.locator("#vt-view").get_attribute("class") or ""):
                    click(demo, "#vt-toggle")
                page.wait_for_timeout(500)
            elif number == 51:
                demo.locator("#cmp-range").fill("50")
            elif number == 53:
                demo.locator("#snap-view").evaluate(
                    '(e) => { e.scrollLeft = 0; e.dispatchEvent(new Event("scroll")); }'
                )
            elif number == 54:
                slider = demo.locator("#prop-slider")
                swatches = demo.locator("#prop-swatches > i")
                if slider.count() != 1 or swatches.count() != 6:
                    raise AssertionError("#54 must contain its hue slider and six swatches")
                slider.fill("58")
                page.wait_for_timeout(250)
                colors = swatches.evaluate_all("xs => xs.map(x => getComputedStyle(x).backgroundColor)")
                if len(set(colors)) != 6:
                    raise AssertionError(f"#54 mobile swatches are not six distinct colors: {colors}")

            page.wait_for_timeout(180)
            stage.scroll_into_view_if_needed()
            page.wait_for_function(
                "id => { const e=document.getElementById(id); if(!e) return false; "
                "const r=e.getBoundingClientRect(); return r.height>0 && r.top>=0 && r.bottom<=innerHeight; }",
                arg=stage_id,
                timeout=6000,
            )
            path = SHOTS / f"g3-mobile-demo-{number:02d}.png"
            stage.screenshot(path=str(path), timeout=12000)
            box = stage.bounding_box()
            if not box or box["width"] < 1 or box["height"] < 1:
                raise AssertionError(f"#{demo_id} mobile stage has no visible bounds")
            with Image.open(path) as image:
                image_size_px = {"width": image.width, "height": image.height}
            entries[str(number)] = {
                "demo_id": demo_id,
                "stage_id": stage_id,
                "capture_selector": f"#{demo_id} .stage",
                "heading": demo.locator(".demo-head h3").inner_text(),
                "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "css_bounds": {"width": round(box["width"], 2), "height": round(box["height"], 2)},
                "image_size_px": image_size_px,
            }
            print(f"captured #{number:02d}: {path.name} -> {stage_id}", flush=True)
        browser.close()

    manifest = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "url": URL,
        "capture_mode": "DOM visual-state capture; real interactions are verified by G3 regression and robustness suites.",
        "viewport": {"width": 390, "height": 844, "device_scale_factor": 2, "touch": True},
        "screenshots": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    if REPORT.exists():
        report = json.loads(REPORT.read_text())
        report["mobile_demo_screenshots"] = {key: item["path"] for key, item in entries.items()}
        report["mobile_screenshots_manifest"] = str(MANIFEST)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"manifest: {MANIFEST}")
    print(f"updated report mapping: {REPORT}")


if __name__ == "__main__":
    main()
