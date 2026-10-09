import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
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

describe('Sistemas (rediseño)', () => {
  it('muestra el contador y [Ver juegos] por sistema', async () => {
    renderApp('/sistemas');
    expect(await screen.findByText('Super Nintendo')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Ver juegos' }).length).toBeGreaterThan(0);
    expect(screen.getAllByText('juegos').length).toBeGreaterThan(0);
  });

  it('valida en vivo que la ruta sea absoluta y explica por qué no se puede crear', async () => {
    renderApp('/sistemas');
    const cmd = await screen.findByLabelText('Comando de lanzamiento');
    const create = screen.getByRole('button', { name: 'Crear sistema' });
    expect(create).toBeDisabled();

    await userEvent.type(screen.getByLabelText('Nombre del sistema'), 'Super Nintendo 2');
    await userEvent.type(screen.getByLabelText('Short name'), 'snes2');
    await userEvent.type(cmd, 'emuladores\\snes9x.exe');
    expect(screen.getByText(/Tiene que ser una ruta absoluta/)).toBeInTheDocument();
    expect(create).toBeDisabled();

    await userEvent.clear(cmd);
    await userEvent.type(cmd, 'C:\\Emuladores\\snes9x.exe');
    expect(screen.queryByText(/Tiene que ser una ruta absoluta/)).not.toBeInTheDocument();
    expect(create).toBeEnabled();
  });
});

describe('Configuración (rediseño)', () => {
  it('[Probar] valida el formato de la ruta de ATTRACT', async () => {
    renderApp('/configuracion');
    const input = await screen.findByLabelText('Ruta de ATTRACT');
    await userEvent.clear(input);
    await userEvent.type(input, 'relativa/attract');
    await userEvent.click(screen.getByRole('button', { name: 'Probar' }));
    expect(await screen.findByText(/✕/)).toBeInTheDocument();

    await userEvent.clear(input);
    await userEvent.type(input, '/mnt/d/Juegos/attract');
    await userEvent.click(screen.getByRole('button', { name: 'Probar' }));
    expect(await screen.findByText(/formato de ruta válido/)).toBeInTheDocument();
  });
});
