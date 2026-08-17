import fielddefs from './fielddefs.json';

export const FIELDDEFS = fielddefs;

export type FieldStatus = 'empty' | 'manual' | 'suggested';
export type GameStatus = 'ready' | 'incomplete' | 'error';
export type IdentitySource = 'mame' | 'screenscraper' | 'manual';
export type MagazineLink = 'empty' | 'linked';
export type ManualStatus = 'unprocessed' | 'processing' | 'processed' | 'failed';
export type RomSource = 'upload' | 'path';

export type IdentityKey = (typeof fielddefs.identity)[number]['key'];
export type ImageKey = (typeof fielddefs.images)[number]['key'];
export type VideoKey = (typeof fielddefs.videos)[number]['key'];
export type TextKey = (typeof fielddefs.texts)[number]['key'];
export type ReviewCat = 'originalidad' | 'graficos' | 'adiccion' | 'sonido' | 'dificultad' | 'animacion';

export interface System {
  id: string;
  name: string;
  shortName: string;
  launchCmd: string;
  valid: boolean;
  errorMsg?: string;
  gameCount: number;
}

export interface FormatError {
  field: string;
  message: string;
}

export type Identity = Record<IdentityKey, string>;

export interface MediaField {
  status: FieldStatus;
  url?: string;
  source?: string;
}

export interface TextField {
  status: FieldStatus;
  value: string;
  source?: string;
}

export interface ReviewField {
  status: FieldStatus;
  source?: string;
  score: number | null;
  cats: Partial<Record<ReviewCat, number>>;
}

export interface CheatEntry {
  name: string;
  input: string;
}

export interface CheatGroup {
  name: string;
  entries: CheatEntry[];
}

export interface CheatsField {
  status: FieldStatus;
  source?: string;
  groups: CheatGroup[];
}

export interface GameManual {
  id: string;
  fileName: string;
  status: ManualStatus;
  pages: number;
  progress?: number;
}

export interface MagazineAppearance {
  id: string;
  magazineName: string;
  country: string;
  language: string;
  issueNumber: string;
  volume?: string;
  date: string;
  platform: string;
  contentType: string;
  source: string;
  appearanceType: string;
}

export interface FieldProvenance {
  source: string;
  originUrl?: string;
  sourceId?: string;
  sourceType: string;
  processedUrls: string[];
}

export interface Game {
  id: string;
  systemId: string;
  identity: Identity;
  identitySource: IdentitySource;
  romSource: RomSource;
  romRef: string;
  errors: FormatError[];
  images: Record<ImageKey, MediaField>;
  video: Record<VideoKey, MediaField>;
  texts: Record<TextKey, TextField>;
  review: ReviewField;
  cheats: CheatsField;
  accent: FieldStatus;
  accentValue: string;
  accent2Value: string;
  manuals: GameManual[];
  magazine: MagazineLink;
  magazineName: string;
  magazineAppearances: MagazineAppearance[];
  coverThumbUrl?: string;
  provenance: Record<string, FieldProvenance>;
}
