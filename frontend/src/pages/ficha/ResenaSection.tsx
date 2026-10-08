import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { DosButton, DosInput, FieldTag, Panel, SectionHeader, SunkenBox } from '@/components/dos';
import type { Game, ReviewCat } from '@/lib/domain/types';
import type { SaveHandle } from './types';
import styles from '../ReadPages.module.css';

export const ReviewSection = forwardRef<SaveHandle, { game: Game; onReview: (score: number | null, cats: Partial<Record<ReviewCat, number>>) => void; onSuggest: () => void }>(function ReviewSection({ game, onReview, onSuggest }, ref) {
  const [reviewScore, setReviewScore] = useState(String(game.review.score ?? ''));
  useEffect(() => setReviewScore(String(game.review.score ?? '')), [game.review.score]);
  useImperativeHandle(ref, () => ({ save: () => onReview(reviewScore ? Number(reviewScore) : null, game.review.cats) }), [onReview, reviewScore, game.review.cats]);
  return (
    <Panel>
      <SectionHeader>RESEÑA</SectionHeader>
      <SunkenBox className={styles.stack}>
        <div className={styles.fieldTop}><span className={styles.name}>Puntaje y categorías</span><FieldTag status={game.review.status} /></div>
        <div className={styles.reviewGrid}>
          <label className={styles.field}>
            <span className={styles.label}>Puntaje</span>
            <DosInput aria-label="Puntaje de reseña" onChange={(event) => setReviewScore(event.target.value)} placeholder="0-100" value={reviewScore} />
          </label>
          <div className={styles.scorePlate}>{reviewScore || '--'}</div>
        </div>
        <div className={styles.catGrid}>
          {Object.entries(game.review.cats).length ? Object.entries(game.review.cats).map(([cat, score]) => (
            <span className={styles.catPill} key={cat}>{cat}: {score}</span>
          )) : <span className={styles.empty}>Sin Información</span>}
        </div>
        <div className={styles.toolbar}>
          <DosButton onClick={() => onReview(reviewScore ? Number(reviewScore) : null, game.review.cats)} variant="primary-small">Guardar reseña</DosButton>
          <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton>
        </div>
      </SunkenBox>
    </Panel>
  );
});
