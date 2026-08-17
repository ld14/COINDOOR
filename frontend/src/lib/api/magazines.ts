import type { Game, MagazineAppearance } from '@/lib/domain/types';
import { fetchJson } from './client';

export interface MagazineSearchResult {
  title: string;
  url: string;
  source: string;
  magazine: string;
  appearance?: MagazineAppearance;
  links?: {
    archiveOrg?: string;
    retroCdn?: string;
  };
}

export function setMagazine(gameId: string, magazineName: string): Promise<Game> {
  return fetchJson<Game>(`/games/${gameId}/fields/magazine`, {
    method: 'PUT',
    body: JSON.stringify({ magazine: magazineName ? 'linked' : 'empty', magazineName }),
  });
}

export function searchMagazines(gameId: string): Promise<MagazineSearchResult[]> {
  return fetchJson<MagazineSearchResult[]>(`/games/${gameId}/magazines/search`);
}

export function addAppearance(gameId: string, appearance: MagazineAppearance): Promise<Game> {
  return fetchJson<Game>(`/games/${gameId}/magazines/appearances`, {
    method: 'POST',
    body: JSON.stringify(appearance),
  });
}

export function removeAppearance(gameId: string, appearanceId: string): Promise<Game> {
  return fetchJson<Game>(`/games/${gameId}/magazines/appearances/${appearanceId}`, {
    method: 'DELETE',
  });
}

export interface MagazineLinks {
  archiveOrg?: string;
  retroCdn?: string;
}

export function buildMagazineLinks(appearance: MagazineAppearance): MagazineLinks {
  const magazine = appearance.magazineName;
  const issue = appearance.issueNumber;
  const date = appearance.date;

  const links: MagazineLinks = {};

  // Retro CDN: link directo a la categoría de la revista
  const retrocdnSlug = magazine.replace(/ /g, '_').replace(/\./g, '');
  links.retroCdn = `https://retrocdn.net/Category:${retrocdnSlug}_scans`;

  // Archive.org: búsqueda específica de la revista
  const queryParts = [magazine];
  if (issue) queryParts.push(`issue ${issue}`);
  if (date) queryParts.push(date);
  links.archiveOrg = `https://archive.org/search?query=${encodeURIComponent(queryParts.join(' '))}&and[]=mediatype%3Atexts`;

  return links;
}
