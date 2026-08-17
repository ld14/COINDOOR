import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '@/App';

function renderApp(path = '/') {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Alta de un juego', () => {
  it('crea juego y navega a la ficha', async () => {
    renderApp('/juegos/nuevo');

    await userEvent.selectOptions(await screen.findByLabelText('Origen del archivo'), 'path');
    await userEvent.type(screen.getByLabelText('ROM'), '/roms/arcade/nuevo.zip');
    await userEvent.type(screen.getByLabelText('title'), 'Nuevo Juego');
    await waitFor(() => expect(screen.getByLabelText('Sistema')).not.toHaveValue(''));

    await userEvent.click(screen.getByRole('button', { name: 'Crear ficha' }));

    expect(await screen.findByRole('heading', { name: 'Nuevo Juego' })).toBeInTheDocument();
  });

  it('ruta relativa en romRef muestra error y no crea ficha', async () => {
    renderApp('/juegos/nuevo');

    await userEvent.type(screen.getByLabelText('ROM'), 'roms/arcade/relativo.zip');
    await userEvent.type(screen.getByLabelText('title'), 'Otro Juego');
    await userEvent.click(screen.getByRole('button', { name: 'Crear ficha' }));

    expect(await screen.findByText('La ruta debe ser absoluta (ej: /opt/emulador/bin o C:\\Emuladores\\bin.exe). Si no, el juego no arranca en el gabinete sin avisar.')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Otro Juego' })).not.toBeInTheDocument();
  });
});

describe('Edición de ficha', () => {
  beforeEach(() => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('editar sinopsis actualiza la ficha y el estado del campo', async () => {
    renderApp('/juegos/mslug');

    await screen.findByRole('heading', { name: 'Metal Slug' });
    const sinopsis = screen.getByLabelText('Sinopsis');
    await userEvent.type(sinopsis, 'Una sinopsis nueva.');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar sinopsis' }));

    await waitFor(() => expect(screen.getByText('● MANUAL')).toBeInTheDocument());
  });

  it('borrar campo manual pide confirmación y vuelve a vacío sin ocultar la sección', async () => {
    renderApp('/juegos/goldnaxe');

    await screen.findByRole('heading', { name: 'Golden Axe' });
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const sinopsisBox = screen.getByLabelText('Sinopsis').parentElement!;
    await userEvent.click(within(sinopsisBox).getByRole('button', { name: 'Borrar' }));

    expect(confirmSpy).toHaveBeenCalled();
    await waitFor(() => expect(screen.getByLabelText('Sinopsis')).toHaveValue(''));
  });

  it('cancelar la confirmación no borra el campo manual', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderApp('/juegos/goldnaxe');

    await screen.findByRole('heading', { name: 'Golden Axe' });
    const sinopsisBox = screen.getByLabelText('Sinopsis').parentElement!;
    await userEvent.click(within(sinopsisBox).getByRole('button', { name: 'Borrar' }));

    expect(screen.getByLabelText('Sinopsis')).toHaveValue('Sinopsis cargada para pruebas.');
  });

  it('review y cheats se guardan como estructura, no como texto', async () => {
    renderApp('/juegos/mslug');

    await screen.findByRole('heading', { name: 'Metal Slug' });
    await userEvent.type(screen.getByLabelText('Puntaje de reseña'), '75');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar reseña' }));
    await userEvent.type(screen.getByLabelText('Nombre del truco'), 'Vidas extra');
    await userEvent.type(screen.getByLabelText('Input del truco'), '↑ ↑ ↓ ↓');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar trucos' }));

    const fetchMock = vi.mocked(fetch);
    const reviewCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/fields/review'));
    const cheatsCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/fields/cheats'));
    expect(reviewCall).toBeDefined();
    expect(cheatsCall).toBeDefined();
    expect(JSON.parse(String(reviewCall?.[1]?.body))).toEqual({ score: 75, cats: {} });
    expect(JSON.parse(String(cheatsCall?.[1]?.body))).toEqual({
      groups: [{ name: 'general', entries: [{ name: 'Vidas extra', input: '↑ ↑ ↓ ↓' }] }],
    });
  });

  it('mark-ready incompleto muestra faltantes exactos', async () => {
    renderApp('/juegos/mslug');

    await screen.findByRole('heading', { name: 'Metal Slug' });
    await userEvent.click(screen.getByRole('button', { name: 'Marcar como listo' }));

    expect(await screen.findByText('NO SE PUEDE MARCAR COMO LISTO — faltan campos requeridos:')).toBeInTheDocument();
    expect(screen.getAllByText('- Identidad: Año').length).toBeGreaterThan(0);
  });

  it('subir media actualiza la tarjeta sin usar el nombre de archivo del cliente', async () => {
    renderApp('/juegos/mslug');

    await screen.findByRole('heading', { name: 'Metal Slug' });
    const logoCard = screen.getByText('Logo').closest('div')!.parentElement!;
    const file = new File(['data'], 'nombre-cliente.png', { type: 'image/png' });
    const input = within(logoCard).getByLabelText('Cargar Logo');
    await userEvent.upload(input, file);

    await waitFor(() => expect(within(logoCard).getByRole('img', { name: 'Logo' })).toHaveAttribute('src', '/media/arcade/mslug/logo.jpg'));
    expect(within(logoCard).queryByText(/nombre-cliente\.png/)).not.toBeInTheDocument();
  });
});
