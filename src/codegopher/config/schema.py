"""Typed settings schema."""

from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class ApprovalMode(str, Enum):
    review = "review"
    auto = "auto"
    yolo = "yolo"


class ProviderApiFamily(str, Enum):
    chat_completions = "chat_completions"
    responses = "responses"


class McpTransport(str, Enum):
    stdio = "stdio"
    sse = "sse"


class ModelConfig(BaseModel):
    provider: str = "openai"
    name: str = Field(default="gpt-4o", min_length=1)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=8192, gt=0)


class ProviderEntry(BaseModel):
    id: str
    name: str
    base_url: str | None = None
    api_key_env: str | None = None
    api_family: ProviderApiFamily = ProviderApiFamily.chat_completions
    context_window: int | None = Field(default=None, gt=0)


class McpServerConfig(BaseModel):
    enabled: bool = True
    transport: McpTransport = McpTransport.stdio
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    cwd: str | None = None
    startup_timeout_seconds: float = Field(default=30.0, gt=0.0)
    url: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    headers_env: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = Field(default=5.0, gt=0.0)
    sse_read_timeout_seconds: float = Field(default=300.0, gt=0.0)

    @model_validator(mode="after")
    def validate_transport_fields(self) -> Self:
        if not self.enabled:
            return self
        if self.transport is McpTransport.stdio and not (self.command or "").strip():
            raise ValueError("stdio MCP servers require command")
        if self.transport is McpTransport.sse and not (self.url or "").strip():
            raise ValueError("sse MCP servers require url")
        return self


class McpConfig(BaseModel):
    enabled: bool = True
    servers: dict[str, McpServerConfig] = Field(default_factory=dict)


class ContextConfig(BaseModel):
    warning_threshold: float = Field(default=0.70, gt=0.0, lt=1.0)
    compaction_threshold: float = Field(default=0.80, gt=0.0, lt=1.0)
    token_encoding: str = Field(default="cl100k_base", min_length=1)

    @model_validator(mode="after")
    def validate_threshold_order(self) -> Self:
        if self.warning_threshold >= self.compaction_threshold:
            raise ValueError("warning_threshold must be less than compaction_threshold")
        return self


class MemoryConfig(BaseModel):
    enabled: bool = True
    session_enabled: bool = True
    project_enabled: bool = True
    max_entries_per_scope: int = Field(default=200, gt=0)
    max_entry_chars: int = Field(default=4000, gt=0)


class SkillConfig(BaseModel):
    enabled: bool = True
    project_dir: str = Field(default=".codegopher/skills", min_length=1)
    user_dir: str = Field(default="skills", min_length=1)
    builtins_enabled: bool = True
    autoload: bool = True


class TodoConfig(BaseModel):
    enabled: bool = True
    max_items: int = Field(default=100, gt=0)


class Settings(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    providers: dict[str, list[ProviderEntry]] = Field(default_factory=dict)
    approval_mode: ApprovalMode = ApprovalMode.review
    ignore_file: str = ".codegopherignore"
    debug: bool = False
    context: ContextConfig = Field(default_factory=ContextConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    skills: SkillConfig = Field(default_factory=SkillConfig)
    todo: TodoConfig = Field(default_factory=TodoConfig)
    mcp: McpConfig = Field(default_factory=McpConfig)
