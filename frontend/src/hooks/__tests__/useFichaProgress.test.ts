import { describe, expect, it } from 'vitest';
import { computeFichaProgress } from '@/hooks/useFichaProgress';
import { missingRequired } from '@/lib/domain/completeness';
import type { Game } from '@/lib/domain/types';
import { games } from '@/mocks/seed';

const juego = (id: string): Game => structuredClone(games.find((g) => g.id === id)!);
const estado = (game: Game, clave: string) => computeFichaProgress(game).secciones.find((s) => s.clave === clave)!;

describe('computeFichaProgress', () => {
  it('sin juego devuelve un progreso vacío con todas las secciones', () => {
    const p = computeFichaProgress(undefined);
    expect(p.percent).toBe(0);
    expect(p.cola).toEqual([]);
    expect(p.secciones.map((s) => s.clave)).toEqual(['identidad', 'imagenes', 'video', 'textos', 'guia', 'trucos', 'presentacion', 'galeria', 'resena', 'manual']);
  });

  it('una ficha completa marca 100% y no deja pendientes', () => {
    const p = computeFichaProgress(juego('goldnaxe'));
    expect(p.percent).toBe(100);
    expect(p.faltantes).toEqual([]);
    expect(p.cola).toEqual([]);
    expect(p.secciones.find((s) => s.clave === 'identidad')?.status).toBe('complete');
  });

  it('cada obligatorio de missingRequired() queda anclado a su sección y campo', () => {
    const game = juego('mslug');
    const p = computeFichaProgress(game);
    expect(p.faltantes.map((f) => f.label)).toEqual(expect.arrayContaining(missingRequired(game)));
    const porLabel = (label: string) => p.faltantes.find((f) => f.label === label)!;
    expect(porLabel('Identidad: Año')).toMatchObject({ seccion: 'identidad', campo: 'year', severity: 'required' });
    expect(porLabel('Carátula')).toMatchObject({ seccion: 'imagenes', campo: 'caratula' });
    expect(porLabel('Sinopsis')).toMatchObject({ seccion: 'textos', campo: 'sinopsis' });
    expect(porLabel('Presentación: Color de acento primario')).toMatchObject({ seccion: 'presentacion', campo: 'accent' });
    expect(p.percent).toBeLessThan(50);
  });

  it('los obligatorios van ordenados por sección y numerados', () => {
    const p = computeFichaProgress(juego('mslug'));
    const pasos = p.faltantes.map((f) => f.step ?? 0);
    expect(pasos).toEqual([...pasos].sort((a, b) => a - b));
    expect(p.faltantes[0].step).toBe(1);
  });

  it('el porcentaje es obligatorios cubiertos sobre el total', () => {
    const game = juego('sf2'); // solo falta el póster
    const p = computeFichaProgress(game);
    expect(p.faltantes).toHaveLength(1);
    expect(p.percent).toBe(Math.round(((p.totalObligatorios - 1) / p.totalObligatorios) * 100));
    expect(estado(game, 'imagenes')).toMatchObject({ status: 'blocking', hint: '1 obligatorio' });
  });

  it('una sugerencia pendiente es una revisión, no un faltante', () => {
    const p = computeFichaProgress(juego('sonic'));
    expect(p.faltantes).toEqual([]);
    expect(p.sugerencias).toEqual([expect.objectContaining({ id: 'sug:logo', seccion: 'imagenes', severity: 'review', aceptarClave: 'logo' })]);
    expect(p.secciones.find((s) => s.clave === 'imagenes')).toMatchObject({ status: 'review', hint: '1 sugerido' });
  });

  it('la reseña sugerida se acepta con la clave review', () => {
    const p = computeFichaProgress(juego('contra'));
    expect(p.sugerencias).toEqual([expect.objectContaining({ seccion: 'resena', aceptarClave: 'review' })]);
  });

  it('la cola pone los obligatorios (rojo) antes que las revisiones', () => {
    const game = juego('mslug');
    game.images.logo = { status: 'suggested', source: 'ArcadeDB', url: '/media/mslug/logo.png' };
    game.review = { status: 'suggested', score: 80, cats: {} };
    const { cola, faltantes, sugerencias } = computeFichaProgress(game);
    expect(cola).toEqual([...faltantes, ...sugerencias]);
    expect(cola.findIndex((p) => p.severity === 'review')).toBe(faltantes.length);
    expect(cola.slice(0, faltantes.length).every((p) => p.severity === 'required')).toBe(true);
  });

  it('suma los requeridos de guiaChecklist y bloquea «Cómo se juega»', () => {
    const game = juego('goldnaxe');
    game.guiaChecklist = [
      { key: 'objetivo', label: 'Objetivo', estado: 'falta', detalle: 'sin objetivo', requerido: true },
      { key: 'primerosPasos', label: 'Primeros pasos', estado: 'falta', detalle: '', requerido: false },
    ];
    const p = computeFichaProgress(game);
    expect(p.faltantes).toEqual([expect.objectContaining({ id: 'req:guia:objetivo', seccion: 'guia', campo: 'objetivo' })]);
    expect(p.percent).toBeLessThan(100);
    expect(p.secciones.find((s) => s.clave === 'guia')?.status).toBe('blocking');
  });

  it('una sección opcional con contenido queda completa y sin contenido en curso', () => {
    expect(estado(juego('contra'), 'trucos').status).toBe('complete');
    expect(estado(juego('goldnaxe'), 'trucos').status).toBe('current');
  });
});
