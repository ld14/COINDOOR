import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { Juegos } from '@/pages/Juegos';
import { colorDeTitulo, iniciales } from './progreso';

function Where() {
  const { pathname, search } = useLocation();
  return <output data-testid="where">{pathname}{search}</output>;
}

function renderJuegos(path = '/juegos') {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={[path]}>
        <Juegos />
        <Where />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Juegos (Flyer)', () => {
  it('muestra el resumen con datos reales y las acciones del encabezado', async () => {
    renderJuegos();
    expect(await screen.findByText(/fichas · \d+ para exportar · \d+ ROMs instalados sin ficha/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '+ Nuevo juego' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ROMs sin ficha/ })).toBeInTheDocument();
  });

  it('las pestañas llevan contador y escriben el filtro en la query string', async () => {
    renderJuegos();
    expect(await screen.findByRole('tab', { name: /Con errores\s*\d+/ })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('tab', { name: /Listos sin exportar/ }));
    await waitFor(() => expect(screen.getByTestId('where')).toHaveTextContent('status=ready'));
    expect(screen.getByTestId('where')).toHaveTextContent('exportStatus=pending');
    expect(screen.getByRole('tab', { name: /Listos sin exportar/ })).toHaveAttribute('aria-selected', 'true');
  });

  it('el chip de sistema filtra por systemId y se puede quitar', async () => {
    renderJuegos();
    const chip = await screen.findByRole('button', { name: /Sega Genesis/ });
    await userEvent.click(chip);
    await waitFor(() => expect(screen.getByTestId('where')).toHaveTextContent('systemId=genesis'));
    expect(await screen.findByRole('link', { name: 'Sonic The Hedgehog' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Golden Axe' })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /Sega Genesis/ }));
    await waitFor(() => expect(screen.getByTestId('where')).not.toHaveTextContent('systemId'));
  });

  it('la banda "Seguís con" aparece cuando hay un juego en carga y lleva a la ficha', async () => {
    renderJuegos();
    const band = await screen.findByRole('region', { name: 'Juego en carga' });
    expect(band).toHaveTextContent(/Seguís con/);
    await userEvent.click(screen.getByRole('button', { name: 'Continuar →' }));
    await waitFor(() => expect(screen.getByTestId('where')).toHaveTextContent(/^\/juegos\/[^?]+/));
  });

  it('las tarjetas ofrecen la acción según el estado y la vista lista se guarda en la URL', async () => {
    renderJuegos('/juegos?exportStatus=exported');
    expect(await screen.findByRole('button', { name: 'Abrir' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('radio', { name: /Lista/ }));
    await waitFor(() => expect(screen.getByTestId('where')).toHaveTextContent('vista=lista'));
    expect(screen.getByRole('link', { name: 'Golden Axe' })).toBeInTheDocument();
  });

  it('el estado "En carga" propone seguir cargando y cuenta lo que falta', async () => {
    renderJuegos('/juegos?status=incomplete');
    expect((await screen.findAllByRole('button', { name: 'Seguir cargando' })).length).toBeGreaterThan(0);
    expect(await screen.findAllByText(/Faltan \d+ obligatorios/)).not.toHaveLength(0);
  });
});

describe('carátula sin imagen', () => {
  it('deriva iniciales y un color estable del título', () => {
    expect(iniciales('Metal Slug')).toBe('MS');
    expect(colorDeTitulo('Metal Slug')).toBe(colorDeTitulo('Metal Slug'));
    expect(colorDeTitulo('Metal Slug')).not.toBe(colorDeTitulo('Contra'));
  });
});
