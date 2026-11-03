import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GalleryPanel } from '@/components/GalleryPanel';
import { listGalleryCandidates } from '@/lib/api/gallery';
import { getJob } from '@/lib/api/jobs';
import type { ResultadoGuardado } from '@/lib/api/gallery';

// Spec 009: el guardado termina bien aunque falle alguna imagen, y eso no puede pasar en silencio.

vi.mock('@/lib/api/gallery', () => ({
  deleteGalleryImage: vi.fn(),
  listGalleryCandidates: vi.fn(async (_gameId: string, source: string) => (source === 'ImageSearch' ? [
    { id: 'a', tipo: null, label: 'Imagen 1', url: 'https://x/a.jpg', delPadre: false, yaGuardada: false, source: 'ImageSearch' },
  ] : [])),
  saveGallery: vi.fn(async () => ({ jobId: 'job-1' })),
  useGalleryImageAs: vi.fn(),
}));

vi.mock('@/lib/api/jobs', () => ({ getJob: vi.fn() }));

async function guardarCon(result: ResultadoGuardado) {
  vi.mocked(getJob).mockResolvedValue({ jobId: 'job-1', status: 'succeeded', progress: 100, result, error: null });
  const onChanged = vi.fn();
  render(<GalleryPanel bare gallery={[]} gameId="prince-of-persia" onChanged={onChanged} />);
  await userEvent.click(screen.getByRole('button', { name: 'Traer de todas las fuentes' }));
  await userEvent.click(await screen.findByRole('checkbox'));
  await userEvent.click(screen.getByRole('button', { name: 'Guardar 1' }));
  return onChanged;
}

describe('Galería: una fuente lenta no frena a las demás', () => {
  beforeEach(() => vi.clearAllMocks());

  it('pide cada fuente por separado y muestra lo que ya llegó', async () => {
    vi.mocked(listGalleryCandidates).mockImplementation((_gameId, source) => (source === 'ImageSearch'
      ? new Promise(() => {})
      : Promise.resolve(source === 'Launchbox'
        ? [{ id: 'b', tipo: null, label: 'Caja', url: 'https://x/b.jpg', delPadre: false, yaGuardada: false, source: 'Launchbox' }]
        : [])));
    render(<GalleryPanel bare gallery={[]} gameId="prince-of-persia" onChanged={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: 'Traer de todas las fuentes' }));

    expect(await screen.findByRole('checkbox', { name: /Caja/ })).toBeInTheDocument();
    expect(vi.mocked(listGalleryCandidates).mock.calls.map((c) => c[1])).toEqual(['ArcadeDB', 'MyAbandonware', 'Launchbox', 'MobyGames', 'ImageSearch']);
  });
});

it('el buscador trae un casillero por vez, muestra cada tanda y no repite imágenes', async () => {
  const imagen = (id: string) => ({ id, tipo: null, label: id, url: `https://x/${id}.jpg`, delPadre: false, yaGuardada: false, source: 'ImageSearch' });
  let terminar: (lista: ReturnType<typeof imagen>[]) => void = () => {};
  vi.mocked(listGalleryCandidates).mockReset();
  vi.mocked(listGalleryCandidates).mockImplementation((_gameId, source, clave) => {
    if (source !== 'ImageSearch') return Promise.resolve([]);
    if (clave === 'caratula') return Promise.resolve([imagen('caja')]);
    if (clave === 'captura') return new Promise((resolve) => { terminar = resolve; });
    return Promise.resolve([imagen('caja'), imagen('logo')]);
  });
  render(<GalleryPanel bare gallery={[]} gameId="prince-of-persia" onChanged={vi.fn()} />);
  await userEvent.click(screen.getByRole('button', { name: 'Traer de todas las fuentes' }));

  // La primera tanda se ve aunque la segunda siga buscando, y no se pidió la tercera.
  expect(await screen.findByRole('checkbox', { name: /caja/ })).toBeInTheDocument();
  expect(await screen.findByText('Buscando más…')).toBeInTheDocument();
  const claves = () => vi.mocked(listGalleryCandidates).mock.calls.filter((c) => c[1] === 'ImageSearch').map((c) => c[2]);
  expect(claves()).toEqual(['caratula', 'captura']);

  terminar([imagen('captura')]);

  expect(await screen.findByRole('checkbox', { name: /logo/ })).toBeInTheDocument();
  expect(claves()).toEqual(['caratula', 'captura', 'poster', 'logo', 'marquesina']);
  expect(screen.getAllByRole('checkbox', { name: /caja/ })).toHaveLength(1);
  expect(screen.queryByText('Buscando más…')).not.toBeInTheDocument();
});

describe('Galería: imágenes que no se pudieron bajar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listGalleryCandidates).mockImplementation(async (_gameId, source) => (source === 'ImageSearch' ? [
      { id: 'a', tipo: null, label: 'Imagen 1', url: 'https://x/a.jpg', delPadre: false, yaGuardada: false, source: 'ImageSearch' },
    ] : []));
  });

  it('avisa cuántas se guardaron y refresca la ficha', async () => {
    const onChanged = await guardarCon({ guardadas: ['g1', 'g2', 'g3'], fallidas: ['u1', 'u2', 'u3'] });
    expect(await screen.findByText('Se guardaron 3 de 6: las otras 3 no se pudieron bajar de su sitio.')).toBeInTheDocument();
    expect(onChanged).toHaveBeenCalled();
  });

  it('no avisa nada si se bajaron todas', async () => {
    const onChanged = await guardarCon({ guardadas: ['g1'], fallidas: [] });
    await vi.waitFor(() => expect(onChanged).toHaveBeenCalled());
    expect(screen.queryByText(/no se pudo|no se pudieron/)).not.toBeInTheDocument();
  });
});
