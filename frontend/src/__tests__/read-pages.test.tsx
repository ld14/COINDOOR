import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
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

describe('Pantallas de lectura', () => {
  it('separa exportados y pendientes y combina búsqueda con el filtro', async () => {
    renderApp('/juegos?exportStatus=exported');
    expect(await screen.findByText('Golden Axe')).toBeInTheDocument();
    expect(screen.getByText('Exportado')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Exportados' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.queryByText('Metal Slug')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Pendientes de exportar' }));
    expect(await screen.findByText('Metal Slug')).toBeInTheDocument();
    expect(screen.queryByText('Golden Axe')).not.toBeInTheDocument();
    expect(screen.getAllByText('Pendiente de exportar').length).toBeGreaterThan(0);
    await userEvent.type(screen.getByLabelText('Buscar juego'), 'contra');
    await waitFor(() => expect(screen.queryByText('Metal Slug')).not.toBeInTheDocument());
    expect(screen.getByText('Contra')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled();
  });

  it('cambiar el filtro reinicia la página y conserva la búsqueda', async () => {
    renderApp('/juegos?page=2&q=Golden');
    await screen.findByText('Ningún juego coincide con la búsqueda o los filtros.');
    await userEvent.click(screen.getByRole('button', { name: 'Exportados' }));
    expect(await screen.findByText('Golden Axe')).toBeInTheDocument();
    expect(screen.getByLabelText('Buscar juego')).toHaveValue('Golden');
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled();
  });

  it('renderiza sistemas y marca cabecera inválida', async () => {
    renderApp('/sistemas');

    expect(await screen.findByRole('heading', { name: 'Sistemas / Plataformas' })).toBeInTheDocument();
    expect(await screen.findByText('Super Nintendo')).toBeInTheDocument();
    expect(screen.getByText('CABECERA INVÁLIDA')).toBeInTheDocument();
  });

  it('crea sistemas desde /sistemas', async () => {
    renderApp('/sistemas');

    await userEvent.type(await screen.findByLabelText('Nombre del sistema'), 'MS-DOS');
    await userEvent.type(screen.getByLabelText('Short name'), 'dos');
    await userEvent.type(screen.getByLabelText('Comando de lanzamiento'), '/usr/bin/true');
    await userEvent.click(screen.getByRole('button', { name: 'Crear sistema' }));

    expect(await screen.findByText('MS-DOS')).toBeInTheDocument();
    expect(screen.getByText('/usr/bin/true')).toBeInTheDocument();
  });

  it('renderiza lista, placeholder y filtros en query string', async () => {
    renderApp('/juegos');

    expect(await screen.findByText('Golden Axe')).toBeInTheDocument();
    expect(screen.getByText('MS')).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('Buscar juego'), 'contra');
    await waitFor(() => expect(screen.queryByText('Golden Axe')).not.toBeInTheDocument());
    expect(screen.getByText('Contra')).toBeInTheDocument();
  });

  it('renderiza ficha con dashboard y secciones vacías visibles', async () => {
    renderApp('/juegos/mslug');

    expect(await screen.findByRole('heading', { name: 'Metal Slug' })).toBeInTheDocument();
    expect(screen.getByText('DASHBOARD DE COMPLETITUD')).toBeInTheDocument();
    expect(screen.getByText('Identidad')).toBeInTheDocument();
    expect(screen.getByText(/\d+ pendiente\(s\)/)).toBeInTheDocument();
    expect(screen.getByLabelText('Año')).toHaveValue('');
    expect(screen.getAllByText(/No Disponible/).length).toBeGreaterThan(0);
  });

  it('muestra contenido cargado de reseña y trucos en ficha', async () => {
    renderApp('/juegos/contra');

    expect(await screen.findByRole('heading', { name: 'Contra' })).toBeInTheDocument();
    expect(screen.getByText('88')).toBeInTheDocument();
    expect(screen.getByText('30 vidas')).toBeInTheDocument();
    expect(screen.getByText('↑ ↑ ↓ ↓ ← → ← → B A')).toBeInTheDocument();
  });

  it('muestra error explícito para juego inexistente', async () => {
    renderApp('/juegos/no-existe');

    expect(await screen.findByText('Juego no encontrado.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '<< Juegos' })).toBeInTheDocument();
  });

  it('muestra errores de formato como bloqueantes', async () => {
    renderApp('/juegos/dkong');

    expect(await screen.findByText('ERRORES DE FORMATO (bloquean el export):')).toBeInTheDocument();
    expect(screen.getByText(/Debe ser un número de 4 dígitos/)).toBeInTheDocument();
  });
});
