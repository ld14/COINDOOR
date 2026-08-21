import { fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { App } from '@/App';

function renderApp(path = '/') {
  return render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>);
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
    expect(screen.getByText('EXPORTAR')).toBeInTheDocument();
  });
});
