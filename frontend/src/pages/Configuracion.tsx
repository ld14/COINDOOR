import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { DosButton, DosInput, Panel, SectionHeader, Spinner } from '@/components/dos';
import { updateConfig } from '@/lib/api/config';
import { useConfig } from '@/hooks/useConfig';
import styles from './ReadPages.module.css';

export function Configuracion() {
  const { data, error, isLoading } = useConfig();
  const queryClient = useQueryClient();
  const [attractDir, setAttractDir] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (data) setAttractDir(data.attractDir ?? '');
  }, [data]);

  const save = useMutation({
    mutationFn: updateConfig,
    onError: () => setSaved(false),
    onSuccess: async (result) => {
      setSaved(true);
      setAttractDir(result.attractDir ?? '');
      await queryClient.invalidateQueries({ queryKey: ['config'] });
    },
  });

  return (
    <div className={styles.page}>
      <header>
        <h1 className={styles.title}>Configuración</h1>
        <p className={styles.subtitle}>
          Ajustes de esta instalación de COINDOOR. Las credenciales de IA y del buscador van en .env, no acá.
        </p>
      </header>

      <Panel>
        <SectionHeader>ATTRACT</SectionHeader>
        <form
          className={styles.fields}
          onSubmit={(event) => {
            event.preventDefault();
            setSaved(false);
            save.mutate(attractDir);
          }}
        >
          <label className={styles.field}>
            <span className={styles.label}>Ruta de ATTRACT</span>
            <DosInput
              aria-label="Ruta de ATTRACT"
              onChange={(event) => setAttractDir(event.target.value)}
              placeholder="/mnt/d/Juegos/attract"
              value={attractDir}
            />
          </label>
          <p className={styles.meta}>
            Checkout local de ATTRACT. Necesaria para &quot;Cargar en ATTRACT&quot; al exportar.
          </p>
          <div className={styles.formActions}>
            <DosButton disabled={save.isPending} type="submit" variant="primary-small">Guardar</DosButton>
          </div>
        </form>
        {isLoading ? <Spinner /> : null}
        {error ? <p className={styles.error}>No se pudo cargar la configuración.</p> : null}
        {save.isError ? (
          <p className={styles.error}>
            {save.error instanceof Error ? save.error.message : 'No se pudo guardar la configuración.'}
          </p>
        ) : null}
        {saved ? <p className={styles.meta}>Guardado.</p> : null}
      </Panel>
    </div>
  );
}
