import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createRef } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { FichaAutosaveContext } from '../autosaveContext';
import { GaleriaSection } from '../GaleriaSection';
import { ReviewSection } from '../ResenaSection';
import { CheatsSection } from '../TrucosSection';
import { esFuenteIA } from '../fuenteIA';
import type { SaveHandle } from '../types';
import type { Game } from '@/lib/domain/types';
import { games } from '@/mocks/seed';

const base = games.find((g) => g.id === 'contra') as Game;

function conGrupos(groups: Game['cheats']['groups'], status: Game['cheats']['status'] = 'manual', source?: string): Game {
  return { ...base, cheats: { status, source, groups } };
}

function renderConAutosave(ui: React.ReactElement, aceptar = vi.fn(), markDirty = vi.fn()) {
  render(<FichaAutosaveContext.Provider value={{ aceptar, markDirty }}>{ui}</FichaAutosaveContext.Provider>);
  return { aceptar, markDirty };
}

describe('esFuenteIA', () => {
  it('reconoce IA y traducido por IA, no otras fuentes', () => {
    expect(esFuenteIA('IA')).toBe(true);
    expect(esFuenteIA('ArcadeDB · traducido por IA')).toBe(true);
    expect(esFuenteIA('ArcadeDB')).toBe(false);
    expect(esFuenteIA('manual')).toBe(false);
    expect(esFuenteIA(undefined)).toBe(false);
  });
});

describe('TrucosSection', () => {
  const grupos = [{ name: 'ArcadeDB', entries: [{ name: '30 vidas', input: '↑ ↓' }, { name: 'Salto', input: 'B' }] }];

  it('save() no escribe si nada cambió y avisa los cambios sin evento nativo', async () => {
    const onCheats = vi.fn();
    const ref = createRef<SaveHandle>();
    const { markDirty } = renderConAutosave(
      <CheatsSection game={conGrupos(grupos)} onCheats={onCheats} onDelete={vi.fn()} onSuggest={vi.fn()} ref={ref} />,
    );
    ref.current?.save();
    expect(onCheats).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole('button', { name: 'Agregar grupo' }));
    expect(markDirty).toHaveBeenCalledWith('trucos');
    ref.current?.save();
    expect(onCheats).toHaveBeenLastCalledWith([...grupos, { name: 'Nuevo grupo', entries: [] }]);
  });

  it('las entradas en blanco no se guardan', async () => {
    const onCheats = vi.fn();
    const ref = createRef<SaveHandle>();
    renderConAutosave(<CheatsSection game={conGrupos(grupos)} onCheats={onCheats} onDelete={vi.fn()} onSuggest={vi.fn()} ref={ref} />);
    await userEvent.click(screen.getByRole('button', { name: '+ Agregar truco' }));
    ref.current?.save();
    expect(onCheats).not.toHaveBeenCalled();
  });

  it('inserta símbolos donde está el cursor sin sacar el foco', async () => {
    const onCheats = vi.fn();
    const ref = createRef<SaveHandle>();
    renderConAutosave(<CheatsSection game={conGrupos(grupos)} onCheats={onCheats} onDelete={vi.fn()} onSuggest={vi.fn()} ref={ref} />);
    const codigo = screen.getAllByLabelText('Código o procedimiento')[0];
    await userEvent.click(codigo);
    await userEvent.click(screen.getByRole('button', { name: '[ATAQUE]' }));
    expect(codigo).toHaveFocus();
    expect(codigo).toHaveValue('↑ ↓[ATAQUE]');
    ref.current?.save();
    expect(onCheats.mock.calls[0][0][0].entries[0].input).toBe('↑ ↓[ATAQUE]');
  });

  it('elimina un grupo y reordena con el teclado', async () => {
    const onCheats = vi.fn();
    const ref = createRef<SaveHandle>();
    renderConAutosave(<CheatsSection game={conGrupos(grupos)} onCheats={onCheats} onDelete={vi.fn()} onSuggest={vi.fn()} ref={ref} />);
    const manija = screen.getByRole('button', { name: /Mover truco 1/ });
    manija.focus();
    await userEvent.keyboard('{ArrowDown}');
    ref.current?.save();
    expect(onCheats.mock.calls[0][0][0].entries.map((e: { name: string }) => e.name)).toEqual(['Salto', '30 vidas']);

    await userEvent.click(screen.getByRole('button', { name: 'Eliminar grupo' }));
    ref.current?.save();
    expect(onCheats.mock.calls[1][0]).toEqual([]);
  });

  it('colapsa las entradas largas y los grupos con muchas entradas', async () => {
    const largas = Array.from({ length: 6 }, (_, i) => ({ name: `Truco ${i + 1}`, input: i === 0 ? 'x'.repeat(150) : 'B' }));
    renderConAutosave(<CheatsSection game={conGrupos([{ name: 'G', entries: largas }])} onCheats={vi.fn()} onDelete={vi.fn()} onSuggest={vi.fn()} />);
    expect(screen.getAllByLabelText('Qué hace el truco')).toHaveLength(3); // 4 visibles, la primera colapsada
    expect(screen.getByRole('button', { name: 'Editar truco' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Ver 2 más' }));
    expect(screen.getAllByLabelText('Qué hace el truco')).toHaveLength(5);
    expect(screen.getByRole('button', { name: 'Ver menos' })).toBeInTheDocument();
  });

  it('un campo sugerido se acepta y la IA queda marcada', async () => {
    const { aceptar } = renderConAutosave(
      <CheatsSection game={conGrupos(grupos, 'suggested', 'ArcadeDB · traducido por IA')} onCheats={vi.fn()} onDelete={vi.fn()} onSuggest={vi.fn()} />,
    );
    expect(screen.getByText('Generado por IA')).toBeInTheDocument();
    expect(screen.getByText('● Sugerido · sin revisar')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Aceptar' }));
    expect(aceptar).toHaveBeenCalledWith('cheats');
  });

  it('«Separar en trucos» deja una propuesta que recién se usa al aceptarla', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ groups: [{ name: 'Guía', entries: [{ name: 'Vida extra', input: 'A B' }] }] }), { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    const onCheats = vi.fn();
    const ref = createRef<SaveHandle>();
    renderConAutosave(<CheatsSection game={conGrupos([])} onCheats={onCheats} onDelete={vi.fn()} onSuggest={vi.fn()} ref={ref} />);
    await userEvent.type(screen.getByLabelText('Texto de trucos a interpretar'), 'Vida extra: A B');
    await userEvent.click(screen.getByRole('button', { name: '✦ Separar en trucos' }));
    expect(await screen.findByRole('group', { name: 'Sugerencia de IA' })).toBeInTheDocument();
    ref.current?.save();
    expect(onCheats).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole('button', { name: 'Usar' }));
    ref.current?.save();
    expect(onCheats).toHaveBeenCalledWith([{ name: 'Guía', entries: [{ name: 'Vida extra', input: 'A B' }] }]);
    vi.unstubAllGlobals();
    localStorage.clear();
  });
});

describe('ReviewSection', () => {
  const conReview = (review: Partial<Game['review']>): Game => ({ ...base, review: { status: 'manual', score: null, cats: {}, ...review } });

  it('muestra «sin reseña» y distingue las categorías incompletas', () => {
    const { unmount } = render(<FichaAutosaveContext.Provider value={{ aceptar: vi.fn(), markDirty: vi.fn() }}><ReviewSection game={conReview({ status: 'empty' })} onReview={vi.fn()} onSuggest={vi.fn()} /></FichaAutosaveContext.Provider>);
    expect(screen.getByText(/Todavía no hay reseña/)).toBeInTheDocument();
    unmount();
    renderConAutosave(<ReviewSection game={conReview({ score: 80, cats: { graficos: 70 } })} onReview={vi.fn()} onSuggest={vi.fn()} />);
    expect(screen.getByText(/1 de 6 categorías cargadas — dejar categorías vacías es válido/)).toBeInTheDocument();
    expect(screen.queryByText(/Todavía no hay reseña/)).not.toBeInTheDocument();
  });

  it('save() guarda solo lo que cambió, con categorías parciales 0–100', async () => {
    const onReview = vi.fn();
    const ref = createRef<SaveHandle>();
    renderConAutosave(<ReviewSection game={conReview({ score: 80, cats: { graficos: 70 } })} onReview={onReview} onSuggest={vi.fn()} ref={ref} />);
    ref.current?.save();
    expect(onReview).not.toHaveBeenCalled();

    await userEvent.type(screen.getByLabelText('Sonido (0–100)'), '150');
    ref.current?.save();
    expect(onReview).toHaveBeenCalledWith(80, { graficos: 70, sonido: 100 });

    await userEvent.clear(screen.getByLabelText('Gráficos (0–100)'));
    ref.current?.save();
    expect(onReview).toHaveBeenLastCalledWith(80, { sonido: 100 });
  });

  it('una reseña de IA sugerida se marca y se acepta sin tocar el valor', async () => {
    const onReview = vi.fn();
    const ref = createRef<SaveHandle>();
    const { aceptar } = renderConAutosave(<ReviewSection game={conReview({ status: 'suggested', source: 'IA', score: 88 })} onReview={onReview} onSuggest={vi.fn()} ref={ref} />);
    expect(screen.getByText('Generado por IA')).toBeInTheDocument();
    expect(screen.getByText('88')).toBeInTheDocument();
    ref.current?.save();
    expect(onReview).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: 'Aceptar' }));
    expect(aceptar).toHaveBeenCalledWith('review');
  });
});

describe('GaleriaSection', () => {
  it('es una Card numerada que envuelve la galería, con la acción de traer imágenes', async () => {
    const gallery = [{ id: 'g1', tipo: 'screenshot', label: 'Captura 1', file: 'a.png', url: '/a.png', source: 'ArcadeDB' }];
    render(<GaleriaSection game={{ ...base, gallery }} numero={8} onChanged={vi.fn()} />);
    expect(screen.getByRole('heading', { name: 'Galería' })).toBeInTheDocument();
    expect(screen.getByAltText('Captura 1')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Traer de ArcadeDB / LaunchBox' })).toBeInTheDocument());
  });
});
