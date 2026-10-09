import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { DosButton, DosInput, Modal } from '@/components/dos';
import { createSystem, type CreateSystemPayload } from '@/lib/api/systems';
import type { System } from '@/lib/domain/types';
import styles from './NuevoJuego.module.css';

const VACIO: CreateSystemPayload = { name: '', shortName: '', launchCmd: '' };

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: (system: System) => void;
}

/** Alta de sistema dentro del asistente: misma mutación que la pantalla Sistemas. */
export function NuevoSistemaModal({ open, onClose, onCreated }: Props) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(VACIO);
  const [error, setError] = useState('');
  const crear = useMutation({
    mutationFn: createSystem,
    onError: (err) => setError(err instanceof Error ? err.message : 'No se pudo crear el sistema.'),
    onSuccess: async (system) => {
      await queryClient.invalidateQueries({ queryKey: ['systems'] });
      setForm(VACIO);
      setError('');
      onCreated(system);
    },
  });

  return (
    <Modal band="var(--accent-3)" onClose={onClose} open={open} title="Nuevo sistema">
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault();
          setError('');
          crear.mutate(form);
        }}
      >
        <label className={styles.field}>
          <span className={styles.label}>Nombre</span>
          <DosInput aria-label="Nombre del sistema" onChange={(event) => setForm({ ...form, name: event.target.value })} required value={form.name} />
        </label>
        <label className={styles.field}>
          <span className={styles.label}>Nombre corto</span>
          <DosInput aria-label="Nombre corto" onChange={(event) => setForm({ ...form, shortName: event.target.value })} required value={form.shortName} />
        </label>
        <label className={styles.field}>
          <span className={styles.label}>Comando de lanzamiento</span>
          <DosInput aria-label="Comando de lanzamiento" onChange={(event) => setForm({ ...form, launchCmd: event.target.value })} required value={form.launchCmd} />
        </label>
        {error ? <p className={styles.error} role="alert">{error}</p> : null}
        <div className={styles.actions}>
          <DosButton onClick={onClose} type="button" variant="ghost">Cancelar</DosButton>
          <DosButton disabled={crear.isPending} type="submit" variant="primary">Crear sistema</DosButton>
        </div>
      </form>
    </Modal>
  );
}
