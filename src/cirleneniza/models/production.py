from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, field_validator, model_validator


class ResearchOutput(BaseModel):
    topic: str
    points: list[str]
    key_data: list[str]


class StyleGuideOutput(BaseModel):
    palette: list[str]
    visual_tone: str
    visual_reference: str
    composition: str


class CenaPrompt(BaseModel):
    scene: str
    hook_technique: str
    locutor: str
    camera: str
    kling_motion_prompt: str
    nota_visual: str
    lighting: str
    atmosphere: str

    @field_validator("locutor")
    @classmethod
    def max_35_words(cls, v: str) -> str:
        count = len(v.split())
        if count > 35:
            raise ValueError(f"LOCUTOR deve ter no máximo 35 palavras, tem {count}")
        return v

    @field_validator("kling_motion_prompt")
    @classmethod
    def valid_kling_prompt(cls, v: str) -> str:
        if "9:16" not in v:
            raise ValueError("kling_motion_prompt deve conter 'Vertical 9:16'")
        if len(v) < 80:
            raise ValueError(f"kling_motion_prompt deve ter ≥80 chars, tem {len(v)}")
        return v


class ScriptOutput(BaseModel):
    intro: str
    main: str
    outro: str
    full_script: str
    cena_prompts: list[CenaPrompt]
    thumbnail_prompts: list[str]

    @field_validator("cena_prompts")
    @classmethod
    def min_six_scenes(cls, v: list[CenaPrompt]) -> list[CenaPrompt]:
        if len(v) < 6:
            raise ValueError(
                f"Mínimo 6 cenas obrigatório, roteiro gerou {len(v)} cenas"
            )
        return v


class ClaimResult(BaseModel):
    claim: str
    status: Literal["ok", "exagero", "errado", "vago"]
    suggestion: str | None = None


class ValidationOutput(BaseModel):
    claims: list[ClaimResult]
    overall_score: float
    status: Literal["approved", "needs_revision"] = "approved"

    @model_validator(mode="after")
    def derive_status(self) -> "ValidationOutput":
        if any(c.status == "errado" for c in self.claims):
            self.status = "needs_revision"
        return self


class AudioOutput(BaseModel):
    intro_path: str
    main_path: str
    outro_path: str
    normalized_paths: dict[str, str] = {}


class EnrichedScene(BaseModel):
    scene: str
    kling_motion_prompt: str
    scene_type: Literal["hook", "informative", "food_broll", "cta"]
    prompt: str  # legacy compat — igual a kling_motion_prompt
