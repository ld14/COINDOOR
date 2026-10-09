import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { App } from '@/App';
import { FIELDDEFS } from '@/lib/domain/types';
import type { System } from '@/lib/domain/types';
import { detectarPorCarpeta, tamano } from '@/pages/nuevo/utils';

function renderApp(path = '/juegos/nuevo') {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const siguiente = () => userEvent.click(screen.getByRole('button', { name: /Siguiente/ }));

describe('detección por carpeta', () => {
  const sistemas = [
    { id: 'arcade', name: 'Arcade' },
    { id: 'ms-dos', name: 'MS-DOS' },
  ] as System[];

  it('mame/ propone Arcade + Copiar', () => {
    expect(detectarPorCarpeta('/roms/mame/sf2.zip', sistemas)).toEqual({ carpeta: 'mame', systemId: 'arcade', tratamiento: 'copiar' });
  });

  it('ms-dos/ propone MS-DOS + Descomprimir', () => {
    expect(detectarPorCarpeta('D:\\juegos\\ms-dos\\doom', sistemas)).toEqual({ carpeta: 'ms-dos', systemId: 'ms-dos', tratamiento: 'descomprimir' });
  });

  it('no propone un sistema que no existe ni mira el nombre del archivo', () => {
    expect(detectarPorCarpeta('/roms/ms-dos/doom.zip', [sistemas[0]])).toBeNull();
    expect(detectarPorCarpeta('/roms/otros/mame.zip', sistemas)).toBeNull();
  });

  it('formatea tamaños', () => {
    expect(tamano(21 * 1024 * 1024)).toBe('21 MB');
    expect(tamano(0)).toBe('');
  });
});

describe('Asistente de alta', () => {
  it('muestra los cuatro pasos y arranca en Archivo con los instalados', async () => {
    renderApp();
    const pasos = screen.getByRole('navigation', { name: 'Pasos del alta' });
    ['Archivo', 'Sistema y tratamiento', 'Identidad', 'Abrir la ficha'].forEach((nombre) => {
      expect(within(pasos).getByRole('button', { name: new RegExp(nombre) })).toBeInTheDocument();
    });
    expect(await screen.findByRole('button', { name: /Ninja Gaiden/ })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Instalados' })).toBeChecked();
  });

  it('elegir un instalado precarga sistema, tratamiento e identidad a lo largo de los pasos', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('button', { name: /Ninja Gaiden/ }));
    const resumen = screen.getByRole('complementary', { name: 'Resumen del alta' });
    expect(within(resumen).getByText('/data/juegos/nes/Ninja Gaiden.nes')).toBeInTheDocument();

    await siguiente();
    expect(screen.getByRole('radio', { name: /Nintendo Entertainment System/ })).toBeChecked();
    expect(screen.getByRole('radio', { name: /Copiar/ })).toBeChecked();
    expect(screen.getByText('Detectado')).toBeInTheDocument();

    await siguiente();
    expect(screen.getByLabelText('Título')).toHaveValue('Ninja Gaiden');
  });

  it('un instalado que es carpeta se da de alta como descomprimir', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('button', { name: /Chrono Trigger/ }));
    await siguiente();
    expect(screen.getByRole('radio', { name: /Descomprimir/ })).toBeChecked();
    expect(screen.getByRole('radio', { name: /Super Nintendo/ })).toBeChecked();
  });

  it('el filtro deja solo los instalados que coinciden y no duplica', async () => {
    renderApp();
    await screen.findByRole('button', { name: /Ninja Gaiden/ });
    expect(screen.getAllByRole('button', { name: /Ninja Gaiden/ })).toHaveLength(1);
    await userEvent.type(screen.getByLabelText('Filtrar instalados'), 'chrono');
    expect(screen.queryByRole('button', { name: /Ninja Gaiden/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Chrono Trigger/ })).toBeInTheDocument();
  });

  it('indicar ruta con carpeta mame/ propone Arcade + Copiar', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('radio', { name: 'Indicar ruta' }));
    await userEvent.type(screen.getByLabelText('ROM'), '/roms/mame/sf2.zip');
    await siguiente();
    expect(screen.getByRole('radio', { name: /Arcade/ })).toBeChecked();
    expect(screen.getByRole('radio', { name: /Copiar/ })).toBeChecked();
    expect(screen.getByText('Detectado')).toBeInTheDocument();
  });

  it('la identidad usa las etiquetas en castellano de fielddefs, no las claves', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('radio', { name: 'Indicar ruta' }));
    await userEvent.type(screen.getByLabelText('ROM'), '/roms/arcade/x.zip');
    await siguiente();
    await siguiente();
    for (const { key, label } of FIELDDEFS.identity) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
      if (key !== label) expect(screen.queryByLabelText(key)).not.toBeInTheDocument();
    }
  });

  it('ruta relativa bloquea el avance y no crea ficha', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('radio', { name: 'Indicar ruta' }));
    await userEvent.type(screen.getByLabelText('ROM'), 'roms/arcade/relativo.zip');
    await siguiente();
    expect(await screen.findByRole('alert')).toHaveTextContent(/La ruta debe ser absoluta/);
    await userEvent.click(screen.getByRole('button', { name: /Crear ficha y empezar/ }));
    expect(screen.queryByRole('heading', { name: 'Otro Juego' })).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Alta de un juego' })).toBeInTheDocument();
  });

  it('subir ROM sin archivo pide seleccionar uno', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('radio', { name: 'Subir ROM' }));
    await siguiente();
    expect(await screen.findByRole('alert')).toHaveTextContent('Seleccioná un archivo para subir.');
  });

  it('crea la ficha desde el resumen y navega a ella', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('radio', { name: 'Indicar ruta' }));
    await userEvent.type(screen.getByLabelText('ROM'), '/roms/arcade/nuevo.zip');
    await siguiente();
    await waitFor(() => expect(screen.getByRole('radio', { name: /Arcade/ })).toBeChecked());
    await siguiente();
    await userEvent.type(screen.getByLabelText('Título'), 'Nuevo Juego');
    await siguiente();

    const resumen = screen.getByRole('complementary', { name: 'Resumen del alta' });
    expect(within(resumen).getByRole('checkbox', { name: 'Precargar ArcadeDB al crear' })).toBeChecked();
    await userEvent.click(within(resumen).getByRole('button', { name: /Crear ficha y empezar a cargar/ }));

    expect(await screen.findByRole('heading', { name: 'Nuevo Juego' })).toBeInTheDocument();
  });

  it('el botón Atrás y la píldora vuelven a pasos ya visitados', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('button', { name: /Ninja Gaiden/ }));
    await siguiente();
    await userEvent.click(screen.getByRole('button', { name: /Atrás/ }));
    expect(screen.getByRole('radio', { name: 'Instalados' })).toBeInTheDocument();
    await userEvent.click(within(screen.getByRole('navigation', { name: 'Pasos del alta' })).getByRole('button', { name: /Sistema y tratamiento/ }));
    expect(screen.getByRole('radio', { name: /Copiar/ })).toBeInTheDocument();
  });

  it('+ Nuevo sistema abre el alta en un modal y deja el sistema elegido', async () => {
    renderApp();
    await userEvent.click(await screen.findByRole('button', { name: /Ninja Gaiden/ }));
    await siguiente();
    await userEvent.click(screen.getByRole('button', { name: '+ Nuevo sistema' }));
    const modal = screen.getByRole('dialog', { name: 'Nuevo sistema' });
    await userEvent.type(within(modal).getByLabelText('Nombre del sistema'), 'Atari 2600');
    await userEvent.type(within(modal).getByLabelText('Nombre corto'), 'atari2600');
    await userEvent.type(within(modal).getByLabelText('Comando de lanzamiento'), '/opt/stella');
    await userEvent.click(within(modal).getByRole('button', { name: 'Crear sistema' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(await screen.findByRole('radio', { name: /Atari 2600/ })).toBeChecked();
  });
});
