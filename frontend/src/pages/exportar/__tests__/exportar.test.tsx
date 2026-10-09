import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '@/App';
import type { ExportOptions } from '@/lib/api/export';
import { etapaDe, seleccionInicial } from '../seleccion';

const opciones: ExportOptions = {
  obligatorio: [
    { key: 'identidad', label: 'Identidad', required: true, disponible: true, bytes: 100 },
    { key: 'caratula', label: 'Carátula', required: true, disponible: true, bytes: 1024 },
  ],
  opcional: [
    { key: 'objetivo', label: 'Objetivo', required: false, disponible: true, bytes: 200 },
    { key: 'modo', label: 'Modo de juego', required: false, disponible: false, bytes: 0, motivo: 'tiene un ejemplo sin reemplazar' },
    { key: 'video', label: 'Video', required: false, disponible: true, bytes: 2048 },
    { key: 'logo', label: 'Logo', required: false, disponible: false, bytes: 0 },
    { key: 'cheats', label: 'Trucos', required: false, disponible: false, bytes: 2 },
    { key: 'review', label: 'Reseña', required: false, disponible: true, bytes: 50 },
  ],
};

const llamadas: { url: string; method: string; body?: string }[] = [];

function respuesta(payload: unknown, status = 200) {
  return { ok: status < 300, status, json: async () => payload } as Response;
}

function stubApi(extra: (url: URL, method: string) => Response | undefined = () => undefined) {
  const base = globalThis.fetch;
  llamadas.length = 0;
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://127.0.0.1');
    const method = init?.method ?? 'GET';
    llamadas.push({ url: url.pathname, method, body: init?.body as string | undefined });
    const propia = extra(url, method);
    if (propia) return propia;
    if (url.pathname === '/api/config') return respuesta({ attractDir: '/mnt/attract' });
    if (url.pathname.endsWith('/export-options')) return respuesta(opciones);
    return base(input, init);
  }));
}

function renderApp(path: string) {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={[path]}><App /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Exportar un juego', () => {
  beforeEach(() => stubApi());

  it('tilda por defecto lo opcional con datos y deshabilita lo vacío con su motivo', async () => {
    renderApp('/exportar/goldnaxe');
    const objetivo = await screen.findByRole('checkbox', { name: /Objetivo/ });
    expect(objetivo).toBeChecked();
    expect(screen.getByRole('checkbox', { name: /Video/ })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: /Reseña/ })).toBeChecked();

    const modo = screen.getByRole('checkbox', { name: /Modo de juego/ });
    expect(modo).toBeDisabled();
    expect(modo).not.toBeChecked();
    expect(screen.getByText('tiene un ejemplo sin reemplazar')).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /Logo/ })).toBeDisabled();
    expect(screen.getByText('sin cargar')).toBeInTheDocument();
  });

  it('Trucos vacío no figura con "2 B": queda deshabilitado con el motivo', async () => {
    renderApp('/exportar/goldnaxe');
    const trucos = await screen.findByRole('checkbox', { name: /Trucos/ });
    expect(trucos).toBeDisabled();
    expect(screen.getByText('no hay trucos')).toBeInTheDocument();
    expect(screen.queryByText('2 B')).not.toBeInTheDocument();
  });

  it('lo obligatorio va tildado y no se puede quitar', async () => {
    renderApp('/exportar/goldnaxe');
    const titulo = await screen.findByRole('heading', { name: 'Siempre incluido' });
    const card = titulo.closest('header')?.parentElement as HTMLElement;
    for (const check of within(card).getAllByRole('checkbox')) {
      expect(check).toBeChecked();
      expect(check).toBeDisabled();
    }
    expect(within(card).queryByRole('button', { name: /Quitar todo/ })).not.toBeInTheDocument();
  });

  it('el total y la cantidad se actualizan en vivo', async () => {
    renderApp('/exportar/goldnaxe');
    await screen.findByRole('checkbox', { name: /Objetivo/ });
    // 100 + 1024 + 200 + 2048 + 50 = 3422 B -> 3.3 KB, 5 elementos
    expect(screen.getByText('3.3 KB')).toBeInTheDocument();
    expect(screen.getByText('5 elementos')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('checkbox', { name: /Video/ }));
    expect(screen.getByText('1.3 KB')).toBeInTheDocument();
    expect(screen.getByText('4 elementos')).toBeInTheDocument();
  });

  it('Quitar todo vacía el grupo de media y deja la guía como estaba', async () => {
    renderApp('/exportar/goldnaxe');
    const titulo = await screen.findByRole('heading', { name: 'Media opcional' });
    const card = titulo.closest('header')?.parentElement as HTMLElement;
    await userEvent.click(within(card).getByRole('button', { name: 'Quitar todo' }));
    expect(screen.getByRole('checkbox', { name: /Video/ })).not.toBeChecked();
    expect(screen.getByRole('checkbox', { name: /Objetivo/ })).toBeChecked();
    expect(within(card).getByRole('button', { name: 'Marcar todo' })).toBeInTheDocument();
  });

  it('exporta con lo tildado por defecto y carga en ATTRACT', async () => {
    stubApi((url, method) => {
      if (url.pathname === '/api/export' && method === 'POST') return respuesta({ runId: 'r1' });
      if (url.pathname === '/api/export/r1') return respuesta({ jobId: 'r1', status: 'succeeded', progress: 100, result: { file: '/x/goldnaxe.coindoor.zip', bytes: 2048, incluye: ['identidad', 'video'], verificado: {} }, error: null });
      if (url.pathname.endsWith('/install-attract')) return respuesta({ ok: true, estado: 'instalado', salida: '' });
      return undefined;
    });
    renderApp('/exportar/goldnaxe');
    await userEvent.click(await screen.findByRole('button', { name: '⇪ Exportar a ATTRACT' }));
    expect(await screen.findByText('Export completado')).toBeInTheDocument();
    expect(await screen.findByText('Instalado en ATTRACT.')).toBeInTheDocument();
    const post = llamadas.find((c) => c.url === '/api/export' && c.method === 'POST');
    const incluir = (JSON.parse(post?.body ?? '{}') as { incluir: string[] }).incluir;
    expect(incluir.sort()).toEqual(['caratula', 'identidad', 'objetivo', 'review', 'video']);
  });

  it('un rechazo no deja resultado ni zip y muestra el motivo', async () => {
    stubApi((url, method) => {
      if (url.pathname === '/api/export' && method === 'POST') return respuesta({ runId: 'r2' });
      if (url.pathname === '/api/export/r2') return respuesta({ jobId: 'r2', status: 'failed', progress: 50, result: null, error: 'ATTRACT doctor rechazo el bundle' });
      return undefined;
    });
    renderApp('/exportar/goldnaxe');
    await userEvent.click(await screen.findByRole('button', { name: '⇪ Exportar a ATTRACT' }));
    expect(await screen.findByText('ATTRACT doctor rechazo el bundle')).toBeInTheDocument();
    expect(screen.queryByText('Export completado')).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Volver a Juegos/ })).not.toBeInTheDocument();
  });
});

describe('Cola de exportación (/exportar sin id)', () => {
  it('lista listos y en carga con un link a cada uno y el botón con la cuenta', async () => {
    stubApi();
    renderApp('/exportar');
    expect(await screen.findByRole('heading', { name: 'Listos' })).toBeInTheDocument();
    expect(screen.queryByText(/Seleccioná un juego/)).not.toBeInTheDocument();
    const boton = await screen.findByRole('button', { name: /Exportar los listos \(\d+\)/ });
    const listos = Number(/\((\d+)\)/.exec(boton.textContent ?? '')?.[1]);
    expect(listos).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: 'En carga' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Metal Slug' })).toHaveAttribute('href', '/exportar/mslug');
    expect(screen.queryByRole('link', { name: 'Golden Axe' })).not.toBeInTheDocument();
  });

  it('exporta los listos uno por uno', async () => {
    stubApi((url, method) => {
      if (url.pathname === '/api/export' && method === 'POST') return respuesta({ runId: 'rc' });
      if (url.pathname === '/api/export/rc') return respuesta({ jobId: 'rc', status: 'succeeded', progress: 100, result: { file: 'f', bytes: 1, incluye: [], verificado: {} }, error: null });
      return undefined;
    });
    renderApp('/exportar');
    const boton = await screen.findByRole('button', { name: /Exportar los listos/ });
    const listos = Number(/\((\d+)\)/.exec(boton.textContent ?? '')?.[1]);
    await userEvent.click(boton);
    await waitFor(() => expect(llamadas.filter((c) => c.url === '/api/export' && c.method === 'POST')).toHaveLength(listos));
  });
});

describe('seleccion', () => {
  it('seleccionInicial incluye obligatorio y opcional con datos, no los vacíos', () => {
    expect([...seleccionInicial(opciones)].sort()).toEqual(['caratula', 'identidad', 'objetivo', 'review', 'video']);
  });

  it('etapaDe sigue los hitos del backend', () => {
    expect(etapaDe(20)).toBe('armando');
    expect(etapaDe(50)).toBe('verificando');
    expect(etapaDe(80)).toBe('resultado');
  });
});
