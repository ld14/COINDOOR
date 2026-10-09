import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ActionBar, CheckTile, FilterChips, FilterTabs, NextPendingCard, StepNav } from '@/components/dos/nav';

describe('StepNav', () => {
  const items = [
    { id: 'a', label: 'Identidad', status: 'complete' as const },
    { id: 'b', label: 'Objetivo', status: 'blocking' as const, hint: 'Objetivo obligatorio' },
    { id: 'c', label: 'Imágenes', status: 'review' as const, hint: '5 sugeridos' },
    { id: 'd', label: 'Texto' },
  ];

  it('muestra ✓, !, número y estado accesible según el status', () => {
    render(<StepNav activeId="d" items={items} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveAttribute('data-status', 'complete');
    expect(buttons[0]).toHaveTextContent('✓');
    expect(buttons[1]).toHaveTextContent('!');
    expect(buttons[1]).toHaveTextContent('Objetivo obligatorio');
    expect(buttons[1]).toHaveTextContent('bloquea la exportación');
    expect(buttons[2]).toHaveTextContent('3');
    expect(buttons[2]).toHaveTextContent('5 sugeridos');
    expect(buttons[3]).toHaveTextContent('4');
    expect(buttons[3]).toHaveAttribute('aria-current', 'step');
    expect(buttons[0]).not.toHaveAttribute('aria-current');
  });

  it('llama onSelect con el id y es operable por teclado', () => {
    const onSelect = vi.fn();
    render(<StepNav items={items} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole('button', { name: /Objetivo/ }));
    expect(onSelect).toHaveBeenCalledWith('b');
    const third = screen.getByRole('button', { name: /Imágenes/ });
    third.focus();
    expect(third).toHaveFocus();
    fireEvent.click(third);
    expect(onSelect).toHaveBeenLastCalledWith('c');
  });
});

describe('CheckTile', () => {
  it('es un checkbox controlado y avisa el cambio', () => {
    const onChange = vi.fn();
    const { rerender } = render(<CheckTile checked={false} label="Video" meta="12 MB" onChange={onChange} />);
    const box = screen.getByRole('checkbox', { name: /Video/ });
    expect(box).not.toBeChecked();
    expect(screen.getByText('12 MB')).toBeInTheDocument();
    fireEvent.click(box);
    expect(onChange).toHaveBeenCalledWith(true);
    rerender(<CheckTile checked label="Video" meta="12 MB" onChange={onChange} />);
    expect(screen.getByRole('checkbox')).toBeChecked();
  });

  it('deshabilitado muestra el motivo, lo asocia y no dispara onChange', () => {
    const onChange = vi.fn();
    render(<CheckTile checked={false} disabled disabledReason="no hay trucos" label="Trucos" meta="3 KB" onChange={onChange} />);
    const box = screen.getByRole('checkbox');
    expect(box).toBeDisabled();
    expect(box).toHaveAccessibleDescription('no hay trucos');
    expect(screen.queryByText('3 KB')).not.toBeInTheDocument();
    fireEvent.click(box);
    expect(onChange).not.toHaveBeenCalled();
  });
});

describe('FilterTabs', () => {
  const tabs = [
    { id: 'all', label: 'Todos', count: 128 },
    { id: 'wip', label: 'En carga', count: 7 },
    { id: 'ok', label: 'Exportados', count: 0 },
  ];

  it('usa role=tablist, contadores y roving tabindex', () => {
    render(<FilterTabs items={tabs} onChange={() => undefined} value="wip" />);
    expect(screen.getByRole('tablist')).toBeInTheDocument();
    const selected = screen.getByRole('tab', { name: /En carga/ });
    expect(selected).toHaveAttribute('aria-selected', 'true');
    expect(selected).toHaveAttribute('tabindex', '0');
    expect(screen.getByRole('tab', { name: /Todos/ })).toHaveAttribute('tabindex', '-1');
    expect(within(selected).getByText('7')).toBeInTheDocument();
    expect(within(screen.getByRole('tab', { name: /Exportados/ })).getByText('0')).toBeInTheDocument();
  });

  it('navega con flechas, Home y End (con vuelta)', () => {
    const onChange = vi.fn();
    render(<FilterTabs items={tabs} onChange={onChange} value="all" />);
    const first = screen.getByRole('tab', { name: /Todos/ });
    fireEvent.keyDown(first, { key: 'ArrowRight' });
    expect(onChange).toHaveBeenLastCalledWith('wip');
    fireEvent.keyDown(first, { key: 'ArrowLeft' });
    expect(onChange).toHaveBeenLastCalledWith('ok');
    fireEvent.keyDown(first, { key: 'End' });
    expect(onChange).toHaveBeenLastCalledWith('ok');
    fireEvent.keyDown(first, { key: 'Home' });
    expect(onChange).toHaveBeenLastCalledWith('all');
  });
});

describe('FilterChips', () => {
  const chips = [
    { id: 'arcade', label: 'Arcade', count: 90 },
    { id: 'dos', label: 'MS-DOS', count: 38 },
  ];

  it('multi: alterna chips y muestra contadores', () => {
    const onChange = vi.fn();
    render(<FilterChips items={chips} onChange={onChange} value={['arcade']} />);
    expect(screen.getByRole('button', { name: /Arcade/ })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /MS-DOS/ })).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByText('38')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /MS-DOS/ }));
    expect(onChange).toHaveBeenLastCalledWith(['arcade', 'dos']);
    fireEvent.click(screen.getByRole('button', { name: /Arcade/ }));
    expect(onChange).toHaveBeenLastCalledWith([]);
  });

  it('single: reemplaza la selección y permite quitarla', () => {
    const onChange = vi.fn();
    render(<FilterChips items={chips} mode="single" onChange={onChange} value={['arcade']} />);
    fireEvent.click(screen.getByRole('button', { name: /MS-DOS/ }));
    expect(onChange).toHaveBeenLastCalledWith(['dos']);
    fireEvent.click(screen.getByRole('button', { name: /Arcade/ }));
    expect(onChange).toHaveBeenLastCalledWith([]);
  });
});

describe('NextPendingCard', () => {
  const items = [
    { id: 'r1', label: 'Sinopsis para revisar', severity: 'review' as const, step: 5 },
    { id: 'q1', label: 'Objetivo obligatorio', severity: 'required' as const, step: 2 },
    { id: 'q2', label: 'Carátula obligatoria', severity: 'required' as const, step: 3 },
  ];

  it('ordena obligatorios primero y ofrece Ir → N con el primero', () => {
    const onGo = vi.fn();
    render(<NextPendingCard items={items} onGo={onGo} />);
    fireEvent.click(screen.getByRole('button', { name: /Ir → 2/ }));
    expect(onGo).toHaveBeenCalledWith(items[1]);
    const queue = within(screen.getByRole('list', { name: 'Cola de pendientes' })).getAllByRole('listitem');
    expect(queue.map((li) => li.textContent)).toEqual(['Carátula obligatoria', 'Sinopsis para revisar']);
    expect(queue[0]).toHaveAttribute('data-severity', 'required');
    expect(queue[1]).toHaveAttribute('data-severity', 'review');
  });

  it('el atajo N va al siguiente, salvo si se está escribiendo', () => {
    const onGo = vi.fn();
    render(<><input aria-label="campo" /><NextPendingCard items={items} onGo={onGo} /></>);
    fireEvent.keyDown(screen.getByLabelText('campo'), { key: 'n' });
    expect(onGo).not.toHaveBeenCalled();
    fireEvent.keyDown(document.body, { key: 'n' });
    expect(onGo).toHaveBeenCalledTimes(1);
    expect(onGo).toHaveBeenCalledWith(items[1]);
  });

  it('sin pendientes avisa que está todo al día', () => {
    render(<NextPendingCard items={[]} onGo={() => undefined} />);
    expect(screen.getByText(/Todo al día/)).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});

describe('ActionBar', () => {
  it('anuncia el progreso con aria-live y muestra atajos como kbd', () => {
    const { container } = render(
      <ActionBar percent={60} requiredCount={3} reviewCount={6} shortcuts={[{ keys: 'Enter', label: 'aceptar sugerencia' }, { keys: 'N', label: 'siguiente pendiente' }]} />,
    );
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveTextContent('60% · 3 obligatorios · 6 para revisar');
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '60');
    expect(container.querySelectorAll('kbd')).toHaveLength(2);
  });

  it('Exportar bloqueado muestra el motivo y no dispara onExport', () => {
    const onExport = vi.fn();
    const onSaveDraft = vi.fn();
    render(<ActionBar exportDisabledReason="faltan 3" onExport={onExport} onSaveDraft={onSaveDraft} percent={40} />);
    const exportButton = screen.getByRole('button', { name: /Exportar \(faltan 3\)/ });
    expect(exportButton).toHaveAttribute('aria-disabled', 'true');
    fireEvent.click(exportButton);
    expect(onExport).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Guardar borrador y salir' }));
    expect(onSaveDraft).toHaveBeenCalledTimes(1);
  });

  it('Exportar habilitado dispara onExport', () => {
    const onExport = vi.fn();
    render(<ActionBar onExport={onExport} percent={100} />);
    const button = screen.getByRole('button', { name: /Exportar/ });
    expect(button).not.toHaveAttribute('aria-disabled');
    fireEvent.click(button);
    expect(onExport).toHaveBeenCalledTimes(1);
  });
});
