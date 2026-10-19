/**
 * RECOrion ortak arayüz bileşenleri. Stiller: src/ui/ui.css
 * Yeni ekranlar satır içi stil yerine bu bileşenlerle yazılmalıdır.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Search, X } from 'lucide-react';

export function Button({ variant = 'primary', size = 'md', icon: Icon, children, className = '', ...props }) {
  return (
    <button className={`ui-btn ui-btn-${variant} ui-btn-${size} ${className}`} {...props}>
      {Icon && <Icon size={size === 'sm' ? 14 : 16} />}
      {children}
    </button>
  );
}

export function Card({ title, subtitle, actions, children, className = '', ...props }) {
  return (
    <section className={`ui-card ${className}`} {...props}>
      {(title || actions) && (
        <header className="ui-card-header">
          <div>
            {title && <h3 className="ui-card-title">{title}</h3>}
            {subtitle && <p className="ui-card-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="ui-card-actions">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export function Badge({ tone = 'neutral', children }) {
  return <span className={`ui-badge ui-badge-${tone}`}>{children}</span>;
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="ui-empty">
      {Icon && <Icon size={34} className="ui-empty-icon" />}
      <h4>{title}</h4>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}

/** Mobilde tam ekran açılan, ESC ile kapanan modal. */
export function Modal({ open, onClose, title, size = 'md', footer, children }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose?.();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="ui-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}>
      <div className={`ui-modal ui-modal-${size}`} role="dialog" aria-modal="true" aria-label={title}>
        <div className="ui-modal-header">
          <h3 className="ui-modal-title">{title}</h3>
          <button type="button" className="ui-icon-btn" onClick={onClose} aria-label="Kapat"><X size={16} /></button>
        </div>
        <div className="ui-modal-body">{children}</div>
        {footer && <div className="ui-modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

/**
 * Arama, sıralama ve sayfalama destekli tablo. Dar ekranlarda satırlar karta dönüşür.
 * columns: [{ key, label, render?(row), sortValue?(row), searchValue?(row), align?, hideOnMobile? }]
 */
export function DataTable({
  columns, rows, rowKey = (r) => r.id, pageSize = 20, searchPlaceholder = 'Ara…',
  emptyText = 'Kayıt bulunamadı.', toolbar, onRowClick,
}) {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState({ key: null, dir: 'asc' });
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    const q = query.trim().toLocaleLowerCase('tr');
    let list = rows || [];
    if (q) {
      list = list.filter((r) => columns.some((c) => {
        const v = c.searchValue ? c.searchValue(r) : r[c.key];
        return v != null && String(v).toLocaleLowerCase('tr').includes(q);
      }));
    }
    if (sort.key) {
      const col = columns.find((c) => c.key === sort.key);
      const val = (r) => (col?.sortValue ? col.sortValue(r) : r[sort.key]);
      list = [...list].sort((a, b) => {
        const x = val(a), y = val(b);
        const cmp = typeof x === 'number' && typeof y === 'number'
          ? x - y
          : String(x ?? '').localeCompare(String(y ?? ''), 'tr', { numeric: true });
        return sort.dir === 'asc' ? cmp : -cmp;
      });
    }
    return list;
  }, [rows, columns, query, sort]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const current = Math.min(page, pageCount - 1);
  const visible = filtered.slice(current * pageSize, current * pageSize + pageSize);

  const toggleSort = (key) => setSort((s) => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }));

  return (
    <div className="ui-table-wrap">
      <div className="ui-table-toolbar">
        <label className="ui-search">
          <Search size={15} />
          <input value={query} onChange={(e) => { setQuery(e.target.value); setPage(0); }} placeholder={searchPlaceholder} aria-label="Tabloda ara" />
        </label>
        {toolbar}
        <span className="ui-table-count">{filtered.length} kayıt</span>
      </div>

      <div className="ui-table-scroll">
        <table className="ui-table">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} style={{ textAlign: c.align || 'left' }} className={c.hideOnMobile ? 'ui-hide-mobile' : ''}>
                  {c.sortable === false ? c.label : (
                    <button type="button" className="ui-th-sort" onClick={() => toggleSort(c.key)}>
                      {c.label}
                      {sort.key === c.key && (sort.dir === 'asc' ? <ChevronUp size={13} /> : <ChevronDown size={13} />)}
                    </button>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr><td colSpan={columns.length} className="ui-table-empty">{emptyText}</td></tr>
            ) : visible.map((r) => (
              <tr key={rowKey(r)} onClick={onRowClick ? () => onRowClick(r) : undefined} className={onRowClick ? 'ui-row-clickable' : ''}>
                {columns.map((c) => (
                  <td key={c.key} data-label={c.label} style={{ textAlign: c.align || 'left' }} className={c.hideOnMobile ? 'ui-hide-mobile' : ''}>
                    {c.render ? c.render(r) : (r[c.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pageCount > 1 && (
        <div className="ui-pagination">
          <button type="button" className="ui-icon-btn" disabled={current === 0} onClick={() => setPage(current - 1)} aria-label="Önceki sayfa"><ChevronLeft size={16} /></button>
          <span>{current + 1} / {pageCount}</span>
          <button type="button" className="ui-icon-btn" disabled={current >= pageCount - 1} onClick={() => setPage(current + 1)} aria-label="Sonraki sayfa"><ChevronRight size={16} /></button>
        </div>
      )}
    </div>
  );
}
