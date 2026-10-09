import { fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { ChoiceCards, Dropzone, InlineSuggestion, ListEditor, NumberStepper, SegmentedControl, itemsALineas, lineasAItems } from '@/components/dos/entrada';

const opciones = [
  { value: 'a', label: 'Alfa' },
  { value: 'b', label: 'Beta', disabled: true },
  { value: 'c', label: 'Gamma' },
];

describe('SegmentedControl', () => {
  it('selecciona por clic y marca la activa', () => {
    const onChange = vi.fn();
    render(<SegmentedControl ariaLabel="Modo" onChange={onChange} options={opciones} value="a" />);
    expect(screen.getByRole('radiogroup', { name: 'Modo' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Alfa' })).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(screen.getByRole('radio', { name: 'Gamma' }));
    expect(onChange).toHaveBeenCalledWith('c');
  });

  it('la opción imposible está disabled y no dispara', () => {
    const onChange = vi.fn();
    render(<SegmentedControl ariaLabel="Modo" onChange={onChange} options={opciones} value="a" />);
    const beta = screen.getByRole('radio', { name: 'Beta' });
    expect(beta).toBeDisabled();
    fireEvent.click(beta);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('las flechas saltean las opciones deshabilitadas', () => {
    const onChange = vi.fn();
    render(<SegmentedControl ariaLabel="Modo" onChange={onChange} options={opciones} value="a" />);
    fireEvent.keyDown(screen.getByRole('radio', { name: 'Alfa' }), { key: 'ArrowRight' });
    expect(onChange).toHaveBeenCalledWith('c');
  });

  it('deshabilitado entero no responde', () => {
    const onChange = vi.fn();
    render(<SegmentedControl ariaLabel="Modo" disabled onChange={onChange} options={opciones} value="a" />);
    fireEvent.click(screen.getByRole('radio', { name: 'Gamma' }));
    expect(onChange).not.toHaveBeenCalled();
  });
});

describe('ChoiceCards', () => {
  const cartas = [
    { value: 'x', label: 'Arcade', subtitle: 'ROM de MAME' },
    { value: 'y', label: 'Consola', subtitle: 'Cartucho', recommended: 'ArcadeDB' },
    { value: 'z', label: 'PC', disabled: true },
  ];

  it('muestra subtítulo y "recomendado por…"', () => {
    render(<ChoiceCards ariaLabel="Formato" onChange={() => undefined} options={cartas} value="x" />);
    expect(screen.getByText('ROM de MAME')).toBeInTheDocument();
    expect(screen.getByText('recomendado por ArcadeDB')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /^Arcade/ })).toHaveAttribute('aria-checked', 'true');
  });

  it('selecciona por clic y teclado, y respeta disabled', () => {
    const onChange = vi.fn();
    render(<ChoiceCards ariaLabel="Formato" onChange={onChange} options={cartas} value="x" />);
    fireEvent.click(screen.getByRole('radio', { name: /Consola/ }));
    expect(onChange).toHaveBeenLastCalledWith('y');
    fireEvent.keyDown(screen.getByRole('radio', { name: /Consola/ }), { key: 'ArrowRight' });
    expect(onChange).toHaveBeenLastCalledWith('x');
    expect(screen.getByRole('radio', { name: /PC/ })).toBeDisabled();
  });
});

describe('NumberStepper', () => {
  it('incrementa, decrementa y respeta límites', () => {
    const onChange = vi.fn();
    const { rerender } = render(<NumberStepper ariaLabel="Jugadores" max={4} min={1} onChange={onChange} value={2} />);
    const spin = screen.getByRole('spinbutton', { name: 'Jugadores' });
    expect(spin).toHaveAttribute('aria-valuenow', '2');
    fireEvent.click(screen.getByRole('button', { name: 'Aumentar' }));
    expect(onChange).toHaveBeenLastCalledWith(3);
    fireEvent.keyDown(spin, { key: 'ArrowDown' });
    expect(onChange).toHaveBeenLastCalledWith(1);
    rerender(<NumberStepper ariaLabel="Jugadores" max={4} min={1} onChange={onChange} value={1} />);
    expect(screen.getByRole('button', { name: 'Disminuir' })).toBeDisabled();
    rerender(<NumberStepper ariaLabel="Jugadores" max={4} min={1} onChange={onChange} value={4} />);
    expect(screen.getByRole('button', { name: 'Aumentar' })).toBeDisabled();
  });

  it('deshabilitado ignora teclado', () => {
    const onChange = vi.fn();
    render(<NumberStepper ariaLabel="Jugadores" disabled onChange={onChange} value={2} />);
    fireEvent.keyDown(screen.getByRole('spinbutton'), { key: 'ArrowUp' });
    expect(onChange).not.toHaveBeenCalled();
  });
});

describe('ListEditor', () => {
  it('serializa líneas ⇄ ítems', () => {
    expect(lineasAItems('uno\r\n  dos \n\n tres')).toEqual(['uno', 'dos', 'tres']);
    expect(itemsALineas(['uno', 'dos'])).toBe('uno\ndos');
    expect(lineasAItems(itemsALineas(['a', 'b']))).toEqual(['a', 'b']);
    expect(lineasAItems('')).toEqual([]);
  });

  function Controlado({ inicial, onItems }: { inicial: string[]; onItems: (i: string[]) => void }) {
    const [items, setItems] = useState(inicial);
    return <ListEditor ariaLabel="Pasos" items={items} onChange={(next) => { setItems(next); onItems(next); }} />;
  }

  it('Enter agrega una fila siguiente con foco y el texto emite array', () => {
    const onItems = vi.fn();
    render(<Controlado inicial={['uno']} onItems={onItems} />);
    fireEvent.keyDown(screen.getByLabelText('Paso 1'), { key: 'Enter' });
    const segundo = screen.getByLabelText('Paso 2');
    expect(segundo).toHaveFocus();
    fireEvent.change(segundo, { target: { value: 'dos' } });
    expect(onItems).toHaveBeenLastCalledWith(['uno', 'dos']);
  });

  it('"+ Agregar paso" agrega y ✕ quita', () => {
    const onItems = vi.fn();
    render(<Controlado inicial={['uno', 'dos']} onItems={onItems} />);
    fireEvent.click(screen.getByRole('button', { name: '+ Agregar paso' }));
    expect(screen.getByLabelText('Paso 3')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Quitar paso 1' }));
    expect(onItems).toHaveBeenLastCalledWith(['dos']);
  });

  it('reordena con teclado desde el asa', () => {
    const onItems = vi.fn();
    render(<Controlado inicial={['uno', 'dos', 'tres']} onItems={onItems} />);
    fireEvent.keyDown(screen.getByRole('button', { name: 'Mover paso 1' }), { key: 'ArrowDown' });
    expect(onItems).toHaveBeenLastCalledWith(['dos', 'uno', 'tres']);
    expect(screen.getByLabelText('Paso 2')).toHaveValue('uno');
  });

  it('reordena por arrastre', () => {
    const onItems = vi.fn();
    render(<Controlado inicial={['uno', 'dos', 'tres']} onItems={onItems} />);
    const dataTransfer = { effectAllowed: '', setData: vi.fn() };
    fireEvent.dragStart(screen.getByRole('button', { name: 'Mover paso 1' }), { dataTransfer });
    const filaTres = screen.getByLabelText('Paso 3').closest('li') as HTMLElement;
    fireEvent.dragOver(filaTres, { dataTransfer });
    fireEvent.drop(filaTres, { dataTransfer });
    expect(onItems).toHaveBeenLastCalledWith(['dos', 'tres', 'uno']);
  });

  it('deshabilitado bloquea los controles', () => {
    render(<ListEditor ariaLabel="Pasos" disabled items={['uno']} onChange={() => undefined} />);
    expect(screen.getByLabelText('Paso 1')).toBeDisabled();
    expect(screen.getByRole('button', { name: '+ Agregar paso' })).toBeDisabled();
  });
});

describe('Dropzone', () => {
  const imagen = () => new File(['x'], 'cover.png', { type: 'image/png' });

  it('entrega el archivo soltado', () => {
    const onFile = vi.fn();
    render(<Dropzone accept="image/*" onFile={onFile} />);
    expect(screen.getByText('Soltá una imagen acá o pegala con Ctrl+V')).toBeInTheDocument();
    const file = imagen();
    fireEvent.drop(screen.getByRole('button', { name: /Soltá una imagen/ }), { dataTransfer: { files: [file] } });
    expect(onFile).toHaveBeenCalledWith(file);
  });

  it('entrega el archivo pegado', () => {
    const onFile = vi.fn();
    render(<Dropzone accept="image/*" onFile={onFile} />);
    const file = imagen();
    fireEvent.paste(screen.getByRole('button', { name: /Soltá una imagen/ }), { clipboardData: { files: [file] } });
    expect(onFile).toHaveBeenCalledWith(file);
  });

  it('entrega el archivo elegido por clic', () => {
    const onFile = vi.fn();
    render(<Dropzone accept="image/*" onFile={onFile} />);
    const file = imagen();
    fireEvent.change(screen.getByTestId('dropzone-input'), { target: { files: [file] } });
    expect(onFile).toHaveBeenCalledWith(file);
  });

  it('con multiple entrega todos los archivos válidos juntos por onFiles', () => {
    const onFiles = vi.fn();
    const onFile = vi.fn();
    render(<Dropzone accept=".pdf" multiple onFile={onFile} onFiles={onFiles} />);
    const a = new File(['x'], 'a.pdf', { type: 'application/pdf' });
    const b = new File(['y'], 'b.pdf', { type: 'application/pdf' });
    const txt = new File(['z'], 'c.txt', { type: 'text/plain' });
    fireEvent.drop(screen.getByRole('button'), { dataTransfer: { files: [a, b, txt] } });
    expect(onFiles).toHaveBeenCalledWith([a, b]);
    expect(onFile).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByTestId('dropzone-input')).toHaveAttribute('multiple');
  });

  it('sin multiple sigue entregando un solo archivo', () => {
    const onFile = vi.fn();
    render(<Dropzone accept=".pdf" onFile={onFile} />);
    const a = new File(['x'], 'a.pdf', { type: 'application/pdf' });
    const b = new File(['y'], 'b.pdf', { type: 'application/pdf' });
    fireEvent.drop(screen.getByRole('button'), { dataTransfer: { files: [a, b] } });
    expect(onFile).toHaveBeenCalledTimes(1);
    expect(onFile).toHaveBeenCalledWith(a);
  });

  it('rechaza tipos no admitidos', () => {
    const onFile = vi.fn();
    render(<Dropzone accept="image/*" onFile={onFile} />);
    const txt = new File(['x'], 'a.txt', { type: 'text/plain' });
    fireEvent.drop(screen.getByRole('button', { name: /Soltá una imagen/ }), { dataTransfer: { files: [txt] } });
    expect(onFile).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('acción secundaria y estado de progreso con Cancelar', () => {
    const onSecondary = vi.fn();
    const onCancel = vi.fn();
    const { rerender } = render(<Dropzone onFile={() => undefined} secondaryAction={{ label: 'Buscar en ArcadeDB', onClick: onSecondary }} />);
    fireEvent.click(screen.getByRole('button', { name: 'Buscar en ArcadeDB' }));
    expect(onSecondary).toHaveBeenCalled();
    rerender(<Dropzone onCancel={onCancel} onFile={() => undefined} progress={40} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '40');
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(onCancel).toHaveBeenCalled();
  });

  it('deshabilitada ignora drop y paste', () => {
    const onFile = vi.fn();
    render(<Dropzone disabled onFile={onFile} />);
    const zona = screen.getByRole('button', { name: /Soltá una imagen/ });
    expect(zona).toHaveAttribute('aria-disabled', 'true');
    fireEvent.drop(zona, { dataTransfer: { files: [imagen()] } });
    fireEvent.paste(zona, { clipboardData: { files: [imagen()] } });
    expect(onFile).not.toHaveBeenCalled();
  });
});

describe('InlineSuggestion', () => {
  it('muestra la fuente y el valor, y dispara Usar / Ignorar', () => {
    const onUse = vi.fn();
    const onIgnore = vi.fn();
    render(<InlineSuggestion onIgnore={onIgnore} onUse={onUse} source="ArcadeDB" value="Golden Axe" />);
    expect(screen.getByText(/ArcadeDB sugiere:/)).toBeInTheDocument();
    expect(screen.getByText('Golden Axe')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Usar' }));
    fireEvent.click(screen.getByRole('button', { name: 'Ignorar' }));
    expect(onUse).toHaveBeenCalled();
    expect(onIgnore).toHaveBeenCalled();
  });
});
