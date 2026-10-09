import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { Card, DosButton, DosInput, OriginChip, ProgressBar } from '@/components/dos';
import { FICHA_SECCIONES } from '@/hooks/useFichaProgress';
import type { Game, ReviewCat } from '@/lib/domain/types';
import { useFichaAutosave } from './autosaveContext';
import { AvisoSugerido, EtiquetaIA } from './origenIA';
import type { SaveHandle } from './types';
import styles from './ResenaSection.module.css';

// La escala guardada es 0-100 también para las categorías (delta D1). Una categoría vacía es un valor legítimo.
const CATEGORIAS: { key: ReviewCat; label: string }[] = [
  { key: 'originalidad', label: 'Originalidad' },
  { key: 'graficos', label: 'Gráficos' },
  { key: 'adiccion', label: 'Adicción' },
  { key: 'sonido', label: 'Sonido' },
  { key: 'dificultad', label: 'Dificultad' },
  { key: 'animacion', label: 'Animación' },
];

type CatsTexto = Record<ReviewCat, string>;

function aNumero(texto: string): number | null {
  if (texto.trim() === '') return null;
  const n = Number(texto);
  return Number.isFinite(n) ? Math.min(100, Math.max(0, Math.round(n))) : null;
}

function catsATexto(cats: Game['review']['cats']): CatsTexto {
  return Object.fromEntries(CATEGORIAS.map(({ key }) => [key, cats[key] === undefined ? '' : String(cats[key])])) as CatsTexto;
}

function catsANumeros(texto: CatsTexto): Game['review']['cats'] {
  const cats: Game['review']['cats'] = {};
  for (const { key } of CATEGORIAS) {
    const valor = aNumero(texto[key]);
    if (valor !== null) cats[key] = valor;
  }
  return cats;
}

const firmaCats = (cats: Game['review']['cats']) => JSON.stringify(CATEGORIAS.map(({ key }) => cats[key] ?? null));

export const ReviewSection = forwardRef<SaveHandle, {
  game: Game;
  onReview: (score: number | null, cats: Partial<Record<ReviewCat, number>>) => void;
  onSuggest: () => void;
  /** Número del círculo del encabezado. Por defecto el del paso en el StepNav. */
  numero?: number;
}>(function ReviewSection({ game, onReview, onSuggest, numero }, ref) {
  const { aceptar } = useFichaAutosave();
  const { score, cats, status, source } = game.review;
  const [puntaje, setPuntaje] = useState(score === null ? '' : String(score));
  const [categorias, setCategorias] = useState<CatsTexto>(() => catsATexto(cats));

  const catsServidor = firmaCats(cats);
  useEffect(() => setPuntaje(score === null ? '' : String(score)), [score]);
  useEffect(() => setCategorias(catsATexto(cats)), [catsServidor]); // eslint-disable-line react-hooks/exhaustive-deps

  const puntajeNumero = aNumero(puntaje);
  const catsNumeros = catsANumeros(categorias);

  // Solo se escribe lo que cambió: una reseña sugerida que nadie tocó no se marca como manual.
  useImperativeHandle(ref, () => ({
    save: () => {
      if (puntajeNumero === score && firmaCats(catsNumeros) === catsServidor) return;
      onReview(puntajeNumero, catsNumeros);
    },
  }), [onReview, puntajeNumero, score, catsNumeros, catsServidor]);

  const cargadas = CATEGORIAS.filter(({ key }) => catsNumeros[key] !== undefined).length;
  const sinResena = puntajeNumero === null && cargadas === 0;
  const pasoNumero = numero ?? FICHA_SECCIONES.findIndex((s) => s.clave === 'resena') + 1;

  return (
    <Card
      actions={(
        <DosButton aria-label="Sugerir reseña" onClick={onSuggest} size="sm" title="Sugerir desde ArcadeDB" variant="secondary">↻</DosButton>
      )}
      band="var(--accent-3)"
      data-campo="review"
      hint="puntaje 0–100 y categorías"
      number={pasoNumero}
      title="Reseña"
    >
      <div className={styles.cuerpo}>
        <div className={styles.origen}>
          <OriginChip source={source} status={status} />
          <EtiquetaIA source={source} />
        </div>

        {status === 'suggested' ? <AvisoSugerido nombre="la reseña" onAceptar={() => aceptar('review')} source={source} /> : null}

        <div className={styles.grilla}>
          <div className={styles.puntaje}>
            <div className={styles.lectura}>
              <span className={styles.numero}>{puntajeNumero === null ? '--' : puntajeNumero}</span>
              <span className={styles.sobre}>/ 100</span>
            </div>
            <ProgressBar label="Puntaje de la reseña" state="ok" value={puntajeNumero ?? 0} />
            <label className={styles.campo}>
              <span className={styles.rotulo}>Puntaje</span>
              <DosInput
                aria-label="Puntaje de reseña"
                className={styles.entrada}
                inputMode="numeric"
                max={100}
                min={0}
                onBlur={() => setPuntaje(puntajeNumero === null ? '' : String(puntajeNumero))}
                onChange={(event) => setPuntaje(event.target.value)}
                placeholder="0–100"
                type="number"
                value={puntaje}
              />
            </label>
          </div>

          <div className={styles.categorias}>
            <span className={styles.rotulo}>Categorías (0–100, todas opcionales)</span>
            {CATEGORIAS.map(({ key, label }) => (
              <div className={styles.cat} key={key}>
                <span className={styles.catNombre}>{label}</span>
                <div className={styles.catBarra}>
                  <ProgressBar label={`Barra de ${label}`} value={catsNumeros[key] ?? 0} />
                </div>
                <DosInput
                  aria-label={`${label} (0–100)`}
                  className={styles.catEntrada}
                  inputMode="numeric"
                  max={100}
                  min={0}
                  onBlur={() => setCategorias((previo) => ({ ...previo, [key]: catsNumeros[key] === undefined ? '' : String(catsNumeros[key]) }))}
                  onChange={(event) => setCategorias((previo) => ({ ...previo, [key]: event.target.value }))}
                  placeholder="—"
                  type="number"
                  value={categorias[key]}
                />
              </div>
            ))}
          </div>
        </div>

        {sinResena ? (
          <p className={styles.estado}>Todavía no hay reseña. Con un puntaje general alcanza; las categorías son opcionales.</p>
        ) : cargadas < CATEGORIAS.length ? (
          <p className={styles.estado}>
            {puntajeNumero === null ? 'Sin puntaje general. ' : ''}
            {cargadas} de {CATEGORIAS.length} categorías cargadas — dejar categorías vacías es válido.
          </p>
        ) : null}
      </div>
    </Card>
  );
});
