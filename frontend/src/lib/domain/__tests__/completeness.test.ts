import { describe, expect, it } from 'vitest';
import { computeGameStatus, missingRequired } from '../completeness';
import { games } from '@/mocks/seed';
import type { Game } from '../types';

const complete = (): Game => structuredClone(games[0]);

describe('completeness', () => {
  it('marca listo un juego completo', () => {
    expect(missingRequired(complete())).toEqual([]);
    expect(computeGameStatus(complete())).toBe('ready');
  });

  it('no bloquea si solo falta marquesina', () => {
    const game = complete();
    game.images.marquesina.status = 'empty';
    expect(missingRequired(game)).toEqual([]);
    expect(computeGameStatus(game)).toBe('ready');
  });

  it('bloquea si falta poster', () => {
    const game = complete();
    game.images.poster.status = 'empty';
    expect(missingRequired(game)).toContain('Póster');
    expect(computeGameStatus(game)).toBe('incomplete');
  });

  it('no bloquea si falta accent2', () => {
    const game = complete();
    game.accent2Value = '';
    expect(missingRequired(game)).toEqual([]);
  });

  it('bloquea si falta acento primario', () => {
    const game = complete();
    game.accent = 'empty';
    game.accentValue = '';
    expect(missingRequired(game)).toContain('Presentación: Color de acento primario');
    expect(computeGameStatus(game)).toBe('incomplete');
  });

  it('prioriza errores aunque el juego esté completo', () => {
    const game = complete();
    game.errors = [{ field: 'Año', message: 'Debe ser un número de 4 dígitos (contrato ATTRACT).' }];
    expect(computeGameStatus(game)).toBe('error');
  });

  it('prioriza errores aunque también falten campos', () => {
    const game = complete();
    game.images.poster.status = 'empty';
    game.errors = [{ field: 'Año', message: 'Debe ser un número de 4 dígitos (contrato ATTRACT).' }];
    expect(computeGameStatus(game)).toBe('error');
  });

  it('no bloquea review parcial ni cheats libres', () => {
    const contra = games.find((game) => game.id === 'contra');
    expect(contra).toBeDefined();
    expect(contra?.review.cats).toEqual({ graficos: 85, adiccion: 92, sonido: 84 });
    expect(contra?.cheats.groups[0]?.name).toBe('modo cooperativo');
    expect(missingRequired(contra as Game)).toEqual([]);
  });

  it('no bloquea ausencia de reseña', () => {
    const game = complete();
    game.review = { status: 'empty', score: null, cats: {} };
    expect(missingRequired(game)).toEqual([]);
  });
});
