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

"""Shared FastMCP instance definition for the mobile automation MCP server."""

import logging
import os

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

try:
    from mcp.server.fastmcp.server import Settings as FastMCPSettings

    FastMCPSettings.model_rebuild()
except Exception as exc:
    # Version-compat shim: older/newer FastMCP releases may not expose
    # Settings or need the rebuild; the server works without it.
    logger.debug("FastMCP Settings.model_rebuild skipped: %s", exc, exc_info=True)


_AGENT_INSTRUCTIONS = (
    "ARTEMIS is an autonomous mobile AI agent and Android UI automation engine. "
    "Use mobile_run_task to launch autonomous UI workflows on connected Android devices or emulators, "
    "mobile_manage_task to check status or steer execution, "
    "mobile_get_device_state to inspect real-time device screen/hierarchy, "
    "mobile_inspect_trace to inspect detailed execution steps and visual action overlays, "
    "and mobile_diagnose whenever a tool errors, no device is found, or the user says "
    "ARTEMIS is not working: it checks the environment and returns ordered fix steps."
)

_HARNESS_INSTRUCTIONS = (
    "ARTEMIS harness mode exposes raw Android control primitives. YOU (the external "
    "coding agent) run the observe-reason-act loop yourself — ARTEMIS does not spawn "
    "its own LLM agent here, so no provider API key is required. "
    "Observe with mobile_get_device_state (view_type='hierarchy' for the labeled "
    "element list, 'screenshot' for an image). Locate targets with mobile_find_element. "
    "Act with mobile_tap / mobile_long_press / mobile_swipe / mobile_type / "
    "mobile_clear_text / mobile_press_back / mobile_press_home / mobile_press_key / "
    "mobile_launch_app / mobile_stop_app / mobile_open_url / mobile_shell. "
    "Capture evidence with mobile_take_screenshot. "
    "Call mobile_diagnose whenever a tool errors or no device is found."
)

_MODE = (os.environ.get("ARTEMIS_MCP_MODE") or "harness").strip().lower()

# Define the shared FastMCP instance for external IDE and agent clients.
mcp = FastMCP(
    "artemis",
    instructions=_HARNESS_INSTRUCTIONS if _MODE == "harness" else _AGENT_INSTRUCTIONS,
)

# Tool registration is intentionally NOT done here: mcp_server/__init__.py
# imports mcp_server.tools (which imports this module), so importing this
# module from anywhere already registers every tool. Importing tools here as
# well would create a circular import (base -> tools -> base).
