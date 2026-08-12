import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { Banner, DosButton, DosInput, DosSelect, DosTextarea, FieldTag, MenuBar, Modal, Panel, ProgressBar, SectionHeader, Spinner, StatusBadge, StatusBar, SunkenBox } from '@/components/dos';

describe('DOS primitives', () => {
  it('renderizan sin props opcionales', () => {
    render(<MemoryRouter><Banner /><DosButton /><DosInput /><DosSelect /><DosTextarea /><FieldTag /><MenuBar /><Panel /><ProgressBar /><SectionHeader /><Spinner /><StatusBadge /><StatusBar /><SunkenBox /></MemoryRouter>);
    expect(screen.getByText('COINDOOR')).toBeInTheDocument();
  });

  it('no dispara onClick si DosButton está deshabilitado', () => {
    const onClick = vi.fn();
    render(<DosButton disabled onClick={onClick}>No disponible</DosButton>);
    fireEvent.click(screen.getByRole('button', { name: 'No disponible' }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('Modal cierra con Esc y devuelve foco', () => {
    const onClose = vi.fn();
    render(<><button type="button">Abrir</button><Modal onClose={onClose} open title="Prueba"><button type="button">Dentro</button></Modal></>);
    const opener = screen.getByRole('button', { name: 'Abrir' });
    opener.focus();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('Modal atrapa foco', () => {
    render(<Modal onClose={() => undefined} open title="Prueba"><button type="button">Primero</button><button type="button">Último</button></Modal>);
    const close = screen.getByRole('button', { name: 'Cerrar' });
    const last = screen.getByRole('button', { name: 'Último' });
    close.focus();
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(last).toHaveFocus();
  });
});
