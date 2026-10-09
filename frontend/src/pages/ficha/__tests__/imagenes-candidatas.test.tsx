import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { SuggestionCandidate } from '@/lib/api/suggestions';
import type { Game } from '@/lib/domain/types';
import { ImagenesSection } from '../ImagenesSection';

const cand = (id: string, fuente: string, clase: SuggestionCandidate['clase'] = 'aplicable'): SuggestionCandidate => ({
  id, key: 'caratula', kind: 'media', nombre: id, fuente, clase, value: null, previewUrl: `/p/${id}.png`, mediaUrl: null,
  origenUrl: null, generadoPorIa: false, meta: {}, trace: null,
});

const juego = {
  id: 'sonic',
  images: { caratula: { status: 'suggested', source: 'ArcadeDB', url: '/m/c.png' } },
  video: {},
} as unknown as Game;

function montar(candidatos: SuggestionCandidate[], onPick = vi.fn()) {
  render(
    <ImagenesSection
      candidatas={{ key: 'caratula', candidatos }}
      game={juego}
      onDelete={vi.fn()}
      onPickCandidata={onPick}
      onSuggestImage={vi.fn()}
      onUpload={vi.fn()}
    />,
  );
  return onPick;
}

describe('Fila de candidatas de imágenes', () => {
  it('con varias opciones muestra la fila, resalta la de la fuente del slot y aplica la elegida', async () => {
    const onPick = montar([cand('a', 'ArcadeDB'), cand('b', 'Launchbox'), cand('c', 'Image Search', 'referencia')]);

    expect(screen.getByText(/encontró 2 opciones — elegí una/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Usar la opción de ArcadeDB' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Usar la opción de Launchbox' })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByText('Usar la mía')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Usar la opción de Launchbox' }));
    expect(onPick).toHaveBeenCalledWith('caratula', 'b');
  });

  it('con una sola opción no dibuja la fila (queda el botón Cambiar y el modal)', () => {
    montar([cand('a', 'ArcadeDB')]);
    expect(screen.queryByText(/elegí una/)).not.toBeInTheDocument();
  });
});
