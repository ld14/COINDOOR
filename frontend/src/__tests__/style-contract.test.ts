import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const src = join(process.cwd(), 'src');

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    return statSync(path).isDirectory() ? files(path) : [path];
  });
}

describe('style contract', () => {
  it('no usa hex fuera de tokens.css', () => {
    const offenders = files(src).filter((file) => !file.endsWith('tokens.css')).filter((file) => /#[0-9A-Fa-f]{3,8}/.test(readFileSync(file, 'utf8'))).map((file) => relative(src, file));
    expect(offenders).toEqual([]);
  });

  it('los radios salen de los tokens --radius-* (ADR-0023)', () => {
    // Se admite 0 y 50% (el spinner es un círculo); cualquier otro valor va por token.
    const allowed = /^(0|0px|50%|var\(--radius-(sm|md|lg|pill)\))$/;
    const offenders = files(src)
      .filter((file) => file.endsWith('.css') && !file.endsWith('tokens.css'))
      .flatMap((file) => [...readFileSync(file, 'utf8').matchAll(/border(?:-[a-z]+){0,2}-radius\s*:\s*([^;}]+)/g)]
        .filter((match) => !match[1].trim().split(/\s+(?![^(]*\))/).every((value) => allowed.test(value)))
        .map((match) => `${relative(src, file)}: ${match[0]}`));
    expect(offenders).toEqual([]);
  });

  it('no hay valores de radio sueltos en estilos inline de TSX', () => {
    const offenders = files(src).filter((file) => file.endsWith('.tsx')).filter((file) => /borderRadius/.test(readFileSync(file, 'utf8'))).map((file) => relative(src, file));
    expect(offenders).toEqual([]);
  });
});
