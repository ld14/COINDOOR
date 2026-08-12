import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { computeGameStatus, missingRequired } from '../completeness';
import { games } from '@/mocks/seed';

const script = `
import json
import sys
from backend.lib.domain.completeness import compute_game_status, missing_required

games = json.load(sys.stdin)
print(json.dumps([
  {"id": game["id"], "missing": missing_required(game), "status": compute_game_status(game)}
  for game in games
], ensure_ascii=False))
`;

describe('TypeScript ↔ Python parity', () => {
  it('devuelve los mismos faltantes y estados sobre el seed', () => {
    const repoRoot = join(process.cwd(), '..');
    const result = spawnSync('python3', ['-c', script], {
      cwd: repoRoot,
      env: { ...process.env, PYTHONPATH: repoRoot },
      input: JSON.stringify(games),
      encoding: 'utf8',
    });

    expect(result.stderr).toBe('');
    expect(result.status).toBe(0);
    expect(JSON.parse(result.stdout)).toEqual(games.map((game) => ({
      id: game.id,
      missing: missingRequired(game),
      status: computeGameStatus(game),
    })));
  });
});
