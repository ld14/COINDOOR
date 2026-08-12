from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.lib.domain.completeness import compute_game_status

FieldStatus = Literal["empty", "manual", "suggested"]
GameStatus = Literal["ready", "incomplete", "error"]
IdentitySource = Literal["catalog", "manual"]
MagazineLink = Literal["empty", "linked"]
ManualStatus = Literal["unprocessed", "processing", "processed", "failed"]
RomSource = Literal["upload", "path"]


class FormatError(BaseModel):
    field: str
    message: str


class Identity(BaseModel):
    title: str = ""
    year: str = ""
    developer: str = ""
    publisher: str = ""
    genre: str = ""
    players: str = ""
    format: str = ""


class MediaField(BaseModel):
    status: FieldStatus = "empty"
    url: str | None = None
    source: str | None = None


class TextField(BaseModel):
    status: FieldStatus = "empty"
    value: str = ""
    source: str | None = None


class ReviewField(BaseModel):
    status: FieldStatus = "empty"
    source: str | None = None
    score: int | None = None
    cats: dict[str, int] = Field(default_factory=dict)


class CheatEntry(BaseModel):
    name: str
    input: str


class CheatGroup(BaseModel):
    name: str
    entries: list[CheatEntry] = Field(default_factory=list)


class CheatsField(BaseModel):
    status: FieldStatus = "empty"
    source: str | None = None
    groups: list[CheatGroup] = Field(default_factory=list)


class GameManual(BaseModel):
    id: str
    fileName: str
    status: ManualStatus
    pages: int = 0
    progress: int | None = None


class StoredGame(BaseModel):
    version: int = 1
    id: str
    systemId: str
    identity: Identity
    identitySource: IdentitySource = "manual"
    romSource: RomSource
    romRef: str
    errors: list[FormatError] = Field(default_factory=list)
    images: dict[str, MediaField] = Field(default_factory=dict)
    video: dict[str, MediaField] = Field(default_factory=dict)
    texts: dict[str, TextField] = Field(default_factory=dict)
    review: ReviewField = Field(default_factory=ReviewField)
    cheats: CheatsField = Field(default_factory=CheatsField)
    accent: FieldStatus = "empty"
    accentValue: str = ""
    accent2Value: str = ""
    manuals: list[GameManual] = Field(default_factory=list)
    magazine: MagazineLink = "empty"
    magazineName: str = ""
    coverThumbUrl: str | None = None


class GameOut(StoredGame):
    status: GameStatus

    @classmethod
    def from_stored(cls, game: StoredGame) -> GameOut:
        data = game.model_dump()
        data["status"] = compute_game_status(data)
        return cls.model_validate(data)


class GameSummary(BaseModel):
    id: str
    title: str
    year: str
    systemName: str
    identitySource: IdentitySource
    status: GameStatus
    coverThumbUrl: str | None = None


class GamesPage(BaseModel):
    items: list[GameSummary]
    page: int
    perPage: int
    total: int


class CreateGame(BaseModel):
    systemId: str
    romSource: RomSource
    romRef: str
    identity: Identity


class PatchGame(BaseModel):
    identity: Identity | None = None
    accent: FieldStatus | None = None
    accentValue: str | None = None
    accent2Value: str | None = None


class System(BaseModel):
    id: str
    name: str
    shortName: str
    launchCmd: str
    valid: bool = True
    errorMsg: str | None = None
    gameCount: int = 0


class NewSystem(BaseModel):
    name: str
    shortName: str
    launchCmd: str


class JobOut(BaseModel):
    jobId: str
    status: str
    progress: int
    result: object | None = None
    error: str | None = None


class MissingRequiredResponse(BaseModel):
    missing: list[str]
