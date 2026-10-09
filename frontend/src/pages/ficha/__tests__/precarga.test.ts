import { describe, expect, it } from 'vitest';
import type { Game } from '@/lib/domain/types';
import { games } from '@/mocks/seed';
import { resumenPrecarga } from '../precarga';

const juego = (id: string): Game => structuredClone(games.find((g) => g.id === id)!);

describe('resumenPrecarga', () => {
  it('cuenta aplicados (fuente externa) y pendientes (sugeridos)', () => {
    const game = juego('mslug');
    game.identitySource = 'manual';
    game.images.logo = { status: 'suggested', source: 'ArcadeDB', url: '/media/x.png' };
    game.images.captura = { status: 'manual', source: 'ArcadeDB', url: '/media/y.png' };
    game.images.poster = { status: 'manual', source: 'manual', url: '/media/z.png' };
    const r = resumenPrecarga(game);
    expect(r.pendientes).toBe(1);
    expect(r.aplicados).toBe(1);
    expect(r.traidos).toBe(2);
    expect(r.fuentes).toEqual(['ArcadeDB']);
  });

  it('la identidad de catálogo cuenta como aplicada, campo por campo', () => {
    const r = resumenPrecarga(juego('goldnaxe'));
    expect(r.aplicados).toBeGreaterThanOrEqual(7);
    expect(r.pendientes).toBe(0);
  });

  it('un juego cargado a mano no trajo nada', () => {
    const game = juego('mslug');
    game.identitySource = 'manual';
    expect(resumenPrecarga(game).traidos).toBe(0);
  });
});
