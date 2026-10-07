import { describe, expect, it } from 'vitest';
import { deriveFase } from '@/hooks/useSuggestionsJob';
import type { SuggestionsResult } from '@/lib/api/suggestions';

function resultado(estados: string[], candidatos = 0, respondieron = 0): SuggestionsResult {
  return {
    candidatos: Array.from({ length: candidatos }, () => ({}) as SuggestionsResult['candidatos'][number]),
    respondieron,
    consultados: estados.length,
    fuentes: estados.map((estado) => ({ nombre: 'IA', tipo: 'api', estado, urlsProcesadas: [], datosObtenidos: [] })),
  };
}

describe('deriveFase', () => {
  it('con candidatos son resultados', () => {
    expect(deriveFase(resultado(['ok'], 1, 1))).toBe('resultados');
  });

  it('un modelo que se niega a inventar es «sin resultados», no un error de la fuente', () => {
    expect(deriveFase(resultado(['respuesta inválida: el modelo no conoce el juego']))).toBe('sin-resultados');
  });

  it('una fuente que no contestó es un error', () => {
    expect(deriveFase(resultado(['timeout', 'HTTP 503']))).toBe('error');
  });

  it('sin fuentes consultadas es un error', () => {
    expect(deriveFase(resultado([]))).toBe('error');
  });

  it('una fuente ok sin candidatos es «sin resultados»', () => {
    expect(deriveFase(resultado(['ok'], 0, 1))).toBe('sin-resultados');
  });
});
