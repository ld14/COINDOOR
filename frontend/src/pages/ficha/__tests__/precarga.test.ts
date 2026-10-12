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
    game.review = { status: 'suggested', source: 'IA', score: 80, cats: {} };
    const r = resumenPrecarga(game);
    expect(r.pendientes).toBe(1);
    // La imagen sugerida pero ya cargada cuenta como aplicada.
    expect(r.aplicados).toBe(2);
    expect(r.traidos).toBe(3);
    expect(r.fuentes).toEqual(['ArcadeDB', 'IA']);
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
