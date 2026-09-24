import styles from './IFrameModalButton.module.css';
import { useRef, type PropsWithChildren } from 'react';

type Props = PropsWithChildren<{
  url: string;
  dialogHeader: string;
}>;

type DialogBounds = Pick<DOMRect, 'top' | 'right' | 'bottom' | 'left'>;

export const isOutsideDialog = (
  clientX: number,
  clientY: number,
  bounds: DialogBounds,
) =>
  clientX < bounds.left ||
  clientX > bounds.right ||
  clientY < bounds.top ||
  clientY > bounds.bottom;

export const IframeModalButton = ({ url, dialogHeader, children }: Props) => {
  const dialogRef = useRef<HTMLDialogElement | null>(null);
  const iframeUrl = `${url}${url.includes('?') ? '&' : '?'}embedded=true`;

  const openModal = (e: React.MouseEvent<HTMLAnchorElement, MouseEvent>) => {
    e.preventDefault();
    if (!dialogRef.current) {
      console.log("didn't find dialog ref");
      return;
    }
    dialogRef.current.showModal();
  };

  const closeModalFromBackdrop = (
    e: React.MouseEvent<HTMLDialogElement, MouseEvent>,
  ) => {
    const dialog = e.currentTarget;
    if (isOutsideDialog(e.clientX, e.clientY, dialog.getBoundingClientRect())) {
      dialog.close();
    }
  };

  return (
    <>
      <a href={url} onClick={openModal}>
        {children}
      </a>
      <dialog
        ref={dialogRef}
        className={styles.dialog}
        aria-label={dialogHeader}
        onClick={closeModalFromBackdrop}
      >
        <div className={styles.dialogHeader}>{dialogHeader}</div>
        <iframe
          src={iframeUrl}
          className={styles.dialogIframe}
          title={dialogHeader}
        ></iframe>
      </dialog>
    </>
  );
};
