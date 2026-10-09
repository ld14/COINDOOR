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
const llamadas = (): LlamadaFetch[] => vi.mocked(fetch).mock.calls as LlamadaFetch[];
const llamadasA = (metodo: string, fragmento: string) =>
  llamadas().filter(([url, init]) => (init?.method ?? 'GET') === metodo && String(url).includes(fragmento));

const CLAVES = ['identidad', 'imagenes', 'video', 'textos', 'guia', 'trucos', 'presentacion', 'galeria', 'resena', 'manual'];

describe('Andamiaje de la ficha', () => {
  it('arma crumbs, hero con progreso, StepNav, columna lateral y ActionBar', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    expect(screen.getByRole('navigation', { name: 'Ruta' })).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'Completitud de la ficha' })).toBeInTheDocument();
    const pasos = screen.getByRole('navigation', { name: 'Secciones de la ficha' });
    expect(within(pasos).getAllByRole('button')).toHaveLength(10);
    expect(screen.getByRole('complementary', { name: 'Pendientes y archivo' })).toBeInTheDocument();
    expect(screen.getByText('Siguiente pendiente')).toBeInTheDocument();
    for (const clave of CLAVES) {
      expect(document.getElementById(`seccion-${clave}`)).not.toBeNull();
    }
  });

  it('monta las 10 secciones en el orden y con la numeración de DESIGN_SPEC §5.1', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    const anclas = [...document.querySelectorAll('section[data-seccion]')].map((el) => el.getAttribute('data-seccion'));
    expect(anclas.filter((c) => CLAVES.includes(String(c)))).toEqual(CLAVES);
    const pasos = screen.getByRole('navigation', { name: 'Secciones de la ficha' });
    expect(within(pasos).getAllByRole('button').map((b) => b.textContent)).toEqual(
      expect.arrayContaining([expect.stringContaining('Video'), expect.stringContaining('Galería')]),
    );
    // «Cómo se juega» no dibuja su Card si el juego no trae checklist: ahí no hay número que verificar.
    for (const [i, clave] of CLAVES.entries()) {
      const numero = document.getElementById(`seccion-${clave}`)?.querySelector('header span[aria-hidden="true"]');
      if (clave === 'guia' && !numero) continue;
      expect(numero?.textContent, clave).toBe(String(i + 1));
    }
    expect(document.getElementById('seccion-gabinete')?.closest('aside')).not.toBeNull();
  });

  it('el StepNav lleva a las anclas de Video y Galería', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });
    const scroll = vi.fn();
    Element.prototype.scrollIntoView = scroll;

    const pasos = screen.getByRole('navigation', { name: 'Secciones de la ficha' });
    await userEvent.click(within(pasos).getByRole('button', { name: /Galería/ }));
    expect(scroll.mock.contexts.at(-1)).toBe(document.getElementById('seccion-galeria'));
    await userEvent.click(within(pasos).getByRole('button', { name: /Video/ }));
    expect(scroll.mock.contexts.at(-1)).toBe(document.getElementById('seccion-video'));
  });

  it('ya no hay botones de guardado global ni de la cabecera', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    expect(screen.queryByRole('button', { name: 'Guardar todo' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Guardar' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Marcar como listo' })).toBeInTheDocument();
  });

  it('las píldoras «Para exportar falta» llevan al campo y lo enfocan', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    const lista = screen.getByRole('list', { name: 'Obligatorios que faltan' });
    await userEvent.click(within(lista).getByRole('button', { name: /Identidad: Año/ }));
    expect(screen.getByLabelText('Año')).toHaveFocus();
  });

  it('Exportar queda deshabilitado con el motivo mientras faltan obligatorios', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    const exportar = screen.getByRole('button', { name: /Exportar \(faltan \d+\)/ });
    expect(exportar).toHaveAttribute('aria-disabled', 'true');
  });

  it('escribir guarda solo, sin botón, y la TopBar lo informa', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    await userEvent.type(screen.getByLabelText('Sinopsis'), 'Disparos y chatarra.');
    expect(llamadasA('PUT', '/fields/sinopsis')).toHaveLength(0);

    await waitFor(() => expect(llamadasA('PUT', '/fields/sinopsis').length).toBeGreaterThan(0), { timeout: 3000 });
    const cuerpo = JSON.parse(String(llamadasA('PUT', '/fields/sinopsis').at(-1)![1]!.body)) as { value: string };
    expect(cuerpo.value).toBe('Disparos y chatarra.');
    expect(await screen.findByText(/Guardado · hace/)).toBeInTheDocument();
  });

  it('al perder el foco guarda sin esperar el debounce', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    await userEvent.type(screen.getByLabelText('Sinopsis'), 'Chatarra.');
    await userEvent.tab();
    await waitFor(() => expect(llamadasA('PUT', '/fields/sinopsis').length).toBeGreaterThan(0), { timeout: 600 });
  });

  it('un error al guardar se muestra en la TopBar con Reintentar', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });
    const original = vi.mocked(fetch).getMockImplementation()!;
    vi.mocked(fetch).mockImplementation(async (input, init) => {
      if (String(input).includes('/fields/sinopsis') && init?.method === 'PUT') {
        return { ok: false, status: 500, json: async () => ({ error: 'El disco está lleno' }) } as Response;
      }
      return original(input, init);
    });

    await userEvent.type(screen.getByLabelText('Sinopsis'), 'Algo.');
    await userEvent.tab();
    expect(await screen.findByText(/Error al guardar/)).toBeInTheDocument();
    const intentos = llamadasA('PUT', '/fields/sinopsis').length;

    // Con un guardado fallido pendiente, cerrar la pestaña avisa.
    const cierre = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(cierre);
    expect(cierre.defaultPrevented).toBe(true);

    // "Reintentar" vuelve a mandar la escritura que falló (y como sigue fallando, el error se mantiene).
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    await waitFor(() => expect(llamadasA('PUT', '/fields/sinopsis').length).toBeGreaterThan(intentos));
    expect(await screen.findByText(/Error al guardar/)).toBeInTheDocument();
  });

  it('el banner de precarga cuenta lo que esperó revisión y «Aceptar todo» lo resuelve', async () => {
    renderApp('/juegos/sonic');
    await screen.findByRole('heading', { name: 'Sonic The Hedgehog' });

    const banner = screen.getByRole('region', { name: 'Resumen de la precarga' });
    expect(banner).toHaveTextContent(/trajo \d+ datos · \d+ aplicados · 1 espera revisión/);

    await userEvent.click(within(banner).getByRole('button', { name: 'Aceptar todo' }));
    await waitFor(() => expect(llamadasA('POST', '/fields/logo/accept')).toHaveLength(1));
    await waitFor(() => expect(screen.queryByRole('region', { name: 'Resumen de la precarga' })).not.toBeInTheDocument());
  });

  it('Enter sobre el campo con foco acepta su sugerencia', async () => {
    renderApp('/juegos/contra');
    await screen.findByRole('heading', { name: 'Contra' });

    await userEvent.click(screen.getByLabelText('Puntaje de reseña'));
    await userEvent.keyboard('{Enter}');
    await waitFor(() => expect(llamadasA('POST', '/fields/review/accept')).toHaveLength(1));
  });

  it('Enter dentro de un textarea escribe un salto de línea y no acepta nada', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    await userEvent.type(screen.getByLabelText('Sinopsis'), 'a{Enter}b');
    expect(screen.getByLabelText('Sinopsis')).toHaveValue('a\nb');
    expect(llamadasA('POST', '/accept')).toHaveLength(0);
  });

  it('«Guardar borrador y salir» guarda lo pendiente y vuelve a Juegos', async () => {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });

    await userEvent.type(screen.getByLabelText('Sinopsis'), 'Pendiente.');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar borrador y salir' }));

    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Metal Slug' })).not.toBeInTheDocument());
    expect(llamadasA('PUT', '/fields/sinopsis').length).toBeGreaterThan(0);
  });

  it('Exportar espera el guardado pendiente antes de navegar', async () => {
    renderApp('/juegos/goldnaxe');
    await screen.findByRole('heading', { name: 'Golden Axe' });
    // La pantalla de Exportar es de otra unidad: acá solo importa que se llegue a ella.
    const original = vi.mocked(fetch).getMockImplementation()!;
    vi.mocked(fetch).mockImplementation(async (input, init) => {
      if (String(input).includes('/export-options')) return { ok: true, status: 200, json: async () => ({ obligatorio: [], opcional: [] }) } as Response;
      return original(input, init);
    });

    await userEvent.type(screen.getByLabelText('Sinopsis'), ' Más.');
    await userEvent.click(screen.getByRole('button', { name: /^⇪ Exportar$/ }));

    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Golden Axe' })).not.toBeInTheDocument());
    expect(llamadasA('PUT', '/fields/sinopsis').length).toBeGreaterThan(0);
  });
});
