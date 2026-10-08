import type { ReactNode } from 'react';
import styles from './Banner.module.css';

interface BannerProps {
  children?: ReactNode;
}

/** Aviso de un problema. No se usa para informar que todo anda bien. */
export function Banner({ children }: BannerProps) {
  return <div className={styles.banner} role="alert"><span aria-hidden="true" className={styles.icon}>!</span><div>{children}</div></div>;
}
