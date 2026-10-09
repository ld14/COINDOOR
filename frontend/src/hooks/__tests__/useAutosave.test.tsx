import { act, fireEvent, render, renderHook, screen } from '@testing-library/react';
import { useRef, useState, type RefObject } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AUTOSAVE_DELAY_MS, useAutosave, useCongeladoMientrasEdita, type Autosave } from '@/hooks/useAutosave';
import { saveStatusStore } from '@/hooks/useSaveStatus';

type Opciones = { save: (ids: string[]) => void | Promise<void>; waitIdle?: () => Promise<void>; isSaving?: () => boolean };

let autosave: Autosave;

function Formulario({ save, waitIdle, isSaving }: Opciones) {
  const ref = useRef<HTMLDivElement>(null);
  autosave = useAutosave({ containerRef: ref, save, waitIdle, isSaving });
  return (
    <div ref={ref}>
      <div data-seccion="identidad">
        <input aria-label="Año" />
        <select aria-label="Formato"><option>a</option><option>b</option></select>
      </div>
      <div data-seccion="textos">
        <textarea aria-label="Sinopsis" />
      </div>
      <div data-seccion="presentacion" data-autosave="blur">
        <input aria-label="Color" />
      </div>
      <input aria-label="Buscar" />
    </div>
  );
}

const escribir = (etiqueta: string, value = 'x') => fireEvent.input(screen.getByLabelText(etiqueta), { target: { value } });

describe('useAutosave', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    saveStatusStore.reset();
  });
  afterEach(() => {
    vi.useRealTimers();
    saveStatusStore.reset();
  });

  it('guarda ~800 ms después de la última tecla (debounce) y reinicia la espera al seguir escribiendo', () => {
    const save = vi.fn();
    render(<Formulario save={save} />);

    escribir('Año', '1');
    act(() => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS - 1); });
    expect(save).not.toHaveBeenCalled();

    escribir('Año', '19'); // otra tecla: la espera empieza de nuevo
    act(() => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS - 1); });
    expect(save).not.toHaveBeenCalled();

    act(() => { vi.advanceTimersByTime(1); });
    expect(save).toHaveBeenCalledTimes(1);
    expect(save).toHaveBeenCalledWith(['identidad']);
    expect(autosave.dirty).toBe(false);
  });

  it('guarda al instante cuando el campo pierde el foco, y no vuelve a guardar por el timer', () => {
    const save = vi.fn();
    render(<Formulario save={save} />);

    escribir('Sinopsis');
    fireEvent.focusOut(screen.getByLabelText('Sinopsis'));
    expect(save).toHaveBeenCalledTimes(1);
    expect(save).toHaveBeenCalledWith(['textos']);

    act(() => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS * 2); });
    expect(save).toHaveBeenCalledTimes(1);
  });

  it('junta las secciones sucias en un solo guardado', () => {
    const save = vi.fn();
    render(<Formulario save={save} />);

    escribir('Año');
    escribir('Sinopsis');
    act(() => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS); });
    expect(save).toHaveBeenCalledTimes(1);
    expect(save.mock.calls[0][0]).toEqual(['identidad', 'textos']);
  });

  it('ignora lo que se edita fuera de una sección', () => {
    const save = vi.fn();
    render(<Formulario save={save} />);

    escribir('Buscar');
    fireEvent.focusOut(screen.getByLabelText('Buscar'));
    act(() => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS); });
    expect(save).not.toHaveBeenCalled();
  });

  it('el change de un select guarda; el de un input de texto no duplica el guardado del input', () => {
    const save = vi.fn();
    render(<Formulario save={save} />);

    fireEvent.change(screen.getByLabelText('Año'), { target: { value: '1990' } });
    act(() => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS); });
    expect(save).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText('Formato'), { target: { value: 'b' } });
    act(() => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS); });
    expect(save).toHaveBeenCalledWith(['identidad']);
  });

  it('data-autosave="blur": no guarda mientras se teclea, sí al salir del campo', () => {
    const save = vi.fn();
    render(<Formulario save={save} />);

    escribir('Color', '#12');
    act(() => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS * 3); });
    expect(save).not.toHaveBeenCalled();
    expect(autosave.hasUnsaved()).toBe(true);

    fireEvent.focusOut(screen.getByLabelText('Color'));
    expect(save).toHaveBeenCalledWith(['presentacion']);
  });

  it('un error al guardar deja la sección sucia, publica el error y retry() lo reintenta', async () => {
    const save = vi.fn().mockRejectedValueOnce(new Error('disco lleno')).mockResolvedValue(undefined);
    render(<Formulario save={save} />);

    escribir('Sinopsis');
    await act(async () => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS); });
    expect(save).toHaveBeenCalledTimes(1);
    expect(saveStatusStore.getSnapshot()).toMatchObject({ kind: 'error', message: 'disco lleno', canRetry: true });
    expect(autosave.dirty).toBe(true);
    expect(autosave.hasUnsaved()).toBe(true);

    await act(async () => { saveStatusStore.retry(); });
    expect(save).toHaveBeenCalledTimes(2);
    expect(save).toHaveBeenLastCalledWith(['textos']);
    expect(saveStatusStore.getSnapshot().kind).not.toBe('error');
    expect(autosave.dirty).toBe(false);
  });

  it('un save que lanza en forma síncrona también cuenta como error', async () => {
    const save = vi.fn(() => { throw new Error('boom'); });
    render(<Formulario save={save} />);

    escribir('Año');
    await act(async () => { vi.advanceTimersByTime(AUTOSAVE_DELAY_MS); });
    expect(saveStatusStore.getSnapshot()).toMatchObject({ kind: 'error', message: 'boom' });
  });

  it('flushAndWait guarda lo pendiente y espera a que no queden escrituras', async () => {
    const orden: string[] = [];
    const save = vi.fn(() => { orden.push('save'); });
    const waitIdle = vi.fn(async () => { orden.push('idle'); });
    render(<Formulario save={save} waitIdle={waitIdle} />);

    escribir('Año');
    await act(async () => { await autosave.flushAndWait(); });
    expect(orden).toEqual(['save', 'idle']);
    expect(autosave.hasUnsaved()).toBe(false);
  });

  it('beforeunload avisa si hay cambios sin guardar o una escritura en vuelo', () => {
    const enVuelo = { valor: false };
    render(<Formulario isSaving={() => enVuelo.valor} save={vi.fn()} />);

    const evento = () => {
      const e = new Event('beforeunload', { cancelable: true });
      window.dispatchEvent(e);
      return e.defaultPrevented;
    };
    expect(evento()).toBe(false);

    escribir('Año');
    expect(evento()).toBe(true);

    act(() => { autosave.flush(); });
    expect(evento()).toBe(false);

    enVuelo.valor = true;
    expect(evento()).toBe(true);
  });

  it('al desmontar guarda lo que quedó sin guardar', () => {
    const save = vi.fn();
    const { unmount } = render(<Formulario save={save} />);

    escribir('Año');
    unmount();
    expect(save).toHaveBeenCalledWith(['identidad']);
  });
});

describe('useCongeladoMientrasEdita', () => {
  function Congelado({ valor, guardando = false }: { valor: string; guardando?: boolean }) {
    const ref: RefObject<HTMLDivElement> = useRef<HTMLDivElement>(null);
    const visto = useCongeladoMientrasEdita(valor, ref, guardando);
    const [, forzar] = useState(0);
    return (
      <div ref={ref}>
        <textarea aria-label="Texto" />
        <input aria-label="Archivo" type="file" />
        <button onClick={() => forzar((n) => n + 1)} type="button">otro</button>
        <output>{visto}</output>
      </div>
    );
  }

  it('sin foco devuelve siempre el valor más reciente', () => {
    const { rerender } = render(<Congelado valor="a" />);
    rerender(<Congelado valor="b" />);
    expect(screen.getByRole('status')).toHaveTextContent('b');
  });

  it('con un campo de texto con foco no pisa el valor; al salir se actualiza', () => {
    const { rerender } = render(<Congelado valor="a" />);

    fireEvent.focusIn(screen.getByLabelText('Texto'));
    rerender(<Congelado valor="b" />);
    expect(screen.getByRole('status')).toHaveTextContent('a');

    fireEvent.focusOut(screen.getByLabelText('Texto'));
    expect(screen.getByRole('status')).toHaveTextContent('b');
  });

  it('pasar de un campo a otro no descongela', () => {
    const { rerender } = render(<Congelado valor="a" />);
    const texto = screen.getByLabelText('Texto');

    fireEvent.focusIn(texto);
    rerender(<Congelado valor="b" />);
    fireEvent.focusOut(texto, { relatedTarget: texto });
    expect(screen.getByRole('status')).toHaveTextContent('a');
  });

  it('un archivo o un botón con foco no congelan (no se teclea en ellos)', () => {
    const { rerender } = render(<Congelado valor="a" />);

    fireEvent.focusIn(screen.getByLabelText('Archivo'));
    rerender(<Congelado valor="b" />);
    expect(screen.getByRole('status')).toHaveTextContent('b');
  });

  it('mientras hay una escritura en vuelo tampoco pisa, aunque el foco ya se haya ido', () => {
    const { rerender } = render(<Congelado valor="a" />);

    rerender(<Congelado guardando valor="b" />);
    expect(screen.getByRole('status')).toHaveTextContent('a');

    rerender(<Congelado valor="b" />);
    expect(screen.getByRole('status')).toHaveTextContent('b');
  });
});

describe('saveStatusStore', () => {
  beforeEach(() => saveStatusStore.reset());
  afterEach(() => saveStatusStore.reset());

  it('pasa por guardando → guardado; un error de una clave solo se borra con esa clave', () => {
    const { result } = renderHook(() => saveStatusStore.getSnapshot());
    expect(result.current.kind).toBe('idle');

    act(() => saveStatusStore.begin());
    expect(saveStatusStore.getSnapshot().kind).toBe('saving');

    act(() => saveStatusStore.fail('500', 'campo:sinopsis'));
    expect(saveStatusStore.getSnapshot()).toMatchObject({ kind: 'error', message: '500', canRetry: false });

    // Otra escritura distinta sale bien: el error de la sinopsis sigue ahí.
    act(() => saveStatusStore.begin());
    act(() => saveStatusStore.succeed('campo:logo', 1000));
    expect(saveStatusStore.getSnapshot().kind).toBe('error');
    expect(saveStatusStore.hasFailures()).toBe(true);

    // Una escritura posterior de la misma clave lo reemplaza.
    act(() => saveStatusStore.begin());
    act(() => saveStatusStore.succeed('campo:sinopsis', 2000));
    expect(saveStatusStore.getSnapshot()).toMatchObject({ kind: 'saved', savedAt: 2000 });
  });

  it('con dos escrituras en vuelo sigue «guardando» hasta que terminan las dos', () => {
    saveStatusStore.begin();
    saveStatusStore.begin();
    saveStatusStore.succeed('a');
    expect(saveStatusStore.getSnapshot().kind).toBe('saving');
    saveStatusStore.succeed('b');
    expect(saveStatusStore.getSnapshot().kind).toBe('saved');
  });

  it('retry() vuelve a ejecutar cada reintento y el error reaparece si falla otra vez', () => {
    const reintentar = vi.fn(() => {
      saveStatusStore.begin();
      saveStatusStore.fail('otra vez', 'campo:x', reintentar);
    });
    saveStatusStore.begin();
    saveStatusStore.fail('primera', 'campo:x', reintentar);
    expect(saveStatusStore.getSnapshot()).toMatchObject({ kind: 'error', canRetry: true });

    saveStatusStore.retry();
    expect(reintentar).toHaveBeenCalledTimes(1);
    expect(saveStatusStore.getSnapshot()).toMatchObject({ kind: 'error', message: 'otra vez' });
  });
});
