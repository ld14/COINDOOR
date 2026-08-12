import { z } from 'zod';

export const ABSOLUTE_PATH_MESSAGE = 'La ruta debe ser absoluta (ej: /opt/emulador/bin o C:\\Emuladores\\bin.exe). Si no, el juego no arranca en el gabinete sin avisar.';
const hash = '#';

export const HEX_COLOR_MESSAGE = `Formato inválido (ej: ${hash}2F6FED)`;
export const YEAR_MESSAGE = 'Debe ser un número de 4 dígitos (contrato ATTRACT).';

export const absolutePath = z.string().refine(
  (value) => value.startsWith('/') || /^[A-Za-z]:\\/.test(value),
  ABSOLUTE_PATH_MESSAGE,
);

export const hexColor = z.string().regex(/^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$/, HEX_COLOR_MESSAGE);
export const yearField = z.string().regex(/^\d{4}$/, YEAR_MESSAGE);

export const newSystemSchema = z.object({
  name: z.string().min(1, 'Requerido'),
  shortName: z.string().min(1, 'Requerido'),
  launchCmd: absolutePath,
});
