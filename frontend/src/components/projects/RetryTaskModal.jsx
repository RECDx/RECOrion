import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { Button, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';

/**
 * C3-43 / C3-50: karantinadaki adımı yeniden denemeye açma. Yönetici personele yönlendirme notu yazar (AI'ya öncelikli
 * düzeltme isteği olarak gider) ve gerekirse adımı başka bir AI personele verir (ör. sorun test uzmanının kapsamı dışındaysa).
 */
export default function RetryTaskModal({ task, onClose, onDone }) {
  const [opts, setOpts] = useState(null);
  const [assignee, setAssignee] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getTaskPeople(task.id).then((o) => { setOpts(o); setAssignee(o.assignee_actor_id || ''); })
      .catch((e) => { toast.error(e.message); onClose(); });
  }, [task.id, onClose]);

  const save = async () => {
    setBusy(true);
    try {
      const changed = opts && assignee && assignee !== opts.assignee_actor_id;
      await api.releaseTask(task.id, 'retry', note.trim(), changed ? assignee : null);
      toast.success('Adım yeniden denemeye açıldı.');
      onDone?.();
      onClose();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const label = (a) => `${a.name}${a.role ? ` — ${a.role}` : ''}`;

  return (
    <Modal open onClose={onClose} title={`Yeniden dene: ${task.title}`}
      footer={<><Button variant="ghost" onClick={onClose}>Vazgeç</Button><Button onClick={save} disabled={busy || !opts}>Yeniden dene</Button></>}>
      {!opts ? <p className="pj-hint">Yükleniyor…</p> : (
        <div className="pj-steps">
          <label className="pj-hint" htmlFor="rt-asg">İşi yapacak AI personel</label>
          <select id="rt-asg" className="ui-input" value={assignee} onChange={(e) => setAssignee(e.target.value)}>
            {opts.assignees.filter((a) => a.id !== opts.reviewer_actor_id).map((a) => <option key={a.id} value={a.id}>{label(a)}</option>)}
          </select>
          <label className="pj-hint" htmlFor="rt-note">Personele yönlendirme notu (isteğe bağlı; ör. sorunun kök nedeni, hangi dosyanın düzeltileceği)</label>
          <textarea id="rt-note" className="ui-input" rows={6} value={note} onChange={(e) => setNote(e.target.value)} maxLength={3000} />
          <p className="pj-hint" style={{ margin: 0 }}>Yeniden denemek ret sayacını sıfırlar; not akış geçmişine yazılır ve personele öncelikli düzeltme isteği olarak gider.</p>
        </div>
      )}
    </Modal>
  );
}
