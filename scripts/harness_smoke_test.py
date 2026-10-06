"""Smoke test for the harness-mode primitives on a real device.

Runs 3 steps against the Tecno device + com.audiobook, directly through the
patched Python API (no MCP in the loop). Proves the harness code works
end-to-end before we validate it through the subagent + MCP path.

Usage:
    PYTHONPATH=/Users/kohuyn/StudioProjects/Artemis \\
    /Users/kohuyn/StudioProjects/Artemis/.venv/bin/python \\
    scripts/harness_smoke_test.py
"""

import asyncio
import json
import os
import sys

DEVICE = "1156625465005157"
PACKAGE = "com.audiobook"


async def main() -> int:
    os.environ.setdefault("ARTEMIS_DEVICE_ID", DEVICE)
    from artemis.mcp.adb_server import _get_controller
    from third_party.mobile_use.utils.app_launch_utils import launch_app_with_retries

    print(f"[1/3] init controller for {DEVICE}")
    controller = _get_controller(device_serial=DEVICE)
    w, h = controller.ctx.device.device_width, controller.ctx.device.device_height
    print(f"      screen = {w}x{h}")

    print(f"[2/3] launch {PACKAGE}")
    ok, err = await launch_app_with_retries(controller.ctx, PACKAGE)
    if not ok:
        print(f"      FAIL: {err}")
        return 2
    print("      launched")
    await asyncio.sleep(2.0)

    print("[3/3] observe hierarchy + tap center")
    screen = await controller.get_screen_data()
    elems = screen.elements
    elem_count = (
        len(elems) if isinstance(elems, list)
        else len(elems.get("children", [])) if isinstance(elems, dict)
        else "?"
    )
    print(f"      hierarchy element count = {elem_count}")

    cx, cy = w // 2, h // 2
    result = await controller.tap_at(x=cx, y=cy, times=1)
    tap_err = getattr(result, "error", None)
    if tap_err:
        print(f"      tap FAIL: {tap_err}")
        return 3
    print(f"      tapped ({cx}, {cy}) OK")

    print(json.dumps({
        "device": DEVICE,
        "package": PACKAGE,
        "screen": [w, h],
        "launch": "ok",
        "hierarchy_elements": elem_count,
        "tap_center": [cx, cy],
        "verdict": "harness primitives end-to-end OK",
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
