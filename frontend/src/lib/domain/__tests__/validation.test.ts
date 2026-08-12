import { describe, expect, it } from 'vitest';
import { ABSOLUTE_PATH_MESSAGE, HEX_COLOR_MESSAGE, YEAR_MESSAGE, absolutePath, hexColor, newSystemSchema, yearField } from '../validation';

describe('domain validation', () => {
  it('acepta rutas absolutas POSIX y Windows', () => {
    expect(absolutePath.parse('/opt/mame/mame64')).toBe('/opt/mame/mame64');
    expect(absolutePath.parse('C:\\Emu\\bin.exe')).toBe('C:\\Emu\\bin.exe');
  });

  it('rechaza rutas relativas con mensaje literal', () => {
    const result = absolutePath.safeParse('emulators/snes9x');
    expect(result.success).toBe(false);
    if (!result.success) expect(result.error.issues[0]?.message).toBe(ABSOLUTE_PATH_MESSAGE);
  });

  it('valida año de cuatro dígitos', () => {
    expect(yearField.parse('1989')).toBe('1989');
    const result = yearField.safeParse('197X');
    expect(result.success).toBe(false);
    if (!result.success) expect(result.error.issues[0]?.message).toBe(YEAR_MESSAGE);
  });

  it('valida HEX', () => {
    const color = `#${'2F6FED'}`;
    expect(hexColor.parse(color)).toBe(color);
    const result = hexColor.safeParse('2F6FED');
    expect(result.success).toBe(false);
    if (!result.success) expect(result.error.issues[0]?.message).toBe(HEX_COLOR_MESSAGE);
  });

  it('valida sistema nuevo', () => {
    expect(newSystemSchema.parse({ name: 'Arcade', shortName: 'arcade', launchCmd: '/usr/local/bin/mame' })).toEqual({ name: 'Arcade', shortName: 'arcade', launchCmd: '/usr/local/bin/mame' });
  });
});
