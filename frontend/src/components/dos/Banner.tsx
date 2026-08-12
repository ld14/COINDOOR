import type { ReactNode } from 'react';
import styles from './Banner.module.css';

interface BannerProps {
  children?: ReactNode;
}

export function Banner({ children = 'Contrato ATTRACT cargado como dato versionado.' }: BannerProps) {
  return <div className={styles.banner}>{children}</div>;
}
