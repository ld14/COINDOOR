import { useEffect } from 'react';
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { Banner, MenuBar, StatusBar } from '@/components/dos';
import { Catalogo } from '@/pages/_Catalogo';
import { EmptyPage } from '@/pages/EmptyPage';
import styles from './App.module.css';

export function App() {
  const navigate = useNavigate();

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
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [navigate]);

  return (
    <div className={styles.app}>
      <header className={styles.titlebar}>COINDOOR · Preparador de metadata arcade</header>
      <main className={styles.body}>
        <MenuBar />
        <section className={styles.content}>
          <Banner />
          <Routes>
            <Route element={<Navigate replace to="/juegos" />} path="/" />
            <Route element={<EmptyPage title="Sistemas" />} path="/sistemas" />
            <Route element={<EmptyPage title="Juegos" />} path="/juegos" />
            <Route element={<EmptyPage title="Nuevo juego" />} path="/juegos/nuevo" />
            <Route element={<EmptyPage title="Ficha del juego" />} path="/juegos/:gameId" />
            <Route element={<EmptyPage title="Exportar" />} path="/exportar" />
            <Route element={<Catalogo />} path="/_catalogo" />
          </Routes>
        </section>
      </main>
      <StatusBar />
    </div>
  );
}
