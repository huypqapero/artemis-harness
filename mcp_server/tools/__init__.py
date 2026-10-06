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

"""MCP Tools package for ARTEMIS.

Two surface modes are selected via the ``ARTEMIS_MCP_MODE`` env var, read
once at import time:

- ``harness`` (default): observation + raw device-control primitives only.
  The external coding agent (e.g. Claude Code) drives the observe-reason-act
  loop itself; no LLM API key is required by this server. ``mobile_run_task``
  / ``mobile_manage_task`` are intentionally not registered in this mode.
- ``agent``: the legacy upstream surface. Registers ``mobile_run_task`` /
  ``mobile_manage_task`` which spawn the internal Flash / Pro LLM agent —
  this is the surface that needs an LLM API key, and the one this fork
  explicitly moves away from by default.
"""

import os

# Always-on: direct observation + inspection + env doctor.
from mcp_server.tools.device_state import mobile_get_device_state
from mcp_server.tools.diagnose import mobile_diagnose
from mcp_server.tools.inspect_trace import mobile_inspect_trace

_MODE = (os.environ.get("ARTEMIS_MCP_MODE") or "harness").strip().lower()

if _MODE == "harness":
    # Harness mode: expose primitive device actions so an external agent
    # can run its own observe-reason-act loop. The LLM-driven run/manage
    # task surface stays hidden here.
    from mcp_server.tools import device_actions  # noqa: F401 — registration side effect

    __all__ = [
        "mobile_get_device_state",
        "mobile_inspect_trace",
        "mobile_diagnose",
    ]
else:
    # Default agent mode: original Flash / Pro autonomous surface.
    from mcp_server.tools.task_manager import mobile_manage_task
    from mcp_server.tools.task_runner import mobile_run_task

    __all__ = [
        "mobile_run_task",
        "mobile_manage_task",
        "mobile_get_device_state",
        "mobile_inspect_trace",
        "mobile_diagnose",
    ]
