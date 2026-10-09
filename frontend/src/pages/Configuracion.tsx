import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, DosButton, DosInput, Spinner } from '@/components/dos';
import { updateConfig } from '@/lib/api/config';
import { absolutePath } from '@/lib/domain/validation';
import { useConfig } from '@/hooks/useConfig';
import styles from './configuracion/configuracion.module.css';

type Probe = { ok: true } | { ok: false; message: string } | null;

export function Configuracion() {
  const { data, error, isLoading } = useConfig();
  const queryClient = useQueryClient();
  const [attractDir, setAttractDir] = useState('');
  const [saved, setSaved] = useState(false);
  const [probe, setProbe] = useState<Probe>(null);

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

  // TODO(backend): no hay endpoint que pruebe el checkout de ATTRACT (existencia + versión de contrato).
  // Hasta entonces [Probar] valida solo el formato de la ruta; no afirma que exista.
  function runProbe() {
    const value = attractDir.trim();
    if (!value) return setProbe({ ok: false, message: 'Escribí la ruta del checkout de ATTRACT.' });
    const parsed = absolutePath.safeParse(value);
    setProbe(parsed.success ? { ok: true } : { ok: false, message: parsed.error.issues[0]?.message ?? 'La ruta no es válida.' });
  }

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <h1>Configuración</h1>
        <p className={styles.sub}>
          Ajustes de esta instalación de COINDOOR. Las credenciales de IA y del buscador van en <code>.env</code>, no acá.
        </p>
      </header>

      <div className={styles.cfg}>
        <Card band="var(--accent-3)" hint="necesario para “Cargar en ATTRACT”" title="ATTRACT">
          <form
            className={styles.form}
            onSubmit={(event) => {
              event.preventDefault();
              setSaved(false);
              save.mutate(attractDir);
            }}
          >
            <label>
              <span className={styles.fieldHead}>
                <span>Ruta de ATTRACT</span>
                {probe?.ok ? <span className={styles.meta}>formato de ruta válido · no se verificó que exista</span> : null}
              </span>
              <span className={styles.inline}>
                <DosInput
                  aria-label="Ruta de ATTRACT"
                  className={styles.mono}
                  errorMessage={probe && !probe.ok ? `✕ ${probe.message}` : undefined}
                  onChange={(event) => { setAttractDir(event.target.value); setProbe(null); setSaved(false); }}
                  placeholder="/mnt/d/Juegos/attract"
                  value={attractDir}
                />
                <DosButton onClick={runProbe} variant="secondary">Probar</DosButton>
              </span>
            </label>
            <p className={styles.meta}>
              Checkout local de ATTRACT. Necesaria para &quot;Cargar en ATTRACT&quot; al exportar.
            </p>
            <div className={styles.actions}>
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
        </Card>

        <Card band="var(--accent-2)" hint="estado de las conexiones (solo lectura)" title="Servicios">
          {/* TODO(backend): sin endpoint de estado de servicios (ArcadeDB, IA, buscador de imágenes). No se inventa uno. */}
          <p className={styles.pending}>
            Pendiente: el backend todavía no expone el estado de ArcadeDB, la IA ni el buscador de imágenes. Cuando lo haga, acá se
            va a ver un punto de estado por servicio y qué se desactiva si falta la clave en <code>.env</code>. Nunca se muestran los valores.
          </p>
        </Card>

        <Card band="var(--accent)" hint="valores por defecto" title="Carga y exportación">
          {/* TODO(backend): configuracion.json (ADR-0022) solo guarda attractDir; faltan campos para estos valores por defecto. */}
          <p className={styles.pending}>
            Pendiente: precargar ArcadeDB al crear, incluir lo opcional al exportar y el tratamiento por defecto necesitan un lugar
            donde guardarse (configuracion.json hoy solo guarda la ruta de ATTRACT).
          </p>
        </Card>
      </div>
    </div>
  );
}
