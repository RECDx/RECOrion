import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';
import { dismissToast, subscribeFeedback } from './feedback';

const ICONS = { success: CheckCircle2, error: AlertCircle, warning: AlertTriangle, info: Info };

function Dialog({ dialog }) {
  const [value, setValue] = useState(dialog.defaultValue ?? '');
  const inputRef = useRef(null);
  const confirmRef = useRef(null);

  useEffect(() => {
    (dialog.kind === 'prompt' ? inputRef.current : confirmRef.current)?.focus();
    const onKey = (e) => {
      if (e.key === 'Escape') dialog.resolve(dialog.kind === 'prompt' ? null : false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [dialog]);

  const submit = (e) => {
    e.preventDefault();
    dialog.resolve(dialog.kind === 'prompt' ? value : true);
  };
  const cancel = () => dialog.resolve(dialog.kind === 'prompt' ? null : false);

  return (
    <div className="ui-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && cancel()}>
      <form className="ui-modal ui-modal-sm" role="alertdialog" aria-modal="true" aria-labelledby="ui-dialog-title" onSubmit={submit}>
        <div className="ui-modal-header">
          <h3 id="ui-dialog-title" className="ui-modal-title">
            {dialog.danger ? <AlertTriangle size={18} className="ui-text-danger" /> : <Info size={18} className="ui-text-accent" />}
            {dialog.title}
          </h3>
          <button type="button" className="ui-icon-btn" onClick={cancel} aria-label="Kapat"><X size={16} /></button>
        </div>
        <div className="ui-modal-body">
          <p className="ui-dialog-message">{dialog.message}</p>
          {dialog.kind === 'prompt' && (
            <input ref={inputRef} className="ui-input" value={value} onChange={(e) => setValue(e.target.value)} />
          )}
        </div>
        <div className="ui-modal-footer">
          <button type="button" className="ui-btn ui-btn-ghost" onClick={cancel}>{dialog.cancelText}</button>
          <button ref={confirmRef} type="submit" className={`ui-btn ${dialog.danger ? 'ui-btn-danger' : 'ui-btn-primary'}`}>
            {dialog.confirmText}
          </button>
        </div>
      </form>
    </div>
  );
}

/** Toast ve onay pencerelerini çizer; uygulamada bir kez kullanılır. */
export default function FeedbackHost() {
  const [state, setState] = useState({ toasts: [], dialog: null });
  useEffect(() => subscribeFeedback(setState), []);

  return (
    <>
      <div className="ui-toast-stack" role="region" aria-live="polite" aria-label="Bildirimler">
        {state.toasts.map((t) => {
          const Icon = ICONS[t.type];
          return (
            <div key={t.id} className={`ui-toast ui-toast-${t.type}`} role={t.type === 'error' ? 'alert' : 'status'}>
              <Icon size={18} className="ui-toast-icon" />
              <div className="ui-toast-message">{t.message}</div>
              <button className="ui-icon-btn" onClick={() => dismissToast(t.id)} aria-label="Bildirimi kapat"><X size={14} /></button>
            </div>
          );
        })}
      </div>
      {state.dialog && <Dialog key={state.dialog.message} dialog={state.dialog} />}
    </>
  );
}
