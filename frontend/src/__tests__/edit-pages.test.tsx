import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '@/App';
import { GuiaChecklist } from '@/pages/FichaJuego';

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

  it('elegir un instalado precarga origen e identidad', async () => {
    renderApp('/juegos/nuevo');

    await userEvent.click(await screen.findByRole('button', { name: /Ninja Gaiden/ }));

    expect(screen.getByLabelText('Sistema')).toHaveValue('nes');
    expect(screen.getByLabelText('Origen del archivo')).toHaveValue('path');
    expect(screen.getByLabelText('ROM')).toHaveValue('/data/juegos/nes/Ninja Gaiden.nes');
    expect(screen.getByLabelText('Tratamiento')).toHaveValue('copiar');
    expect(screen.getByLabelText('title')).toHaveValue('Ninja Gaiden');
  });

  it('un instalado que es carpeta se da de alta como descomprimir', async () => {
    renderApp('/juegos/nuevo');

    await userEvent.click(await screen.findByRole('button', { name: /Chrono Trigger/ }));

    expect(screen.getByLabelText('Tratamiento')).toHaveValue('descomprimir');
    expect(screen.getByLabelText('Sistema')).toHaveValue('snes');
  });

  it('el filtro deja solo los instalados que coinciden', async () => {
    renderApp('/juegos/nuevo');

    await screen.findByRole('button', { name: /Ninja Gaiden/ });
    await userEvent.type(screen.getByLabelText('Filtrar instalados'), 'chrono');

    expect(screen.queryByRole('button', { name: /Ninja Gaiden/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Chrono Trigger/ })).toBeInTheDocument();
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

  it('el objetivo se guarda aparte de la sinopsis y es opcional', async () => {
    renderApp('/juegos/mslug');

    await screen.findByRole('heading', { name: 'Metal Slug' });
    const caja = screen.getByLabelText('Objetivo').parentElement!;
    expect(within(caja).getByText('○ VACÍO')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Objetivo'), 'Rescatar a los prisioneros.');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar objetivo' }));

    await waitFor(() => expect(within(caja).getByText('● MANUAL')).toBeInTheDocument());
    expect(screen.getByLabelText('Sinopsis')).toHaveValue('');
  });

  it('primeros pasos, reglas y modo de la guía se guardan por separado', async () => {
    renderApp('/juegos/mslug');

    await screen.findByRole('heading', { name: 'Metal Slug' });
    const pasos = screen.getByLabelText('Primeros pasos').parentElement!;
    await userEvent.type(screen.getByLabelText('Primeros pasos'), 'Mover la paleta');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar primeros pasos' }));
    await waitFor(() => expect(within(pasos).getByText('● MANUAL')).toBeInTheDocument());

    const modo = screen.getByLabelText('Modo multijugador').parentElement!;
    await userEvent.selectOptions(screen.getByLabelText('Modo multijugador'), 'versus');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar modo' }));
    await waitFor(() => expect(within(modo).getByText('● MANUAL')).toBeInTheDocument());
    expect(within(screen.getByLabelText('Reglas esenciales').parentElement!).getByText('○ VACÍO')).toBeInTheDocument();
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

  it('los trucos se leen como ledger y solo se vuelven editables al pedirlo', async () => {
    renderApp('/juegos/contra');

    await screen.findByRole('heading', { name: 'Contra' });
    // Vista: el truco se lee como texto, no como un campo.
    expect(screen.getByText('30 vidas')).toBeInTheDocument();
    expect(screen.queryByLabelText('Qué hace el truco')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Editar trucos' }));

    expect(screen.getByLabelText('Qué hace el truco')).toHaveValue('30 vidas');
    expect(screen.getByLabelText('Código o procedimiento')).toHaveValue('↑ ↑ ↓ ↓ ← → ← → B A');

    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }));

    expect(screen.queryByLabelText('Qué hace el truco')).not.toBeInTheDocument();
    expect(screen.getByText('30 vidas')).toBeInTheDocument();
  });

  it('editar un truco lo guarda como estructura de grupos', async () => {
    renderApp('/juegos/contra');

    await screen.findByRole('heading', { name: 'Contra' });
    await userEvent.click(screen.getByRole('button', { name: 'Editar trucos' }));

    const campo = screen.getByLabelText('Código o procedimiento');
    await userEvent.clear(campo);
    await userEvent.type(campo, 'ARRIBA ARRIBA ABAJO');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar trucos' }));

    const fetchMock = vi.mocked(fetch);
    const call = fetchMock.mock.calls.find(([input]) => String(input).includes('/fields/cheats'));
    expect(call).toBeDefined();
    expect(JSON.parse(String(call?.[1]?.body))).toEqual({
      groups: [{ name: 'modo cooperativo', entries: [{ name: '30 vidas', input: 'ARRIBA ARRIBA ABAJO' }] }],
    });
  });

  it('review se guarda como estructura, no como texto', async () => {
    renderApp('/juegos/mslug');

    await screen.findByRole('heading', { name: 'Metal Slug' });
    await userEvent.type(screen.getByLabelText('Puntaje de reseña'), '75');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar reseña' }));

    const fetchMock = vi.mocked(fetch);
    const reviewCall = fetchMock.mock.calls.find(([input]) => String(input).includes('/fields/review'));
    expect(reviewCall).toBeDefined();
    expect(JSON.parse(String(reviewCall?.[1]?.body))).toEqual({ score: 75, cats: {} });
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

describe('Video desde YouTube', () => {
  beforeEach(() => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  async function pedirDescarga(url: string) {
    renderApp('/juegos/mslug');
    await screen.findByRole('heading', { name: 'Metal Slug' });
    await userEvent.type(screen.getByLabelText('URL de YouTube'), url);
    await userEvent.click(screen.getByRole('button', { name: 'Descargar' }));
  }

  it('URL que no es de YouTube muestra el error sin llamar a la API', async () => {
    await pedirDescarga('https://vimeo.com/76979871');

    expect(await screen.findByText('La URL tiene que ser de un video de youtube.com o youtu.be.')).toBeInTheDocument();
    expect(vi.mocked(fetch).mock.calls.some(([input]) => String(input).includes('/youtube'))).toBe(false);
  });

  it('video cargado a mano pide confirmación y, si se cancela, no descarga', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderApp('/juegos/goldnaxe');
    await screen.findByRole('heading', { name: 'Golden Axe' });
    await userEvent.type(screen.getByLabelText('URL de YouTube'), 'https://youtu.be/earaCnLVL98');
    await userEvent.click(screen.getByRole('button', { name: 'Descargar' }));

    expect(confirmSpy).toHaveBeenCalledWith('El video actual fue cargado a mano. ¿Reemplazarlo con el de YouTube?');
    expect(vi.mocked(fetch).mock.calls.some(([input]) => String(input).includes('/youtube'))).toBe(false);
  });

  it('descarga exitosa muestra el video nuevo en el reproductor', async () => {
    await pedirDescarga('https://youtu.be/earaCnLVL98');

    await waitFor(() => {
      const fuentes = Array.from(document.querySelectorAll('video'), (video) => video.getAttribute('src'));
      expect(fuentes).toContainEqual(expect.stringMatching(/^\/media\/arcade\/mslug\/video\.mp4\?v=\d+$/));
    });
  });

  it('job fallido muestra su mensaje', async () => {
    const base = vi.mocked(fetch).getMockImplementation()!;
    vi.mocked(fetch).mockImplementation(async (input, init) => (String(input).includes('/api/jobs/')
      ? ({ ok: true, status: 200, json: async () => ({ jobId: 'yt-job', status: 'failed', progress: 0, result: null, error: 'El video dura más de 10 minutos.' }) } as Response)
      : base(input, init)));

    await pedirDescarga('https://youtu.be/earaCnLVL98');

    expect(await screen.findByText('El video dura más de 10 minutos.')).toBeInTheDocument();
  });
});

describe('Checklist de la guía', () => {
  const items = [
    { key: 'objetivo', label: 'Objetivo', estado: 'falta' as const, detalle: 'Sin objetivo la guía no se exporta', requerido: true },
    { key: 'primerosPasos', label: 'Primeros pasos', estado: 'falta' as const, detalle: 'Escribilo o usá Sugerir', requerido: false },
    { key: 'perifericos', label: 'Periféricos', estado: 'ok' as const, detalle: 'dial', requerido: false },
    { key: 'acciones', label: 'Acciones de los botones', estado: 'falta' as const, detalle: 'ArcadeDB no publica botones con acción para este juego', requerido: false },
  ];

  it('marca lo que hay, lo que falta y lo obligatorio, con el motivo', () => {
    render(<GuiaChecklist fallos={{}} items={items} />);

    const lista = within(screen.getByRole('list', { name: 'Checklist de la guía' }));
    expect(screen.getByText(/1 de 4 listos/)).toBeInTheDocument();
    expect(screen.getByText(/Sin objetivo la guía no se exporta\.$/)).toBeInTheDocument();
    expect(lista.getByText(/Falta \(obligatorio\)/)).toBeInTheDocument();
    expect(lista.getByText(/Listo — dial/)).toBeInTheDocument();
    expect(lista.getByText(/ArcadeDB no publica botones con acción/)).toBeInTheDocument();
    expect(screen.getAllByRole('listitem').map((li) => li.getAttribute('data-estado'))).toEqual(['falta', 'falta', 'ok', 'falta']);
  });

  it('dice «no se pudo generar» cuando la sugerencia de IA no produjo nada', () => {
    render(<GuiaChecklist fallos={{ primerosPasos: 'el modelo no conoce el juego', perifericos: 'ignorado' }} items={items} />);

    expect(screen.getByText(/No se pudo generar: el modelo no conoce el juego\. Escribilo o usá Sugerir/)).toBeInTheDocument();
    // Un ítem que ya está listo no muestra fallos viejos.
    expect(screen.queryByText(/ignorado/)).toBeNull();
  });

  it('no dibuja nada si la ficha no trae checklist', () => {
    const { container } = render(<GuiaChecklist fallos={{}} items={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('la ficha de un mock sin checklist se sigue abriendo', async () => {
    renderApp('/juegos/goldnaxe');
    await screen.findByRole('heading', { name: 'Golden Axe' });
    expect(screen.queryByRole('list', { name: 'Checklist de la guía' })).toBeNull();
  });
});
