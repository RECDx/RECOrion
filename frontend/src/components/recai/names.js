// #349: RECAi adları (müşteriye görünen). Arkasındaki modeli yalnızca Süper Admin "RECAi Adları" ekranında değiştirir.
export const RECAI_TIERS = [
  { code: 'MERGEN', name: 'RECAi Mergen', hint: 'Genel işler' },
  { code: 'HIZLI', name: 'RECAi Hızlı', hint: 'Kısa ve hızlı yanıtlar' },
  { code: 'DERIN', name: 'RECAi Derin', hint: 'Derin analiz ve uzun metin' },
];

// Paket özelliği (plans.features) → yetenek adı
export const RECAI_CAPABILITIES = [
  { code: 'GORSEL', feature: 'vision_enabled', name: 'RECAi Görsel', hint: 'Görsel ve ekran görüntüsü okuma' },
  { code: 'SES', feature: 'transcription_enabled', name: 'RECAi Ses', hint: 'Toplantı ve ses kaydını yazıya dökme' },
  { code: 'OKUR', feature: 'ocr_enabled', name: 'RECAi Okur', hint: 'Taranmış belge ve PDF okuma (OCR)' },
];

export const recaiTierName = (code) => RECAI_TIERS.find((t) => t.code === code)?.name || 'RECAi';
