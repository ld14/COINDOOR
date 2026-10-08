import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { DosButton, DosInput, Panel, SectionHeader, SunkenBox } from '@/components/dos';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, Identity, IdentityKey } from '@/lib/domain/types';
import type { SaveHandle } from './types';
import styles from '../ReadPages.module.css';

export const IdentitySection = forwardRef<SaveHandle, { game: Game; onSave: (identity: Identity) => void; onSuggest: (key: IdentityKey) => void; onSuggestBatch: () => void }>(function IdentitySection({ game, onSave, onSuggest, onSuggestBatch }, ref) {
  const [identity, setIdentity] = useState(game.identity);
  useEffect(() => setIdentity(game.identity), [game.identity]);
  useImperativeHandle(ref, () => ({ save: () => onSave(identity) }), [onSave, identity]);
  return (
    <Panel>
      <SectionHeader>IDENTIDAD</SectionHeader>
      <SunkenBox className={styles.fields}>
        {FIELDDEFS.identity.map((field) => (
          <label className={styles.field} key={field.key}>
            <span className={styles.label}>{field.label}</span>
            <DosInput
              aria-label={field.label}
              onChange={(event) => setIdentity({ ...identity, [field.key]: event.target.value })}
              value={identity[field.key]}
            />
            <DosButton onClick={() => onSuggest(field.key)} type="button" variant="ghost-small">Sugerir</DosButton>
          </label>
        ))}
      </SunkenBox>
      <div className={styles.toolbar}>
        <span className={styles.meta}>Fuente actual: {game.identitySource}</span>
        <DosButton onClick={onSuggestBatch} variant="ghost-small">Sugerir todo</DosButton>
        <DosButton onClick={() => onSave(identity)} variant="primary-small">Guardar identidad</DosButton>
      </div>
    </Panel>
  );
});
