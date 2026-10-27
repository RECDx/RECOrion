// İzin kontrolü (kaynak: backend/app/core/permission_catalog.py). Ekranda gizlemek kolaylıktır; asıl denetim sunucudadır.

export const can = (user, ...codes) => {
  const perms = user?.permissions || [];
  return !!user?.is_super_admin || perms.includes('*') || codes.some((c) => perms.includes(c));
};

// Şirket Yönetimi menüleri: sekme -> açan izinlerden biri
export const MENU_PERMISSIONS = {
  DASHBOARD: ['dashboard:view'],
  USERS: ['user:invite', 'user:manage'],
  AI_AGENTS: ['agent:hire', 'agent:configure', 'agent:quarantine'],
  DEPARTMENTS: ['org:manage'],
  JOB_TITLES: ['agent:custom_title'],
  MANIFESTO: ['manifesto:manage'],
  BRAIN: ['brain:manage'],
  INTEGRATIONS: ['integration:manage', 'mapping:manage', 'integration:approve'],
  AUTOMATIONS: ['automation:manage'],
  REGULATIONS: ['regulation:manage'],
  CREDITS: ['billing:view'],
};

export const canOpenTab = (user, tab) => can(user, ...(MENU_PERMISSIONS[tab] || []));

// Şirket Yönetimi konsolunu açan izinler (biri yeterli)
export const canOpenCompanyConsole = (user) =>
  user?.role === 'COMPANY_ADMIN' || user?.role === 'SUPER_ADMIN' || can(user, 'tenant:manage', ...Object.values(MENU_PERMISSIONS).flat());

// Rol kodu -> ekranda görünen ad (/auth/me role_name yoksa)
const ROLE_LABELS = { SUPER_ADMIN: 'Süper Yönetici', COMPANY_ADMIN: 'Şirket Yöneticisi', PROJECT_MANAGER: 'Proje Yöneticisi', USER: 'Uzman Kullanıcı', MEMBER: 'Uzman Kullanıcı' };
export const roleLabel = (user) => user?.role_name || ROLE_LABELS[user?.role] || user?.role || '';

// İzin modülleri (müşteri menüsü sırasıyla; sunucudaki permission_catalog.MODULES ile aynı)
export const PERMISSION_MODULES = [
  ['PLATFORM', 'Şirket & Platform'], ['REPORTS', 'Genel Bakış & Raporlar'], ['RBAC', 'Kullanıcılar & Roller'],
  ['AGENTS', 'AI Personel'], ['ORG', 'Organizasyon'], ['INTELLIGENCE', 'Kurum Zekâsı'], ['INTEGRATIONS', 'Entegrasyon & Otomasyon'],
  ['BILLING', 'Kredi & Kullanım'], ['PROJECTS', 'Projeler & İş Akışı'], ['CHAT', 'Sohbet & İletişim'], ['MEMORY', 'Kurum Hafızası'],
  ['CONNECTIONS', 'Bağlantılarım'],
];
export const moduleName = (code) => (PERMISSION_MODULES.find(([c]) => c === code) || [code, code])[1];
