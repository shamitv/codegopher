"""Typed settings schema."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ApprovalMode(str, Enum):
    review = "review"
    auto = "auto"
    yolo = "yolo"


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
    context_window: int | None = Field(default=None, gt=0)


class Settings(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    providers: dict[str, list[ProviderEntry]] = Field(default_factory=dict)
    approval_mode: ApprovalMode = ApprovalMode.review
    ignore_file: str = ".codegopherignore"
    debug: bool = False
