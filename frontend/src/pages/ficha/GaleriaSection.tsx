import { Card } from '@/components/dos';
import { GalleryPanel } from '@/components/GalleryPanel';
import type { Game } from '@/lib/domain/types';

/**
 * Galería (DESIGN_SPEC §5.1, paso 8): imágenes extra de ArcadeDB / ImageSearch / LaunchBox que viajan
 * en `media/_gallery/` si se tilda «Galería» al exportar (ADR-0016). No tiene estado local ni `save()`:
 * cada acción (traer, usar como…, borrar) escribe directo y avisa con `onChanged`.
 *
 * Para montarla, FichaJuego la usa como `node` de una sección `galeria` (hay que sumarla a `FICHA_SECCIONES`)
 * o la deja debajo de «Imágenes y video» en lugar del `GalleryPanel` viejo.
 */
export function GaleriaSection({ game, onChanged, numero = 8 }: {
  game: Game;
  onChanged: () => void;
  numero?: number;
}) {
  const cantidad = (game.gallery ?? []).length;
  return (
    <Card
      band="var(--accent-3)"
      data-campo="galeria"
      hint={cantidad > 0 ? `${cantidad} ${cantidad === 1 ? 'imagen' : 'imágenes'}` : 'opcional'}
      number={numero}
      title="Galería"
    >
      <GalleryPanel bare gallery={game.gallery ?? []} gameId={game.id} onChanged={onChanged} />
    </Card>
  );
}
