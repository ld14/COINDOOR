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

  it('no usa border-radius fuera del spinner', () => {
    const offenders = files(src).filter((file) => !file.endsWith('Spinner.module.css')).filter((file) => /border-radius\s*:\s*(?!0\b)/.test(readFileSync(file, 'utf8'))).map((file) => relative(src, file));
    expect(offenders).toEqual([]);
  });
});
