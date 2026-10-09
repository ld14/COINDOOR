import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Card } from '@/components/dos/Card';
import { DosButton } from '@/components/dos/DosButton';
import { DosInput } from '@/components/dos/DosInput';
import { DosSelect } from '@/components/dos/DosSelect';
import { DosTextarea } from '@/components/dos/DosTextarea';
import { FieldTag } from '@/components/dos/FieldTag';
import { Modal } from '@/components/dos/Modal';
import { OriginChip } from '@/components/dos/OriginChip';
import { Panel } from '@/components/dos/Panel';
import { ProgressBar } from '@/components/dos/ProgressBar';
import { StatusBadge } from '@/components/dos/StatusBadge';

describe('OriginChip', () => {
  it('mapea estado y fuente a la etiqueta (DESIGN_SPEC §3)', () => {
    render(<>
      <OriginChip status="empty" />
      <OriginChip status="suggested" />
      <OriginChip source="arcadedb" status="manual" />
      <OriginChip source="screenscraper" status="manual" />
      <OriginChip source="manual" status="manual" />
      <OriginChip status="manual" />
    </>);
    expect(screen.getByText('○ Vacío')).toBeInTheDocument();
    expect(screen.getByText('● Sugerido · sin revisar')).toBeInTheDocument();
    expect(screen.getByText('● ArcadeDB')).toBeInTheDocument();
    expect(screen.getByText('● ScreenScraper')).toBeInTheDocument();
    expect(screen.getAllByText('● Manual')).toHaveLength(2);
  });

  it('muestra OBLIGATORIO solo en vacíos que lo piden', () => {
    const { rerender } = render(<OriginChip required status="empty" />);
    expect(screen.getByText('OBLIGATORIO')).toBeInTheDocument();
    rerender(<OriginChip required status="manual" />);
    expect(screen.queryByText('OBLIGATORIO')).not.toBeInTheDocument();
  });

  it('FieldTag delega en OriginChip', () => {
    render(<FieldTag source="mame" status="manual" />);
    expect(screen.getByText('● MAME')).toBeInTheDocument();
  });
});

describe('StatusBadge', () => {
  it('cada estado lleva ícono y texto', () => {
    render(<><StatusBadge status="incomplete" /><StatusBadge status="ready" /><StatusBadge status="error" /><StatusBadge status="exported" /></>);
    expect(screen.getByText('● En carga')).toBeInTheDocument();
    expect(screen.getByText('✓ Listo')).toBeInTheDocument();
    expect(screen.getByText('✕ Con errores')).toBeInTheDocument();
    expect(screen.getByText('⇪ Exportado')).toBeInTheDocument();
  });
});

describe('inputs con invalid', () => {
  it('DosInput muestra el mensaje y lo enlaza con aria-describedby', () => {
    render(<DosInput aria-label="Año" errorMessage="Año inválido" />);
    const input = screen.getByLabelText('Año');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    const message = screen.getByText('Año inválido');
    expect(input.getAttribute('aria-describedby')).toContain(message.id);
  });

  it('invalid sin mensaje marca aria-invalid y no agrega nodos', () => {
    const { container } = render(<DosSelect aria-label="Sistema" invalid><option>a</option></DosSelect>);
    expect(screen.getByLabelText('Sistema')).toHaveAttribute('aria-invalid', 'true');
    expect(container.children).toHaveLength(1);
  });

  it('sin invalid no hay aria-invalid y se respeta aria-describedby propio', () => {
    render(<DosTextarea aria-describedby="ayuda" aria-label="Sinopsis" />);
    const area = screen.getByLabelText('Sinopsis');
    expect(area).not.toHaveAttribute('aria-invalid');
    expect(area).toHaveAttribute('aria-describedby', 'ayuda');
  });
});

describe('DosButton', () => {
  it('disabledReason aparece como title solo si está deshabilitado', () => {
    const { rerender } = render(<DosButton disabled disabledReason="Faltan 3">Exportar</DosButton>);
    expect(screen.getByRole('button', { name: 'Exportar' })).toHaveAttribute('title', 'Faltan 3');
    rerender(<DosButton disabledReason="Faltan 3">Exportar</DosButton>);
    expect(screen.getByRole('button', { name: 'Exportar' })).not.toHaveAttribute('title');
  });

  it('acepta las variantes nuevas y las viejas', () => {
    render(<><DosButton variant="secondary">A</DosButton><DosButton size="sm" variant="danger">B</DosButton><DosButton variant="danger-small">C</DosButton></>);
    expect(screen.getAllByRole('button')).toHaveLength(3);
  });
});

describe('ProgressBar', () => {
  it('expone role progressbar con aria-valuenow acotado', () => {
    const { rerender } = render(<ProgressBar value={42} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '42');
    rerender(<ProgressBar value={500} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
  });
});

describe('Card y Panel', () => {
  it('Card con título renderiza número, título, hint y acciones', () => {
    render(<Card actions={<button type="button">Acción</button>} hint="ayuda" number={2} title="Identidad">contenido</Card>);
    expect(screen.getByRole('heading', { name: 'Identidad' })).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('ayuda')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Acción' })).toBeInTheDocument();
  });

  it('Panel sin título no agrega encabezado y conserva className', () => {
    render(<Panel className="x" data-testid="p">hola</Panel>);
    expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    expect(screen.getByTestId('p')).toHaveClass('x');
  });
});

describe('Modal', () => {
  it('Esc cierra y el click afuera también; adentro no', () => {
    const onClose = vi.fn();
    render(<Modal onClose={onClose} open title="Prueba"><button type="button">Dentro</button></Modal>);
    expect(screen.getByRole('dialog', { name: 'Prueba' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Dentro' }));
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.mouseDown(screen.getByRole('button', { name: 'Dentro' }));
    fireEvent.click(screen.getByRole('presentation'));
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.mouseDown(screen.getByRole('presentation'));
    fireEvent.click(screen.getByRole('presentation'));
    expect(onClose).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it('el botón Cerrar cierra', () => {
    const onClose = vi.fn();
    render(<Modal onClose={onClose} open title="Prueba" />);
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
    expect(onClose).toHaveBeenCalled();
  });
});
