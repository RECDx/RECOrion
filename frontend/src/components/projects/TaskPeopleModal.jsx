import React, { useEffect, useState } from 'react';
import { api } from '../../api';
import { Button, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';

/**
 * F92: plan onaylandıktan sonra adımın kontrol personelini (veya onaylayıcısını, başlamamışsa AI personelini) değiştirme.
 * Kontrol personeli kaldırılabilir; değişiklik akış geçmişine yazılır, çalışan adımda bir sonraki teslimde geçerli olur.
 */
export default function TaskPeopleModal({ task, onClose, onSaved }) {
  const [opts, setOpts] = useState(null);
  const [form, setForm] = useState({ reviewer: '', approver: '', assignee: '', note: '' });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getTaskPeople(task.id).then((o) => {
      setOpts(o);
      setForm({ reviewer: o.reviewer_actor_id || '', approver: o.approver_actor_id || '', assignee: o.assignee_actor_id || '', note: '' });
    }).catch((e) => { toast.error(e.message); onClose(); });
  }, [task.id, onClose]);

  const save = async () => {
    setBusy(true);
    try {
      await api.setTaskPeople(task.id, {
        reviewer_actor_id: form.reviewer || null, approver_actor_id: form.approver || null,
        assignee_actor_id: opts.can_change_assignee ? (form.assignee || null) : null, note: form.note || null,
      });
      toast.success('Adımın kişileri güncellendi.');
      onSaved?.();
      onClose();
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const label = (a) => `${a.name}${a.role ? ` — ${a.role}` : ''}`;

  return (
    <Modal open onClose={onClose} title={`Adımın kişileri: ${task.title}`}
      footer={<><Button variant="ghost" onClick={onClose}>Vazgeç</Button><Button onClick={save} disabled={busy || !opts}>Kaydet</Button></>}>
      {!opts ? <p className="pj-hint">Yükleniyor…</p> : (
        <div className="pj-steps">
          <label className="pj-hint" htmlFor="tp-rev">Kontrol personeli (AI)</label>
          <select id="tp-rev" className="ui-input" value={form.reviewer} onChange={set('reviewer')}>
            <option value="">Kontrol personeli yok (doğrudan onaya düşer)</option>
            {opts.reviewers.filter((a) => a.id !== form.assignee).map((a) => <option key={a.id} value={a.id}>{label(a)}</option>)}
          </select>
          <label className="pj-hint" htmlFor="tp-app">Onaylayıcı</label>
          <select id="tp-app" className="ui-input" value={form.approver} onChange={set('approver')}>
            <option value="">Proje yöneticisi</option>
            {opts.approvers.map((a) => <option key={a.id} value={a.id}>{label(a)}</option>)}
          </select>
          {opts.can_change_assignee && (
            <>
              <label className="pj-hint" htmlFor="tp-asg">İşi yapacak AI personel (adım henüz başlamadı)</label>
              <select id="tp-asg" className="ui-input" value={form.assignee} onChange={set('assignee')}>
                {opts.assignees.map((a) => <option key={a.id} value={a.id}>{label(a)}</option>)}
              </select>
            </>
          )}
          <label className="pj-hint" htmlFor="tp-note">Not (isteğe bağlı, akış geçmişine yazılır)</label>
          <input id="tp-note" className="ui-input" value={form.note} onChange={set('note')} maxLength={1000} />
          <p className="pj-hint" style={{ margin: 0 }}>Çalışan adımda değişiklik bir sonraki teslimde geçerli olur.</p>
        </div>
      )}
    </Modal>
  );
}
