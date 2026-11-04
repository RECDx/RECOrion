import React from 'react';
import { LifeBuoy } from 'lucide-react';
import { openHelp } from './helpBus';

/** Üst çubuktaki Yardım düğmesi (ADIM 15.3): bulunulan ekranın anlatımını açar; F1 ile aynı. */
export default function HelpButton({ compact = false }) {
  return (
    <button type="button" className="ui-btn ui-btn-ghost ui-btn-sm hp-btn" onClick={() => openHelp()} title="Yardım ve RECAi'ye sor (F1)" aria-label="Yardım (F1)">
      <LifeBuoy size={15} />{!compact && <span>Yardım</span>}
    </button>
  );
}
