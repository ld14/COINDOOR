import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { App } from '@/App';
import { computeGameStatus } from '@/lib/domain/completeness';
import { contractStatusOf } from '@/lib/contractStatus';
import { games, romCandidates, systems } from '@/mocks/seed';

function renderApp(path = '/', contract?: Parameters<typeof App>[0]['contract']) {
  return render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={[path]}><App contract={contract} /></MemoryRouter></QueryClientProvider>);
}

describe('App shell', () => {
  it('redirige a juegos por defecto', () => {
    renderApp();
    expect(screen.getByRole('heading', { name: 'Juegos' })).toBeInTheDocument();
  });

  it('F2, F3 y F4 navegan', () => {
    renderApp('/juegos');
    fireEvent.keyDown(window, { key: 'F2' });
    expect(screen.getByRole('heading', { name: 'Sistemas / Plataformas' })).toBeInTheDocument();
    fireEvent.keyDown(window, { key: 'F3' });
    expect(screen.getByRole('heading', { name: 'Juegos' })).toBeInTheDocument();
    fireEvent.keyDown(window, { key: 'F4' });
    expect(screen.getByRole('heading', { name: 'Exportar' })).toBeInTheDocument();
  });

  it('F5 navega a configuración', () => {
    renderApp('/juegos');
    fireEvent.keyDown(window, { key: 'F5' });
    expect(screen.getByRole('link', { name: /Configuración/ })).toHaveClass(/active/);
  });
});

describe('Rail', () => {
  it('muestra contadores reales y no el "0 juegos cargados" fijo', async () => {
    renderApp('/juegos');
    const rail = screen.getByRole('navigation', { name: 'Secciones' });
    const pendientes = games.filter((game) => game.id !== 'goldnaxe' && computeGameStatus(game) === 'ready').length;
    await waitFor(() => expect(within(within(rail).getByRole('link', { name: /^Juegos/ })).getByText(String(games.length))).toBeInTheDocument());
    expect(within(within(rail).getByRole('link', { name: /^Sistemas/ })).getByText(String(systems.length))).toBeInTheDocument();
    expect(within(within(rail).getByRole('link', { name: /^Nuevo juego/ })).getByText(String(romCandidates.length))).toBeInTheDocument();
    await waitFor(() => expect(within(within(rail).getByRole('link', { name: /^Exportar/ })).getByText(String(pendientes))).toBeInTheDocument());
    expect(screen.queryByText(/0 juegos cargados/)).not.toBeInTheDocument();
  });

  it('marca activo un solo ítem en /juegos/nuevo', () => {
    renderApp('/juegos/nuevo');
    expect(screen.getByRole('link', { name: /^Nuevo juego/ })).toHaveClass(/active/);
    expect(screen.getByRole('link', { name: /^Juegos/ })).not.toHaveClass(/active/);
  });
});

describe('Búsqueda global', () => {
  it('"/" enfoca la búsqueda', () => {
    renderApp('/sistemas');
    const search = screen.getByRole('searchbox', { name: /Buscar juego/ });
    expect(search).not.toHaveFocus();
    fireEvent.keyDown(window, { key: '/' });
    expect(search).toHaveFocus();
  });

  it('"/" no interfiere cuando se escribe en un campo', async () => {
    const user = userEvent.setup();
    renderApp('/sistemas');
    const search = screen.getByRole('searchbox', { name: /Buscar juego/ });
    await user.click(search);
    await user.keyboard('a/b');
    expect(search).toHaveValue('a/b');
    expect(search).toHaveFocus();
  });

  it('"/" con Ctrl queda libre', () => {
    renderApp('/sistemas');
    fireEvent.keyDown(window, { key: '/', ctrlKey: true });
    expect(screen.getByRole('searchbox', { name: /Buscar juego/ })).not.toHaveFocus();
  });

  it('Enter lleva a /juegos filtrado por la búsqueda', async () => {
    const user = userEvent.setup();
    renderApp('/sistemas');
    await user.type(screen.getByRole('searchbox', { name: /Buscar juego/ }), 'sonic{Enter}');
    expect(await screen.findByRole('heading', { name: 'Juegos' })).toBeInTheDocument();
  });
});

describe('Contrato ATTRACT', () => {
  it('sin problemas: indicador en topbar y statusbar, sin banner', () => {
    renderApp('/sistemas');
    expect(screen.getAllByTestId('contract-badge')).toHaveLength(2);
    expect(screen.getAllByText(/Contrato ATTRACT v1/)).toHaveLength(2);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('con un problema: aparece el banner', () => {
    renderApp('/sistemas', contractStatusOf({ version: 'roto' }));
    expect(screen.getByRole('alert')).toHaveTextContent(/versión del contrato/);
  });

  it('contractStatusOf detecta un contrato incompleto', () => {
    expect(contractStatusOf({ version: 'attract-2', metadataFields: { required: [] }, assets: {} }).ok).toBe(false);
    expect(contractStatusOf({ version: 'attract-2', metadataFields: { required: ['game'] }, assets: {} })).toMatchObject({ ok: true, label: 'Contrato ATTRACT v2' });
  });
});
