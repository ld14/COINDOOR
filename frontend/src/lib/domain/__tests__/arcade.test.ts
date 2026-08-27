import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { soportaArcadeDb } from '../arcade';

// Sistemas reales, variantes de mayusculas y los que no deben disparar precarga.
const casos = ['arcade', 'mame', 'MAME', 'Arcade', 'fbneo', 'neogeo', 'cps2', 'msdos', 'MSDOS', 'nes', 'genesis', 'snes', ''];

const script = `
import json
import sys
from backend.lib.domain.arcade import soporta_arcadedb

print(json.dumps([soporta_arcadedb(s) for s in json.load(sys.stdin)]))
`;

describe('soportaArcadeDb', () => {
  it('habilita sistemas de romsets MAME y descarta el resto', () => {
    expect(casos.map(soportaArcadeDb)).toEqual([
      true, true, true, true, true, true, true,
      false, false, false, false, false, false,
    ]);
  });

  it('TypeScript ↔ Python deciden igual', () => {
    const repoRoot = join(process.cwd(), '..');
    const result = spawnSync('python3', ['-c', script], {
      cwd: repoRoot,
      env: { ...process.env, PYTHONPATH: repoRoot },
      input: JSON.stringify(casos),
      encoding: 'utf8',
    });

    expect(result.stderr).toBe('');
    expect(result.status).toBe(0);
    expect(JSON.parse(result.stdout)).toEqual(casos.map(soportaArcadeDb));
  });
});
