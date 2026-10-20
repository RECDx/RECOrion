import React, { useEffect, useState } from 'react';
import { Library } from 'lucide-react';
import { api } from '../../api';
import { Badge, Button, EmptyState, Modal } from '../../ui/components';
import { toast } from '../../ui/feedback';
import './catalog.css';

const GROUPS = [
  [0, 'Meslek grubunuza özel'],
  [1, 'Sektörünüze özel'],
  [2, 'Genel departmanlar'],
];

/** Şirket: sektör ve meslek gruplarına uygun katalog departmanlarını seçip şirkete ekler. */
export default function CatalogImportModal({ tenantId, open, onClose, onImported }) {
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    setData(null);
    api.getCompanyCatalogRecommended(tenantId)
      .then((d) => { setData(d); setSelected(d.departments.filter((x) => !x.imported && x.rank < 2).map((x) => x.id)); })
      .catch((e) => toast.error(e.message));
  }, [open, tenantId]);

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const submit = async () => {
    setBusy(true);
    try {
      const r = await api.importCatalogDepartments(tenantId, selected);
      toast.success(r.created.length ? `${r.created.length} departman eklendi.` : 'Seçilen departmanlar zaten tanımlı.');
      onImported?.();
      onClose();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Katalogdan Departman Ekle" size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Vazgeç</Button><Button onClick={submit} disabled={busy || !selected.length}>{selected.length} Departmanı Ekle</Button></>}>
      {!data ? <p className="cat-hint">Yükleniyor…</p> : data.departments.length === 0 ? (
        <EmptyState icon={Library} title="Uygun departman bulunamadı" description="Şirketinizin sektör ve meslek grubu bilgilerini Sektörel Manifesto sekmesinden kontrol edin." />
      ) : (
        <div className="cat-pick">
          <span className="cat-hint">Şirketinizin sektör ve meslek gruplarına göre önerilen RECOrion departmanları. Eklenen departmanlara ait unvanlar AI personel işe alımında önerilir.</span>
          {GROUPS.map(([rank, label]) => {
            const rows = data.departments.filter((d) => d.rank === rank);
            if (!rows.length) return null;
            return (
              <React.Fragment key={rank}>
                <strong style={{ fontSize: '0.8rem', marginTop: 8 }}>{label}</strong>
                {rows.map((d) => (
                  <label key={d.id} className={d.imported ? 'done' : ''}>
                    <input type="checkbox" disabled={d.imported} checked={d.imported || selected.includes(d.id)} onChange={() => toggle(d.id)} />
                    <span style={{ flex: 1 }}>
                      {d.name} {d.imported && <Badge tone="success">Ekli</Badge>}
                      <p>{d.description} · {d.title_count} uygun unvan</p>
                    </span>
                  </label>
                ))}
              </React.Fragment>
            );
          })}
        </div>
      )}
    </Modal>
  );
}
