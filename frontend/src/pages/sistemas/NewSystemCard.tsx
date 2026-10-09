import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, DosButton, DosInput } from '@/components/dos';
import { createSystem, type CreateSystemPayload } from '@/lib/api/systems';
import { absolutePath } from '@/lib/domain/validation';
import styles from './sistemas.module.css';

const EMPTY_SYSTEM: CreateSystemPayload = { name: '', shortName: '', launchCmd: '' };
const ABSOLUTE_HINT = 'Tiene que ser una ruta absoluta (ej.: /opt/emulador/bin o C:\\Emuladores\\snes9x.exe)';

export function NewSystemCard() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(EMPTY_SYSTEM);
  const [createError, setCreateError] = useState<string | null>(null);
  const create = useMutation({
    mutationFn: createSystem,
    onError: (err) => setCreateError(err instanceof Error ? err.message : 'No se pudo crear el sistema.'),
    onSuccess: async () => {
      setForm(EMPTY_SYSTEM);
      setCreateError(null);
      await queryClient.invalidateQueries({ queryKey: ['systems'] });
    },
  });

  const cmd = form.launchCmd.trim();
  const cmdError = cmd && !absolutePath.safeParse(cmd).success ? ABSOLUTE_HINT : undefined;
  const reason = !form.name.trim()
    ? 'Falta el nombre.'
    : !form.shortName.trim()
      ? 'Falta el nombre corto.'
      : !cmd
        ? 'Falta el comando de lanzamiento.'
        : cmdError;

  return (
    <Card className={[styles.scard, styles.new].join(' ')}>
      <h2 className={styles.newTitle}>Nuevo sistema</h2>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault();
          if (reason) return;
          create.mutate({ name: form.name.trim(), shortName: form.shortName.trim(), launchCmd: cmd });
        }}
      >
        <label className={styles.field}>
          Nombre
          <DosInput aria-label="Nombre del sistema" onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Ej.: Super Nintendo" required value={form.name} />
        </label>
        <label className={styles.field}>
          <span>Short name <span className={styles.hint}>· se usa en rutas y en el paquete</span></span>
          <DosInput aria-label="Short name" className={styles.mono} onChange={(event) => setForm({ ...form, shortName: event.target.value })} required value={form.shortName} />
        </label>
        <label className={styles.field}>
          Comando de lanzamiento
          <DosInput
            aria-label="Comando de lanzamiento"
            className={styles.mono}
            errorMessage={cmdError ? `✕ ${cmdError}` : undefined}
            onChange={(event) => setForm({ ...form, launchCmd: event.target.value })}
            required
            value={form.launchCmd}
          />
        </label>
        {/* TODO(backend): [Examinar…] necesita un endpoint que abra un selector de archivos del lado del servidor; el navegador no expone rutas absolutas. */}
        <div className={styles.actions}>
          <DosButton onClick={() => { setForm(EMPTY_SYSTEM); setCreateError(null); }} size="sm" variant="ghost">Cancelar</DosButton>
          <DosButton disabled={create.isPending || !!reason} disabledReason={reason} size="sm" type="submit" variant="primary">Crear sistema</DosButton>
        </div>
        {createError ? <p className={styles.error}>{createError}</p> : null}
      </form>
    </Card>
  );
}
