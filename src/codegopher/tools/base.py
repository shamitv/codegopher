"""Base tool contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel

from codegopher.tools.context import AccessTracker


class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class ToolContext:
    cwd: Path
    access: AccessTracker = field(init=False)

    def __post_init__(self) -> None:
        self.access = AccessTracker(root=self.cwd)


class Tool(Protocol):
    name: str
    description: str
    parameters: dict[str, Any]
    requires_approval: bool

    async def execute(self, arguments: dict[str, Any], context: ToolContext) -> ToolResult:
        ...

