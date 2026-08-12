import { http, HttpResponse } from 'msw';
import { games, systems } from './seed';

const clone = <T>(value: T): T => structuredClone(value);

export const handlers = [
  http.get('/api/systems', () => HttpResponse.json(clone(systems))),
  http.get('/api/games', () => HttpResponse.json(clone(games))),
  http.get('/api/games/:id', ({ params }) => {
    const game = games.find((item) => item.id === params.id);
    return game ? HttpResponse.json(clone(game)) : new HttpResponse(null, { status: 404 });
  }),
];
