import { useEffect } from 'react';
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { Banner, Rail, StatusBar, TopBar } from '@/components/dos';
import { useShellCounts } from '@/hooks/useShellCounts';
import { contractStatus, type ContractStatus } from '@/lib/contractStatus';
import { Catalogo } from '@/pages/_Catalogo';
import { Configuracion } from '@/pages/Configuracion';
import { ExportPage } from '@/pages/ExportPage';
import { FichaJuego } from '@/pages/FichaJuego';
import { Juegos } from '@/pages/Juegos';
import { NuevoJuego } from '@/pages/NuevoJuego';
import { Sistemas } from '@/pages/Sistemas';
import styles from './App.module.css';

interface AppProps {
  /** Solo para tests: por defecto es el estado del contrato vendoreado. */
  contract?: ContractStatus;
}

export function App({ contract = contractStatus }: AppProps) {
  const navigate = useNavigate();
  const counts = useShellCounts();

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.defaultPrevented) return;
      if (event.key === 'F2') {
        event.preventDefault();
        navigate('/sistemas');
      } else if (event.key === 'F3') {
        event.preventDefault();
        navigate('/juegos');
      } else if (event.key === 'F4') {
        event.preventDefault();
        navigate('/exportar');
      } else if (event.key === 'F5') {
        event.preventDefault();
        navigate('/configuracion');
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [navigate]);

  return (
    <div className={styles.app}>
      <TopBar contract={contract} />
      <div className={styles.body}>
        <Rail counts={counts} />
        <main className={styles.content}>
          {!contract.ok && <Banner>{contract.problem}</Banner>}
          <Routes>
            <Route element={<Navigate replace to="/juegos" />} path="/" />
            <Route element={<Sistemas />} path="/sistemas" />
            <Route element={<Juegos />} path="/juegos" />
            <Route element={<NuevoJuego />} path="/juegos/nuevo" />
            <Route element={<FichaJuego />} path="/juegos/:gameId" />
            <Route element={<ExportPage />} path="/exportar" />
            <Route element={<ExportPage />} path="/exportar/:gameId" />
            <Route element={<Configuracion />} path="/configuracion" />
            <Route element={<Catalogo />} path="/_catalogo" />
          </Routes>
        </main>
      </div>
      <StatusBar contract={contract} />
    </div>
  );
}
