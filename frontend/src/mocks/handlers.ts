import { http, HttpResponse } from 'msw';
import { computeGameStatus } from '@/lib/domain/completeness';
import type { GameStatus } from '@/lib/domain/types';
import { games, romCandidates, systems } from './seed';

const clone = <T>(value: T): T => structuredClone(value);

export const handlers = [
  http.get('/api/systems', () => HttpResponse.json(clone(systems))),
  http.get('/api/roms/candidates', () => HttpResponse.json(clone(romCandidates))),
  http.get('/api/games', ({ request }) => {
    const url = new URL(request.url);
    const q = url.searchParams.get('q')?.toLowerCase() ?? '';
    const systemId = url.searchParams.get('systemId') ?? '';
    const status = (url.searchParams.get('status') ?? '') as GameStatus | '';
    let items = games.map((game) => ({
      id: game.id,
      title: game.identity.title,
      year: game.identity.year,
      systemName: systems.find((system) => system.id === game.systemId)?.name ?? game.systemId,
      identitySource: game.identitySource,
      status: computeGameStatus(game),
      exportStatus: game.id === 'goldnaxe' ? 'exported' : 'pending',
      coverThumbUrl: game.coverThumbUrl,
    }));
    if (q) items = items.filter((game) => game.title.toLowerCase().includes(q));
    if (systemId) items = items.filter((game) => games.find((full) => full.id === game.id)?.systemId === systemId);
    if (status) items = items.filter((game) => game.status === status);
    const exportStatus = url.searchParams.get('exportStatus');
    if (exportStatus) items = items.filter((game) => game.exportStatus === exportStatus);
    const page = Number(url.searchParams.get('page') || 1);
    const perPage = Number(url.searchParams.get('perPage') || 50);
    return HttpResponse.json({ items: clone(items.slice((page - 1) * perPage, page * perPage)), page, perPage, total: items.length });
  }),
  http.get('/api/games/:id', ({ params }) => {
    const game = games.find((item) => item.id === params.id);
    return game ? HttpResponse.json(clone(game)) : new HttpResponse(null, { status: 404 });
  }),
];
