import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
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
const llamadasA = (metodo: string, fragmento: string) =>
  (vi.mocked(fetch).mock.calls as LlamadaFetch[]).filter(([url, init]) => (init?.method ?? 'GET') === metodo && String(url).includes(fragmento));

describe('Ficha · Identidad', () => {
  it('es una Card numerada sin botón Guardar, con ↻ por campo y Sugerir todo', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    const identidad = document.getElementById('seccion-identidad')!;
    expect(within(identidad).getByRole('heading', { name: 'Identidad' })).toBeInTheDocument();
    expect(within(identidad).queryByRole('button', { name: 'Guardar identidad' })).not.toBeInTheDocument();
    expect(within(identidad).getByRole('button', { name: '↻ Sugerir todo' })).toBeInTheDocument();
    const sugerirAnio = within(identidad).getByRole('button', { name: 'Sugerir Año' });
    expect(sugerirAnio).toHaveAttribute('title', 'Sugerir desde ArcadeDB');
  });

  it('un obligatorio vacío se marca como bloqueante', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    const identidad = document.getElementById('seccion-identidad')!;
    expect(within(identidad).getAllByText('✕ Bloquea la exportación').length).toBeGreaterThan(0);
    expect(within(identidad).getAllByText('OBLIGATORIO').length).toBeGreaterThan(0);
    expect(within(identidad).getByLabelText('Año')).toHaveAttribute('aria-invalid', 'true');
  });

  it('Formato usa ChoiceCards y Jugadores un NumberStepper', async () => {
    renderApp('/juegos/goldnaxe');
    await screen.findByRole('heading', { name: 'Golden Axe' });

    const formato = screen.getByRole('radiogroup', { name: 'Formato' });
    expect(within(formato).getByRole('radio', { name: /Arcade/ })).toHaveAttribute('aria-checked', 'true');
    // "1-2" no cabe en un stepper: sigue siendo texto.
    expect(screen.queryByRole('spinbutton', { name: 'Jugadores' })).not.toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: 'Jugadores' })).toBeInTheDocument();
  });

  it('Jugadores vacío o numérico se edita con el NumberStepper', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    const stepper = screen.getByRole('spinbutton', { name: 'Jugadores' });
    await userEvent.click(within(stepper.parentElement!).getByRole('button', { name: 'Aumentar' }));
    expect(stepper).toHaveAttribute('aria-valuenow', '1');
  });

  it('editar guarda solo, sin botón, y escribe solo lo que cambió', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    await userEvent.type(screen.getByLabelText('Año'), '1996');
    expect(llamadasA('PATCH', '/games/mslug')).toHaveLength(0);
    await waitFor(() => expect(llamadasA('PATCH', '/games/mslug').length).toBeGreaterThan(0), { timeout: 3000 });
    const cuerpo = JSON.parse(String(llamadasA('PATCH', '/games/mslug').at(-1)![1]!.body)) as { identity: { year: string } };
    expect(cuerpo.identity.year).toBe('1996');
  });
});

describe('Ficha · Imágenes y Video', () => {
  it('Imágenes y Video son Cards numeradas 2 y 3, con Dropzone en vez de input de archivo', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    expect(screen.getByRole('heading', { name: 'Imágenes' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Video' })).toBeInTheDocument();
    const logo = screen.getByRole('group', { name: 'Logo' });
    expect(within(logo).getByTestId('dropzone-input')).toBeInTheDocument();
    expect(within(logo).getByRole('button', { name: 'Sugerir Logo' })).toHaveAttribute('title', 'Sugerir desde ArcadeDB');
    expect(screen.getByLabelText('URL de YouTube')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Descargar' })).toBeInTheDocument();
  });

  it('una carátula obligatoria vacía bloquea la exportación', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    const caratula = screen.getByRole('group', { name: 'Carátula' });
    expect(within(caratula).getByText('✕ Bloquea la exportación')).toBeInTheDocument();
  });

  it('una imagen cargada desde una fuente se ve aceptada, sin pedir validación', async () => {
    renderApp('/juegos/sonic');
    await screen.findByRole('heading', { name: 'Sonic The Hedgehog' });

    const logo = screen.getByRole('group', { name: 'Logo' });
    expect(within(logo).queryByText('● Sugerido · sin revisar')).not.toBeInTheDocument();
    expect(within(logo).queryByRole('button', { name: /Aceptar/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Aceptar las/ })).not.toBeInTheDocument();
    expect(within(logo).getByRole('button', { name: 'Sugerir Logo' })).toBeInTheDocument();
    expect(within(logo).getByRole('button', { name: 'Borrar Logo' })).toBeInTheDocument();
  });
});
