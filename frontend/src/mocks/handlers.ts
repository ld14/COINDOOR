import { http, HttpResponse } from 'msw';
import { computeGameStatus } from '@/lib/domain/completeness';
import type { GameStatus } from '@/lib/domain/types';
import { games, systems } from './seed';

const clone = <T>(value: T): T => structuredClone(value);

export const handlers = [
  http.get('/api/systems', () => HttpResponse.json(clone(systems))),
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
      coverThumbUrl: game.coverThumbUrl,
    }));
    if (q) items = items.filter((game) => game.title.toLowerCase().includes(q));
    if (systemId) items = items.filter((game) => games.find((full) => full.id === game.id)?.systemId === systemId);
    if (status) items = items.filter((game) => game.status === status);
    return HttpResponse.json({ items: clone(items), page: 1, perPage: 50, total: items.length });
  }),
  http.get('/api/games/:id', ({ params }) => {
    const game = games.find((item) => item.id === params.id);
    return game ? HttpResponse.json(clone(game)) : new HttpResponse(null, { status: 404 });
  }),
];
