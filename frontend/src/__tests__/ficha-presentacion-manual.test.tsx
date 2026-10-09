import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createRef } from 'react';
import { describe, expect, it, vi } from 'vitest';
import type { Game } from '@/lib/domain/types';
import { CabinetSection } from '@/pages/ficha/GabineteSection';
import { ManualSection } from '@/pages/ficha/ManualSection';
import { luminancia, normalizarHex, PresentationSection } from '@/pages/ficha/PresentacionSection';
import { MagazineSection } from '@/pages/ficha/RevistasSection';
import type { PresentationHandle } from '@/pages/ficha/types';

const hex = (value: string) => `#${value}`;
const ROJO = hex('aa0000');
const VERDE = hex('00ff00');

const casiNegro = vi.hoisted(() => ({ colors: [] as { hex: string; rgb: [number, number, number] }[] }));
vi.mock('@/hooks/useDominantColors', () => ({
  useDominantColors: () => ({ colors: casiNegro.colors, loading: false }),
}));

function juego(parcial: Partial<Game> = {}): Game {
  return {
    id: 'g1',
    accent: 'empty',
    accentValue: '',
    accent2Value: '',
    images: {},
    manuals: [],
    magazine: 'empty',
    magazineName: '',
    magazineAppearances: [],
    ...parcial,
  } as unknown as Game;
}

function conCliente(nodo: React.ReactNode) {
  return render(<QueryClientProvider client={new QueryClient()}>{nodo}</QueryClientProvider>);
}

describe('helpers de color', () => {
  it('luminancia: negro y casi negro bajo 0.05, claro por encima', () => {
    expect(luminancia([0, 0, 0])).toBe(0);
    expect(luminancia([17, 34, 51])).toBeLessThan(0.05);
    expect(luminancia([255, 201, 60])).toBeGreaterThan(0.05);
  });

  it('normalizarHex acepta 6 dígitos con o sin # y rechaza lo incompleto', () => {
    expect(normalizarHex('AA0000')).toBe(ROJO);
    expect(normalizarHex(ROJO)).toBe(ROJO);
    expect(normalizarHex(hex('aa00'))).toBeNull();
  });
});

describe('Presentación', () => {
  it('un hex a medias muestra el error y save() no escribe', async () => {
    casiNegro.colors = [];
    const onSave = vi.fn();
    const ref = createRef<PresentationHandle>();
    render(<PresentationSection game={juego()} onSave={onSave} ref={ref} />);

    await userEvent.type(screen.getByLabelText('Color de acento primario'), hex('aa00'));
    expect(screen.getByRole('alert')).toHaveTextContent('Hex incompleto: 6 dígitos');
    ref.current?.save();
    expect(onSave).not.toHaveBeenCalled();

    await userEvent.type(screen.getByLabelText('Color de acento primario'), '00');
    ref.current?.save();
    expect(onSave).toHaveBeenCalledWith(ROJO, '');
  });

  it('save() sin cambios no escribe (no marca manual lo sugerido)', () => {
    casiNegro.colors = [];
    const onSave = vi.fn();
    const ref = createRef<PresentationHandle>();
    render(<PresentationSection game={juego({ accent: 'suggested', accentValue: ROJO.toUpperCase() })} onSave={onSave} ref={ref} />);
    ref.current?.save();
    expect(onSave).not.toHaveBeenCalled();
  });

  it('elegir un preset en el secundario se guarda junto con el primario existente', async () => {
    casiNegro.colors = [];
    const onSave = vi.fn();
    const ref = createRef<PresentationHandle>();
    render(<PresentationSection game={juego({ accent: 'manual', accentValue: ROJO })} onSave={onSave} ref={ref} />);
    await userEvent.click(screen.getByRole('button', { name: 'Color de acento secundario cian' }));
    ref.current?.save();
    expect(onSave).toHaveBeenCalledWith(ROJO, hex('00aaaa'));
  });

  it('con colores casi negros avisa y propone sugeridos + detectados', async () => {
    casiNegro.colors = [{ hex: hex('050505'), rgb: [5, 5, 5] }];
    render(<PresentationSection game={juego()} onSave={vi.fn()} />);
    expect(screen.getByText('Sugeridos con buen contraste')).toBeInTheDocument();
    expect(screen.getByText('Detectados')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: `Detectado ${hex('050505')}` }));
    expect(screen.getByLabelText('Color de acento primario')).toHaveValue(hex('050505'));
  });

  it('con colores claros no avisa', () => {
    casiNegro.colors = [{ hex: VERDE, rgb: [0, 255, 0] }];
    render(<PresentationSection game={juego()} onSave={vi.fn()} />);
    expect(screen.queryByText('Sugeridos con buen contraste')).not.toBeInTheDocument();
  });
});

describe('Manual y revistas', () => {
  it('el Dropzone PDF entrega el archivo y la lista permite borrar', async () => {
    const onUpload = vi.fn();
    const onDelete = vi.fn();
    const manual = { id: 'm1', fileName: 'manual.pdf', status: 'processed' as const, pages: 12 };
    render(<ManualSection game={juego({ manuals: [manual] })} onDelete={onDelete} onUpload={onUpload} />);
    expect(screen.getByText('manual.pdf')).toBeInTheDocument();
    expect(screen.getByText(/12 páginas/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Borrar' }));
    expect(onDelete).toHaveBeenCalledWith('m1');

    const archivo = new File(['x'], 'otro.pdf', { type: 'application/pdf' });
    await userEvent.upload(screen.getByTestId('dropzone-input'), archivo);
    expect(onUpload).toHaveBeenCalledWith(archivo);
  });

  it('revistas: estado vacío claro y acción Buscar con IA, sin descarga ni estado roto', () => {
    conCliente(<MagazineSection game={juego()} />);
    expect(screen.getByRole('button', { name: 'Buscar con IA' })).toBeInTheDocument();
    expect(screen.getByText(/Sin cobertura en revistas/)).toBeInTheDocument();
    expect(screen.queryByText(/faltante|roto|broken/i)).not.toBeInTheDocument();
  });
});

describe('Gabinete', () => {
  it('muestra specs y la tabla del mapa de botones con color', () => {
    const cabinet = {
      resolution: '320x224',
      orientation: 'Horizontal',
      controls: 'joy 8-way',
      buttons: 3,
      button_list: [{ control: 'P1_BUTTON1', action: 'Golpe', color: 'Rojo' }],
    };
    render(<CabinetSection game={juego({ cabinet } as Partial<Game>)} />);
    expect(screen.getByText('320x224')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Color' })).toBeInTheDocument();
    expect(screen.getByText('Rojo')).toBeInTheDocument();
  });

  it('sin datos dice que no hay información', () => {
    render(<CabinetSection game={juego()} />);
    expect(screen.getByText(/Sin información de gabinete/)).toBeInTheDocument();
  });
});
