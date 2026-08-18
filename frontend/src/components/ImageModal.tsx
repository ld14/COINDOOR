import { Modal } from '@/components/dos';
import styles from './ImageModal.module.css';

interface ImageModalProps {
  onClose: () => void;
  open: boolean;
  src: string;
  alt: string;
}

export function ImageModal({ onClose, open, src, alt }: ImageModalProps) {
  return (
    <Modal onClose={onClose} open={open} size="large" title={alt}>
      <div className={styles.container}>
        <img alt={alt} className={styles.image} src={src} />
      </div>
    </Modal>
  );
}
