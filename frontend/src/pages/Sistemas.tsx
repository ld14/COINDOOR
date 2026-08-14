import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { DosButton, DosInput, Panel, SectionHeader, Spinner, SunkenBox } from '@/components/dos';
import { createSystem, type CreateSystemPayload } from '@/lib/api/systems';
import { useSystems } from '@/hooks/useSystems';
import styles from './ReadPages.module.css';

const EMPTY_SYSTEM: CreateSystemPayload = { name: '', shortName: '', launchCmd: '' };

export function Sistemas() {
  const { data, error, isLoading } = useSystems();
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

  return (
    <div className={styles.page}>
      <header>
        <h1 className={styles.title}>Sistemas / Plataformas</h1>
        <p className={styles.subtitle}>Un juego siempre pertenece a un sistema. La ruta del comando de lanzamiento debe ser absoluta.</p>
      </header>

      <Panel>
        <SectionHeader>Nuevo sistema</SectionHeader>
        <form
          className={styles.fields}
          onSubmit={(event) => {
            event.preventDefault();
            create.mutate(form);
          }}
        >
          <label className={styles.field}>
            <span className={styles.label}>Nombre</span>
            <DosInput aria-label="Nombre del sistema" onChange={(event) => setForm({ ...form, name: event.target.value })} required value={form.name} />
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Short name</span>
            <DosInput aria-label="Short name" onChange={(event) => setForm({ ...form, shortName: event.target.value })} required value={form.shortName} />
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Comando de lanzamiento</span>
            <DosInput aria-label="Comando de lanzamiento" onChange={(event) => setForm({ ...form, launchCmd: event.target.value })} required value={form.launchCmd} />
          </label>
          <div className={styles.formActions}>
            <DosButton disabled={create.isPending} type="submit" variant="primary-small">Crear sistema</DosButton>
          </div>
        </form>
        {createError ? <p className={styles.error}>{createError}</p> : null}
      </Panel>

      {isLoading ? <Spinner /> : null}
      {error ? <p className={styles.error}>No se pudieron cargar los sistemas.</p> : null}

      <div className={styles.grid}>
        {(data ?? []).map((system) => (
          <Panel className={[styles.systemCard, !system.valid ? styles.invalidCard : ''].filter(Boolean).join(' ')} key={system.id}>
            <div className={styles.cardTop}>
              <div>
                <div className={styles.name}>{system.name}</div>
                <p className={styles.meta}>{system.shortName}</p>
              </div>
              {!system.valid ? <span className={styles.invalidLabel}>CABECERA INVÁLIDA</span> : null}
            </div>
            <p className={styles.meta}>{system.gameCount} juegos</p>
            <div className={styles.command}>{system.launchCmd}</div>
            {!system.valid ? <p className={styles.error}>X {system.errorMsg}</p> : null}
          </Panel>
        ))}
      </div>

      {!isLoading && data?.length === 0 ? (
        <Panel><SectionHeader>Sistemas</SectionHeader><SunkenBox><p className={styles.empty}>No hay sistemas cargados.</p></SunkenBox></Panel>
      ) : null}
    </div>
  );
}
