import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';
import { computeGameStatus, missingRequired } from '@/lib/domain/completeness';
import type { Game, GameStatus, System } from '@/lib/domain/types';
import { games, systems } from '@/mocks/seed';

const clone = <T>(value: T): T => structuredClone(value);
let storedGames: Game[] = [];
let storedSystems: System[] = [];

beforeEach(() => {
  storedGames = clone(games);
  storedSystems = clone(systems);
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://127.0.0.1');
    const method = init?.method ?? 'GET';
    if (url.pathname === '/api/systems' && method === 'GET') return json(clone(storedSystems));
    if (url.pathname === '/api/systems' && method === 'POST') return createSystem(init?.body);
    if (url.pathname === '/api/games' && method === 'GET') return json(gamesPage(url));
    if (url.pathname === '/api/games' && method === 'POST') return createGame(init?.body);
    if (url.pathname.startsWith('/api/games/')) return gameRoute(url, method, init);
    return json({ error: `Unhandled ${method} ${url.pathname}` }, 500);
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
  cleanup();
});

function json(payload: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  } as Response;
}

function bodyAsObject(body: BodyInit | null | undefined) {
  return JSON.parse(String(body ?? '{}')) as Record<string, unknown>;
}

function createSystem(body: BodyInit | null | undefined) {
  const payload = bodyAsObject(body);
  const system: System = {
    id: String(payload.shortName),
    name: String(payload.name),
    shortName: String(payload.shortName),
    launchCmd: String(payload.launchCmd),
    valid: String(payload.launchCmd).startsWith('/'),
    errorMsg: String(payload.launchCmd).startsWith('/') ? undefined : 'La ruta debe ser absoluta (ej: /opt/emulador/bin o C:\\Emuladores\\bin.exe). Si no, el juego no arranca en el gabinete sin avisar.',
    gameCount: 0,
  };
  storedSystems = storedSystems.filter((item) => item.id !== system.id).concat(system);
  return json(clone(system));
}

function createGame(body: BodyInit | null | undefined) {
  const payload = bodyAsObject(body);
  const identity = payload.identity as Game['identity'];
  const game: Game = {
    id: identity.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
    systemId: String(payload.systemId),
    identity,
    identitySource: 'manual',
    gallery: [],
    romSource: payload.romSource as Game['romSource'],
    romRef: String(payload.romRef),
    file_format: String(payload.file_format ?? ''),
    tratamiento: String(payload.tratamiento ?? ''),
    errors: [],
    images: { caratula: { status: 'empty' }, marquesina: { status: 'empty' }, poster: { status: 'empty' }, logo: { status: 'empty' }, captura: { status: 'empty' } },
    video: { video: { status: 'empty' } },
    texts: { sinopsis: { status: 'empty', value: '' } },
    review: { status: 'empty', score: null, cats: {} },
    cheats: { status: 'empty', groups: [] },
    accent: 'empty',
    accentValue: '',
    accent2Value: '',
    manuals: [],
    magazine: 'empty',
    magazineName: '',
    magazineAppearances: [],
    provenance: {},
  };
  storedGames.push(game);
  return json(clone(game));
}

function gameRoute(url: URL, method: string, init?: RequestInit) {
  const parts = url.pathname.split('/');
  const id = parts[3];
  const game = storedGames.find((item) => item.id === id);
  if (!game) return json({ error: 'Juego no encontrado' }, 404);
  if (method === 'GET') return json(clone(game));
  if (method === 'PATCH') {
    Object.assign(game, bodyAsObject(init?.body));
    return json(clone(game));
  }
  if (method === 'POST' && parts[4] === 'mark-ready') {
    const missing = missingRequired(game);
    return missing.length ? json({ error: 'El juego está incompleto', detail: { missing } }, 409) : json(clone(game));
  }
  if (parts[4] === 'fields') return fieldRoute(game, parts[5], method, init);
  if (parts[4] === 'media' && method === 'PUT') {
    const key = parts[5] as keyof Game['images'];
    if (key in game.images) game.images[key] = { status: 'manual', url: `/media/${game.systemId}/${game.id}/${key}.jpg` };
    return json(clone(game));
  }
  return json({ error: `Unhandled ${method} ${url.pathname}` }, 500);
}

function fieldRoute(game: Game, key: string, method: string, init?: RequestInit) {
  if (method === 'DELETE') {
    if (key === 'sinopsis') game.texts.sinopsis = { status: 'empty', value: '' };
    return json(clone(game));
  }
  if (method !== 'PUT') return json({ error: 'Método inválido' }, 500);
  const payload = bodyAsObject(init?.body);
  if (key === 'sinopsis') game.texts.sinopsis = { status: 'manual', value: String(payload.value ?? '') };
  if (key === 'review') game.review = { status: 'manual', score: payload.score as number | null, cats: payload.cats as Game['review']['cats'] };
  if (key === 'cheats') game.cheats = { status: 'manual', groups: payload.groups as Game['cheats']['groups'] };
  return json(clone(game));
}

function gamesPage(url: URL) {
  const q = url.searchParams.get('q')?.toLowerCase() ?? '';
  const systemId = url.searchParams.get('systemId') ?? '';
  const status = (url.searchParams.get('status') ?? '') as GameStatus | '';
  let items = storedGames.map((game) => ({
    id: game.id,
    title: game.identity.title,
    year: game.identity.year,
    systemName: storedSystems.find((system) => system.id === game.systemId)?.name ?? game.systemId,
    identitySource: game.identitySource,
    status: computeGameStatus(game),
    coverThumbUrl: game.coverThumbUrl,
  }));
  if (q) items = items.filter((game) => game.title.toLowerCase().includes(q));
  if (systemId) {
    items = items.filter((game) => storedGames.find((full) => full.id === game.id)?.systemId === systemId);
  }
  if (status) items = items.filter((game) => game.status === status);
  return { items: clone(items), page: 1, perPage: 50, total: items.length };
}
