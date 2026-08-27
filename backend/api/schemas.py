from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.lib.domain.completeness import compute_game_status

FieldStatus = Literal["empty", "manual", "suggested"]
GameStatus = Literal["ready", "incomplete", "error"]
IdentitySource = Literal["mame", "screenscraper", "manual"]
MagazineLink = Literal["empty", "linked"]
ManualStatus = Literal["unprocessed", "processing", "processed", "failed"]
RomSource = Literal["upload", "path"]
Tratamiento = Literal["copiar", "descomprimir"]


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


class MagazineValue(BaseModel):
    magazine: str = "empty"
    magazineName: str = ""


class GameManual(BaseModel):
    id: str
    fileName: str
    status: ManualStatus
    pages: int = 0
    progress: int | None = None


class MagazineAppearance(BaseModel):
    id: str
    magazineName: str
    country: str = ""
    language: str = ""
    issueNumber: str = ""
    volume: str | None = None
    date: str = ""
    platform: str = ""
    contentType: str = ""
    source: str = ""
    appearanceType: str = "no_determinado"


class GalleryImage(BaseModel):
    """Una imagen del banco, fuera de los assets del contrato (ADR-0016).

    ``file`` es un NOMBRE suelto dentro de ``_gallery/``, nunca una ruta: es la
    misma regla que ``_chk_manual_doc`` hace cumplir del lado de ATTRACT, y lo que
    permite que el theme concatene el prefijo tal cual sin riesgo de traversal.
    """

    id: str
    tipo: str
    label: str
    file: str
    url: str
    source: str = "ArcadeDB"


class FieldProvenance(BaseModel):
    source: str
    originUrl: str | None = None
    sourceId: str | None = None
    sourceType: str = "api"
    processedUrls: list[str] = Field(default_factory=list)


class CabinetButton(BaseModel):
    control: str
    color: str
    action: str


class CabinetInfo(BaseModel):
    resolution: str = ""
    orientation: str = ""
    controls: str = ""
    buttons: int = 0
    button_list: list[CabinetButton] = Field(default_factory=list)


class StoredGame(BaseModel):
    version: int = 1
    id: str
    systemId: str
    identity: Identity
    identitySource: IdentitySource = "manual"
    romSource: RomSource
    romRef: str
    file_format: str = ""
    tratamiento: str = ""
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
    # Banco de imagenes, aparte de ``images``: es una lista sin asset del contrato,
    # asi que no entra en fielddefs.images[] ni cuenta para la completitud (ADR-0016).
    gallery: list[GalleryImage] = Field(default_factory=list)
    magazine: MagazineLink = "empty"
    magazineName: str = ""
    magazineAppearances: list[MagazineAppearance] = Field(default_factory=list)
    coverThumbUrl: str | None = None
    provenance: dict[str, FieldProvenance] = Field(default_factory=dict)
    cabinet: CabinetInfo = Field(default_factory=CabinetInfo)


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
    file_format: str = ""
    tratamiento: str = ""
    identity: Identity


class PatchGame(BaseModel):
    systemId: str | None = None
    identity: Identity | None = None
    romRef: str | None = None
    file_format: str | None = None
    tratamiento: str | None = None
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


class SuggestionJob(BaseModel):
    jobId: str


class ExportRequest(BaseModel):
    gameId: str
    incluir: list[str] = Field(default_factory=list)


class ExportJob(BaseModel):
    runId: str


class ApplySuggestion(BaseModel):
    candidateId: str


class ReviewValue(BaseModel):
    score: int | None = None
    cats: dict[str, int] = Field(default_factory=dict)


class CheatsValue(BaseModel):
    groups: list[CheatGroup] = Field(default_factory=list)


class MissingRequiredResponse(BaseModel):
    missing: list[str]
