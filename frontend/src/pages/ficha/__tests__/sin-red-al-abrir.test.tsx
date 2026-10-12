import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { App } from '@/App';

function renderApp(path: string) {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

type LlamadaFetch = [RequestInfo | URL, RequestInit | undefined];
const busquedas = () =>
  (vi.mocked(fetch).mock.calls as LlamadaFetch[]).filter(([url, init]) => (init?.method ?? 'GET') === 'POST' && String(url).includes('/suggestions'));

// tech-stack §Convenciones y ADR-0015: todo lo que sale a la red es a pedido; nada corre al abrir una ficha.
describe('La ficha no busca sugerencias por su cuenta', () => {
  it('abrir una ficha con una imagen sugerida no dispara ninguna búsqueda', async () => {
    renderApp('/juegos/sonic');
    await screen.findByRole('heading', { name: 'Sonic The Hedgehog' });
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(busquedas()).toHaveLength(0);
  });

  it('la búsqueda sale recién cuando la persona la pide con ↻', async () => {
    renderApp('/juegos/sonic');
    await screen.findByRole('heading', { name: 'Sonic The Hedgehog' });
    expect(busquedas()).toHaveLength(0);

    await userEvent.click(screen.getByRole('button', { name: 'Sugerir Logo' }));
    await vi.waitFor(() => expect(busquedas().length).toBeGreaterThan(0));
  });
});
