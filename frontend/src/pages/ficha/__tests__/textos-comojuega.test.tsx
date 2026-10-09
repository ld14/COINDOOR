import { createRef } from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { Game, GuiaChecklistItem } from '@/lib/domain/types';
import { games } from '@/mocks/seed';
import { FichaAutosaveContext } from '../autosaveContext';
import { GuiaChecklist } from '../ComoSeJuegaSection';
import { TextSection } from '../TextosSection';
import type { SaveHandle } from '../types';

const juego = (id = 'mslug'): Game => structuredClone(games.find((g) => g.id === id)!);

function montarTextos(game: Game) {
  const onText = vi.fn();
  const onSuggest = vi.fn();
  const onDelete = vi.fn();
  const aceptar = vi.fn();
  const markDirty = vi.fn();
  const ref = createRef<SaveHandle>();
  render(
    <FichaAutosaveContext.Provider value={{ aceptar, markDirty }}>
      <TextSection game={game} onDelete={onDelete} onSuggest={onSuggest} onText={onText} ref={ref} />
    </FichaAutosaveContext.Provider>,
  );
  return { aceptar, markDirty, onDelete, onSuggest, onText, ref };
}

describe('TextSection', () => {
  it('muestra el contador de la sinopsis y placeholders con ejemplo', async () => {
    const game = juego();
    game.texts.sinopsis = { status: 'manual', value: 'Hola' };
    montarTextos(game);
    expect(screen.getByText(/^4 \/ \d+$/)).toBeInTheDocument();
    expect(screen.getByLabelText('Objetivo')).toHaveAttribute('placeholder', expect.stringContaining('Ej.: «Eliminá a los criminales'));
  });

  it('save() no toca la sinopsis ni los demás textos cuando solo cambió uno', async () => {
    const game = juego();
    game.texts.sinopsis = { status: 'suggested', value: 'Sinopsis sugerida', source: 'arcadedb' };
    const { onText, ref } = montarTextos(game);

    await userEvent.type(screen.getByLabelText('Objetivo'), 'Rescatar a los prisioneros.');
    ref.current!.save();

    expect(onText).toHaveBeenCalledTimes(1);
    expect(onText).toHaveBeenCalledWith('objetivo', 'Rescatar a los prisioneros.');
  });

  it('save() sin cambios no escribe nada', () => {
    const game = juego();
    game.texts.sinopsis = { status: 'suggested', value: 'Sinopsis sugerida' };
    const { onText, ref } = montarTextos(game);
    ref.current!.save();
    expect(onText).not.toHaveBeenCalled();
  });

  it('editar la sinopsis escribe solo la sinopsis', async () => {
    const game = juego();
    game.texts.sinopsis = { status: 'manual', value: 'A' };
    const { onText, ref } = montarTextos(game);
    await userEvent.type(screen.getByLabelText('Sinopsis'), 'B');
    ref.current!.save();
    expect(onText).toHaveBeenCalledTimes(1);
    expect(onText).toHaveBeenCalledWith('sinopsis', 'AB');
  });

  it('un campo sugerido muestra «Aceptar» y lo acepta sin escribir', async () => {
    const game = juego();
    game.texts.sinopsis = { status: 'suggested', value: 'Sugerida', source: 'arcadedb' };
    const { aceptar, onText } = montarTextos(game);
    expect(screen.getByText('● Sugerido · sin revisar')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Aceptar sinopsis' }));
    expect(aceptar).toHaveBeenCalledWith('sinopsis');
    expect(onText).not.toHaveBeenCalled();
  });

  it('el objetivo obligatorio vacío bloquea con el motivo; «Proponer» usa la IA existente', async () => {
    const game = juego();
    game.guiaChecklist = [{ key: 'objetivo', label: 'Objetivo', estado: 'falta', detalle: '', requerido: true }];
    const { onSuggest } = montarTextos(game);
    expect(screen.getByText('✕ Sin objetivo la guía de «Cómo se juega» no se exporta')).toBeInTheDocument();
    expect(screen.getByLabelText('Objetivo')).toHaveAttribute('aria-invalid', 'true');
    await userEvent.click(screen.getByRole('button', { name: 'Proponer un objetivo' }));
    expect(onSuggest).toHaveBeenCalledWith('objetivo');
  });

  it('los pasos son una lista editable que se serializa en líneas', async () => {
    const game = juego();
    game.texts.primerosPasos = { status: 'manual', value: 'Uno\nDos' };
    const { onText, markDirty, ref } = montarTextos(game);
    const lista = screen.getByRole('list', { name: 'Primeros pasos' });
    expect(within(lista).getAllByRole('textbox')).toHaveLength(2);

    await userEvent.click(within(lista).getByRole('button', { name: 'Quitar paso 1' }));
    expect(markDirty).toHaveBeenCalledWith('textos');
    ref.current!.save();
    expect(onText).toHaveBeenCalledWith('primerosPasos', 'Dos');
  });

  it('escribir un espacio en un paso no pierde el foco ni el texto', async () => {
    const game = juego();
    game.texts.primerosPasos = { status: 'manual', value: 'Uno' };
    const { onText, ref } = montarTextos(game);
    const paso = screen.getByLabelText('Paso 1');
    await userEvent.type(paso, ' dos tres');
    expect(screen.getByLabelText('Paso 1')).toHaveFocus();
    expect(screen.getByLabelText('Paso 1')).toHaveValue('Uno dos tres');
    ref.current!.save();
    expect(onText).toHaveBeenCalledWith('primerosPasos', 'Uno dos tres');
  });

  it('Borrar un texto manual pide confirmación', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const game = juego();
    game.texts.sinopsis = { status: 'manual', value: 'A' };
    const { onDelete } = montarTextos(game);
    const caja = screen.getByLabelText('Sinopsis').closest('[data-grupo]') as HTMLElement;
    await userEvent.click(within(caja).getByRole('button', { name: 'Borrar' }));
    expect(window.confirm).toHaveBeenCalled();
    expect(onDelete).toHaveBeenCalledWith('sinopsis');
  });
});

describe('GuiaChecklist (Cómo se juega)', () => {
  const items: GuiaChecklistItem[] = [
    { key: 'objetivo', label: 'Objetivo', estado: 'falta', detalle: 'Sin objetivo la guía no se exporta', requerido: true },
    { key: 'modo', label: 'Modo multijugador', estado: 'falta', detalle: 'Juego simultáneo: elegí cooperativo o versus', requerido: false },
  ];

  it('resuelve el modo en la misma fila y deshabilita «Individual» en juegos simultáneos', async () => {
    const game = juego();
    game.cabinet = { resolution: '', orientation: '', controls: '', buttons: 1, nplayers: '2P sim', button_list: [] };
    const onText = vi.fn();
    render(
      <FichaAutosaveContext.Provider value={{ aceptar: vi.fn(), markDirty: vi.fn() }}>
        <GuiaChecklist fallos={{}} game={game} items={items} onText={onText} />
      </FichaAutosaveContext.Provider>,
    );
    const modo = screen.getByRole('radiogroup', { name: 'Modo multijugador' });
    expect(within(modo).getByRole('radio', { name: 'Individual' })).toBeDisabled();
    await userEvent.click(within(modo).getByRole('radio', { name: 'Versus' }));
    expect(onText).toHaveBeenCalledWith('modo', 'versus');
  });

  it('un modo sugerido ofrece Aceptar', async () => {
    const game = juego();
    game.texts.modo = { status: 'suggested', value: 'cooperativo', source: 'ia' };
    const aceptar = vi.fn();
    render(
      <FichaAutosaveContext.Provider value={{ aceptar, markDirty: vi.fn() }}>
        <GuiaChecklist fallos={{}} game={game} items={items} onText={vi.fn()} />
      </FichaAutosaveContext.Provider>,
    );
    await userEvent.click(screen.getByRole('button', { name: 'Aceptar modo multijugador' }));
    expect(aceptar).toHaveBeenCalledWith('modo');
  });

  it('«Escribir ↑» lleva al campo del objetivo', async () => {
    render(
      <>
        <textarea aria-label="Objetivo" data-campo="objetivo" />
        <GuiaChecklist fallos={{}} items={items} />
      </>,
    );
    await userEvent.click(screen.getByRole('button', { name: 'Escribir objetivo' }));
    expect(screen.getByLabelText('Objetivo')).toHaveFocus();
  });
});
