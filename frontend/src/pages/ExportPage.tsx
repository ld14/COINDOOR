import { useParams } from 'react-router-dom';
import { ColaExportar } from './exportar/ColaExportar';
import { ExportarJuego } from './exportar/ExportarJuego';

/** `/exportar/:gameId` arma el paquete de un juego; `/exportar` es la cola. */
export function ExportPage() {
  const { gameId } = useParams<{ gameId: string }>();
  return gameId ? <ExportarJuego gameId={gameId} key={gameId} /> : <ColaExportar />;
}
