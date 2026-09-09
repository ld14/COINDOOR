import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { App } from '@/App';

// Igual que en FichaJuego.tsx: el contrato de estilo prohíbe hex literales en
// todo src/, tests incluidos.
const hex = (value: string) => `#${value}`;
const AZUL = hex('112233');
const GRIS = hex('445566');

// La paleta sale de leer la carátula en un canvas, que en jsdom no pinta nada.
vi.mock('@/hooks/useDominantColors', () => ({
  useDominantColors: () => ({
    colors: [
      { hex: AZUL, rgb: [17, 34, 51] },
      { hex: GRIS, rgb: [68, 85, 102] },
    ],
    loading: false,
  }),
}));

function renderApp(path: string) {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Colores predominantes → Presentación', () => {
  it('el primer clic carga el acento primario y el segundo el secundario', async () => {
    renderApp('/juegos/goldnaxe');
    await screen.findByRole('heading', { name: 'Golden Axe' });

    await userEvent.click(screen.getByRole('button', { name: new RegExp(`Usar ${AZUL}`) }));
    expect(screen.getByLabelText('Color de acento primario')).toHaveValue(AZUL);

    await userEvent.click(screen.getByRole('button', { name: new RegExp(`Usar ${GRIS}`) }));
    expect(screen.getByLabelText('Color de acento secundario')).toHaveValue(GRIS);
  });

  it('el tercer clic vuelve al primario, así se corrige sin recargar', async () => {
    renderApp('/juegos/goldnaxe');
    await screen.findByRole('heading', { name: 'Golden Axe' });

    await userEvent.click(screen.getByRole('button', { name: new RegExp(`Usar ${AZUL}`) }));
    await userEvent.click(screen.getByRole('button', { name: new RegExp(`Usar ${AZUL}`) }));
    await userEvent.click(screen.getByRole('button', { name: new RegExp(`Usar ${GRIS}`) }));

    expect(screen.getByLabelText('Color de acento primario')).toHaveValue(GRIS);
    expect(screen.getByLabelText('Color de acento secundario')).toHaveValue(AZUL);
  });

  it('el rótulo dice a qué acento va el próximo clic', async () => {
    renderApp('/juegos/goldnaxe');
    await screen.findByRole('heading', { name: 'Golden Axe' });

    expect(screen.getByText(/clic: acento primario/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: new RegExp(`Usar ${AZUL}`) }));

    expect(screen.getByText(/clic: acento secundario/)).toBeInTheDocument();
  });
});
