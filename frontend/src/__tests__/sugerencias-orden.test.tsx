import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { SuggestionsModal } from '@/components/SuggestionsModal';
import type { SuggestionCandidate, SuggestionTrace, SuggestionsResult } from '@/lib/api/suggestions';

// ADR-0027: las fuentes se muestran en el orden de la cadena y MobyGames, que no hizo falta, se
// puede consultar igual.

const retrySource = vi.fn();

function traza(nombre: string, estado: string): SuggestionTrace {
  return { nombre, tipo: 'scrape', estado, urlsProcesadas: [], datosObtenidos: [] };
}

function candidato(fuente: string, value: string): SuggestionCandidate {
  return {
    id: `${fuente}:developer`,
    key: 'developer',
    kind: 'identity',
    nombre: `Desarrollador (${fuente})`,
    fuente,
    clase: 'aplicable',
    value,
    previewUrl: null,
    mediaUrl: null,
    origenUrl: null,
    generadoPorIa: false,
    meta: {},
    trace: null,
  };
}

const resultado: SuggestionsResult = {
  candidatos: [candidato('Launchbox', 'Brøderbund Software'), candidato('MyAbandonware', 'Brøderbund Software, Inc.')],
  respondieron: 2,
  consultados: 3,
  fuentes: [
    traza('ArcadeDB', 'sin resultados'),
    traza('MyAbandonware', 'ok'),
    traza('Launchbox', 'ok'),
    traza('MobyGames', 'no hizo falta'),
  ],
};

vi.mock('@/hooks/useSuggestionsJob', () => ({
  useSuggestionsJob: () => ({ phase: 'resultados', result: resultado, retry: vi.fn(), retrySource }),
}));

function abrir() {
  render(
    <SuggestionsModal
      fieldKey="developer"
      gameId="prince-of-persia"
      hasContent={false}
      isManual={false}
      label="Desarrollador"
      onApply={vi.fn()}
      onClose={vi.fn()}
      open
    />,
  );
}

describe('Sugerir: orden de las fuentes', () => {
  it('lista las fuentes en el orden en que se consultaron', () => {
    abrir();
    const secciones = screen.getAllByRole('heading', { level: 4 }).map((h) => h.textContent);
    expect(secciones).toEqual(['ArcadeDB', 'MyAbandonware', 'Launchbox', 'MobyGames', 'Image Search']);
  });

  it('ofrece consultar MobyGames cuando no hizo falta', async () => {
    abrir();
    await userEvent.click(screen.getByRole('button', { name: 'Consultar' }));
    expect(retrySource).toHaveBeenCalledWith('MobyGames');
    expect(screen.getAllByRole('button', { name: 'Reintentar' })).toHaveLength(1); // ArcadeDB
  });
});
