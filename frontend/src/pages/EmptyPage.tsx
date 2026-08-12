import { Panel, SectionHeader, SunkenBox } from '@/components/dos';
import styles from './EmptyPage.module.css';

interface EmptyPageProps {
  title: string;
}

export function EmptyPage({ title }: EmptyPageProps) {
  return <div className={styles.page}><h1>{title}</h1><Panel><SectionHeader>{title}</SectionHeader><SunkenBox><p className={styles.text}>Pantalla vacía. Contenido fuera de alcance de feature003.</p></SunkenBox></Panel></div>;
}
