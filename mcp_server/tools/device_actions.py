# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Harness-mode MCP action primitives.

Exposes low-level device-control tools so that an external coding agent
(e.g. Claude Code) can run the observe-reason-act loop itself, instead of
delegating to ARTEMIS's internal LLM-driven agent. These tools are only
registered when the server is launched in harness mode (ARTEMIS_MCP_MODE
=harness), so the default agent-mode surface stays unchanged.
"""

import json

from mcp_server.base import mcp
from artemis.mcp.adb_server import _get_controller
from artemis.mcp.actuators.adb import ensure_focus_at_coords as _ensure_focus_at_coords
from third_party.mobile_use.utils.app_launch_utils import launch_app_with_retries


# ---------- Tap / long-press ----------


@mcp.tool()
async def mobile_tap(
    x: int,
    y: int,
    times: int = 1,
    delay_ms: int = 100,
    device_serial: str | None = None,
) -> str:
    """Tap on the screen at pixel coordinates (x, y).

    Args:
        x: X coordinate in pixels.
        y: Y coordinate in pixels.
        times: Number of consecutive taps (default 1).
        delay_ms: Delay in ms between consecutive taps (default 100).
        device_serial: Optional device serial (omit to use default).
    """
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    result = await controller.tap_at(x=x, y=y, times=times, delay_ms=delay_ms)
    if getattr(result, "error", None):
        return f"Error: {result.error}"
    return "Success"


@mcp.tool()
async def mobile_long_press(
    x: int,
    y: int,
    duration_ms: int = 1000,
    device_serial: str | None = None,
) -> str:
    """Long-press on the screen at pixel coordinates (x, y) for duration_ms."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    result = await controller.tap_at(
        x=x, y=y, long_press=True, long_press_duration=duration_ms
    )
    if getattr(result, "error", None):
        return f"Error: {result.error}"
    return "Success"


# ---------- Swipe ----------


@mcp.tool()
async def mobile_swipe(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: int = 400,
    device_serial: str | None = None,
) -> str:
    """Swipe from (start_x, start_y) to (end_x, end_y) over duration_ms.

    Set duration_ms >= 1000 to drag-and-drop.
    """
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    error = await controller.swipe_coords(
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
        duration=duration_ms,
    )
    if error:
        return f"Error: {error}"
    return "Success"


# ---------- Keys ----------


@mcp.tool()
async def mobile_press_back(device_serial: str | None = None) -> str:
    """Press the system Back button."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    success = await controller.go_back()
    return "Success" if success else "Failed"


@mcp.tool()
async def mobile_press_home(device_serial: str | None = None) -> str:
    """Press the Home key (KEYCODE_HOME)."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    try:
        success = await controller.press_key("KEYCODE_HOME")
        return "Success" if success else "Failed"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def mobile_press_key(
    keycode: str,
    device_serial: str | None = None,
) -> str:
    """Press an arbitrary Android key event (e.g. KEYCODE_ENTER, KEYCODE_TAB)."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    try:
        success = await controller.press_key(keycode)
        return "Success" if success else "Failed"
    except Exception as e:
        return f"Error: {e}"


# ---------- Text input ----------


@mcp.tool()
async def mobile_type(
    text: str,
    x: int | None = None,
    y: int | None = None,
    clear_before_input: bool = False,
    device_serial: str | None = None,
) -> str:
    """Type text into the focused field.

    If (x, y) is provided, tap first to focus the target field. Supports
    multi-line content with '\\n'. clear_before_input=True erases existing
    text before typing; otherwise text is appended at the cursor.
    """
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    if x is not None and y is not None:
        err = await _ensure_focus_at_coords(controller, x, y)
        if err:
            return f"Error focusing element: {err}"

    if clear_before_input:
        success = await controller.erase_text()
        if not success:
            return "Failed to clear existing text"

    success = await controller.type_text(text, clear_existing=False)
    return "Success" if success else "Failed"


@mcp.tool()
async def mobile_clear_text(
    x: int | None = None,
    y: int | None = None,
    device_serial: str | None = None,
) -> str:
    """Clear the text of the focused field, or of the field at (x, y) if given."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    if x is not None and y is not None:
        err = await _ensure_focus_at_coords(controller, x, y)
        if err:
            return f"Error focusing element: {err}"

    success = await controller.erase_text()
    return "Success" if success else "Failed"


# ---------- App lifecycle ----------


@mcp.tool()
async def mobile_launch_app(
    package_name: str,
    device_serial: str | None = None,
) -> str:
    """Launch an Android app by package name, retrying on cold-start flakes."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    success, error_msg = await launch_app_with_retries(controller.ctx, package_name)
    return "Success" if success else f"Failed: {error_msg}"


@mcp.tool()
async def mobile_stop_app(
    package_name: str,
    device_serial: str | None = None,
) -> str:
    """Force-stop an Android app by package name."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    success = await controller.terminate_app(package_name)
    return "Success" if success else "Failed"


@mcp.tool()
async def mobile_open_url(
    url: str,
    device_serial: str | None = None,
) -> str:
    """Open a URL or deep link on the device."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    success = await controller.open_url(url)
    return "Success" if success else "Failed"


# ---------- Shell / raw ADB ----------


@mcp.tool()
async def mobile_shell(
    command: str,
    device_serial: str | None = None,
) -> str:
    """Run a raw `adb shell` command on the target device, returning its stdout.

    The command runs as a single shell string. Prefer dedicated tools
    (mobile_tap, mobile_launch_app, ...) when they exist.
    """
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    try:
        device = controller.ctx.adb_client.device(controller.ctx.device.device_id)
        output = device.shell(command)
        return output if isinstance(output, str) else str(output)
    except Exception as e:
        return f"Error: {e}"


# ---------- Pure observers (complement mobile_get_device_state) ----------


@mcp.tool()
async def mobile_take_screenshot(device_serial: str | None = None) -> str:
    """Return a base64-encoded JPEG screenshot of the device screen."""
    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return f"Error: Controller init failed: {e}"

    try:
        return await controller.take_screenshot()
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def mobile_find_element(
    text: str | None = None,
    resource_id: str | None = None,
    content_desc: str | None = None,
    device_serial: str | None = None,
) -> str:
    """Locate the first matching UI element on-screen.

    At least one of text / resource_id / content_desc must be supplied. The
    match is case-insensitive substring for text/content_desc, exact for
    resource_id. Returns a JSON object:

        {"found": true,  "bounds": [l,t,r,b], "center": [x,y], "text": "...",
         "resource_id": "...", "content_desc": "...", "class": "..."}
        {"found": false}
    """
    if not any([text, resource_id, content_desc]):
        return json.dumps(
            {"error": "Provide at least one of text / resource_id / content_desc"}
        )

    try:
        controller = _get_controller(device_serial=device_serial)
    except Exception as e:
        return json.dumps({"error": f"Controller init failed: {e}"})

    try:
        elements = await controller.get_ui_elements()
    except Exception as e:
        return json.dumps({"error": f"Failed to get UI elements: {e}"})

    def _norm(s):
        return (s or "").strip().lower()

    want_text = _norm(text)
    want_desc = _norm(content_desc)

    def _iter_elements(root):
        if root is None:
            return
        if isinstance(root, list):
            for item in root:
                yield from _iter_elements(item)
            return
        if isinstance(root, dict):
            yield root
            for child in root.get("children") or []:
                yield from _iter_elements(child)

    for el in _iter_elements(elements):
        el_text = _norm(el.get("text"))
        el_rid = el.get("resource_id") or el.get("resourceId") or ""
        el_desc = _norm(el.get("content_desc") or el.get("contentDescription"))
        if want_text and want_text not in el_text and want_text not in el_desc:
            continue
        if resource_id and resource_id != el_rid:
            continue
        if want_desc and want_desc not in el_desc:
            continue

        bounds = el.get("bounds") or el.get("bbox") or el.get("rect")
        if isinstance(bounds, dict):
            # {"left":..,"top":..,"right":..,"bottom":..}
            l = bounds.get("left", bounds.get("x", 0))
            t = bounds.get("top", bounds.get("y", 0))
            r = bounds.get("right", l + bounds.get("width", 0))
            b = bounds.get("bottom", t + bounds.get("height", 0))
            bounds = [l, t, r, b]
        if isinstance(bounds, (list, tuple)) and len(bounds) == 4:
            cx = (bounds[0] + bounds[2]) // 2
            cy = (bounds[1] + bounds[3]) // 2
            return json.dumps(
                {
                    "found": True,
                    "bounds": list(bounds),
                    "center": [cx, cy],
                    "text": el.get("text") or "",
                    "resource_id": el_rid,
                    "content_desc": el.get("content_desc")
                    or el.get("contentDescription")
                    or "",
                    "class": el.get("class") or el.get("className") or "",
                }
            )

    return json.dumps({"found": False})
