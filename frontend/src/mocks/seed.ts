import type { CheatsField, Game, Identity, ImageKey, MediaField, ReviewField, System, TextKey, VideoKey } from '@/lib/domain/types';

const fullIdentity: Identity = {
  title: 'Golden Axe',
  year: '1989',
  developer: 'Sega',
  publisher: 'Sega',
  genre: "Beat 'em up",
  players: '1-2',
  format: 'Arcade',
};

const hex = (value: string) => `#${value}`;

const manual = (url = '/media/placeholder.png'): MediaField => ({ status: 'manual', url });
const empty = (): MediaField => ({ status: 'empty' });
const suggested = (url = '/media/suggested.png'): MediaField => ({ status: 'suggested', source: 'MobyGames', url });

const images = (overrides: Partial<Record<ImageKey, MediaField>> = {}): Record<ImageKey, MediaField> => ({
  caratula: manual('/media/goldnaxe/boxFront.jpg'),
  marquesina: manual('/media/goldnaxe/marquee.jpeg'),
  poster: manual('/media/goldnaxe/poster.jpg'),
  logo: empty(),
  captura: empty(),
  ...overrides,
});

const video = (overrides: Partial<Record<VideoKey, MediaField>> = {}): Record<VideoKey, MediaField> => ({
  video: empty(),
  ...overrides,
});

const texts = (overrides: Partial<Record<TextKey, { status: 'empty' | 'manual' | 'suggested'; value: string; source?: string }>> = {}) => ({
  sinopsis: { status: 'manual' as const, value: 'Sinopsis cargada para pruebas.' },
  ...overrides,
});

const review = (overrides: Partial<ReviewField> = {}): ReviewField => ({
  status: 'empty',
  score: null,
  cats: {},
  ...overrides,
});

const cheats = (overrides: Partial<CheatsField> = {}): CheatsField => ({
  status: 'empty',
  groups: [],
  ...overrides,
});

const game = (overrides: Partial<Game> & { id: string; title: string; systemId?: string }): Game => {
  const { id, title, systemId, identity, ...rest } = overrides;
  return {
    id,
    systemId: systemId ?? 'arcade',
    identity: { ...fullIdentity, title, ...(identity ?? {}) },
    identitySource: (systemId ?? 'arcade') === 'arcade' ? 'mame' : 'screenscraper',
    romSource: 'path',
    romRef: `${id}.zip`,
    errors: [],
    images: images(),
    video: video(),
    texts: texts(),
    review: review(),
    cheats: cheats(),
    accent: 'manual',
    accentValue: hex('d4a017'),
    accent2Value: hex('3d2f08'),
    manuals: [],
    magazine: 'empty',
    magazineName: '',
    magazineAppearances: [],
    provenance: {},
    ...rest,
  };
};

export const systems: System[] = [
  { id: 'arcade', name: 'Arcade', shortName: 'arcade', launchCmd: '/usr/local/bin/mame', valid: true, gameCount: 4 },
  { id: 'nes', name: 'Nintendo Entertainment System', shortName: 'nes', launchCmd: '/opt/emulators/fceux', valid: true, gameCount: 2 },
  { id: 'genesis', name: 'Sega Genesis', shortName: 'genesis', launchCmd: '/opt/emulators/genesis-plus-gx', valid: true, gameCount: 2 },
  { id: 'snes', name: 'Super Nintendo', shortName: 'snes', launchCmd: 'emulators/snes9x', valid: false, errorMsg: 'La ruta debe ser absoluta (ej: /opt/emulador/bin o C:\\Emuladores\\bin.exe). Si no, el juego no arranca en el gabinete sin avisar.', gameCount: 2 },
];

export const games: Game[] = [
  game({ id: 'goldnaxe', title: 'Golden Axe', video: video({ video: manual('/media/goldnaxe/video.mp4') }), manuals: [{ id: 'manual-goldnaxe', fileName: 'manual.pdf', status: 'processed', pages: 26 }] }),
  game({ id: 'sonic', title: 'Sonic The Hedgehog', systemId: 'genesis', identity: { format: 'Cartucho' }, images: images({ logo: suggested('/media/sonic/logo.png') }) }),
  game({ id: 'sf2', title: 'Street Fighter II', images: images({ poster: empty() }) }),
  game({ id: 'mslug', title: 'Metal Slug', identity: { title: 'Metal Slug', year: '', developer: '', publisher: '', genre: '', players: '', format: '' }, images: images({ caratula: empty(), marquesina: empty(), poster: empty() }), texts: texts({ sinopsis: { status: 'empty', value: '' } }), accent: 'empty', accentValue: '', accent2Value: '' }),
  game({ id: 'pacman', title: 'Pac-Man', errors: [{ field: 'Export', message: 'Rechazado por ATTRACT doctor.' }] }),
  game({ id: 'dkong', title: 'Donkey Kong', identity: { year: '197X' }, errors: [{ field: 'Año', message: 'Debe ser un número de 4 dígitos (contrato ATTRACT).' }] }),
  game({ id: 'mario', title: 'Super Mario Bros.', systemId: 'nes', identity: { format: 'Cartucho' }, manuals: [{ id: 'manual-mario', fileName: 'manual.pdf', status: 'unprocessed', pages: 0 }] }),
  game({ id: 'zelda', title: 'The Legend of Zelda', systemId: 'nes', identity: { format: 'Cartucho JP' }, errors: [{ field: 'Formato', message: 'Formato no reconocido por contrato ATTRACT.' }] }),
  game({ id: 'sor2', title: 'Streets of Rage 2', systemId: 'genesis', identity: { format: 'Cartucho' }, manuals: [{ id: 'manual-sor2', fileName: 'manual.pdf', status: 'processed', pages: 18 }] }),
  game({ id: 'contra', title: 'Contra', systemId: 'snes', identity: { format: 'Cartucho', year: '1987', developer: 'Konami', publisher: 'Konami', genre: 'Run and gun', players: '1-2' }, review: review({ status: 'suggested', source: 'IA', score: 88, cats: { graficos: 85, adiccion: 92, sonido: 84 } }), cheats: cheats({ status: 'manual', groups: [{ name: 'modo cooperativo', entries: [{ name: '30 vidas', input: '↑ ↑ ↓ ↓ ← → ← → B A' }] }] }) }),
];
