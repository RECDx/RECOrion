import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard,
  Building2, 
  KeyRound, 
  Cpu, 
  Package, 
  CheckCircle2, 
  Clock, 
  RefreshCw, 
  LogOut, 
  ExternalLink, 
  Search, 
  Plus, 
  Mail, 
  Phone, 
  CreditCard,
  ChevronRight,
  ChevronLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
  User,
  Settings,
  Tag,
  Briefcase,
  Lock,
  Copy,
  Check,
  Trash2,
  Edit,
  X,
  Zap,
  ShieldCheck,
  Layers,
  ArrowRight,
  AlertCircle,
  Calendar,
  AlertTriangle,
  LayoutGrid,
  List,
  Send,
  Eye,
  Code,
  FileText,
  HelpCircle,
  Bell,
  Save,
  GripVertical,
  ArrowUp,
  ArrowDown,
  Image as ImageIcon,
  PauseCircle,
  PlayCircle,
  Globe
} from 'lucide-react';
import { api } from '../api';

const TAB_SLUG_MAP = {
  DASHBOARD: 'dashboard',
  LEADS: 'leads',
  TENANTS: 'tenants',
  PERMISSIONS: 'permissions',
  PLANS: 'plans',
  EMAIL_TEMPLATES: 'email-templates',
  SCHEDULES: 'schedules',
  AI_MODEL_SETTINGS: 'ai-models',
  MODELS: 'models',
  NACE: 'nace',
  TITLES: 'job-titles'
};

const SLUG_TAB_MAP = {
  'dashboard': 'DASHBOARD',
  'leads': 'LEADS',
  'tenants': 'TENANTS',
  'permissions': 'PERMISSIONS',
  'plans': 'PLANS',
  'email-templates': 'EMAIL_TEMPLATES',
  'schedules': 'SCHEDULES',
  'ai-models': 'AI_MODEL_SETTINGS',
  'models': 'MODELS',
  'nace': 'NACE',
  'job-titles': 'TITLES'
};

function getTabFromHash() {
  if (typeof window === 'undefined') return 'DASHBOARD';
  const hash = window.location.hash || '';
  if (hash.startsWith('#/super-admin/')) {
    const slug = hash.replace('#/super-admin/', '').split('?')[0].split('/')[0];
    if (SLUG_TAB_MAP[slug]) return SLUG_TAB_MAP[slug];
  }
  return 'DASHBOARD';
}

const EMAIL_PRESET_BLOCKS = [
  {
    type: 'HEADER',
    label: 'Kurumsal Başlık & Logo',
    subtitle: 'Yapay Zeka Destekli Yeni Nesil ERP Platformu',
    logoUrl: '',
    renderHtml: (b) => `<div style="background: linear-gradient(135deg, #1e1b4b 0%, #31104b 50%, #0f172a 100%); padding: 32px 25px; border-radius: 12px 12px 0 0; text-align: center; border-bottom: 2px solid #7134e2;">
  ${b.logoUrl ? `<div style="margin-bottom: 12px;"><img src="${b.logoUrl}" alt="Kurumsal Logo" style="max-height: 55px; max-width: 220px; object-fit: contain;" /></div>` : '<div style="font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: 0.5px;">🪐 RECOrion</div>'}
  <div style="font-size: 13px; color: #a78bfa; margin-top: 5px; font-weight: 600;">${b.subtitle || 'Yapay Zeka Destekli Kurumsal İşletim Sistemi'}</div>
</div>`
  },
  {
    type: 'IMAGE',
    label: 'Özel Görsel / Logo / Banner',
    imageUrl: '',
    caption: '',
    renderHtml: (b) => b.imageUrl ? `<div style="padding: 15px 25px; background: #0b0f19; text-align: center;">
  <img src="${b.imageUrl}" alt="${b.caption || 'Görsel'}" style="max-width: 100%; max-height: 250px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); object-fit: contain;" />
  ${b.caption ? `<div style="font-size: 11px; color: #94a3b8; margin-top: 6px;">${b.caption}</div>` : ''}
</div>` : ''
  },
  {
    type: 'GREETING',
    label: 'Karşılama Metni',
    text: 'Sayın <b>{{company_name}}</b> Yetkilisi, Sayın <b>{{contact_name}}</b>,',
    renderHtml: (b) => `<div style="padding: 22px 25px 12px 25px; background: #0b0f19; color: #f1f5f9; font-size: 15px; line-height: 1.6;">
  <p style="margin: 0;">${b.text || 'Sayın <b>{{company_name}}</b> Yetkilisi,'}</p>
</div>`
  },
  {
    type: 'CONTENT',
    label: 'Açıklama / Duyuru Paragrafı',
    text: 'RECOrion kurumsal aboneliğiniz başarıyla aktif edilmiştir. Kurumunuza özel olarak hazırlanan yapay zeka ajanları ve şirket çalışma ortamınız hazır durumdadır.',
    renderHtml: (b) => `<div style="padding: 10px 25px 15px 25px; background: #0b0f19; color: #cbd5e1; font-size: 14px; line-height: 1.7;">
  <p style="margin: 0;">${b.text || ''}</p>
</div>`
  },
  {
    type: 'PACKAGE_INFO',
    label: 'Paket & Süre Özeti',
    planName: '{{plan_name}}',
    expiryDate: '{{package_expiry_date}}',
    daysRemaining: '{{days_remaining}}',
    renderHtml: (b) => `<div style="padding: 15px 25px; background: #0b0f19;">
  <div style="background: rgba(113, 52, 226, 0.12); border: 1px solid rgba(113, 52, 226, 0.35); border-radius: 10px; padding: 18px 20px;">
    <div style="font-size: 12px; font-weight: 800; color: #a78bfa; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">📦 Kurumsal Abonelik Özeti</div>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #e2e8f0;">
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Tanımlanan Paket:</td>
        <td style="padding: 5px 0; text-align: right; font-weight: 800; color: #38bdf8;">${b.planName || '{{plan_name}}'}</td>
      </tr>
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Paket Bitiş Tarihi:</td>
        <td style="padding: 5px 0; text-align: right; font-weight: 700; color: #34d399;">${b.expiryDate || '{{package_expiry_date}}'}</td>
      </tr>
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Kalan Kullanım Süresi:</td>
        <td style="padding: 5px 0; text-align: right; font-weight: 700; color: #fbbf24;">${b.daysRemaining || '{{days_remaining}}'} Gün</td>
      </tr>
    </table>
  </div>
</div>`
  },
  {
    type: 'CREDENTIALS',
    label: 'Yönetici Giriş Bilgileri Kartı',
    loginEmail: '{{login_email}}',
    passwordText: '{{password}}',
    renderHtml: (b) => `<div style="padding: 15px 25px; background: #0b0f19;">
  <div style="background: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 10px; padding: 18px 20px;">
    <div style="font-size: 12px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">🔐 Yönetici Giriş Bilgileri</div>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #e2e8f0;">
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Kullanıcı E-Posta:</td>
        <td style="padding: 5px 0; text-align: right; font-family: monospace; font-weight: 700; color: #ffffff;">${b.loginEmail || '{{login_email}}'}</td>
      </tr>
      <tr>
        <td style="padding: 5px 0; color: #94a3b8;">Geçici Şifre:</td>
        <td style="padding: 5px 0; text-align: right; font-family: monospace; font-weight: 700; color: #fbbf24;">${b.passwordText || '{{password}}'}</td>
      </tr>
    </table>
  </div>
</div>`
  },
  {
    type: 'BUTTON',
    label: 'Aksiyon Butonu (CTA)',
    buttonText: 'Yönetim Paneline Giriş Yap →',
    buttonUrl: '{{login_url}}',
    renderHtml: (b) => `<div style="padding: 20px 25px; background: #0b0f19; text-align: center;">
  <a href="${b.buttonUrl || '{{login_url}}'}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #7134e2 0%, #146ceb 100%); color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 800; padding: 13px 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(113, 52, 226, 0.4);">
    ${b.buttonText || 'Panele Giriş Yap →'}
  </a>
</div>`
  },
  {
    type: 'DIVIDER',
    label: 'Ayırıcı Çizgi',
    renderHtml: () => `<div style="padding: 10px 25px; background: #0b0f19;">
  <hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent); margin: 0;" />
</div>`
  },
  {
    type: 'FOOTER',
    label: 'Kurumsal Alt Bilgi & İmza',
    footerText: 'Bu e-posta RECDx Bilişim Teknolojileri ve Yapay Zeka A.Ş. tarafından otomatik olarak iletilmiştir. Destek için info@recdx.com adresiyle iletişime geçebilirsiniz.',
    renderHtml: (b) => `<div style="padding: 25px; background: #060911; border-radius: 0 0 12px 12px; border-top: 1px solid rgba(255,255,255,0.06); text-align: center; color: #64748b; font-size: 11px; line-height: 1.6;">
  <div style="font-weight: 700; color: #94a3b8; margin-bottom: 4px;">RECDx Bilişim Teknolojileri ve Yapay Zeka A.Ş.</div>
  <div>${b.footerText}</div>
  <div style="margin-top: 8px; color: #475569;">© 2026 RECOrion. Tüm Hakları Saklıdır.</div>
</div>`
  }
];

function compileBlocksToHtml(blocks) {
  const inner = blocks.map(b => {
    const preset = EMAIL_PRESET_BLOCKS.find(p => p.type === b.type);
    return preset ? preset.renderHtml(b) : '';
  }).filter(Boolean).join('\n');

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RECOrion Kurumsal Bildirim</title>
</head>
<body style="margin: 0; padding: 30px 15px; background-color: #030712; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
  <div style="max-width: 620px; margin: 0 auto; background: #0b0f19; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 40px rgba(0,0,0,0.6);">
${inner}
  </div>
</body>
</html>`;
}

export default function SuperAdminConsole({ 
  currentUser, 
  onLogout, 
  onSwitchToWorkspace, 
  onGoToOfficialSite, 
  onUpdateCurrentUser 
}) {
  // Sol Menü Daraltma / Genişletme State'i (Madde 4)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Aktif Menü Sekmesi (URL Hash Senkronize)
  const [activeTab, setActiveTab] = useState(getTabFromHash); 
  // 'DASHBOARD' | 'LEADS' | 'TENANTS' | 'EMAIL_TEMPLATES' | 'SCHEDULES' | 'PERMISSIONS' | 'MODELS' | 'PLANS' | 'NACE' | 'TITLES' | 'AI_MODEL_SETTINGS'

  const switchTab = (newTab, options = {}) => {
    setActiveTab(newTab);
    const slug = TAB_SLUG_MAP[newTab] || 'dashboard';
    const targetHash = `#/super-admin/${slug}`;
    if (window.location.hash !== targetHash) {
      if (options.replace) {
        window.history.replaceState(null, '', targetHash);
      } else {
        window.location.hash = targetHash;
      }
    }
  };

  // Tarayıcı İleri/Geri Butonlarını Dinle ve Sekmeyi Senkronize Et
  useEffect(() => {
    const syncTabFromHash = () => {
      const tab = getTabFromHash();
      setActiveTab(tab);
    };

    const currentHash = window.location.hash;
    if (currentHash === '#/super-admin' || currentHash === '#/super-admin/' || !currentHash.startsWith('#/super-admin/')) {
      const slug = TAB_SLUG_MAP[activeTab] || 'dashboard';
      window.history.replaceState(null, '', `#/super-admin/${slug}`);
    }

    window.addEventListener('hashchange', syncTabFromHash);
    window.addEventListener('popstate', syncTabFromHash);
    return () => {
      window.removeEventListener('hashchange', syncTabFromHash);
      window.removeEventListener('popstate', syncTabFromHash);
    };
  }, []);

  // Menü Görünüm Modları (Madde 2: 'KANBAN' | 'LIST')
  const [tenantViewMode, setTenantViewMode] = useState('KANBAN');
  const [leadViewMode, setLeadViewMode] = useState('LIST');
  const [permissionViewMode, setPermissionViewMode] = useState('LIST');
  const [planViewMode, setPlanViewMode] = useState('KANBAN');
  const [modelViewMode, setModelViewMode] = useState('LIST');
  const [naceViewMode, setNaceViewMode] = useState('LIST');
  const [titleViewMode, setTitleViewMode] = useState('KANBAN');
  const [templateViewMode, setTemplateViewMode] = useState('KANBAN');
  const [scheduleViewMode, setScheduleViewMode] = useState('KANBAN');

  // E-Posta Şablonu Drag & Drop Builder State'leri (Madde 5)
  const [templateEditorTab, setTemplateEditorTab] = useState('BUILDER'); // 'BUILDER' | 'CODE'
  const [templateCanvasBlocks, setTemplateCanvasBlocks] = useState([]);
  const [draggedPresetType, setDraggedPresetType] = useState(null);
  const [draggedBlockIdx, setDraggedBlockIdx] = useState(null);

  // Ortak Segmentli Kanban / Liste Seçici Bileşeni (Madde 2)
  const renderViewModeToggle = (mode, setMode) => (
    <div style={{ display: 'flex', background: 'rgba(255,255,255,0.06)', padding: 3, borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)' }}>
      <button
        type="button"
        onClick={() => setMode('KANBAN')}
        className="super-admin-btn-secondary"
        style={{
          padding: '5px 10px',
          fontSize: '0.75rem',
          border: 'none',
          background: mode === 'KANBAN' ? '#7134e2' : 'transparent',
          color: mode === 'KANBAN' ? '#fff' : '#94a3b8'
        }}
        title="Kanban Kart Görünümü"
      >
        <LayoutGrid style={{ width: 14, height: 14 }} />
        <span>Kanban</span>
      </button>
      <button
        type="button"
        onClick={() => setMode('LIST')}
        className="super-admin-btn-secondary"
        style={{
          padding: '5px 10px',
          fontSize: '0.75rem',
          border: 'none',
          background: mode === 'LIST' ? '#7134e2' : 'transparent',
          color: mode === 'LIST' ? '#fff' : '#94a3b8'
        }}
        title="Liste Tablo Görünümü"
      >
        <List style={{ width: 14, height: 14 }} />
        <span>Liste</span>
      </button>
    </div>
  );

  // Şirketler Onay Durum Filtresi ('ALL' | 'APPROVED' | 'PENDING')
  const [tenantStatusFilter, setTenantStatusFilter] = useState('ALL');

  // Başvuru Onay Durum Filtresi (Madde 8: 'PENDING' | 'APPROVED')
  const [leadApprovalFilter, setLeadApprovalFilter] = useState('PENDING');

  // Temel Veriler
  const [leads, setLeads] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [models, setModels] = useState([]);
  const [plans, setPlans] = useState([]);
  const [naceList, setNaceList] = useState([]);
  const [jobTitles, setJobTitles] = useState([]);
  const [systemSettings, setSystemSettings] = useState({ default_manifesto_model: 'deepseek-v4.1-flash' });
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [schedules, setSchedules] = useState([]);

  // Arama & Filtre State'leri
  const [searchQuery, setSearchQuery] = useState('');
  const [naceSearch, setNaceSearch] = useState('');
  const [jobTitleCategoryFilter, setJobTitleCategoryFilter] = useState('ALL');
  const [permissionModuleFilter, setPermissionModuleFilter] = useState('ALL');

  // UI & Geri Bildirim
  const [loading, setLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState(null);
  const [processingId, setProcessingId] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);

  // ================= MODAL STATE'LERİ =================
  // 1. Profil Modal (Madde 1 & 2)
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [profileForm, setProfileForm] = useState({
    display_name: currentUser?.display_name || 'Muhammed Cüneyt ERDİL',
    email: currentUser?.email || 'cuneyterdil@recdx.com',
    phone: currentUser?.phone || '',
    address: currentUser?.address || '',
    new_password: ''
  });

  // 2. İzin Detay / Ekleme Modal (Madde 4)
  const [permissionModalOpen, setPermissionModalOpen] = useState(false);
  const [editingPermission, setEditingPermission] = useState(null);
  const [permissionForm, setPermissionForm] = useState({
    code: '',
    module: 'AGENTS',
    name: '',
    description: '',
    default_for_roles: ['SUPER_ADMIN', 'COMPANY_ADMIN']
  });

  // 3. Şirket Detay & Yönetici Modal (Madde 5 & 12)
  const [tenantDetailModalOpen, setTenantDetailModalOpen] = useState(false);
  const [tenantDetailLoading, setTenantDetailLoading] = useState(false);
  const [selectedTenantDetails, setSelectedTenantDetails] = useState(null);
  const [tenantEditForm, setTenantEditForm] = useState({
    name: '',
    tax_id: '',
    tax_office: '',
    phone: '',
    address: '',
    website: '',
    contact_email: '',
    is_active: true,
    sector_manifesto: '',
    plan_id: '',
    nace_codes: [],
    package_expiry_date: ''
  });
  const [tenantAdminForm, setTenantAdminForm] = useState({
    actor_id: null,
    display_name: '',
    email: '',
    phone: '',
    address: '',
    new_password: ''
  });
  const [generatedAdminPassword, setGeneratedAdminPassword] = useState(null);
  const [detailNaceSearch, setDetailNaceSearch] = useState('');
  const [detailNaceResults, setDetailNaceResults] = useState([]);
  const [isGeneratingDetailManifesto, setIsGeneratingDetailManifesto] = useState(false);
  const [tenantDetailActiveTab, setTenantDetailActiveTab] = useState('COMPANY'); // 'COMPANY' | 'ADMIN' | 'ALL'
  const [justCreatedTenantAlert, setJustCreatedTenantAlert] = useState(null);

  // 3.1 Yeni Müşteri Ekle Modal (Madde 9 & 13)
  const [newTenantModalOpen, setNewTenantModalOpen] = useState(false);
  const [newTenantForm, setNewTenantForm] = useState({
    name: '',
    tax_id: '',
    tax_office: '',
    phone: '',
    address: '',
    website: '',
    contact_email: '',
    admin_name: '',
    admin_password: '',
    plan_id: '',
    nace_codes: []
  });
  const [newTenantNaceSearch, setNewTenantNaceSearch] = useState('');
  const [newTenantNaceResults, setNewTenantNaceResults] = useState([]);
  const [newTenantManifesto, setNewTenantManifesto] = useState('');
  const [isGeneratingNewTenantManifesto, setIsGeneratingNewTenantManifesto] = useState(false);

  // 4. Plan Detay / Ekleme Modal (Madde 7 & 15)
  const [planModalOpen, setPlanModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [planForm, setPlanForm] = useState({
    code: '',
    name: '',
    description: '',
    monthly_price: 15000,
    currency: 'TRY',
    max_humans: 5,
    max_agents: 5,
    max_projects: 3,
    monthly_credits: 1000,
    storage_gb: 10,
    allowed_models: ['deepseek-v3'],
    can_create_custom_titles: false,
    is_active: true
  });

  // 4.1 E-Posta Şablonu Modal (Madde 1)
  const [templateModalOpen, setTemplateModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [templateForm, setTemplateForm] = useState({
    code: '',
    name: '',
    subject: '',
    html_content: '',
    text_content: '',
    variables: [],
    is_active: true
  });
  const [testEmailModalOpen, setTestEmailModalOpen] = useState(false);
  const [testEmailTarget, setTestEmailTarget] = useState('cuneyterdil@recdx.com');

  // 4.2 Zamanlayıcı (Schedule) Modal (Madde 2)
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [scheduleForm, setScheduleForm] = useState({
    name: '',
    trigger_type: 'BEFORE_EXPIRATION_INTERVAL',
    template_code: 'PACKAGE_EXPIRATION_REMINDER',
    frequency_days: 15,
    target_lead_days: 90,
    is_active: true
  });

  // 5. EVREN Model Detay / Ekleme Modal (Madde 8)
  const [modelModalOpen, setModelModalOpen] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [modelForm, setModelForm] = useState({
    model_code: '',
    display_name: '',
    model_type: 'CHAT',
    context_window: 131072,
    effort_coefficient: 1.0,
    status: 'ACTIVE'
  });

  // 6. NACE Detay / Ekleme Modal (Madde 12)
  const [naceModalOpen, setNaceModalOpen] = useState(false);
  const [editingNace, setEditingNace] = useState(null);
  const [naceForm, setNaceForm] = useState({
    code: '',
    title: '',
    sector_group: 'Bilişim & Yazılım',
    description: ''
  });

  // 7. Sektörel Ünvan Detay / Ekleme Modal (Madde 13)
  const [titleModalOpen, setTitleModalOpen] = useState(false);
  const [editingTitle, setEditingTitle] = useState(null);
  const [titleForm, setTitleForm] = useState({
    code: '',
    title: '',
    category: 'YAZILIM',
    description: '',
    base_role_prompt: '',
    required_skills: ['Yazılım Mimarisi', 'Temiz Kod'],
    recommended_model_code: 'glm-5.3',
    autonomy_level: 'L1'
  });
  const [regeneratingPrompt, setRegeneratingPrompt] = useState(false);

  // ESC Tuşu ile Açık Olan Detay / Düzenleme Modalını Kaydetmeden Kapatma (Madde 3)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' || e.keyCode === 27) {
        if (templateModalOpen) {
          setTemplateModalOpen(false);
        } else if (tenantDetailModalOpen) {
          setTenantDetailModalOpen(false);
        } else if (newTenantModalOpen) {
          setNewTenantModalOpen(false);
        } else if (planModalOpen) {
          setPlanModalOpen(false);
        } else if (scheduleModalOpen) {
          setScheduleModalOpen(false);
        } else if (profileModalOpen) {
          setProfileModalOpen(false);
        } else if (permissionModalOpen) {
          setPermissionModalOpen(false);
        } else if (modelModalOpen) {
          setModelModalOpen(false);
        } else if (naceModalOpen) {
          setNaceModalOpen(false);
        } else if (titleModalOpen) {
          setTitleModalOpen(false);
        } else if (testEmailModalOpen) {
          setTestEmailModalOpen(false);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    templateModalOpen,
    tenantDetailModalOpen,
    newTenantModalOpen,
    planModalOpen,
    scheduleModalOpen,
    profileModalOpen,
    permissionModalOpen,
    modelModalOpen,
    naceModalOpen,
    titleModalOpen,
    testEmailModalOpen
  ]);

  // ================= VERİLERİ YÜKLEME =================
  const loadAllData = async () => {
    setLoading(true);
    setActionFeedback(null);
    try {
      const [lData, tData, pData, mData, plData, nData, jData, sData, etData, scData] = await Promise.all([
        api.getLeads().catch(() => []),
        api.getTenants().catch(() => []),
        api.getPermissions().catch(() => []),
        api.getModels().catch(() => []),
        api.getPlans().catch(() => []),
        api.getNaceCatalog().catch(() => []),
        api.getJobTitles().catch(() => []),
        api.getSystemSettings().catch(() => ({ default_manifesto_model: 'deepseek-v3' })),
        api.getEmailTemplates().catch(() => []),
        api.getSchedules().catch(() => [])
      ]);

      setLeads(lData || []);
      setTenants(tData || []);
      setPermissions(pData || []);
      setModels(mData || []);
      setPlans(plData || []);
      setNaceList(nData || []);
      setJobTitles(jData || []);
      setSystemSettings(sData || { default_manifesto_model: 'deepseek-v3' });
      setEmailTemplates(etData || []);
      setSchedules(scData || []);

      // Güncel profil verisi
      if (currentUser?.actor_id) {
        api.getProfile(currentUser.actor_id).then((freshProfile) => {
          if (freshProfile) {
            setProfileForm({
              display_name: freshProfile.display_name,
              email: freshProfile.email,
              phone: freshProfile.phone || '',
              address: freshProfile.address || '',
              new_password: ''
            });
            if (onUpdateCurrentUser) onUpdateCurrentUser(freshProfile);
          }
        }).catch(() => {});
      }
    } catch (err) {
      console.error("Super Admin veri yükleme hatası:", err);
      setActionFeedback({ type: 'error', text: 'Veriler yüklenirken hata: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // NACE Arama
  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        const res = await api.searchNace(naceSearch, 50);
        setNaceList(res || []);
      } catch (err) {
        console.error("NACE arama hatası:", err);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [naceSearch]);

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  // ================= 1. PROFİL GÜNCELLEME (Madde 1 & 2) =================
  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    if (!currentUser?.actor_id) {
      setActionFeedback({ type: 'error', text: 'Kullanıcı oturumu bulunamadı.' });
      return;
    }
    try {
      setProcessingId('profile');
      const updated = await api.updateProfile(currentUser.actor_id, {
        display_name: profileForm.display_name,
        email: profileForm.email,
        phone: profileForm.phone,
        address: profileForm.address,
        new_password: profileForm.new_password || undefined
      });
      if (onUpdateCurrentUser) onUpdateCurrentUser(updated);
      setProfileModalOpen(false);
      setActionFeedback({ type: 'success', text: `✓ Sayın ${updated.display_name}, profil bilgileriniz başarıyla güncellendi!` });
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Profil güncelleme başarısız: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 2. LEAD ONAYLAMA =================
  const handleApproveLead = async (lead) => {
    try {
      setProcessingId(lead.id);
      setActionFeedback(null);
      await api.approveLead(lead.id);
      setActionFeedback({
        type: 'success',
        text: `✓ '${lead.company_name}' onaylandı! Odoo 19 siparişi resmileştirildi, şirket ortamı aktive edildi ve aktivasyon e-postası iletildi.`
      });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Onay işlemi başarısız: ' + (err.message || '') });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 3. ŞİRKET DETAY & ADMIN KULLANICI (Madde 5 & 12) =================
  const handleOpenTenantDetails = async (t, initialTab = 'COMPANY', justCreatedNotice = null, initialPassword = null) => {
    setTenantDetailModalOpen(true);
    setTenantDetailLoading(true);
    setSelectedTenantDetails(null);
    setTenantDetailActiveTab(initialTab);
    setJustCreatedTenantAlert(justCreatedNotice);
    setGeneratedAdminPassword(initialPassword || null);
    try {
      const details = await api.getTenantDetails(t.id);
      setSelectedTenantDetails(details);
      setTenantEditForm({
        name: details.tenant.name,
        tax_id: details.tenant.tax_id || '',
        tax_office: details.tenant.tax_office || '',
        phone: details.tenant.phone || '',
        address: details.tenant.address || '',
        website: details.tenant.website || '',
        contact_email: details.tenant.contact_email || '',
        is_active: details.tenant.is_active,
        sector_manifesto: details.tenant.sector_manifesto || '',
        plan_id: details.tenant.plan_id || '',
        nace_codes: details.tenant.nace_codes || [],
        package_expiry_date: details.tenant.package_expiry_date || ''
      });
      const firstAdmin = details.admins && details.admins.length > 0 ? details.admins[0] : null;
      setTenantAdminForm({
        actor_id: firstAdmin ? firstAdmin.id : null,
        display_name: firstAdmin ? firstAdmin.display_name : (newTenantForm.admin_name || 'Şirket Yöneticisi'),
        email: firstAdmin ? firstAdmin.email : (details.tenant.contact_email || ''),
        phone: firstAdmin ? (firstAdmin.phone || '') : (details.tenant.phone || ''),
        address: firstAdmin ? (firstAdmin.address || '') : '',
        new_password: initialPassword || ''
      });
      if (initialPassword) {
        setGeneratedAdminPassword(initialPassword);
      }
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Şirket detayları alınamadı: ' + err.message });
      setTenantDetailModalOpen(false);
    } finally {
      setTenantDetailLoading(false);
    }
  };

  const handleSaveTenantDetails = async (e) => {
    e.preventDefault();
    if (!selectedTenantDetails?.tenant?.id) return;
    try {
      setProcessingId('save-tenant');
      await api.updateTenant(selectedTenantDetails.tenant.id, {
        name: tenantEditForm.name,
        tax_id: tenantEditForm.tax_id,
        tax_office: tenantEditForm.tax_office,
        phone: tenantEditForm.phone,
        address: tenantEditForm.address,
        website: tenantEditForm.website,
        contact_email: tenantEditForm.contact_email,
        is_active: tenantEditForm.is_active,
        sector_manifesto: tenantEditForm.sector_manifesto,
        plan_id: tenantEditForm.plan_id || null,
        nace_codes: tenantEditForm.nace_codes || [],
        package_expiry_date: tenantEditForm.package_expiry_date || null
      });
      setActionFeedback({ type: 'success', text: `✓ '${tenantEditForm.name}' şirket bilgileri başarıyla kaydedildi!` });
      setTenantDetailModalOpen(false);
      setSelectedTenantDetails(null);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Şirket güncelleme hatası: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleGenerateManifestoForTenant = async () => {
    if (!tenantEditForm.name.trim()) {
      alert("Lütfen önce şirket adını giriniz.");
      return;
    }
    try {
      setIsGeneratingDetailManifesto(true);
      const res = await api.generateManifesto({
        company_name: tenantEditForm.name,
        nace_codes: tenantEditForm.nace_codes || [],
        website: tenantEditForm.website || null
      });
      setTenantEditForm(prev => ({ ...prev, sector_manifesto: res.manifesto }));
      setActionFeedback({ type: 'success', text: `✓ RECOrion LLM tarafından '${res.sector_focus}' odaklı manifesto üretildi!` });
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Manifesto üretimi başarısız: ' + err.message });
    } finally {
      setIsGeneratingDetailManifesto(false);
    }
  };

  // Müşterinin kartını pasife alma / aktife alma (Madde 4)
  const handleToggleTenantStatus = async (t) => {
    const isCurrentlyActive = t.is_active;
    const confirmMsg = isCurrentlyActive
      ? `'${t.name}' şirketinin kartını PASİFE almak istediğinize emin misiniz?\n\nPasife alındığında şirket yöneticisi ve kullanıcıları sisteme giriş yapamayacaktır.`
      : `'${t.name}' şirketinin kartını tekrar AKTİFE almak istediğinize emin misiniz?\n\nAktife alındığında şirket kullanıcılarının sisteme erişimi açılacaktır.`;

    if (!window.confirm(confirmMsg)) return;

    try {
      setProcessingId('toggle-status-' + t.id);
      const res = await api.toggleTenantStatus(t.id);
      const newStatus = res.is_active;
      setActionFeedback({
        type: 'success',
        text: `✓ ${res.message || `'${t.name}' şirket durumu başarıyla güncellendi.`}`
      });
      alert(`✓ İşlem Başarılı!\n\n${res.message || `'${t.name}' şirketi ${newStatus ? 'Aktif' : 'Pasif'} duruma getirildi.`}`);

      // Eğer detay modalı bu şirket için açıksa formu da anında senkronize et
      if (selectedTenantDetails?.tenant?.id === t.id) {
        setTenantEditForm(prev => ({ ...prev, is_active: newStatus }));
        setSelectedTenantDetails(prev => prev ? {
          ...prev,
          tenant: { ...prev.tenant, is_active: newStatus }
        } : prev);
      }

      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Şirket durumu değiştirilemedi: ' + err.message });
      alert(`⚠️ Hata Alındı!\n\nŞirket durumu değiştirilemedi: ${err.message || 'Bilinmeyen hata'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Manuel Paket Süre Dolum Hatırlatıcı Gönder (Madde 14)
  const handleSendManualReminder = async (t) => {
    if (!window.confirm(`'${t.name}' şirketine (${t.contact_email}) paket kullanım süresi hatırlatıcı e-postası göndermek istiyor musunuz?`)) return;
    try {
      setProcessingId('reminder-' + t.id);
      const res = await api.sendManualReminder(t.id);
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
      alert(`✓ E-Posta Başarıyla Gönderildi!\n\n${res.message || `'${t.name}' şirketine hatırlatıcı e-postası başarıyla iletildi.`}`);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Hatırlatıcı e-postası gönderilemedi: ' + err.message });
      alert(`⚠️ E-Posta Gönderilemedi!\n\nHata Alındı: ${err.message || 'Bilinmeyen bir hata oluştu.'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Kayıtlı Şirketler Ekranından Hızlı Onaylama
  const handleQuickApproveTenant = async (t) => {
    if (!window.confirm(`'${t.name}' şirketinin üyeliğini ve 1 yıllık kurumsal paketini onaylamak istiyor musunuz?`)) return;
    try {
      setProcessingId('approve-' + t.id);
      await api.approveRegisteredTenant(t.id);
      setActionFeedback({ type: 'success', text: `✓ '${t.name}' şirketi başarıyla onaylandı ve 1 yıllık paketi aktif edildi!` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Onaylama başarısız: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // Otomatik Zamanlayıcıyı Manuel Tetikleme (Madde 2)
  const handleTriggerSchedule = async (sched) => {
    try {
      setProcessingId('sched-' + sched.id);
      const res = await api.triggerSchedule(sched.id);
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
      alert(`✓ Zamanlayıcı E-Postaları Başarıyla Gönderildi!\n\n${res.message || 'Zamanlayıcı kuralı başarıyla işletildi.'}`);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Zamanlayıcı çalıştırılamadı: ' + err.message });
      alert(`⚠️ Zamanlayıcı E-Postası Gönderilemedi!\n\nHata Alındı: ${err.message || 'Bilinmeyen bir hata oluştu.'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Süper Admin Doğrudan Müşteri Ekleme (Madde 9)
  const handleOpenNewTenantModal = () => {
    setNewTenantForm({
      name: '',
      tax_id: '',
      tax_office: '',
      phone: '',
      address: '',
      website: '',
      contact_email: '',
      admin_name: '',
      admin_password: '',
      plan_id: plans.length > 0 ? plans[0].id : '',
      nace_codes: []
    });
    setNewTenantNaceSearch('');
    setNewTenantNaceResults([]);
    setNewTenantManifesto('');
    setNewTenantModalOpen(true);
  };

  const handleGenerateManifestoForNewTenant = async () => {
    if (!newTenantForm.name.trim()) {
      alert("Lütfen önce şirket adını giriniz.");
      return;
    }
    try {
      setIsGeneratingNewTenantManifesto(true);
      const res = await api.generateManifesto({
        company_name: newTenantForm.name,
        nace_codes: newTenantForm.nace_codes || [],
        website: newTenantForm.website || null
      });
      setNewTenantManifesto(res.manifesto);
      setActionFeedback({ type: 'success', text: `✓ '${res.sector_focus}' odağında kurumsal AI manifestosu üretildi!` });
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Manifesto üretimi başarısız: ' + err.message });
    } finally {
      setIsGeneratingNewTenantManifesto(false);
    }
  };

  const handleSaveNewTenant = async (e, options = { activate: true, sendEmail: true }) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!newTenantForm.name.trim() || !newTenantForm.contact_email.trim()) {
      alert("Lütfen şirket adı ve e-posta adresini doldurunuz.");
      return;
    }
    try {
      const modeId = options.activate ? 'create-new-tenant-activate' : 'create-new-tenant-draft';
      setProcessingId(modeId);
      const res = await api.adminCreateTenant({
        ...newTenantForm,
        sector_manifesto: newTenantManifesto,
        activate_package: options.activate,
        send_welcome_email: options.sendEmail
      });
      const companyName = newTenantForm.name;
      const tenantId = res.tenant_id;
      const initialPassword = res.admin_password;

      // Yeni müşteri modalını kapat ve listeleri tazele
      setNewTenantModalOpen(false);
      await loadAllData();

      // Madde 1: Yeni Şirket Bilgileri kayıt edildikten sonra yönetici tanımlaması bölümü otomatik açılır!
      if (tenantId) {
        await handleOpenTenantDetails(
          { id: tenantId, name: companyName },
          'ADMIN', // Yönetici Tanımlama sekmesini doğrudan aç
          `✓ '${companyName}' kurumu başarıyla kaydedildi! Şimdi bu şirketin Yönetici (Admin) bilgilerini tanımlayabilir, güçlü şifresini belirleyebilir veya kopyalayabilirsiniz.`,
          initialPassword
        );
      } else {
        setActionFeedback({
          type: 'success',
          text: `✓ '${companyName}' kurumu başarıyla eklendi!`
        });
      }
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Müşteri ekleme hatası: ' + err.message });
      alert(`⚠️ Müşteri Kaydedilemedi!\n\nHata: ${err.message || 'Bilinmeyen hata'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Müşteriye Manuel Hoş Geldiniz E-Postası Gönderme (Madde 1)
  const handleSendManualWelcome = async (t) => {
    if (!t?.id) return;
    try {
      setProcessingId('welcome-' + t.id);
      const res = await api.sendManualWelcome(t.id);
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
      alert(`✓ E-Posta Başarıyla Gönderildi!\n\n${res.message || `'${t.name}' şirketine kurumsal Hoş Geldiniz e-postası başarıyla iletildi.`}`);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Hoş geldiniz e-postası gönderilemedi: ' + err.message });
      alert(`⚠️ E-Posta Gönderilemedi!\n\nHata Alındı: ${err.message || 'Bilinmeyen bir hata oluştu.'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // E-Posta Şablonu İşlemleri & Sürükle-Bırak Editör (Madde 4 & 5)
  const handleOpenTemplateModal = (tmpl = null) => {
    const defaultBlocks = [
      { id: 'b_1', type: 'HEADER', subtitle: 'Yapay Zeka Destekli Kurumsal İşletim Sistemi' },
      { id: 'b_2', type: 'GREETING', text: 'Sayın <b>{{company_name}}</b> Yetkilisi, Sayın <b>{{contact_name}}</b>,' },
      { id: 'b_3', type: 'CONTENT', text: 'RECOrion kurumsal aboneliğiniz başarıyla aktif edilmiştir. Kurumunuza özel olarak hazırlanan yapay zeka ajanları ve şirket çalışma ortamınız hazır durumdadır.' },
      { id: 'b_4', type: 'PACKAGE_INFO', planName: '{{plan_name}}', expiryDate: '{{package_expiry_date}}', daysRemaining: '{{days_remaining}}' },
      { id: 'b_5', type: 'CREDENTIALS', loginEmail: '{{login_email}}', passwordText: '{{password}}' },
      { id: 'b_6', type: 'BUTTON', buttonText: 'Yönetim Paneline Giriş Yap →', buttonUrl: '{{login_url}}' },
      { id: 'b_7', type: 'DIVIDER' },
      { id: 'b_8', type: 'FOOTER', footerText: 'Bu e-posta RECDx Bilişim Teknolojileri ve Yapay Zeka A.Ş. tarafından otomatik olarak iletilmiştir.' }
    ];

    if (tmpl) {
      setEditingTemplate(tmpl);
      setTemplateForm({
        code: tmpl.code,
        name: tmpl.name,
        subject: tmpl.subject,
        html_content: tmpl.html_content,
        text_content: tmpl.text_content || '',
        variables: tmpl.variables || [],
        is_active: tmpl.is_active
      });
      setTemplateCanvasBlocks(defaultBlocks);
      setTemplateEditorTab('BUILDER');
    } else {
      setEditingTemplate(null);
      const generatedHtml = compileBlocksToHtml(defaultBlocks);
      setTemplateForm({
        code: '',
        name: '',
        subject: 'RECDx | RECOrion Kurumsal Bildirim',
        html_content: generatedHtml,
        text_content: '',
        variables: ['company_name', 'contact_name', 'plan_name', 'package_expiry_date', 'days_remaining', 'login_email', 'password', 'login_url'],
        is_active: true
      });
      setTemplateCanvasBlocks(defaultBlocks);
      setTemplateEditorTab('BUILDER');
    }
    setTemplateModalOpen(true);
  };

  const handleAddBlockToCanvas = (type) => {
    const preset = EMAIL_PRESET_BLOCKS.find(p => p.type === type);
    if (!preset) return;
    const newBlock = {
      id: 'b_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
      type: preset.type,
      ...preset
    };
    const updated = [...templateCanvasBlocks, newBlock];
    setTemplateCanvasBlocks(updated);
    setTemplateForm(prev => ({
      ...prev,
      html_content: compileBlocksToHtml(updated)
    }));
  };

  const handleRemoveBlockFromCanvas = (id) => {
    const updated = templateCanvasBlocks.filter(b => b.id !== id);
    setTemplateCanvasBlocks(updated);
    setTemplateForm(prev => ({
      ...prev,
      html_content: compileBlocksToHtml(updated)
    }));
  };

  const handleMoveBlock = (index, direction) => {
    const targetIdx = index + direction;
    if (targetIdx < 0 || targetIdx >= templateCanvasBlocks.length) return;
    const updated = [...templateCanvasBlocks];
    const temp = updated[index];
    updated[index] = updated[targetIdx];
    updated[targetIdx] = temp;
    setTemplateCanvasBlocks(updated);
    setTemplateForm(prev => ({
      ...prev,
      html_content: compileBlocksToHtml(updated)
    }));
  };

  const handleUpdateBlockField = (id, field, value) => {
    const updated = templateCanvasBlocks.map(b => b.id === id ? { ...b, [field]: value } : b);
    setTemplateCanvasBlocks(updated);
    setTemplateForm(prev => ({
      ...prev,
      html_content: compileBlocksToHtml(updated)
    }));
  };

  const handleTestSendFromModal = async () => {
    const toEmail = prompt(`'${templateForm.name || "E-Posta"}' şablonunu test etmek için alıcı e-posta adresi giriniz:`, currentUser?.email || 'cuneyterdil@recdx.com');
    if (!toEmail) return;
    try {
      setProcessingId('test-mail-modal');
      if (editingTemplate?.id) {
        const res = await api.testSendEmailTemplate(editingTemplate.id, {
          to_email: toEmail,
          context: {
            subject: templateForm.subject,
            html_content: templateForm.html_content
          }
        });
        setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
        alert(`✓ Test e-postası '${toEmail}' adresine başarıyla gönderildi!`);
      } else {
        if (!templateForm.code.trim() || !templateForm.name.trim() || !templateForm.subject.trim()) {
          alert("Lütfen önce şablon kodu, adı ve konusunu doldurunuz.");
          return;
        }
        const created = await api.createEmailTemplate(templateForm);
        setEditingTemplate(created);
        const res = await api.testSendEmailTemplate(created.id, { to_email: toEmail });
        setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
        alert(`✓ Şablon kaydedildi ve test e-postası '${toEmail}' adresine iletildi!`);
        await loadAllData();
      }
    } catch (err) {
      alert(`⚠️ Test e-postası iletilemedi:\n\n${err.message}`);
      setActionFeedback({ type: 'error', text: 'Test gönderim hatası: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleSaveTemplate = async (e) => {
    e.preventDefault();
    if (!templateForm.code.trim() || !templateForm.name.trim() || !templateForm.subject.trim()) return;
    try {
      setProcessingId('save-template');
      if (editingTemplate) {
        await api.updateEmailTemplate(editingTemplate.id, templateForm);
        setActionFeedback({ type: 'success', text: `✓ '${templateForm.name}' e-posta şablonu güncellendi.` });
      } else {
        await api.createEmailTemplate(templateForm);
        setActionFeedback({ type: 'success', text: `✓ '${templateForm.name}' e-posta şablonu oluşturuldu.` });
      }
      setTemplateModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Şablon kaydedilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteTemplate = async (tmpl) => {
    if (!window.confirm(`'${tmpl.name}' (${tmpl.code}) e-posta şablonunu silmek istediğinize emin misiniz?\n\nNot: Bu şablon aktif zamanlayıcılarda veya sistem akışında kullanılmıyorsa silinebilir.`)) return;
    try {
      setProcessingId('del-tmpl-' + tmpl.id);
      await api.deleteEmailTemplate(tmpl.id);
      setActionFeedback({ type: 'success', text: `✓ '${tmpl.name}' şablonu silindi.` });
      await loadAllData();
    } catch (err) {
      alert(`⚠️ E-POSTA ŞABLONU SİLİNEMEZ!\n\n${err.message}`);
      setActionFeedback({ type: 'error', text: 'Şablon silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleTestSendTemplate = async (tmpl) => {
    const toEmail = prompt(`'${tmpl.name}' şablonunu test etmek için alıcı e-posta adresi giriniz:`, currentUser?.email || 'cuneyterdil@recdx.com');
    if (!toEmail) return;
    try {
      setProcessingId('test-mail-' + tmpl.id);
      const res = await api.testSendEmailTemplate(tmpl.id, { to_email: toEmail });
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
      alert(`✓ Test E-Postası Başarıyla Gönderildi!\n\nAlıcı: ${toEmail}\n${res.message || 'E-posta SMTP üzerinden başarıyla iletildi.'}`);
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Test e-postası gönderilemedi: ' + err.message });
      alert(`⚠️ Test E-Postası Gönderilemedi!\n\nHata Alındı: ${err.message || 'Bilinmeyen hata'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Zamanlayıcı (Schedule) İşlemleri (Madde 2)
  const handleOpenScheduleModal = (sched = null) => {
    if (sched) {
      setEditingSchedule(sched);
      setScheduleForm({
        name: sched.name,
        trigger_type: sched.trigger_type,
        template_code: sched.template_code,
        frequency_days: sched.frequency_days,
        target_lead_days: sched.target_lead_days,
        is_active: sched.is_active
      });
    } else {
      setEditingSchedule(null);
      setScheduleForm({
        name: '',
        trigger_type: 'BEFORE_EXPIRATION_INTERVAL',
        template_code: 'PACKAGE_EXPIRATION_REMINDER',
        frequency_days: 15,
        target_lead_days: 90,
        is_active: true
      });
    }
    setScheduleModalOpen(true);
  };

  const handleSaveSchedule = async (e) => {
    e.preventDefault();
    if (!scheduleForm.name.trim()) return;
    try {
      setProcessingId('save-sched');
      if (editingSchedule) {
        await api.updateSchedule(editingSchedule.id, scheduleForm);
        setActionFeedback({ type: 'success', text: `✓ '${scheduleForm.name}' zamanlama kuralı güncellendi.` });
      } else {
        await api.createSchedule(scheduleForm);
        setActionFeedback({ type: 'success', text: `✓ '${scheduleForm.name}' zamanlama kuralı oluşturuldu.` });
      }
      setScheduleModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Zamanlama kaydedilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteSchedule = async (sched) => {
    if (!window.confirm(`'${sched.name}' zamanlama kuralını silmek istediğinize emin misiniz?`)) return;
    try {
      setProcessingId('del-sched-' + sched.id);
      await api.deleteSchedule(sched.id);
      setActionFeedback({ type: 'success', text: `✓ '${sched.name}' zamanlama kuralı silindi.` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Zamanlama silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleSaveTenantAdmin = async (e) => {
    e.preventDefault();
    if (!selectedTenantDetails?.tenant?.id) return;
    try {
      setProcessingId('save-tenant-admin');
      const res = await api.updateTenantAdmin(selectedTenantDetails.tenant.id, tenantAdminForm);
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
      alert(`✓ Yönetici Bilgileri Kaydedildi!\n\n${res.message || 'Yönetici bilgileri ve erişim şifresi başarıyla güncellendi.'}`);
      setTenantAdminForm(prev => ({ ...prev, new_password: '' }));
      const refreshed = await api.getTenantDetails(selectedTenantDetails.tenant.id);
      setSelectedTenantDetails(refreshed);
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Yönetici güncelleme hatası: ' + err.message });
      alert(`⚠️ Yönetici Kaydedilemedi!\n\nHata: ${err.message || 'Bilinmeyen hata'}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleGenerateTenantPassword = async () => {
    if (!selectedTenantDetails?.tenant?.id) return;
    try {
      setProcessingId('gen-pass');
      const res = await api.generateTenantAdminPassword(selectedTenantDetails.tenant.id);
      setGeneratedAdminPassword(res.generated_password);
      setActionFeedback({ type: 'success', text: `✓ Güçlü şifre üretildi: ${res.generated_password}` });
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Şifre üretme hatası: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleApproveTenantInModal = async () => {
    if (!selectedTenantDetails?.tenant?.id) return;
    try {
      setProcessingId('approve-tenant');
      await api.approveRegisteredTenant(selectedTenantDetails.tenant.id);
      setActionFeedback({ type: 'success', text: `✓ Şirket ve hesabı onaylandı!` });
      setTenantEditForm(prev => ({ ...prev, is_active: true }));
      await loadAllData();
      const refreshed = await api.getTenantDetails(selectedTenantDetails.tenant.id);
      setSelectedTenantDetails(refreshed);
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Onay hatası: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 4. İZİN KATALOĞU CRUD (Madde 4) =================
  const handleOpenPermissionModal = (perm = null) => {
    if (perm) {
      setEditingPermission(perm);
      setPermissionForm({
        code: perm.code,
        module: perm.module,
        name: perm.name,
        description: perm.description || '',
        default_for_roles: perm.default_for_roles || ['SUPER_ADMIN']
      });
    } else {
      setEditingPermission(null);
      setPermissionForm({
        code: '',
        module: 'AGENTS',
        name: '',
        description: '',
        default_for_roles: ['SUPER_ADMIN', 'COMPANY_ADMIN']
      });
    }
    setPermissionModalOpen(true);
  };

  const handleSavePermission = async (e) => {
    e.preventDefault();
    if (!permissionForm.code.trim() || !permissionForm.name.trim()) return;
    try {
      setProcessingId('save-perm');
      if (editingPermission) {
        await api.updatePermission(editingPermission.id, permissionForm);
        setActionFeedback({ type: 'success', text: `✓ '${permissionForm.name}' güncellendi.` });
      } else {
        await api.createPermission(permissionForm);
        setActionFeedback({ type: 'success', text: `✓ '${permissionForm.name}' yetkisi eklendi.` });
      }
      setPermissionModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'İzin kaydetme hatası: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeletePermission = async (perm) => {
    if (!window.confirm(`'${perm.name}' (${perm.code}) iznini silmek istediğinize emin misiniz?`)) return;
    try {
      setProcessingId(perm.id);
      await api.deletePermission(perm.id);
      setActionFeedback({ type: 'success', text: `✓ '${perm.name}' silindi.` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'İzin silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 5. PLAN CRUD (Madde 7) =================
  const handleOpenPlanModal = (plan = null) => {
    if (plan) {
      setEditingPlan(plan);
      setPlanForm({
        code: plan.code,
        name: plan.name,
        description: plan.description || '',
        monthly_price: plan.monthly_price,
        currency: plan.currency || 'TRY',
        max_humans: plan.max_humans,
        max_agents: plan.max_agents,
        max_projects: plan.max_projects,
        monthly_credits: plan.monthly_credits,
        storage_gb: plan.storage_gb,
        allowed_models: plan.allowed_models || ['deepseek-v3'],
        can_create_custom_titles: !!plan.can_create_custom_titles,
        is_active: plan.is_active
      });
    } else {
      setEditingPlan(null);
      setPlanForm({
        code: '',
        name: '',
        description: '',
        monthly_price: 25000,
        currency: 'TRY',
        max_humans: 10,
        max_agents: 10,
        max_projects: 5,
        monthly_credits: 3000,
        storage_gb: 25,
        allowed_models: ['deepseek-v3', 'glm-5.3'],
        can_create_custom_titles: true,
        is_active: true
      });
    }
    setPlanModalOpen(true);
  };

  const handleSavePlan = async (e) => {
    e.preventDefault();
    if (!planForm.code.trim() || !planForm.name.trim()) return;
    try {
      setProcessingId('save-plan');
      if (editingPlan) {
        await api.updatePlan(editingPlan.id, planForm);
        setActionFeedback({ type: 'success', text: `✓ '${planForm.name}' paketi güncellendi.` });
      } else {
        await api.createPlan(planForm);
        setActionFeedback({ type: 'success', text: `✓ '${planForm.name}' paketi oluşturuldu.` });
      }
      setPlanModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Paket kaydedilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeletePlan = async (plan) => {
    if (!window.confirm(`'${plan.name}' (${plan.code}) kiralama paketini silmek istediğinize emin misiniz?\n\nNot: Bu paket hiçbir müşteri tarafından alınmamışsa silinebilir.`)) return;
    try {
      setProcessingId(plan.id);
      await api.deletePlan(plan.id);
      setActionFeedback({ type: 'success', text: `✓ '${plan.name}' paketi silindi.` });
      await loadAllData();
    } catch (err) {
      alert(`⚠️ KİRALAMA PAKETİ SİLİNEMEZ!\n\n${err.message}`);
      setActionFeedback({ type: 'error', text: 'Paket silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 6. EVREN MODEL CRUD (Madde 8) =================
  const handleOpenModelModal = (model = null) => {
    if (model) {
      setEditingModel(model);
      setModelForm({
        model_code: model.model_code,
        display_name: model.display_name,
        model_type: model.model_type,
        context_window: model.context_window,
        effort_coefficient: model.effort_coefficient,
        status: model.status
      });
    } else {
      setEditingModel(null);
      setModelForm({
        model_code: '',
        display_name: '',
        model_type: 'CHAT',
        context_window: 131072,
        effort_coefficient: 1.0,
        status: 'ACTIVE'
      });
    }
    setModelModalOpen(true);
  };

  const handleSaveModel = async (e) => {
    e.preventDefault();
    if (!modelForm.model_code.trim() || !modelForm.display_name.trim()) return;
    try {
      setProcessingId('save-model');
      if (editingModel) {
        await api.updateModel(editingModel.id, modelForm);
        setActionFeedback({ type: 'success', text: `✓ '${modelForm.display_name}' güncellendi.` });
      } else {
        await api.createModel(modelForm);
        setActionFeedback({ type: 'success', text: `✓ '${modelForm.display_name}' modeli eklendi.` });
      }
      setModelModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Model kaydedilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteModel = async (model) => {
    if (!window.confirm(`'${model.display_name}' modelini silmek istediğinize emin misiniz?`)) return;
    try {
      setProcessingId(model.id);
      await api.deleteModel(model.id);
      setActionFeedback({ type: 'success', text: `✓ '${model.display_name}' silindi.` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Model silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 7. GENEL AI MODELİ SEÇİMİ (Madde 6) =================
  const handleSelectDefaultManifestoModel = async (modelCode) => {
    try {
      setProcessingId('save-manifesto-model');
      const res = await api.setDefaultManifestoModel(modelCode);
      setSystemSettings(prev => ({ ...prev, default_manifesto_model: modelCode }));
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Model seçilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 8. NACE KODLARI CRUD (Madde 12) =================
  const handleOpenNaceModal = (item = null) => {
    if (item) {
      setEditingNace(item);
      setNaceForm({
        code: item.code,
        title: item.title,
        sector_group: item.sector_group,
        description: item.description || ''
      });
    } else {
      setEditingNace(null);
      setNaceForm({
        code: '',
        title: '',
        sector_group: 'Bilişim & Yazılım',
        description: ''
      });
    }
    setNaceModalOpen(true);
  };

  const handleSaveNace = async (e) => {
    e.preventDefault();
    if (!naceForm.code.trim() || !naceForm.title.trim()) return;
    try {
      setProcessingId('save-nace');
      if (editingNace) {
        await api.updateNace(editingNace.code, {
          title: naceForm.title,
          sector_group: naceForm.sector_group,
          description: naceForm.description
        });
        setActionFeedback({ type: 'success', text: `✓ '${naceForm.code}' NACE kodu güncellendi.` });
      } else {
        await api.createNace(naceForm);
        setActionFeedback({ type: 'success', text: `✓ '${naceForm.code}' yeni NACE kodu eklendi.` });
      }
      setNaceModalOpen(false);
      const res = await api.searchNace(naceSearch, 50);
      setNaceList(res || []);
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'NACE kaydedilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteNace = async (item) => {
    if (!window.confirm(`'${item.code}' NACE kodunu silmek istediğinize emin misiniz?`)) return;
    try {
      setProcessingId(item.code);
      await api.deleteNace(item.code);
      setActionFeedback({ type: 'success', text: `✓ '${item.code}' silindi.` });
      const res = await api.searchNace(naceSearch, 50);
      setNaceList(res || []);
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'NACE silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 9. SEKTOREL ÜNVANLAR & PROMPT (Madde 13) =================
  const handleOpenTitleModal = (jt = null) => {
    if (jt) {
      setEditingTitle(jt);
      setTitleForm({
        code: jt.code,
        title: jt.title,
        category: jt.category,
        description: jt.description || '',
        base_role_prompt: jt.base_role_prompt,
        required_skills: jt.required_skills || [],
        recommended_model_code: jt.recommended_model_code || 'glm-5.3',
        autonomy_level: jt.autonomy_level || 'L1'
      });
    } else {
      setEditingTitle(null);
      setTitleForm({
        code: '',
        title: '',
        category: 'YAZILIM',
        description: '',
        base_role_prompt: '',
        required_skills: ['Yazılım Geliştirme', 'Algoritma'],
        recommended_model_code: 'glm-5.3',
        autonomy_level: 'L1'
      });
    }
    setTitleModalOpen(true);
  };

  const handleSaveTitle = async (e) => {
    e.preventDefault();
    if (!titleForm.code.trim() || !titleForm.title.trim()) return;
    try {
      setProcessingId('save-title');
      if (editingTitle) {
        await api.updateJobTitle(editingTitle.id, {
          title: titleForm.title,
          category: titleForm.category,
          description: titleForm.description,
          base_role_prompt: titleForm.base_role_prompt,
          required_skills: titleForm.required_skills,
          recommended_model_code: titleForm.recommended_model_code,
          autonomy_level: titleForm.autonomy_level
        });
        setActionFeedback({ type: 'success', text: `✓ '${titleForm.title}' güncellendi.` });
      } else {
        await api.createAdminJobTitle(titleForm);
        setActionFeedback({ type: 'success', text: `✓ '${titleForm.title}' ünvanı eklendi.` });
      }
      setTitleModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Ünvan kaydedilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteTitle = async (jt) => {
    if (!window.confirm(`'${jt.title}' ünvanını silmek istediğinize emin misiniz?`)) return;
    try {
      setProcessingId(jt.id);
      await api.deleteJobTitle(jt.id);
      setActionFeedback({ type: 'success', text: `✓ '${jt.title}' silindi.` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Ünvan silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleRegeneratePromptWithAI = async () => {
    if (!editingTitle?.id) {
      alert("Lütfen önce mevcut bir ünvanı düzenleyin.");
      return;
    }
    try {
      setRegeneratingPrompt(true);
      const res = await api.regenerateJobTitlePrompt(editingTitle.id);
      setTitleForm(prev => ({ ...prev, base_role_prompt: res.new_prompt }));
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Prompt üretimi başarısız: ' + err.message });
    } finally {
      setRegeneratingPrompt(false);
    }
  };

  // Filtrelenmiş Listeler
  const filteredLeads = leads
    .filter(l => {
      if (leadApprovalFilter === 'PENDING') return l.status === 'PENDING';
      if (leadApprovalFilter === 'APPROVED') return l.status === 'APPROVED';
      return true;
    })
    .filter(l => 
      !searchQuery || 
      (l.company_name && l.company_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (l.contact_email && l.contact_email.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (l.phone && l.phone.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (l.plan_code && l.plan_code.toLowerCase().includes(searchQuery.toLowerCase()))
    );

  const filteredTenants = tenants.filter(t => {
    const matchesSearch = !searchQuery || 
      (t.name && t.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (t.contact_email && t.contact_email.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (t.slug && t.slug.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (t.tax_id && t.tax_id.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = tenantStatusFilter === 'ALL' ||
      (tenantStatusFilter === 'APPROVED' && t.is_active) ||
      (tenantStatusFilter === 'PENDING' && !t.is_active);

    return matchesSearch && matchesStatus;
  });

  const filteredPermissions = permissions.filter(p => {
    const matchMod = permissionModuleFilter === 'ALL' || p.module === permissionModuleFilter;
    const matchSearch = !searchQuery || 
      p.code.toLowerCase().includes(searchQuery.toLowerCase()) || 
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchMod && matchSearch;
  });

  const filteredJobTitles = jobTitles.filter(jt => {
    const matchCat = jobTitleCategoryFilter === 'ALL' || jt.category === jobTitleCategoryFilter;
    const matchSearch = !searchQuery || 
      jt.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
      jt.code.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCat && matchSearch;
  });

  const filteredModels = models.filter(m => 
    !searchQuery || 
    (m.model_code && m.model_code.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (m.display_name && m.display_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (m.model_type && m.model_type.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const filteredEmailTemplates = emailTemplates.filter(t =>
    !searchQuery ||
    (t.name && t.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (t.code && t.code.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (t.subject && t.subject.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const filteredSchedules = schedules.filter(s =>
    !searchQuery ||
    (s.name && s.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (s.trigger_type && s.trigger_type.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (s.template_code && s.template_code.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="super-admin-layout">
      
      {/* ======================================================== */}
      {/* SOL NAVBAR MENÜ (Kapanabilir 3D Sidebar - Madde 3 & 4)    */}
      {/* ======================================================== */}
      <aside className={`super-admin-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        {/* LOGO & KURUMSAL METİN (Madde 3: Kapanınca ikon üstte ortalanır) */}
        <div className="super-admin-sidebar-header" style={{ padding: sidebarCollapsed ? '16px 8px' : '16px 14px' }}>
          {sidebarCollapsed ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, width: '100%' }}>
              <div 
                className="super-admin-logo-box" 
                title="RECOrion Süper Yönetim"
                style={{ width: 38, height: 38, fontSize: '1.2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto', boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)' }}
              >
                🪐
              </div>
              <button
                onClick={() => setSidebarCollapsed(false)}
                className="super-admin-sidebar-toggle-btn"
                title="Menüyü Genişlet (Aç)"
                style={{ margin: '0 auto', width: 30, height: 30, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <PanelLeftOpen style={{ width: 16, height: 16 }} />
              </button>
            </div>
          ) : (
            <div className="super-admin-logo-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, overflow: 'hidden' }}>
                <div className="super-admin-logo-box" title="RECOrion Süper Yönetim">🪐</div>
                <div style={{ overflow: 'hidden' }}>
                  <div className="super-admin-brand-name">
                    <span>RECOrion</span>
                    <span className="super-admin-brand-tag">SÜPER</span>
                  </div>
                  <div className="super-admin-brand-sub">
                    Operitional Reasoning Intelligence Orchestration Network
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSidebarCollapsed(true)}
                className="super-admin-sidebar-toggle-btn"
                title="Menüyü Sola Doğru Kapat"
              >
                <PanelLeftClose style={{ width: 16, height: 16 }} />
              </button>
            </div>
          )}
        </div>

        {/* MENÜ LİSTESİ */}
        <nav className="super-admin-nav">
          <div className="super-admin-nav-section-title">Genel & Operasyon</div>

          {/* DASHBOARD (Madde 7) */}
          <button
            onClick={() => { switchTab('DASHBOARD'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'DASHBOARD' ? 'active' : ''}`}
            title="Dashboard (Genel Bakış)"
          >
            <div className="super-admin-nav-item-left">
              <LayoutDashboard style={{ width: 17, height: 17, color: '#a78bfa' }} />
              {!sidebarCollapsed && <span>Dashboard (Genel Bakış)</span>}
            </div>
          </button>

          {/* BAŞVURU ONAY DURUM (Madde 8) */}
          <button
            onClick={() => { switchTab('LEADS'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'LEADS' ? 'active' : ''}`}
            title="Başvuru Onay Durum"
          >
            <div className="super-admin-nav-item-left">
              <Clock style={{ width: 17, height: 17, color: '#38bdf8' }} />
              {!sidebarCollapsed && <span>Başvuru Onay Durum</span>}
            </div>
            {leads.filter(l => l.status === 'PENDING').length > 0 && (
              <span style={{ 
                background: '#f59e0b', 
                color: '#000', 
                fontSize: '0.65rem', 
                fontWeight: 800, 
                padding: '2px 6px', 
                borderRadius: 999,
                boxShadow: '0 0 8px rgba(245, 158, 11, 0.5)'
              }}>
                {leads.filter(l => l.status === 'PENDING').length}
              </span>
            )}
          </button>

          {/* KAYITLI ŞİRKETLER */}
          <button
            onClick={() => { switchTab('TENANTS'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'TENANTS' ? 'active' : ''}`}
            title="Kayıtlı Şirketler"
          >
            <div className="super-admin-nav-item-left">
              <Building2 style={{ width: 17, height: 17, color: '#818cf8' }} />
              {!sidebarCollapsed && <span>Kayıtlı Şirketler</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>{tenants.length}</span>
            )}
          </button>

          <div className="super-admin-nav-section-title">Yetki & Paketler</div>

          {/* İZİN KATALOĞU */}
          <button
            onClick={() => { switchTab('PERMISSIONS'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'PERMISSIONS' ? 'active' : ''}`}
            title="İzin Kataloğu (RBAC)"
          >
            <div className="super-admin-nav-item-left">
              <KeyRound style={{ width: 17, height: 17, color: '#fbbf24' }} />
              {!sidebarCollapsed && <span>İzin Kataloğu (RBAC)</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>{permissions.length}</span>
            )}
          </button>

          {/* KİRALAMA PAKETLERİ */}
          <button
            onClick={() => { switchTab('PLANS'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'PLANS' ? 'active' : ''}`}
            title="Kiralama Paketleri"
          >
            <div className="super-admin-nav-item-left">
              <Package style={{ width: 17, height: 17, color: '#34d399' }} />
              {!sidebarCollapsed && <span>Kiralama Paketleri</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>{plans.length}</span>
            )}
          </button>

          <div className="super-admin-nav-section-title">İletişim & Otomasyon</div>

          {/* E-POSTA ŞABLONLARI (Madde 1) */}
          <button
            onClick={() => { switchTab('EMAIL_TEMPLATES'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'EMAIL_TEMPLATES' ? 'active' : ''}`}
            title="E-Posta Şablonları & HTML Editör"
          >
            <div className="super-admin-nav-item-left">
              <Mail style={{ width: 17, height: 17, color: '#f43f5e' }} />
              {!sidebarCollapsed && <span>E-Posta Şablonları</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>{emailTemplates.length}</span>
            )}
          </button>

          {/* ZAMANLAYICILAR (Madde 2) */}
          <button
            onClick={() => { switchTab('SCHEDULES'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'SCHEDULES' ? 'active' : ''}`}
            title="Zamanlayıcılar (Schedules)"
          >
            <div className="super-admin-nav-item-left">
              <Clock style={{ width: 17, height: 17, color: '#10b981' }} />
              {!sidebarCollapsed && <span>Zamanlayıcılar (Schedules)</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>{schedules.length}</span>
            )}
          </button>

          <div className="super-admin-nav-section-title">Yapay Zeka & Sektörel</div>

          {/* GENEL AI MODELİ */}
          <button
            onClick={() => { switchTab('AI_MODEL_SETTINGS'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'AI_MODEL_SETTINGS' ? 'active' : ''}`}
            title="Genel AI Modeli (Manifesto)"
          >
            <div className="super-admin-nav-item-left">
              <Zap style={{ width: 17, height: 17, color: '#f43f5e' }} />
              {!sidebarCollapsed && <span>Genel AI Modeli</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ background: 'rgba(244,63,94,0.2)', color: '#f43f5e', fontSize: '0.6rem', padding: '2px 5px', borderRadius: 4, fontWeight: 700 }}>
                ÇEKİRDEK
              </span>
            )}
          </button>

          {/* EVREN MODELLERİ */}
          <button
            onClick={() => { switchTab('MODELS'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'MODELS' ? 'active' : ''}`}
            title="EVREN Modelleri"
          >
            <div className="super-admin-nav-item-left">
              <Cpu style={{ width: 17, height: 17, color: '#a78bfa' }} />
              {!sidebarCollapsed && <span>EVREN Modelleri</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>{models.length}</span>
            )}
          </button>

          {/* NACE KODLARI */}
          <button
            onClick={() => { switchTab('NACE'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'NACE' ? 'active' : ''}`}
            title="NACE Kodları Kataloğu"
          >
            <div className="super-admin-nav-item-left">
              <Tag style={{ width: 17, height: 17, color: '#38bdf8' }} />
              {!sidebarCollapsed && <span>NACE Kodları</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>2,160+</span>
            )}
          </button>

          {/* SEKTÖREL ROLLER */}
          <button
            onClick={() => { switchTab('TITLES'); setSearchQuery(''); }}
            className={`super-admin-nav-item ${activeTab === 'TITLES' ? 'active' : ''}`}
            title="Sektörel Roller & Promptlar"
          >
            <div className="super-admin-nav-item-left">
              <Briefcase style={{ width: 17, height: 17, color: '#ec4899' }} />
              {!sidebarCollapsed && <span>Sektörel Roller</span>}
            </div>
            {!sidebarCollapsed && (
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>{jobTitles.length}</span>
            )}
          </button>
        </nav>

        {/* ALT AKSİYONLAR */}
        <div className="super-admin-sidebar-footer" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {/* RECDx Resmi Web Sitesi Butonu (Yeni Sekmede Açılır - Madde 6) */}
          <a
            href="https://www.recdx.com"
            target="_blank"
            rel="noopener noreferrer"
            className="super-admin-btn-secondary"
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 7,
              padding: '9px 12px',
              borderRadius: 12,
              fontSize: '0.785rem',
              fontWeight: 700,
              color: '#38bdf8',
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              textDecoration: 'none',
              boxSizing: 'border-box',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            title="RECDx Resmi Web Sitesine Git (https://www.recdx.com - Yeni Sekmede Açılır)"
          >
            <Globe style={{ width: 15, height: 15, color: '#38bdf8', flexShrink: 0 }} />
            {!sidebarCollapsed && <span>www.recdx.com</span>}
            {!sidebarCollapsed && <ExternalLink style={{ width: 12, height: 12, opacity: 0.8 }} />}
          </a>

          <button
            onClick={onLogout}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              padding: '9px 12px',
              borderRadius: 12,
              fontSize: '0.785rem',
              fontWeight: 600,
              color: '#f87171',
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            title="Güvenli Çıkış Yap"
          >
            <LogOut style={{ width: 14, height: 14 }} />
            {!sidebarCollapsed && <span>Güvenli Çıkış</span>}
          </button>
        </div>
      </aside>

      {/* ======================================================== */}
      {/* SAĞ ANA ALAN (Madde 3 - KUSURSUZ SCROLLING)              */}
      {/* ======================================================== */}
      <main className="super-admin-main">
        
        {/* ÜST HEADER */}
        <header className="super-admin-header">
          <div className="super-admin-header-title">
            <span>RECDx Süper Yönetim Konsolu</span>
            <span style={{ color: '#64748b', fontSize: '0.8rem' }}>/</span>
            <span style={{ color: '#146ceb', fontSize: '0.825rem' }}>
              {activeTab === 'DASHBOARD' && 'Sistem Genel Bakış & Dashboard'}
              {activeTab === 'LEADS' && 'Başvuru Onay Durum Masası'}
              {activeTab === 'TENANTS' && 'Kayıtlı Kurumlar & Şirket Yönetimi'}
              {activeTab === 'EMAIL_TEMPLATES' && 'Kurumsal E-Posta Şablonları & HTML Editörü'}
              {activeTab === 'SCHEDULES' && 'Otomatik Zamanlayıcılar (Schedules)'}
              {activeTab === 'PERMISSIONS' && 'Sistem Yetki Kataloğu (RBAC)'}
              {activeTab === 'PLANS' && 'Kiralama Paketleri Yönetimi'}
              {activeTab === 'MODELS' && 'EVREN Model Kataloğu'}
              {activeTab === 'AI_MODEL_SETTINGS' && 'Çekirdek Manifesto & Ajan AI Modeli Seçimi'}
              {activeTab === 'NACE' && 'NACE Faaliyet Kodları Kataloğu (Rev.2)'}
              {activeTab === 'TITLES' && 'Sektörel Personel Ünvanları & Rol Promptları'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={loadAllData}
              disabled={loading}
              className="super-admin-btn-secondary"
              style={{ padding: '7px 10px' }}
              title="Verileri Yenile"
            >
              <RefreshCw style={{ width: 15, height: 15 }} className={loading ? 'animate-spin' : ''} />
            </button>

            {/* SAĞ ÜST KULLANICI PROFİL KARTI */}
            <button
              id="top-profile-button"
              onClick={() => setProfileModalOpen(true)}
              className="super-admin-user-btn"
            >
              <div className="super-admin-user-avatar">MC</div>
              <div>
                <div style={{ fontSize: '0.785rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>{currentUser?.display_name || 'Muhammed Cüneyt ERDİL'}</span>
                  <Settings style={{ width: 12, height: 12, opacity: 0.7 }} />
                </div>
                <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {currentUser?.email || 'cuneyterdil@recdx.com'}
                </div>
              </div>
            </button>
          </div>
        </header>

        {/* GERİ BİLDİRİM BANNERI */}
        {actionFeedback && (
          <div 
            style={{
              padding: '10px 28px',
              fontSize: '0.785rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: actionFeedback.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: actionFeedback.type === 'success' ? '#6ee7b7' : '#fca5a5',
              borderBottom: '1px solid ' + (actionFeedback.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)')
            }}
          >
            <span>{actionFeedback.text}</span>
            <button 
              onClick={() => setActionFeedback(null)} 
              style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.75rem' }}
            >
              ✕ Kapat
            </button>
          </div>
        )}

        {/* İÇERİK GÖVDESİ */}
        <div className="super-admin-content">
          
          {/* TAB 0: DASHBOARD (GENEL BAKIŞ & METRİKLER - Madde 7) */}
          {activeTab === 'DASHBOARD' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* Sayfa Başlığı */}
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <LayoutDashboard style={{ width: 22, height: 22, color: '#a78bfa' }} />
                    <span>Süper Yönetim Kontrol Paneli (Dashboard)</span>
                  </h2>
                  <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
                    RECOrion platformunun kurumsal başvuru, şirket, yapay zeka modelleri ve altyapı metrikleri.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ 
                    padding: '6px 14px', 
                    borderRadius: 999, 
                    background: 'rgba(16, 185, 129, 0.12)', 
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    color: '#6ee7b7',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6
                  }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', display: 'inline-block', boxShadow: '0 0 8px #10b981' }}></span>
                    <span>Sistem Çevrimiçi</span>
                  </div>
                </div>
              </div>

              {/* 3D KPI KARTLARI GRİDİ (Madde 7) */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 18 }}>
                
                {/* KART 1: Aktif Edilmemiş Yeni Müşteri Sayısı (Tıklayınca Onaylanmamışlar Filtreli Açılır) */}
                <div 
                  onClick={() => { switchTab('LEADS'); setLeadApprovalFilter('PENDING'); setSearchQuery(''); }}
                  className="super-admin-kpi-card-3d glow-amber"
                  title="Onay bekleyen başvuruları görüntülemek için tıklayın"
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Bekleyen Başvurular
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: 2 }}>
                        Aktif Edilmemiş Yeni Müşteriler
                      </div>
                    </div>
                    <div style={{ 
                      width: 42, 
                      height: 42, 
                      borderRadius: 12, 
                      background: 'rgba(245, 158, 11, 0.15)', 
                      border: '1px solid rgba(245, 158, 11, 0.35)',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      color: '#fbbf24' 
                    }}>
                      <Clock style={{ width: 22, height: 22 }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: '#fff', lineHeight: 1 }}>
                      {leads.filter(l => l.status === 'PENDING').length}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 700 }}>
                      Başvuru Onay Bekliyor
                    </span>
                  </div>

                  <div style={{ 
                    marginTop: 14, 
                    paddingTop: 12, 
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    fontSize: '0.725rem',
                    color: '#fbbf24'
                  }}>
                    <span style={{ fontWeight: 600 }}>Onay Listesine Git</span>
                    <ArrowRight style={{ width: 14, height: 14 }} />
                  </div>
                </div>

                {/* KART 2: Kayıtlı Şirketlerin Toplamı (Tıklayınca Müşteri Listesi Açılır) */}
                <div 
                  onClick={() => { switchTab('TENANTS'); setSearchQuery(''); }}
                  className="super-admin-kpi-card-3d glow-purple"
                  title="Kayıtlı şirketleri listelemek için tıklayın"
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#c084fc', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Kurumsal Portföy
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: 2 }}>
                        Kayıtlı Şirketlerin Toplamı
                      </div>
                    </div>
                    <div style={{ 
                      width: 42, 
                      height: 42, 
                      borderRadius: 12, 
                      background: 'rgba(113, 52, 226, 0.2)', 
                      border: '1px solid rgba(113, 52, 226, 0.4)',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      color: '#a78bfa' 
                    }}>
                      <Building2 style={{ width: 22, height: 22 }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: '#fff', lineHeight: 1 }}>
                      {tenants.length}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: '#c084fc', fontWeight: 700 }}>
                      Kayıtlı Kurum / Şirket
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.72rem', color: '#cbd5e1', marginTop: 4 }}>
                    <span style={{ color: '#34d399', fontWeight: 700 }}>{tenants.filter(t => t.is_active).length} Onaylı</span>
                    <span>•</span>
                    <span style={{ color: '#fbbf24', fontWeight: 700 }}>{tenants.filter(t => !t.is_active).length} Onay Bekliyor</span>
                  </div>

                  <div style={{ 
                    marginTop: 14, 
                    paddingTop: 12, 
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    fontSize: '0.725rem',
                    color: '#c084fc'
                  }}>
                    <span style={{ fontWeight: 600 }}>Şirketler Listesini Aç</span>
                    <ArrowRight style={{ width: 14, height: 14 }} />
                  </div>
                </div>

                {/* KART 3: Onaylanmış Müşteri Başvuruları */}
                <div 
                  onClick={() => { switchTab('LEADS'); setLeadApprovalFilter('APPROVED'); setSearchQuery(''); }}
                  className="super-admin-kpi-card-3d"
                  style={{ borderColor: 'rgba(16, 185, 129, 0.3)' }}
                  title="Onaylanmış müşteri başvurularını incelemek için tıklayın"
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Onaylanmış Başvurular
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: 2 }}>
                        Odoo & Sistemde Aktif
                      </div>
                    </div>
                    <div style={{ 
                      width: 42, 
                      height: 42, 
                      borderRadius: 12, 
                      background: 'rgba(16, 185, 129, 0.15)', 
                      border: '1px solid rgba(16, 185, 129, 0.35)',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      color: '#34d399' 
                    }}>
                      <CheckCircle2 style={{ width: 22, height: 22 }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: '#fff', lineHeight: 1 }}>
                      {leads.filter(l => l.status === 'APPROVED').length}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: '#34d399', fontWeight: 700 }}>
                      Müşteri Satışı Resmileşti
                    </span>
                  </div>

                  <div style={{ 
                    marginTop: 14, 
                    paddingTop: 12, 
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    fontSize: '0.725rem',
                    color: '#34d399'
                  }}>
                    <span style={{ fontWeight: 600 }}>Onaylananları Filtrele</span>
                    <ArrowRight style={{ width: 14, height: 14 }} />
                  </div>
                </div>

                {/* KART 4: EVREN Model Kataloğu */}
                <div 
                  onClick={() => { switchTab('MODELS'); setSearchQuery(''); }}
                  className="super-admin-kpi-card-3d"
                  style={{ borderColor: 'rgba(56, 189, 248, 0.3)' }}
                  title="EVREN modellerini görüntülemek için tıklayın"
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Yapay Zeka Altyapısı
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: 2 }}>
                        Tanımlı EVREN Modelleri
                      </div>
                    </div>
                    <div style={{ 
                      width: 42, 
                      height: 42, 
                      borderRadius: 12, 
                      background: 'rgba(56, 189, 248, 0.15)', 
                      border: '1px solid rgba(56, 189, 248, 0.35)',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      color: '#38bdf8' 
                    }}>
                      <Cpu style={{ width: 22, height: 22 }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: '#fff', lineHeight: 1 }}>
                      {models.length}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 700 }}>
                      LLM Muhakeme Motoru
                    </span>
                  </div>

                  <div style={{ 
                    marginTop: 14, 
                    paddingTop: 12, 
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    fontSize: '0.725rem',
                    color: '#38bdf8'
                  }}>
                    <span style={{ fontWeight: 600 }}>Model Kataloğuna Git</span>
                    <ArrowRight style={{ width: 14, height: 14 }} />
                  </div>
                </div>

              </div>

              {/* DASHBOARD ALT ALAN: Bekleyen Başvuru Özeti & Sistem Durumu */}
              <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
                
                {/* SOL: Bekleyen Yeni Başvurular Önizleme */}
                <div style={{ 
                  background: 'linear-gradient(180deg, #101628 0%, #0d1222 100%)',
                  borderRadius: 18,
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  padding: 20,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Clock style={{ width: 18, height: 18, color: '#f59e0b' }} />
                      <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#fff' }}>
                        Onay Bekleyen Son Başvurular
                      </h3>
                    </div>
                    <button
                      onClick={() => { switchTab('LEADS'); setLeadApprovalFilter('PENDING'); }}
                      className="super-admin-btn-secondary"
                      style={{ fontSize: '0.725rem', padding: '5px 10px' }}
                    >
                      Tümünü Gör ({leads.filter(l => l.status === 'PENDING').length})
                    </button>
                  </div>

                  {leads.filter(l => l.status === 'PENDING').length === 0 ? (
                    <div style={{ padding: '36px 20px', textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                      <CheckCircle2 style={{ width: 36, height: 36, color: '#10b981', margin: '0 auto 8px', opacity: 0.8 }} />
                      <div>Şu anda onay bekleyen yeni başvuru bulunmuyor.</div>
                      <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: 4 }}>Tüm müşteri talepleri işleme alındı.</div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {leads.filter(l => l.status === 'PENDING').slice(0, 4).map((ld) => (
                        <div 
                          key={ld.id}
                          style={{
                            background: 'rgba(255, 255, 255, 0.02)',
                            border: '1px solid rgba(245, 158, 11, 0.2)',
                            borderRadius: 12,
                            padding: '12px 14px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            transition: 'all 0.15s'
                          }}
                        >
                          <div>
                            <div style={{ fontWeight: 800, color: '#fff', fontSize: '0.85rem' }}>
                              {ld.company_name}
                            </div>
                            <div style={{ fontSize: '0.725rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: 12, marginTop: 4 }}>
                              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Mail style={{ width: 12, height: 12, color: '#818cf8' }} />
                                {ld.contact_email}
                              </span>
                              <span style={{ color: '#38bdf8', fontWeight: 600 }}>
                                {ld.plan?.name || 'Paket Bilgisi'}
                              </span>
                            </div>
                          </div>

                          <button
                            onClick={() => { switchTab('LEADS'); setLeadApprovalFilter('PENDING'); }}
                            className="super-admin-btn-corporate"
                            style={{ 
                              padding: '6px 12px', 
                              fontSize: '0.725rem',
                              background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
                              borderColor: 'rgba(253, 230, 138, 0.4)'
                            }}
                          >
                            <span>İncele / Onayla</span>
                            <ArrowRight style={{ width: 12, height: 12 }} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* SAĞ: Sistem Entegrasyonları ve Altyapı Özeti */}
                <div style={{ 
                  background: 'linear-gradient(180deg, #101628 0%, #0d1222 100%)',
                  borderRadius: 18,
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  padding: 20,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <ShieldCheck style={{ width: 18, height: 18, color: '#818cf8' }} />
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#fff' }}>
                      Altyapı & Entegrasyon Durumu
                    </h3>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    
                    <div style={{ 
                      padding: '10px 12px', 
                      borderRadius: 10, 
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Sparkles style={{ width: 15, height: 15, color: '#c084fc' }} />
                        <div>
                          <div style={{ fontSize: '0.775rem', fontWeight: 700, color: '#fff' }}>EVREN LLM Gateway</div>
                          <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontFamily: 'monospace' }}>https://evren-llmapi.ssyz.org.tr/v1</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.68rem', fontWeight: 800, color: '#34d399', background: 'rgba(16,185,129,0.15)', padding: '2px 8px', borderRadius: 999 }}>
                        Aktif
                      </span>
                    </div>

                    <div style={{ 
                      padding: '10px 12px', 
                      borderRadius: 10, 
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Cpu style={{ width: 15, height: 15, color: '#38bdf8' }} />
                        <div>
                          <div style={{ fontSize: '0.775rem', fontWeight: 700, color: '#fff' }}>Çekirdek Manifesto Modeli</div>
                          <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Ajan rolleri ve şirket manifestosu</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#fff', background: '#7134e2', padding: '2px 8px', borderRadius: 6, fontFamily: 'monospace' }}>
                        {systemSettings?.default_manifesto_model || 'deepseek-v3'}
                      </span>
                    </div>

                    <div style={{ 
                      padding: '10px 12px', 
                      borderRadius: 10, 
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Layers style={{ width: 15, height: 15, color: '#fbbf24' }} />
                        <div>
                          <div style={{ fontSize: '0.775rem', fontWeight: 700, color: '#fff' }}>Odoo 19 ERP Modülleri</div>
                          <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>sale.order & res.partner senkronizasyonu</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.68rem', fontWeight: 800, color: '#34d399', background: 'rgba(16,185,129,0.15)', padding: '2px 8px', borderRadius: 999 }}>
                        Bağlı
                      </span>
                    </div>

                    <div style={{ 
                      padding: '10px 12px', 
                      borderRadius: 10, 
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <KeyRound style={{ width: 15, height: 15, color: '#10b981' }} />
                        <div>
                          <div style={{ fontSize: '0.775rem', fontWeight: 700, color: '#fff' }}>Yetki & Rol Tanımları</div>
                          <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>RBAC kataloğu ve personel ünvanları</div>
                        </div>
                      </div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#cbd5e1', fontFamily: 'monospace' }}>
                        {permissions.length} İzin / {jobTitles.length} Rol
                      </span>
                    </div>

                  </div>
                </div>

              </div>

            </div>
          )}

          {/* TAB 1: LEADS & ODOO ONAY (Madde 8) */}
          {activeTab === 'LEADS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Clock style={{ width: 20, height: 20, color: '#38bdf8' }} />
                    <span>Başvuru Onay Durum Masası</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    Resmi siteden paket kiralayan müşterilerin Odoo 19 siparişleri ve onay süreçleri.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  {/* 3D Segmentli Filtre Butonları (Madde 8) */}
                  <div className="super-admin-toggle-3d-group">
                    <button
                      type="button"
                      onClick={() => setLeadApprovalFilter('PENDING')}
                      className={`super-admin-toggle-3d-btn pending ${leadApprovalFilter === 'PENDING' ? 'active' : ''}`}
                      title="Onay Bekleyen Başvuruları Listele"
                    >
                      <Clock style={{ width: 15, height: 15 }} />
                      <span>Başvurusu Onaylanmamışlar ({leads.filter(l => l.status === 'PENDING').length})</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setLeadApprovalFilter('APPROVED')}
                      className={`super-admin-toggle-3d-btn approved ${leadApprovalFilter === 'APPROVED' ? 'active' : ''}`}
                      title="Onaylanmış Başvuruları Listele"
                    >
                      <CheckCircle2 style={{ width: 15, height: 15 }} />
                      <span>Başvurusu Onaylanmışlar ({leads.filter(l => l.status === 'APPROVED').length})</span>
                    </button>
                  </div>

                  {renderViewModeToggle(leadViewMode, setLeadViewMode)}

                  <div style={{ width: 220, position: 'relative' }}>
                    <Search style={{ width: 14, height: 14, position: 'absolute', left: 10, top: 11, color: '#64748b' }} />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Şirket veya e-posta ara..."
                      className="super-admin-input"
                      style={{ paddingLeft: 32 }}
                    />
                  </div>
                </div>
              </div>

              {leadViewMode === 'KANBAN' ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, alignItems: 'start' }}>
                  {/* Kolon 1: Onay Bekleyenler */}
                  <div style={{ background: 'rgba(255,255,255,0.02)', borderRadius: 14, border: '1px solid rgba(245,158,11,0.25)', padding: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid rgba(255,255,255,0.06)', marginBottom: 14 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Clock style={{ width: 16, height: 16, color: '#fbbf24' }} />
                        <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#fff', margin: 0 }}>Onay Bekleyen Başvurular</h4>
                      </div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 800, background: 'rgba(245,158,11,0.2)', color: '#fbbf24', padding: '2px 8px', borderRadius: 999 }}>
                        {leads.filter(l => l.status === 'PENDING').length}
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {leads.filter(l => l.status === 'PENDING').filter(l => !searchQuery || l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) || l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())).length === 0 ? (
                        <div style={{ padding: '28px', textAlign: 'center', color: '#64748b', fontSize: '0.8rem' }}>
                          Onay bekleyen başvuru bulunmuyor.
                        </div>
                      ) : (
                        leads.filter(l => l.status === 'PENDING').filter(l => !searchQuery || l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) || l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())).map(lead => (
                          <div key={lead.id} className="super-admin-card" style={{ padding: 14, border: '1px solid rgba(245,158,11,0.25)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span style={{ fontFamily: 'monospace', fontSize: '0.7rem', color: '#34d399', fontWeight: 800 }}>
                                {lead.odoo_order_name || 'Odoo: Otomatik'}
                              </span>
                              <span style={{ fontSize: '0.68rem', fontWeight: 800, color: '#fbbf24', background: 'rgba(245,158,11,0.2)', padding: '2px 6px', borderRadius: 4 }}>
                                ⏳ Onay Bekliyor
                              </span>
                            </div>
                            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#fff', margin: '8px 0 4px 0' }}>{lead.company_name}</h4>
                            <div style={{ fontSize: '0.725rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: 3 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Mail style={{ width: 12, height: 12, color: '#818cf8' }} />
                                <span>{lead.contact_email}</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Phone style={{ width: 12, height: 12 }} />
                                <span>{lead.phone || '-'}</span>
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#a78bfa' }}>
                                {lead.plan?.name || 'Standart Paket'}
                              </span>
                              <button
                                type="button"
                                onClick={() => handleApproveLead(lead)}
                                disabled={processingId === lead.id}
                                className="super-admin-btn-corporate"
                                style={{ padding: '5px 12px', fontSize: '0.72rem' }}
                              >
                                {processingId === lead.id ? <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" /> : <CheckCircle2 style={{ width: 12, height: 12 }} />}
                                <span>Onayla & Aktif Et</span>
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Kolon 2: Onaylananlar */}
                  <div style={{ background: 'rgba(255,255,255,0.02)', borderRadius: 14, border: '1px solid rgba(16,185,129,0.25)', padding: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid rgba(255,255,255,0.06)', marginBottom: 14 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <CheckCircle2 style={{ width: 16, height: 16, color: '#34d399' }} />
                        <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#fff', margin: 0 }}>Onaylanan ve Aktif Başvurular</h4>
                      </div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 800, background: 'rgba(16,185,129,0.2)', color: '#34d399', padding: '2px 8px', borderRadius: 999 }}>
                        {leads.filter(l => l.status === 'APPROVED').length}
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {leads.filter(l => l.status === 'APPROVED').filter(l => !searchQuery || l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) || l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())).length === 0 ? (
                        <div style={{ padding: '28px', textAlign: 'center', color: '#64748b', fontSize: '0.8rem' }}>
                          Henüz onaylanmış başvuru bulunmuyor.
                        </div>
                      ) : (
                        leads.filter(l => l.status === 'APPROVED').filter(l => !searchQuery || l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) || l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())).map(lead => (
                          <div key={lead.id} className="super-admin-card" style={{ padding: 14, border: '1px solid rgba(16,185,129,0.25)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span style={{ fontFamily: 'monospace', fontSize: '0.7rem', color: '#34d399', fontWeight: 800 }}>
                                {lead.odoo_order_name || 'Odoo: Onaylandı'}
                              </span>
                              <span style={{ fontSize: '0.68rem', fontWeight: 800, color: '#34d399', background: 'rgba(16,185,129,0.2)', padding: '2px 6px', borderRadius: 4 }}>
                                ✓ Aktif
                              </span>
                            </div>
                            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#fff', margin: '8px 0 4px 0' }}>{lead.company_name}</h4>
                            <div style={{ fontSize: '0.725rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: 3 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Mail style={{ width: 12, height: 12, color: '#818cf8' }} />
                                <span>{lead.contact_email}</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Phone style={{ width: 12, height: 12 }} />
                                <span>{lead.phone || '-'}</span>
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#a78bfa' }}>
                                {lead.plan?.name || 'Paket'}
                              </span>
                              <span style={{ fontSize: '0.72rem', color: '#6ee7b7', fontWeight: 700 }}>
                                Aktivasyon Tamamlandı
                              </span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th>Şirket Ünvanı & Yetkili</th>
                        <th>İletişim & NACE</th>
                        <th>Seçilen Paket</th>
                        <th>Odoo Sipariş No</th>
                        <th>Durum</th>
                        <th style={{ textAlign: 'right' }}>Aksiyon</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredLeads.length === 0 ? (
                        <tr>
                          <td colSpan="6" style={{ textAlign: 'center', padding: '36px', color: '#64748b' }}>
                            {leadApprovalFilter === 'PENDING'
                              ? 'Şu anda onay bekleyen müşteri başvurusu bulunmuyor.'
                              : 'Henüz onaylanmış müşteri başvurusu bulunmuyor.'}
                          </td>
                        </tr>
                      ) : (
                        filteredLeads.map((lead) => (
                          <tr key={lead.id}>
                            <td>
                              <div style={{ fontWeight: 800, color: '#fff' }}>{lead.company_name}</div>
                              <div style={{ fontSize: '0.725rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                                <Mail style={{ width: 12, height: 12, color: '#818cf8' }} />
                                <span>{lead.contact_email}</span>
                              </div>
                            </td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Phone style={{ width: 12, height: 12 }} />
                                <span>{lead.phone || '-'}</span>
                              </div>
                              <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 3 }}>
                                {lead.nace_codes && lead.nace_codes.length > 0 ? lead.nace_codes.slice(0, 2).join(', ') : 'NACE yok'}
                              </div>
                            </td>
                            <td>
                              <span style={{ fontWeight: 700, color: '#fff' }}>
                                {lead.plan ? lead.plan.name : 'Standart Paket'}
                              </span>
                            </td>
                            <td style={{ fontFamily: 'monospace', color: '#34d399', fontWeight: 700 }}>
                              {lead.odoo_order_name || 'Otomatik'}
                            </td>
                            <td>
                              {lead.status === 'APPROVED' ? (
                                <span style={{ background: 'rgba(16,185,129,0.2)', color: '#6ee7b7', border: '1px solid rgba(16,185,129,0.3)', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800 }}>
                                  ✓ Onaylandı & Aktif
                                </span>
                              ) : (
                                <span style={{ background: 'rgba(245,158,11,0.2)', color: '#fcd34d', border: '1px solid rgba(245,158,11,0.3)', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800 }}>
                                  ⏳ Onay Bekliyor
                                </span>
                              )}
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              {lead.status !== 'APPROVED' ? (
                                <button
                                  onClick={() => handleApproveLead(lead)}
                                  disabled={processingId === lead.id}
                                  className="super-admin-btn-corporate"
                                  style={{ padding: '6px 12px', fontSize: '0.725rem' }}
                                >
                                  {processingId === lead.id ? <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" /> : <CheckCircle2 style={{ width: 12, height: 12 }} />}
                                  <span>Onayla & Aktif Et</span>
                                </button>
                              ) : (
                                <span style={{ fontSize: '0.725rem', color: '#64748b' }}>Aktivasyon Tamamlandı</span>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: KAYITLI ŞİRKETLER (Maddeler 8, 9, 10, 11, 14) */}
          {activeTab === 'TENANTS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Building2 style={{ width: 20, height: 20, color: '#818cf8' }} />
                    <span>Kayıtlı Kurumlar ve Şirketler (Tenants)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    Kayıtlı kurumlar, paket süreleri, 3 ay bitim alarmları, yönetici hesapları ve sözleşme durumları.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  {/* Yeni Müşteri Ekle Butonu (Madde 9) */}
                  <button
                    onClick={handleOpenNewTenantModal}
                    className="super-admin-btn-corporate"
                    style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                  >
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>+ Yeni Müşteri Ekle</span>
                  </button>

                  {/* Durum Filtresi (Tümü / Onaylananlar / Onay Bekleyenler) */}
                  <div style={{ display: 'flex', background: 'rgba(255,255,255,0.06)', padding: 3, borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)' }}>
                    <button
                      onClick={() => setTenantStatusFilter('ALL')}
                      className="super-admin-btn-secondary"
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.75rem',
                        border: 'none',
                        background: tenantStatusFilter === 'ALL' ? '#7134e2' : 'transparent',
                        color: tenantStatusFilter === 'ALL' ? '#fff' : '#94a3b8'
                      }}
                      title="Tüm Şirketleri Listele"
                    >
                      <span>Tümü ({tenants.length})</span>
                    </button>
                    <button
                      onClick={() => setTenantStatusFilter('APPROVED')}
                      className="super-admin-btn-secondary"
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.75rem',
                        border: 'none',
                        background: tenantStatusFilter === 'APPROVED' ? 'rgba(16,185,129,0.3)' : 'transparent',
                        color: tenantStatusFilter === 'APPROVED' ? '#34d399' : '#94a3b8'
                      }}
                      title="Aktif Durumdaki Şirketleri Listele"
                    >
                      <CheckCircle2 style={{ width: 13, height: 13, color: '#34d399' }} />
                      <span>Aktif ({tenants.filter(t => t.is_active).length})</span>
                    </button>
                    <button
                      onClick={() => setTenantStatusFilter('PENDING')}
                      className="super-admin-btn-secondary"
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.75rem',
                        border: 'none',
                        background: tenantStatusFilter === 'PENDING' ? 'rgba(239,68,68,0.25)' : 'transparent',
                        color: tenantStatusFilter === 'PENDING' ? '#f87171' : '#94a3b8'
                      }}
                      title="Pasife Alınmış veya Onay Bekleyen Şirketleri Listele"
                    >
                      <PauseCircle style={{ width: 13, height: 13, color: '#f87171' }} />
                      <span>Pasif / Bekleyen ({tenants.filter(t => !t.is_active).length})</span>
                    </button>
                  </div>

                  {/* Kanban / Liste Format Butonları (Madde 8) */}
                  <div style={{ display: 'flex', background: 'rgba(255,255,255,0.06)', padding: 3, borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)' }}>
                    <button
                      onClick={() => setTenantViewMode('KANBAN')}
                      className="super-admin-btn-secondary"
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.75rem',
                        border: 'none',
                        background: tenantViewMode === 'KANBAN' ? '#7134e2' : 'transparent',
                        color: tenantViewMode === 'KANBAN' ? '#fff' : '#94a3b8'
                      }}
                      title="Kanban Kart Görünümü"
                    >
                      <LayoutGrid style={{ width: 14, height: 14 }} />
                      <span>Kanban</span>
                    </button>
                    <button
                      onClick={() => setTenantViewMode('LIST')}
                      className="super-admin-btn-secondary"
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.75rem',
                        border: 'none',
                        background: tenantViewMode === 'LIST' ? '#7134e2' : 'transparent',
                        color: tenantViewMode === 'LIST' ? '#fff' : '#94a3b8'
                      }}
                      title="Liste Tablo Görünümü"
                    >
                      <List style={{ width: 14, height: 14 }} />
                      <span>Liste</span>
                    </button>
                  </div>

                  {/* Arama */}
                  <div style={{ width: 240, position: 'relative' }}>
                    <Search style={{ width: 14, height: 14, position: 'absolute', left: 10, top: 11, color: '#64748b' }} />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Şirket adı veya VKN ara..."
                      className="super-admin-input"
                      style={{ paddingLeft: 32 }}
                    />
                  </div>
                </div>
              </div>

              {/* KANBAN FORMAT GÖRÜNÜMÜ (Madde 10) */}
              {tenantViewMode === 'KANBAN' && (
                <div className="super-admin-card-grid">
                  {filteredTenants.map((t) => (
                    <div 
                      key={t.id} 
                      className="super-admin-card"
                      style={t.is_warning_3_months ? {
                        borderColor: 'rgba(239,68,68,0.5)',
                        boxShadow: '0 0 16px rgba(239,68,68,0.2)'
                      } : {}}
                    >
                      <div>
                        {/* Üst Kısım: Logo & Onay Durum Rozeti (Madde 10) */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <div style={{ width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(135deg, rgba(113,52,226,0.4), rgba(20,108,235,0.4))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, color: '#fff', border: '1px solid rgba(255,255,255,0.1)' }}>
                            {t.name.slice(0, 2).toUpperCase()}
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            {/* Satın Alma Onay İkonu */}
                            {t.is_active ? (
                              <span style={{
                                padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800,
                                background: 'rgba(16,185,129,0.2)', color: '#6ee7b7', border: '1px solid rgba(16,185,129,0.3)',
                                display: 'flex', alignItems: 'center', gap: 4
                              }}>
                                <CheckCircle2 style={{ width: 12, height: 12 }} />
                                <span>AKTİF</span>
                              </span>
                            ) : (
                              <span style={{
                                padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800,
                                background: 'rgba(239,68,68,0.2)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.3)',
                                display: 'flex', alignItems: 'center', gap: 4
                              }}>
                                <PauseCircle style={{ width: 12, height: 12 }} />
                                <span>PASİF</span>
                              </span>
                            )}
                          </div>
                        </div>

                        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff', marginTop: 12 }}>{t.name}</h3>

                        {/* Açıklamalı Slug / Sistem Kimliği Etiketi (Madde 10 - Kullanıcı Sorusu Cevabı) */}
                        <div style={{ 
                          fontSize: '0.7rem', color: '#94a3b8', background: 'rgba(255,255,255,0.03)', 
                          padding: '4px 8px', borderRadius: 6, marginTop: 4, display: 'flex', alignItems: 'center', gap: 6 
                        }}>
                          <Tag style={{ width: 12, height: 12, color: '#38bdf8' }} />
                          <span><strong>🔑 Sistem Kimliği / URL:</strong> <code style={{ color: '#38bdf8' }}>{t.slug}</code></span>
                        </div>

                        {/* Paket & Bitiş Tarihi Bilgileri (Madde 10) */}
                        <div style={{ marginTop: 10, padding: '8px 10px', borderRadius: 8, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexDirection: 'column', gap: 5 }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                            <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: 5 }}>
                              <Package style={{ width: 13, height: 13, color: '#a78bfa' }} /> Paket:
                            </span>
                            <span style={{ color: '#fff', fontWeight: 700 }}>{t.plan_name || 'Standart Kiralama'}</span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                            <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: 5 }}>
                              <Calendar style={{ width: 13, height: 13, color: '#60a5fa' }} /> Kira Bitiş:
                            </span>
                            <span style={{ color: !t.is_active ? '#fbbf24' : (t.is_warning_3_months ? '#f87171' : '#cbd5e1'), fontWeight: 700 }}>
                              {!t.is_active ? 'Onay Bekliyor / Pasif' : (t.package_expiry_date ? new Date(t.package_expiry_date).toLocaleDateString('tr-TR') : '1 Yıl')}
                            </span>
                          </div>
                        </div>

                        {/* 3 Ay Bitiş Uyarısı Banner (Madde 10) */}
                        {t.is_active && t.is_warning_3_months && (
                          <div style={{
                            marginTop: 10, padding: '7px 10px', borderRadius: 8,
                            background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)',
                            display: 'flex', alignItems: 'center', gap: 6, color: '#fca5a5', fontSize: '0.72rem', fontWeight: 700
                          }}>
                            <AlertTriangle style={{ width: 14, height: 14, color: '#ef4444', flexShrink: 0 }} />
                            <span>⚠️ Paket Bitimine 3 Aydan Az Kaldı! (Kalan: {t.days_remaining} gün)</span>
                          </div>
                        )}

                        {/* Başvuru Onay Bekliyor / Pasif Banner */}
                        {!t.is_active && (
                          <div style={{
                            marginTop: 10, padding: '7px 10px', borderRadius: 8,
                            background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)',
                            display: 'flex', alignItems: 'center', gap: 6, color: '#fca5a5', fontSize: '0.72rem', fontWeight: 700
                          }}>
                            <PauseCircle style={{ width: 14, height: 14, color: '#f87171', flexShrink: 0 }} />
                            <span>⏸️ Şirket Kartı Pasif Durumda (Girişler Kapalı)</span>
                          </div>
                        )}

                        {/* İletişim Detayları */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 12, fontSize: '0.75rem', color: '#94a3b8' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Mail style={{ width: 13, height: 13, color: '#818cf8' }} />
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.contact_email || 'E-posta yok'}</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Phone style={{ width: 13, height: 13, color: '#34d399' }} />
                            <span>{t.phone || 'Telefon yok'}</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <CreditCard style={{ width: 13, height: 13, color: '#fbbf24' }} />
                            <span>VKN: {t.tax_id || '-'} {t.tax_office ? `(${t.tax_office} V.D.)` : ''}</span>
                          </div>
                        </div>
                      </div>

                      {/* Kart Altı Aksiyon Butonları (Madde 10 & 14 & Madde 4) */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        {!t.is_active && (
                          <button
                            onClick={() => handleQuickApproveTenant(t)}
                            disabled={processingId === 'approve-' + t.id}
                            className="super-admin-btn-corporate"
                            style={{ flex: 1, justifyContent: 'center', fontSize: '0.75rem', padding: '6px 10px', background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                            title="Şirketi ve 1 Yıllık Paketi Hemen Onayla"
                          >
                            {processingId === 'approve-' + t.id ? (
                              <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                            ) : (
                              <CheckCircle2 style={{ width: 13, height: 13 }} />
                            )}
                            <span>Hemen Onayla</span>
                          </button>
                        )}

                        {/* Müşteri Kartını Pasife Al / Aktife Al Butonu (Madde 4) */}
                        <button
                          onClick={() => handleToggleTenantStatus(t)}
                          disabled={processingId === 'toggle-status-' + t.id}
                          className="super-admin-btn-secondary"
                          style={{
                            padding: '6px 10px', fontSize: '0.75rem',
                            color: t.is_active ? '#f87171' : '#34d399',
                            borderColor: t.is_active ? 'rgba(239,68,68,0.35)' : 'rgba(16,185,129,0.35)',
                            background: t.is_active ? 'rgba(239,68,68,0.08)' : 'rgba(16,185,129,0.08)'
                          }}
                          title={t.is_active ? "Müşteri kartını pasife al (girişleri durdur)" : "Müşteri kartını aktife al (girişleri aç)"}
                        >
                          {processingId === 'toggle-status-' + t.id ? (
                            <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                          ) : t.is_active ? (
                            <>
                              <PauseCircle style={{ width: 13, height: 13 }} />
                              <span>Pasife Al</span>
                            </>
                          ) : (
                            <>
                              <PlayCircle style={{ width: 13, height: 13 }} />
                              <span>Aktife Al</span>
                            </>
                          )}
                        </button>

                        <button
                          onClick={() => handleOpenTenantDetails(t)}
                          className="super-admin-btn-corporate"
                          style={{ flex: t.is_active ? 1 : 'none', justifyContent: 'center', fontSize: '0.75rem', padding: '6px 10px' }}
                        >
                          <Edit style={{ width: 13, height: 13 }} />
                          <span>Detay & Yönetim</span>
                        </button>

                        {/* Manuel Hoş Geldin Mail Gönder (Madde 1) */}
                        <button
                          onClick={() => handleSendManualWelcome(t)}
                          disabled={processingId === 'welcome-' + t.id}
                          className="super-admin-btn-secondary"
                          style={{ padding: '6px 10px', fontSize: '0.75rem', color: '#38bdf8', borderColor: 'rgba(56,189,248,0.3)' }}
                          title="Hoş Geldiniz E-postası Gönder"
                        >
                          {processingId === 'welcome-' + t.id ? (
                            <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                          ) : (
                            <Mail style={{ width: 13, height: 13 }} />
                          )}
                          <span>Hoş Geldin Maili</span>
                        </button>

                        {/* Manuel Hatırlatıcı Mail Gönder (Madde 14) */}
                        {t.is_active && (
                          <button
                            onClick={() => handleSendManualReminder(t)}
                            disabled={processingId === 'reminder-' + t.id}
                            className="super-admin-btn-secondary"
                            style={{ padding: '6px 10px', fontSize: '0.75rem', color: '#f59e0b', borderColor: 'rgba(245,158,11,0.3)' }}
                            title="Paket Süre Dolum Hatırlatma E-postası Gönder"
                          >
                            {processingId === 'reminder-' + t.id ? (
                              <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                            ) : (
                              <Send style={{ width: 13, height: 13 }} />
                            )}
                            <span>Hatırlatıcı Mail</span>
                          </button>
                        )}

                        {onSwitchToWorkspace && (
                          <button
                            onClick={() => onSwitchToWorkspace(t)}
                            className="super-admin-btn-secondary"
                            title="Şirket Çalışma Alanına Geç"
                            style={{ padding: '6px 8px' }}
                          >
                            <ChevronRight style={{ width: 15, height: 15 }} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* LİSTE FORMAT GÖRÜNÜMÜ (Madde 11) */}
              {tenantViewMode === 'LIST' && (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th>Durum</th>
                        <th>Firma Adı & Kimlik</th>
                        <th>Vergi No / Dairesi</th>
                        <th>Telefon</th>
                        <th>Web Adres</th>
                        <th>Yönetici Adı</th>
                        <th>Email</th>
                        <th>Aldığı Paket</th>
                        <th>Kira Bitiş Tarihi</th>
                        <th>3 Ay Uyarısı</th>
                        <th style={{ textAlign: 'right' }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTenants.length === 0 ? (
                        <tr>
                          <td colSpan="11" style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                            Aramaya uygun şirket kaydı bulunamadı.
                          </td>
                        </tr>
                      ) : (
                        filteredTenants.map((t) => (
                          <tr key={t.id} style={t.is_warning_3_months ? { background: 'rgba(239,68,68,0.06)' } : {}}>
                            {/* 1. Onay & Aktiflik Durumu İkonu */}
                            <td>
                              {t.is_active ? (
                                <span style={{ background: 'rgba(16,185,129,0.2)', color: '#6ee7b7', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                  <CheckCircle2 style={{ width: 12, height: 12 }} /> Aktif
                                </span>
                              ) : (
                                <span style={{ background: 'rgba(239,68,68,0.2)', color: '#fca5a5', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                  <PauseCircle style={{ width: 12, height: 12 }} /> Pasif
                                </span>
                              )}
                            </td>

                            {/* 2. Firma Adı & Slug */}
                            <td>
                              <div style={{ fontWeight: 800, color: '#fff' }}>{t.name}</div>
                              <div style={{ fontSize: '0.68rem', color: '#38bdf8', fontFamily: 'monospace' }}>
                                URL: {t.slug}
                              </div>
                            </td>

                            {/* 3. Vergi No / Dairesi (Madde 12) */}
                            <td>
                              <div style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>{t.tax_id || '-'}</div>
                              <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>{t.tax_office ? `${t.tax_office} V.D.` : 'V.D. Yok'}</div>
                            </td>

                            {/* 4. Telefon */}
                            <td style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>{t.phone || '-'}</td>

                            {/* 5. Web Adres */}
                            <td style={{ fontSize: '0.75rem' }}>
                              {t.website ? (
                                <a href={t.website.startsWith('http') ? t.website : `https://${t.website}`} target="_blank" rel="noreferrer" style={{ color: '#60a5fa', display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none' }}>
                                  <span>{t.website.replace('https://', '').replace('http://', '')}</span>
                                  <ExternalLink style={{ width: 11, height: 11 }} />
                                </a>
                              ) : '-'}
                            </td>

                            {/* 6. Yönetici Adı */}
                            <td style={{ fontSize: '0.75rem', fontWeight: 600, color: '#e2e8f0' }}>{t.admin_name || '-'}</td>

                            {/* 7. Email */}
                            <td style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>{t.contact_email || '-'}</td>

                            {/* 8. Aldığı Paket */}
                            <td>
                              <span style={{ background: 'rgba(113,52,226,0.2)', color: '#c084fc', padding: '2px 7px', borderRadius: 6, fontSize: '0.72rem', fontWeight: 700 }}>
                                {t.plan_name || 'Standart'}
                              </span>
                            </td>

                            {/* 9. Kira Bitiş Tarihi */}
                            <td style={{ fontSize: '0.75rem', fontWeight: 700, color: !t.is_active ? '#fbbf24' : (t.is_warning_3_months ? '#f87171' : '#fff') }}>
                              {!t.is_active ? 'Onay Bekliyor / Pasif' : (t.package_expiry_date ? new Date(t.package_expiry_date).toLocaleDateString('tr-TR') : '1 Yıl')}
                            </td>

                            {/* 10. 3 Ay Uyarısı */}
                            <td>
                              {!t.is_active ? (
                                <span style={{ color: '#fca5a5', fontSize: '0.72rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                  <PauseCircle style={{ width: 12, height: 12 }} /> Pasif Durumda
                                </span>
                              ) : t.is_warning_3_months ? (
                                <span style={{ background: 'rgba(239,68,68,0.2)', color: '#fca5a5', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                  <AlertTriangle style={{ width: 12, height: 12 }} />
                                  <span>3 Ay Kaldı ({t.days_remaining}g)</span>
                                </span>
                              ) : (
                                <span style={{ color: '#64748b', fontSize: '0.72rem' }}>Normal ({t.days_remaining}g)</span>
                              )}
                            </td>

                            {/* 11. İşlemler */}
                            <td style={{ textAlign: 'right' }}>
                              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                                {!t.is_active && (
                                  <button
                                    onClick={() => handleQuickApproveTenant(t)}
                                    disabled={processingId === 'approve-' + t.id}
                                    style={{
                                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                      color: '#fff', border: 'none', borderRadius: 6,
                                      padding: '5px 8px', fontSize: '0.72rem', fontWeight: 700,
                                      cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 4
                                    }}
                                    title="Şirketi ve 1 Yıllık Paketi Hemen Onayla"
                                  >
                                    {processingId === 'approve-' + t.id ? (
                                      <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                                    ) : (
                                      <CheckCircle2 style={{ width: 12, height: 12 }} />
                                    )}
                                    <span>Onayla</span>
                                  </button>
                                )}

                                {/* Müşteri Kartını Pasife Al / Aktife Al Butonu (Madde 4) */}
                                <button
                                  onClick={() => handleToggleTenantStatus(t)}
                                  disabled={processingId === 'toggle-status-' + t.id}
                                  className="super-admin-btn-secondary"
                                  style={{
                                    padding: '5px 8px',
                                    fontSize: '0.72rem',
                                    color: t.is_active ? '#f87171' : '#34d399',
                                    borderColor: t.is_active ? 'rgba(239,68,68,0.35)' : 'rgba(16,185,129,0.35)',
                                    background: t.is_active ? 'rgba(239,68,68,0.08)' : 'rgba(16,185,129,0.08)'
                                  }}
                                  title={t.is_active ? "Müşteri kartını pasife al" : "Müşteri kartını aktife al"}
                                >
                                  {processingId === 'toggle-status-' + t.id ? (
                                    <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                                  ) : t.is_active ? (
                                    <>
                                      <PauseCircle style={{ width: 12, height: 12 }} />
                                      <span>Pasif</span>
                                    </>
                                  ) : (
                                    <>
                                      <PlayCircle style={{ width: 12, height: 12 }} />
                                      <span>Aktif</span>
                                    </>
                                  )}
                                </button>

                                <button
                                  onClick={() => handleOpenTenantDetails(t)}
                                  className="super-admin-btn-corporate"
                                  style={{ padding: '5px 10px', fontSize: '0.72rem' }}
                                  title="Firma Detay Ekranını Aç"
                                >
                                  <Edit style={{ width: 12, height: 12 }} />
                                  <span>Detay</span>
                                </button>

                                {/* Manuel Hoş Geldin Mail Gönder (Madde 1) */}
                                <button
                                  onClick={() => handleSendManualWelcome(t)}
                                  disabled={processingId === 'welcome-' + t.id}
                                  className="super-admin-btn-secondary"
                                  style={{ padding: '5px 8px', fontSize: '0.72rem', color: '#38bdf8' }}
                                  title="Hoş Geldiniz E-postası Gönder"
                                >
                                  {processingId === 'welcome-' + t.id ? (
                                    <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                                  ) : (
                                    <Mail style={{ width: 12, height: 12 }} />
                                  )}
                                </button>

                                {t.is_active && (
                                  <button
                                    onClick={() => handleSendManualReminder(t)}
                                    disabled={processingId === 'reminder-' + t.id}
                                    className="super-admin-btn-secondary"
                                    style={{ padding: '5px 8px', fontSize: '0.72rem', color: '#f59e0b' }}
                                    title="Paket Süre Dolum Hatırlatma E-postası Gönder"
                                  >
                                    {processingId === 'reminder-' + t.id ? (
                                      <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                                    ) : (
                                      <Send style={{ width: 12, height: 12 }} />
                                    )}
                                  </button>
                                )}

                                {onSwitchToWorkspace && (
                                  <button
                                    onClick={() => onSwitchToWorkspace(t)}
                                    className="super-admin-btn-secondary"
                                    style={{ padding: '5px 8px' }}
                                    title="Çalışma Alanına Geç"
                                  >
                                    <ChevronRight style={{ width: 13, height: 13 }} />
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: İZİN KATALOĞU (RBAC) (Madde 4) */}
          {activeTab === 'PERMISSIONS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <KeyRound style={{ width: 20, height: 20, color: '#fbbf24' }} />
                    <span>Sistem Yetki ve İzin Kataloğu (RBAC)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    Modül bazlı yetkiler. Detayları inceleyebilir, güncelleyebilir veya yeni yetki tanımlayabilirsiniz.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    onClick={() => handleOpenPermissionModal(null)}
                    className="super-admin-btn-corporate"
                  >
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>Yeni İzin Tanımla</span>
                  </button>

                  {renderViewModeToggle(permissionViewMode, setPermissionViewMode)}

                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="İzin kodu veya adı ara..."
                    className="super-admin-input"
                    style={{ width: 220 }}
                  />
                </div>
              </div>

              {/* Modül Filtreleri */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {['ALL', 'PLATFORM', 'RBAC', 'AGENTS', 'PROJECTS', 'CHAT', 'MEMORY', 'BILLING'].map((mod) => (
                  <button
                    key={mod}
                    onClick={() => setPermissionModuleFilter(mod)}
                    className="super-admin-btn-secondary"
                    style={permissionModuleFilter === mod ? { background: '#7134e2', color: '#fff', borderColor: '#7134e2' } : {}}
                  >
                    {mod === 'ALL' ? 'TÜM MODÜLLER' : mod}
                  </button>
                ))}
              </div>

              {permissionViewMode === 'KANBAN' ? (
                <div className="super-admin-card-grid">
                  {filteredPermissions.map((perm) => (
                    <div key={perm.id} className="super-admin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span style={{ background: 'rgba(20,108,235,0.2)', color: '#60a5fa', padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.68rem', fontWeight: 700 }}>
                            {perm.module}
                          </span>
                          <span style={{ fontFamily: 'monospace', fontWeight: 800, color: '#a78bfa', fontSize: '0.75rem' }}>
                            {perm.code}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#fff', margin: '6px 0 4px 0' }}>{perm.name}</h4>
                        <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '4px 0 10px 0', lineHeight: 1.4 }}>{perm.description || '-'}</p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
                          {(perm.default_for_roles || []).map((r, i) => (
                            <span key={i} style={{ background: 'rgba(255,255,255,0.06)', color: '#cbd5e1', padding: '2px 6px', borderRadius: 4, fontSize: '0.65rem' }}>
                              {r}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6, marginTop: 14, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        <button
                          onClick={() => handleOpenPermissionModal(perm)}
                          className="super-admin-btn-secondary"
                          style={{ padding: '5px 8px' }}
                          title="Düzenle"
                        >
                          <Edit style={{ width: 13, height: 13 }} />
                          <span style={{ fontSize: '0.72rem', marginLeft: 4 }}>Düzenle</span>
                        </button>
                        <button
                          onClick={() => handleDeletePermission(perm)}
                          className="super-admin-btn-secondary"
                          style={{ padding: '5px 8px', color: '#f87171' }}
                          title="Sil"
                        >
                          <Trash2 style={{ width: 13, height: 13 }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th>Yetki Kodu</th>
                        <th>Modül</th>
                        <th>İzin Adı & Açıklama</th>
                        <th>Varsayılan Roller</th>
                        <th style={{ textAlign: 'right' }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPermissions.map((perm) => (
                        <tr key={perm.id}>
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: '#a78bfa' }}>{perm.code}</td>
                          <td>
                            <span style={{ background: 'rgba(20,108,235,0.2)', color: '#60a5fa', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.68rem' }}>
                              {perm.module}
                            </span>
                          </td>
                          <td>
                            <div style={{ fontWeight: 700, color: '#fff' }}>{perm.name}</div>
                            <div style={{ fontSize: '0.725rem', color: '#94a3b8' }}>{perm.description || '-'}</div>
                          </td>
                          <td>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                              {perm.default_for_roles && perm.default_for_roles.map((r, i) => (
                                <span key={i} style={{ background: 'rgba(255,255,255,0.06)', padding: '2px 5px', borderRadius: 4, fontSize: '0.65rem' }}>
                                  {r}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              onClick={() => handleOpenPermissionModal(perm)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 8px', marginRight: 6 }}
                              title="Düzenle"
                            >
                              <Edit style={{ width: 13, height: 13 }} />
                            </button>
                            <button
                              onClick={() => handleDeletePermission(perm)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 8px', color: '#f87171' }}
                              title="Sil"
                            >
                              <Trash2 style={{ width: 13, height: 13 }} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: KİRALAMA PAKETLERİ (Madde 7) */}
          {activeTab === 'PLANS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Package style={{ width: 20, height: 20, color: '#34d399' }} />
                    <span>Kiralama Paketleri Yönetimi</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    Abonelik paketlerinin detayları, fiyatlandırma, kotalar ve model yetkileri.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button onClick={() => handleOpenPlanModal(null)} className="super-admin-btn-corporate">
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>Yeni Paket Tanımla</span>
                  </button>
                  {renderViewModeToggle(planViewMode, setPlanViewMode)}
                </div>
              </div>

              {planViewMode === 'KANBAN' ? (
                <div className="super-admin-card-grid">
                  {plans.map((p) => (
                    <div key={p.id} className="super-admin-card">
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontFamily: 'monospace', fontWeight: 800, fontSize: '0.75rem', background: 'rgba(113,52,226,0.2)', color: '#c084fc', padding: '2px 8px', borderRadius: 4 }}>
                            {p.code}
                          </span>
                          <span style={{ fontSize: '0.68rem', fontWeight: 800, color: p.is_active ? '#34d399' : '#f87171' }}>
                            {p.is_active ? 'AKTİF' : 'PASİF'}
                          </span>
                        </div>

                        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', marginTop: 10 }}>{p.name}</h3>
                        <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 4 }}>{p.description}</p>

                        <div style={{ marginTop: 16, marginBottom: 16 }}>
                          <span style={{ fontSize: '1.5rem', fontWeight: 900, color: '#fff' }}>
                            {Number(p.monthly_price).toLocaleString('tr-TR')}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginLeft: 4 }}>{p.currency} / ay</span>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.75rem', color: '#cbd5e1', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 12 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#94a3b8' }}>İnsan Kullanıcı:</span>
                            <b>{p.max_humans}</b>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#94a3b8' }}>AI Ajan Personel:</span>
                            <b>{p.max_agents}</b>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#94a3b8' }}>Aylık Kredi:</span>
                            <b>{p.monthly_credits}</b>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#94a3b8' }}>Özel AI Ünvan Tanımlama:</span>
                            <b style={{ color: p.can_create_custom_titles ? '#34d399' : '#64748b' }}>
                              {p.can_create_custom_titles ? 'Evet' : 'Hayır'}
                            </b>
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 18, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        <button
                          onClick={() => handleOpenPlanModal(p)}
                          className="super-admin-btn-secondary"
                          style={{ flex: 1, justifyContent: 'center' }}
                        >
                          <Edit style={{ width: 13, height: 13 }} />
                          <span>Düzenle</span>
                        </button>
                        <button
                          onClick={() => handleDeletePlan(p)}
                          className="super-admin-btn-secondary"
                          style={{ color: '#f87171' }}
                          title="Sil"
                        >
                          <Trash2 style={{ width: 13, height: 13 }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th>Paket Kodu & Adı</th>
                        <th>Aylık Fiyat</th>
                        <th>Limitler (İnsan / Ajan / Kredi)</th>
                        <th>Depolama</th>
                        <th>Özel Ünvan</th>
                        <th>Durum</th>
                        <th style={{ textAlign: 'right' }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {plans.map((p) => (
                        <tr key={p.id}>
                          <td>
                            <div style={{ fontWeight: 800, color: '#fff' }}>{p.name}</div>
                            <div style={{ fontFamily: 'monospace', fontSize: '0.725rem', color: '#a78bfa' }}>{p.code}</div>
                          </td>
                          <td>
                            <span style={{ fontWeight: 800, color: '#38bdf8' }}>{Number(p.monthly_price).toLocaleString('tr-TR')} {p.currency}</span>
                            <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}> / ay</span>
                          </td>
                          <td>
                            <span style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                              {p.max_humans} İnsan | {p.max_agents} Ajan | {p.monthly_credits} Kredi
                            </span>
                          </td>
                          <td>
                            <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#cbd5e1' }}>{p.storage_gb} GB</span>
                          </td>
                          <td>
                            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: p.can_create_custom_titles ? '#34d399' : '#64748b' }}>
                              {p.can_create_custom_titles ? '✓ İzinli' : '✗ Kapalı'}
                            </span>
                          </td>
                          <td>
                            <span style={{
                              fontSize: '0.68rem', fontWeight: 800, padding: '2px 8px', borderRadius: 999,
                              background: p.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                              color: p.is_active ? '#34d399' : '#f87171'
                            }}>
                              {p.is_active ? 'AKTİF' : 'PASİF'}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              onClick={() => handleOpenPlanModal(p)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 8px', marginRight: 6 }}
                              title="Düzenle"
                            >
                              <Edit style={{ width: 13, height: 13 }} />
                            </button>
                            <button
                              onClick={() => handleDeletePlan(p)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 8px', color: '#f87171' }}
                              title="Sil"
                            >
                              <Trash2 style={{ width: 13, height: 13 }} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: GENEL AI & MANİFESTO MODELİ SEÇİMİ (Madde 6) */}
          {activeTab === 'AI_MODEL_SETTINGS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div style={{
                background: 'linear-gradient(135deg, rgba(113,52,226,0.18) 0%, rgba(49,76,205,0.15) 50%, rgba(20,108,235,0.18) 100%)',
                border: '1px solid rgba(113,52,226,0.4)',
                borderRadius: 16,
                padding: '24px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 16
              }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 14,
                  background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', flexShrink: 0, boxShadow: '0 0 16px rgba(113,52,226,0.5)'
                }}>
                  <Sparkles style={{ width: 24, height: 24 }} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff' }}>
                    Çekirdek Genel AI Modeli (Manifesto & Ajan Rol Mimarı)
                  </h2>
                  <p style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: 4, lineHeight: 1.5, maxWidth: 750 }}>
                    Seçilen NACE kodları bazında müşterilerin <strong>şirket manifestosunu yazan</strong> ve 
                    AI Ajan personel unvanlarının <strong>sistem rollerini/promptlarını oluşturan</strong> en güçlü EVREN modelini buradan seçebilirsiniz.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, fontSize: '0.8rem' }}>
                    <span style={{ color: '#94a3b8' }}>Aktif Seçili Model:</span>
                    <span style={{ background: '#7134e2', color: '#fff', padding: '3px 10px', borderRadius: 6, fontFamily: 'monospace', fontWeight: 800 }}>
                      {systemSettings.default_manifesto_model}
                    </span>
                  </div>
                </div>
              </div>

              <div className="super-admin-card-grid">
                {models.map((m) => {
                  const isSelected = systemSettings.default_manifesto_model === m.model_code;
                  return (
                    <div
                      key={m.id}
                      onClick={() => handleSelectDefaultManifestoModel(m.model_code)}
                      className="super-admin-card"
                      style={isSelected ? {
                        borderColor: '#7134e2',
                        boxShadow: '0 0 24px rgba(113,52,226,0.4)',
                        background: '#12182c'
                      } : { cursor: 'pointer' }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontFamily: 'monospace', fontSize: '0.725rem', color: '#94a3b8' }}>
                            {m.model_code}
                          </span>
                          {isSelected && (
                            <span style={{ background: '#7134e2', color: '#fff', fontSize: '0.65rem', fontWeight: 800, padding: '2px 8px', borderRadius: 999 }}>
                              ✓ SEÇİLİ MODEL
                            </span>
                          )}
                        </div>

                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', marginTop: 8 }}>{m.display_name}</h3>

                        <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                          <span style={{ background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: 4, fontSize: '0.68rem', fontFamily: 'monospace' }}>
                            {m.model_type}
                          </span>
                          <span style={{ background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: 4, fontSize: '0.68rem', fontFamily: 'monospace' }}>
                            {m.context_window.toLocaleString()} token
                          </span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 20, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Efor: {m.effort_coefficient}x</span>
                        <button
                          disabled={isSelected}
                          className={isSelected ? "super-admin-btn-secondary" : "super-admin-btn-corporate"}
                          style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                        >
                          {isSelected ? 'Aktif Model' : 'Bunu Model Yap'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 6: EVREN MODELLERİ (Madde 8) */}
          {activeTab === 'MODELS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Cpu style={{ width: 20, height: 20, color: '#a78bfa' }} />
                    <span>EVREN Modelleri Kataloğu</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    TÜBİTAK BİLGEM EVREN modelleri ve sisteme yeni eklenebilecek modellerin yönetimi.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button onClick={() => handleOpenModelModal(null)} className="super-admin-btn-corporate">
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>Yeni Model Ekle</span>
                  </button>
                  {renderViewModeToggle(modelViewMode, setModelViewMode)}
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Model ara..."
                    className="super-admin-input"
                    style={{ width: 200 }}
                  />
                </div>
              </div>

              {modelViewMode === 'KANBAN' ? (
                <div className="super-admin-card-grid">
                  {filteredModels.map((m) => (
                    <div key={m.id} className="super-admin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span style={{ background: 'rgba(255,255,255,0.06)', padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.68rem', color: '#cbd5e1' }}>
                            {m.model_type}
                          </span>
                          <span style={{
                            padding: '2px 6px', borderRadius: 4, fontSize: '0.68rem', fontWeight: 800,
                            background: m.status === 'ACTIVE' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                            color: m.status === 'ACTIVE' ? '#6ee7b7' : '#fca5a5'
                          }}>
                            {m.status}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '1rem', fontWeight: 800, color: '#38bdf8', margin: '4px 0 2px 0' }}>{m.display_name}</h4>
                        <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#94a3b8', marginBottom: 12 }}>{m.model_code}</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.75rem', color: '#cbd5e1', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 10 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#94a3b8' }}>Bağlam Penceresi:</span>
                            <b style={{ fontFamily: 'monospace' }}>{m.context_window?.toLocaleString()} token</b>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#94a3b8' }}>Efor Katsayısı:</span>
                            <b style={{ fontFamily: 'monospace' }}>{m.effort_coefficient}x</b>
                          </div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6, marginTop: 14, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        <button
                          onClick={() => handleOpenModelModal(m)}
                          className="super-admin-btn-secondary"
                          style={{ padding: '5px 8px' }}
                          title="Düzenle"
                        >
                          <Edit style={{ width: 13, height: 13 }} />
                          <span style={{ fontSize: '0.72rem', marginLeft: 4 }}>Düzenle</span>
                        </button>
                        <button
                          onClick={() => handleDeleteModel(m)}
                          className="super-admin-btn-secondary"
                          style={{ padding: '5px 8px', color: '#f87171' }}
                          title="Sil"
                        >
                          <Trash2 style={{ width: 13, height: 13 }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th>Model Kodu</th>
                        <th>Görünen İsim</th>
                        <th>Tür</th>
                        <th>Bağlam (Token)</th>
                        <th>Efor Katsayısı</th>
                        <th>Durum</th>
                        <th style={{ textAlign: 'right' }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredModels.map((m) => (
                        <tr key={m.id}>
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: '#fff' }}>{m.model_code}</td>
                          <td style={{ fontWeight: 700, color: '#38bdf8' }}>{m.display_name}</td>
                          <td>
                            <span style={{ background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.68rem' }}>
                              {m.model_type}
                            </span>
                          </td>
                          <td style={{ fontFamily: 'monospace' }}>{m.context_window.toLocaleString()} token</td>
                          <td style={{ fontFamily: 'monospace' }}>{m.effort_coefficient}x</td>
                          <td>
                            <span style={{
                              padding: '2px 6px', borderRadius: 4, fontSize: '0.68rem', fontWeight: 800,
                              background: m.status === 'ACTIVE' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                              color: m.status === 'ACTIVE' ? '#6ee7b7' : '#fca5a5'
                            }}>
                              {m.status}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              onClick={() => handleOpenModelModal(m)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 8px', marginRight: 6 }}
                            >
                              <Edit style={{ width: 13, height: 13 }} />
                            </button>
                            <button
                              onClick={() => handleDeleteModel(m)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 8px', color: '#f87171' }}
                            >
                              <Trash2 style={{ width: 13, height: 13 }} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 7: NACE KODLARI KATALOĞU (Madde 12) */}
          {activeTab === 'NACE' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Tag style={{ width: 20, height: 20, color: '#38bdf8' }} />
                    <span>NACE Faaliyet Kodları Kataloğu (Rev.2)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    Sistemde kayıtlı 2,160+ NACE kodunun listesi, filtrelemesi, ekleme ve düzenleme ekranı.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button onClick={() => handleOpenNaceModal(null)} className="super-admin-btn-corporate">
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>Yeni NACE Ekle</span>
                  </button>
                  {renderViewModeToggle(naceViewMode, setNaceViewMode)}
                  <input
                    type="text"
                    value={naceSearch}
                    onChange={(e) => setNaceSearch(e.target.value)}
                    placeholder="Kod veya faaliyet ara (örn: 62.01, yazılım)..."
                    className="super-admin-input"
                    style={{ width: 280 }}
                  />
                </div>
              </div>

              {naceViewMode === 'KANBAN' ? (
                <div className="super-admin-card-grid">
                  {naceList.map((item) => (
                    <div key={item.code} className="super-admin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                          <span style={{ fontFamily: 'monospace', fontWeight: 800, color: '#38bdf8', background: 'rgba(56,189,248,0.15)', padding: '2px 8px', borderRadius: 6, fontSize: '0.75rem' }}>
                            {item.code}
                          </span>
                          <span style={{ fontSize: '0.68rem', color: '#94a3b8', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: 4 }}>
                            {item.sector_group || 'Genel'}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', margin: '6px 0 4px 0' }}>{item.title}</h4>
                        <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '4px 0 8px 0', lineHeight: 1.4 }}>{item.description || '-'}</p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6, marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        <button
                          onClick={() => handleOpenNaceModal(item)}
                          className="super-admin-btn-secondary"
                          style={{ padding: '5px 8px' }}
                          title="Düzenle"
                        >
                          <Edit style={{ width: 12, height: 12 }} />
                          <span style={{ fontSize: '0.72rem', marginLeft: 4 }}>Düzenle</span>
                        </button>
                        <button
                          onClick={() => handleDeleteNace(item)}
                          className="super-admin-btn-secondary"
                          style={{ padding: '5px 8px', color: '#f87171' }}
                          title="Sil"
                        >
                          <Trash2 style={{ width: 12, height: 12 }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th style={{ width: 110 }}>NACE Kodu</th>
                        <th style={{ width: 180 }}>Sektör Grubu</th>
                        <th>Faaliyet Alanı / Ünvan</th>
                        <th>Açıklama</th>
                        <th style={{ textAlign: 'right', width: 90 }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {naceList.map((item) => (
                        <tr key={item.code}>
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: '#38bdf8' }}>{item.code}</td>
                          <td style={{ fontWeight: 600, color: '#fff' }}>{item.sector_group}</td>
                          <td style={{ fontWeight: 700, color: '#cbd5e1' }}>{item.title}</td>
                          <td style={{ fontSize: '0.725rem', color: '#94a3b8' }}>{item.description || '-'}</td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              onClick={() => handleOpenNaceModal(item)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', marginRight: 4 }}
                            >
                              <Edit style={{ width: 12, height: 12 }} />
                            </button>
                            <button
                              onClick={() => handleDeleteNace(item)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', color: '#f87171' }}
                            >
                              <Trash2 style={{ width: 12, height: 12 }} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 8: SEKTOREL ÜNVANLAR & PROMPT (Madde 13) */}
          {activeTab === 'TITLES' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Briefcase style={{ width: 20, height: 20, color: '#ec4899' }} />
                    <span>Sektörel Personel Ünvanları ve Rol Promptları</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    AI personellerinin ünvan tanımları, yetenek profilleri ve AI tarafından yeniden üretilebilen rol promptları.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button onClick={() => handleOpenTitleModal(null)} className="super-admin-btn-corporate">
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>Yeni Ünvan Tanımla</span>
                  </button>
                  {renderViewModeToggle(titleViewMode, setTitleViewMode)}
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Ünvan ara..."
                    className="super-admin-input"
                    style={{ width: 200 }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {['ALL', 'YAZILIM', 'ANALIZ', 'FINANS', 'YONETIM', 'HUKUK', 'PAZARLAMA', 'OPERASYON'].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setJobTitleCategoryFilter(cat)}
                    className="super-admin-btn-secondary"
                    style={jobTitleCategoryFilter === cat ? { background: '#ec4899', color: '#fff', borderColor: '#ec4899' } : {}}
                  >
                    {cat === 'ALL' ? 'TÜM KATEGORİLER' : cat}
                  </button>
                ))}
              </div>

              {titleViewMode === 'KANBAN' ? (
                <div className="super-admin-card-grid">
                  {filteredJobTitles.map((jt) => (
                    <div key={jt.id} className="super-admin-card">
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '2px 6px', borderRadius: 4, background: 'rgba(236,72,153,0.2)', color: '#f472b6' }}>
                            {jt.category}
                          </span>
                          <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', color: '#64748b' }}>{jt.code}</span>
                        </div>

                        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff', marginTop: 8 }}>{jt.title}</h3>
                        <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 2 }}>{jt.description || '-'}</p>

                        <div style={{ marginTop: 12, padding: '10px', borderRadius: 8, background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.06)' }}>
                          <div style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', color: '#a78bfa', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Sparkles style={{ width: 12, height: 12 }} />
                            <span>Sistem Rol Promptu:</span>
                          </div>
                          <div style={{ fontSize: '0.725rem', color: '#cbd5e1', fontFamily: 'monospace', maxHeight: 60, overflow: 'hidden' }}>
                            {jt.base_role_prompt}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        <button
                          onClick={() => handleOpenTitleModal(jt)}
                          className="super-admin-btn-corporate"
                          style={{ flex: 1, justifyContent: 'center' }}
                        >
                          <Edit style={{ width: 13, height: 13 }} />
                          <span>Detay & Prompt</span>
                        </button>
                        <button
                          onClick={() => handleDeleteTitle(jt)}
                          className="super-admin-btn-secondary"
                          style={{ color: '#f87171' }}
                          title="Sil"
                        >
                          <Trash2 style={{ width: 13, height: 13 }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th style={{ width: 90 }}>Kod</th>
                        <th style={{ width: 120 }}>Kategori</th>
                        <th style={{ width: 200 }}>Ünvan</th>
                        <th>Açıklama & Sistem Rol Prompt Özeti</th>
                        <th style={{ textAlign: 'right', width: 90 }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredJobTitles.map((jt) => (
                        <tr key={jt.id}>
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: '#ec4899' }}>{jt.code}</td>
                          <td>
                            <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '2px 6px', borderRadius: 4, background: 'rgba(236,72,153,0.2)', color: '#f472b6' }}>
                              {jt.category}
                            </span>
                          </td>
                          <td style={{ fontWeight: 700, color: '#fff' }}>{jt.title}</td>
                          <td>
                            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{jt.description || '-'}</div>
                            <div style={{ fontSize: '0.7rem', color: '#a78bfa', fontFamily: 'monospace', marginTop: 2, maxHeight: 38, overflow: 'hidden' }}>
                              {jt.base_role_prompt}
                            </div>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              onClick={() => handleOpenTitleModal(jt)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', marginRight: 4 }}
                              title="Düzenle"
                            >
                              <Edit style={{ width: 12, height: 12 }} />
                            </button>
                            <button
                              onClick={() => handleDeleteTitle(jt)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', color: '#f87171' }}
                              title="Sil"
                            >
                              <Trash2 style={{ width: 12, height: 12 }} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 8: E-POSTA ŞABLONLARI YÖNETİMİ & HTML EDİTÖRÜ (Madde 1) */}
          {activeTab === 'EMAIL_TEMPLATES' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Mail style={{ width: 20, height: 20, color: '#38bdf8' }} />
                    <span>HTML E-Posta Şablonları & Canlı Editör</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    RECDx kurumsal logosunu içeren Hoş Geldiniz, 3 Ay Bitiş Hatırlatıcı ve özel e-posta şablonları.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    onClick={() => handleOpenTemplateModal(null)}
                    className="super-admin-btn-corporate"
                    style={{ background: 'linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%)' }}
                  >
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>+ Yeni Şablon Oluştur</span>
                  </button>

                  {renderViewModeToggle(templateViewMode, setTemplateViewMode)}

                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Şablon kodu veya konu ara..."
                    className="super-admin-input"
                    style={{ width: 220 }}
                  />
                </div>
              </div>

              {templateViewMode === 'KANBAN' ? (
                /* Şablon Kartları Grid */
                <div className="super-admin-card-grid">
                  {filteredEmailTemplates.map((tmpl) => (
                    <div key={tmpl.id} className="super-admin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: 'rgba(56,189,248,0.2)', color: '#38bdf8' }}>
                            {tmpl.code}
                          </span>
                          <span style={{
                            padding: '2px 7px', borderRadius: 999, fontSize: '0.65rem', fontWeight: 800,
                            background: tmpl.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                            color: tmpl.is_active ? '#6ee7b7' : '#fca5a5'
                          }}>
                            {tmpl.is_active ? 'AKTİF' : 'PASİF'}
                          </span>
                        </div>

                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', marginTop: 10 }}>{tmpl.name}</h3>
                        <div style={{ fontSize: '0.785rem', color: '#cbd5e1', marginTop: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                          <strong style={{ color: '#94a3b8' }}>Konu:</strong> {tmpl.subject}
                        </div>

                        {/* Değişken Rozetleri */}
                        <div style={{ marginTop: 12 }}>
                          <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginBottom: 4, fontWeight: 700 }}>DİNAMİK DEĞİŞKENLER:</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            {(tmpl.variables || []).map((v, i) => (
                              <span key={i} style={{ fontSize: '0.65rem', fontFamily: 'monospace', padding: '2px 6px', borderRadius: 4, background: 'rgba(255,255,255,0.06)', color: '#a78bfa' }}>
                                {`{{${v}}}`}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* HTML Önizleme Kutusu */}
                        <div style={{ marginTop: 14, borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)', height: 110, background: '#0b0f19', position: 'relative' }}>
                          <iframe
                            title={tmpl.name}
                            srcDoc={tmpl.html_content}
                            style={{ width: '100%', height: '100%', border: 'none', pointerEvents: 'none', transform: 'scale(0.7)', transformOrigin: 'top left', width: '142%', height: '142%' }}
                          />
                        </div>
                      </div>

                      {/* Aksiyon Butonları */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        <button
                          onClick={() => handleOpenTemplateModal(tmpl)}
                          className="super-admin-btn-corporate"
                          style={{ flex: 1, justifyContent: 'center', fontSize: '0.75rem', padding: '6px 10px' }}
                        >
                          <Edit style={{ width: 13, height: 13 }} />
                          <span>Düzenle & Önizle</span>
                        </button>

                        <button
                          onClick={() => handleTestSendTemplate(tmpl)}
                          disabled={processingId === 'test-mail-' + tmpl.id}
                          className="super-admin-btn-secondary"
                          style={{ padding: '6px 10px', fontSize: '0.75rem', color: '#38bdf8' }}
                          title="Test E-postası Gönder"
                        >
                          {processingId === 'test-mail-' + tmpl.id ? (
                            <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                          ) : (
                            <Send style={{ width: 13, height: 13 }} />
                          )}
                          <span>Test</span>
                        </button>

                        <button
                          onClick={() => handleDeleteTemplate(tmpl)}
                          className="super-admin-btn-secondary"
                          style={{ color: '#f87171', padding: '6px 8px' }}
                          title="Sil"
                        >
                          <Trash2 style={{ width: 13, height: 13 }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                /* Şablon Tablo Listesi */
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th style={{ width: 160 }}>Şablon Kodu</th>
                        <th style={{ width: 220 }}>Şablon Adı</th>
                        <th>E-Posta Konusu (Subject)</th>
                        <th>Dinamik Değişkenler</th>
                        <th style={{ width: 90 }}>Durum</th>
                        <th style={{ textAlign: 'right', width: 150 }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredEmailTemplates.map((tmpl) => (
                        <tr key={tmpl.id}>
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: '#38bdf8' }}>{tmpl.code}</td>
                          <td style={{ fontWeight: 700, color: '#fff' }}>{tmpl.name}</td>
                          <td style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>{tmpl.subject}</td>
                          <td>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                              {(tmpl.variables || []).slice(0, 4).map((v, i) => (
                                <span key={i} style={{ fontSize: '0.62rem', fontFamily: 'monospace', padding: '1px 5px', borderRadius: 3, background: 'rgba(255,255,255,0.06)', color: '#a78bfa' }}>
                                  {`{{${v}}}`}
                                </span>
                              ))}
                              {(tmpl.variables || []).length > 4 && (
                                <span style={{ fontSize: '0.62rem', color: '#64748b' }}>+{tmpl.variables.length - 4}</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <span style={{
                              padding: '2px 7px', borderRadius: 999, fontSize: '0.65rem', fontWeight: 800,
                              background: tmpl.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                              color: tmpl.is_active ? '#6ee7b7' : '#fca5a5'
                            }}>
                              {tmpl.is_active ? 'AKTİF' : 'PASİF'}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              onClick={() => handleOpenTemplateModal(tmpl)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', marginRight: 4 }}
                              title="Düzenle & Önizle"
                            >
                              <Edit style={{ width: 12, height: 12 }} />
                            </button>
                            <button
                              onClick={() => handleTestSendTemplate(tmpl)}
                              disabled={processingId === 'test-mail-' + tmpl.id}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', marginRight: 4, color: '#38bdf8' }}
                              title="Test E-postası Gönder"
                            >
                              {processingId === 'test-mail-' + tmpl.id ? <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" /> : <Send style={{ width: 12, height: 12 }} />}
                            </button>
                            <button
                              onClick={() => handleDeleteTemplate(tmpl)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', color: '#f87171' }}
                              title="Sil"
                            >
                              <Trash2 style={{ width: 12, height: 12 }} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 9: SCHEDULE (ZAMANLAYICI) YÖNETİMİ (Madde 2) */}
          {activeTab === 'SCHEDULES' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Clock style={{ width: 20, height: 20, color: '#fbbf24' }} />
                    <span>Otomatik Bildirim Zamanlayıcıları (Notification Schedules)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: '#94a3b8', marginTop: 2 }}>
                    Kayıt sonrası tek seferlik gönderim ve paket bitişine 3 ay kala 15 günde bir periyodik hatırlatma kuralları.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    onClick={() => handleOpenScheduleModal(null)}
                    className="super-admin-btn-corporate"
                    style={{ background: 'linear-gradient(135deg, #fbbf24 0%, #d97706 100%)', color: '#000', fontWeight: 800 }}
                  >
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>+ Yeni Zamanlama Kuralı</span>
                  </button>

                  {renderViewModeToggle(scheduleViewMode, setScheduleViewMode)}
                </div>
              </div>

              {scheduleViewMode === 'KANBAN' ? (
                /* Zamanlayıcı Kuralları Kartları */
                <div className="super-admin-card-grid">
                  {filteredSchedules.map((sch) => (
                    <div key={sch.id} className="super-admin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: 'rgba(251,191,36,0.2)', color: '#fbbf24' }}>
                            {sch.trigger_type}
                          </span>
                          <span style={{
                            padding: '2px 7px', borderRadius: 999, fontSize: '0.65rem', fontWeight: 800,
                            background: sch.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                            color: sch.is_active ? '#6ee7b7' : '#fca5a5'
                          }}>
                            {sch.is_active ? 'AKTİF' : 'PASİF'}
                          </span>
                        </div>

                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', marginTop: 10 }}>{sch.name}</h3>

                        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.785rem', color: '#cbd5e1' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 6, background: 'rgba(255,255,255,0.03)' }}>
                            <span style={{ color: '#94a3b8' }}>Bağlı Şablon:</span>
                            <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 700 }}>{sch.template_code}</span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 6, background: 'rgba(255,255,255,0.03)' }}>
                            <span style={{ color: '#94a3b8' }}>Çalışma Mantığı:</span>
                            <span style={{ color: '#fff', fontWeight: 700 }}>
                              {sch.trigger_type === 'ON_REGISTRATION'
                                ? 'Kayıt anında tek sefer gönder'
                                : `${sch.target_lead_days || 90} gün kala, her ${sch.frequency_days || 15} günde bir`}
                            </span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 6, background: 'rgba(255,255,255,0.03)' }}>
                            <span style={{ color: '#94a3b8' }}>Son Gönderim:</span>
                            <span style={{ color: '#a78bfa' }}>
                              {sch.last_run_at ? new Date(sch.last_run_at).toLocaleString('tr-TR') : 'Henüz tetiklenmedi'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Aksiyon Butonları */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        <button
                          onClick={() => handleTriggerSchedule(sch)}
                          disabled={processingId === 'sched-' + sch.id}
                          className="super-admin-btn-corporate"
                          style={{ flex: 1, justifyContent: 'center', fontSize: '0.75rem', padding: '6px 10px', background: 'linear-gradient(135deg, #fbbf24 0%, #d97706 100%)', color: '#000', fontWeight: 800 }}
                          title="Zamanlayıcıyı şimdi tara ve gönderilecek mailleri gönder"
                        >
                          {processingId === 'sched-' + sch.id ? (
                            <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                          ) : (
                            <Zap style={{ width: 13, height: 13 }} />
                          )}
                          <span>Şimdi Tetikle</span>
                        </button>

                        <button
                          onClick={() => handleOpenScheduleModal(sch)}
                          className="super-admin-btn-secondary"
                          style={{ padding: '6px 10px', fontSize: '0.75rem' }}
                          title="Zamanlama Kuralını Düzenle"
                        >
                          <Edit style={{ width: 13, height: 13 }} />
                        </button>

                        <button
                          onClick={() => handleDeleteSchedule(sch)}
                          className="super-admin-btn-secondary"
                          style={{ color: '#f87171', padding: '6px 8px' }}
                          title="Sil"
                        >
                          <Trash2 style={{ width: 13, height: 13 }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                /* Zamanlayıcılar Tablo Listesi */
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th style={{ width: 160 }}>Tetikleyici Türü</th>
                        <th style={{ width: 220 }}>Kural Adı</th>
                        <th style={{ width: 180 }}>Bağlı Şablon</th>
                        <th>Çalışma Mantığı & Periyot</th>
                        <th style={{ width: 160 }}>Son Tetikleme</th>
                        <th style={{ width: 85 }}>Durum</th>
                        <th style={{ textAlign: 'right', width: 130 }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSchedules.map((sch) => (
                        <tr key={sch.id}>
                          <td>
                            <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: 'rgba(251,191,36,0.2)', color: '#fbbf24' }}>
                              {sch.trigger_type}
                            </span>
                          </td>
                          <td style={{ fontWeight: 700, color: '#fff' }}>{sch.name}</td>
                          <td style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 700 }}>{sch.template_code}</td>
                          <td style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                            {sch.trigger_type === 'ON_REGISTRATION'
                              ? 'Kayıt anında tek sefer gönderim'
                              : `${sch.target_lead_days || 90} gün kala, her ${sch.frequency_days || 15} günde bir`}
                          </td>
                          <td style={{ fontSize: '0.75rem', color: '#a78bfa' }}>
                            {sch.last_run_at ? new Date(sch.last_run_at).toLocaleString('tr-TR') : 'Henüz çalışmadı'}
                          </td>
                          <td>
                            <span style={{
                              padding: '2px 7px', borderRadius: 999, fontSize: '0.65rem', fontWeight: 800,
                              background: sch.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                              color: sch.is_active ? '#6ee7b7' : '#fca5a5'
                            }}>
                              {sch.is_active ? 'AKTİF' : 'PASİF'}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              onClick={() => handleTriggerSchedule(sch)}
                              disabled={processingId === 'sched-' + sch.id}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', marginRight: 4, color: '#fbbf24' }}
                              title="Şimdi Tetikle"
                            >
                              {processingId === 'sched-' + sch.id ? <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" /> : <Zap style={{ width: 12, height: 12 }} />}
                            </button>
                            <button
                              onClick={() => handleOpenScheduleModal(sch)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', marginRight: 4 }}
                              title="Düzenle"
                            >
                              <Edit style={{ width: 12, height: 12 }} />
                            </button>
                            <button
                              onClick={() => handleDeleteSchedule(sch)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', color: '#f87171' }}
                              title="Sil"
                            >
                              <Trash2 style={{ width: 12, height: 12 }} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

        </div>
      </main>

      {/* ======================================================== */}
      {/* 1. PROFİL MODALI (Madde 1 & 2)                            */}
      {/* ======================================================== */}
      {profileModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <User style={{ width: 18, height: 18 }} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff' }}>Süper Admin Profil Bilgileri</h3>
                  <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Ad, telefon, e-posta, adres ve şifre güncelleyin.</p>
                </div>
              </div>
              <button onClick={() => setProfileModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Ad Soyad</label>
                <input
                  type="text"
                  required
                  value={profileForm.display_name}
                  onChange={(e) => setProfileForm({ ...profileForm, display_name: e.target.value })}
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Telefon</label>
                  <input
                    type="text"
                    value={profileForm.phone}
                    onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                    placeholder="+90 5XX XXX XX XX"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>E-posta</label>
                  <input
                    type="email"
                    required
                    value={profileForm.email}
                    onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                    className="super-admin-input"
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Adres</label>
                <textarea
                  rows="3"
                  value={profileForm.address}
                  onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
                  placeholder="Maslak Teknopark, Sarıyer / İstanbul"
                  className="super-admin-input"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Yeni Şifre (İsteğe Bağlı)</label>
                <input
                  type="password"
                  value={profileForm.new_password}
                  onChange={(e) => setProfileForm({ ...profileForm, new_password: e.target.value })}
                  placeholder="Değiştirmek istemiyorsanız boş bırakın"
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <button type="button" onClick={() => setProfileModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>
                <button type="submit" disabled={processingId === 'profile'} className="super-admin-btn-corporate">
                  {processingId === 'profile' ? <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" /> : <Check style={{ width: 14, height: 14 }} />}
                  <span>Bilgilerimi Güncelle</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 2. ŞİRKET DETAY MODALI (Madde 5)                          */}
      {/* ======================================================== */}
      {tenantDetailModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box" style={{ maxWidth: 720 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff' }}>{tenantEditForm.name || 'Şirket Detayları'}</h3>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Şirket bilgileri, onaylama ve Şirket Admin kullanıcısı.</p>
              </div>
              <button onClick={() => setTenantDetailModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            {/* Sekme Butonları: 1. Kurumsal Bilgiler | 2. Yönetici Tanımlaması */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14, borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: 10, flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => setTenantDetailActiveTab('COMPANY')}
                className="super-admin-btn-secondary"
                style={{
                  padding: '7px 14px',
                  fontSize: '0.785rem',
                  fontWeight: 700,
                  background: tenantDetailActiveTab === 'COMPANY' ? '#7134e2' : 'rgba(255,255,255,0.05)',
                  color: tenantDetailActiveTab === 'COMPANY' ? '#fff' : '#94a3b8',
                  borderColor: tenantDetailActiveTab === 'COMPANY' ? '#7134e2' : 'rgba(255,255,255,0.1)'
                }}
              >
                <Building2 style={{ width: 14, height: 14 }} />
                <span>1. Kurumsal Bilgiler & Paket</span>
              </button>

              <button
                type="button"
                onClick={() => setTenantDetailActiveTab('ADMIN')}
                className="super-admin-btn-secondary"
                style={{
                  padding: '7px 14px',
                  fontSize: '0.785rem',
                  fontWeight: 700,
                  background: tenantDetailActiveTab === 'ADMIN' ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'rgba(255,255,255,0.05)',
                  color: tenantDetailActiveTab === 'ADMIN' ? '#fff' : '#94a3b8',
                  borderColor: tenantDetailActiveTab === 'ADMIN' ? '#10b981' : 'rgba(255,255,255,0.1)',
                  boxShadow: tenantDetailActiveTab === 'ADMIN' ? '0 0 12px rgba(16,185,129,0.3)' : 'none'
                }}
              >
                <User style={{ width: 14, height: 14 }} />
                <span>2. Şirket Yöneticisi Tanımlaması</span>
                {justCreatedTenantAlert && (
                  <span style={{ width: 8, height: 8, borderRadius: 999, background: '#34d399', display: 'inline-block' }} />
                )}
              </button>

              <button
                type="button"
                onClick={() => setTenantDetailActiveTab('ALL')}
                className="super-admin-btn-secondary"
                style={{
                  padding: '7px 12px',
                  fontSize: '0.725rem',
                  marginLeft: 'auto',
                  background: tenantDetailActiveTab === 'ALL' ? 'rgba(255,255,255,0.15)' : 'transparent',
                  color: tenantDetailActiveTab === 'ALL' ? '#fff' : '#64748b',
                  border: 'none'
                }}
                title="Tüm Bölümleri Alt Alta Göster"
              >
                <span>Tümünü Göster</span>
              </button>
            </div>

            {justCreatedTenantAlert && (
              <div style={{
                marginTop: 12,
                padding: '10px 14px',
                borderRadius: 10,
                background: 'rgba(16,185,129,0.15)',
                border: '1px solid rgba(16,185,129,0.35)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                color: '#6ee7b7',
                fontSize: '0.785rem',
                fontWeight: 700
              }}>
                <CheckCircle2 style={{ width: 16, height: 16, color: '#34d399', flexShrink: 0 }} />
                <span>{justCreatedTenantAlert}</span>
              </div>
            )}

            {tenantDetailLoading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>Yükleniyor...</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20, marginTop: 16 }}>
                
                {/* 1. Şirket Bilgileri */}
                {(tenantDetailActiveTab === 'COMPANY' || tenantDetailActiveTab === 'ALL') && (
                <form onSubmit={handleSaveTenantDetails} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, padding: '8px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase' }}>
                        1. Kurumsal Bilgiler & Durum:
                      </span>
                      {tenantEditForm.is_active ? (
                        <span style={{ padding: '2px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, background: 'rgba(16,185,129,0.2)', color: '#6ee7b7', border: '1px solid rgba(16,185,129,0.3)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <CheckCircle2 style={{ width: 11, height: 11 }} /> AKTİF
                        </span>
                      ) : (
                        <span style={{ padding: '2px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, background: 'rgba(239,68,68,0.2)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.3)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <PauseCircle style={{ width: 11, height: 11 }} /> PASİF
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {/* Pasife Al / Aktife Al Butonu (Madde 4) */}
                      {selectedTenantDetails?.tenant && (
                        <button
                          type="button"
                          onClick={() => handleToggleTenantStatus(selectedTenantDetails.tenant)}
                          disabled={processingId === 'toggle-status-' + selectedTenantDetails.tenant.id}
                          className="super-admin-btn-secondary"
                          style={{
                            fontSize: '0.725rem',
                            padding: '5px 12px',
                            color: tenantEditForm.is_active ? '#f87171' : '#34d399',
                            borderColor: tenantEditForm.is_active ? 'rgba(239,68,68,0.4)' : 'rgba(16,185,129,0.4)',
                            background: tenantEditForm.is_active ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)'
                          }}
                          title={tenantEditForm.is_active ? "Müşteri kartını pasife al" : "Müşteri kartını aktife al"}
                        >
                          {processingId === 'toggle-status-' + selectedTenantDetails.tenant.id ? (
                            <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                          ) : tenantEditForm.is_active ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                              <PauseCircle style={{ width: 12, height: 12 }} />
                              <span>Kartı Pasife Al</span>
                            </span>
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                              <PlayCircle style={{ width: 12, height: 12 }} />
                              <span>Kartı Aktife Al</span>
                            </span>
                          )}
                        </button>
                      )}

                      {!tenantEditForm.is_active && (
                        <button
                          type="button"
                          onClick={handleApproveTenantInModal}
                          disabled={processingId === 'approve-tenant'}
                          className="super-admin-btn-corporate"
                          style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', fontSize: '0.725rem', padding: '5px 10px' }}
                        >
                          <CheckCircle2 style={{ width: 13, height: 13 }} />
                          <span>Şirketi Onayla & 1 Yıl Başlat</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Müşteri Kartı Aktiflik Durumu Checkbox Kontrolü (Madde 4) */}
                  <div style={{
                    padding: '8px 12px',
                    borderRadius: 8,
                    background: tenantEditForm.is_active ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                    border: `1px solid ${tenantEditForm.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700, color: tenantEditForm.is_active ? '#6ee7b7' : '#fca5a5' }}>
                      <input
                        type="checkbox"
                        checked={tenantEditForm.is_active}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, is_active: e.target.checked })}
                        style={{ width: 16, height: 16, cursor: 'pointer', accentColor: '#10b981' }}
                      />
                      <span>Müşteri Kartı Aktif Durumda (İşaret kaldırılırsa müşteri ve tüm kullanıcıları pasife alınır)</span>
                    </label>
                    <span style={{ fontSize: '0.7rem', color: tenantEditForm.is_active ? '#34d399' : '#f87171', fontWeight: 800 }}>
                      {tenantEditForm.is_active ? '● Aktif' : '○ Pasif'}
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 10 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Şirket Ünvanı</label>
                      <input
                        type="text"
                        value={tenantEditForm.name}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, name: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Vergi No (VKN)</label>
                      <input
                        type="text"
                        value={tenantEditForm.tax_id}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, tax_id: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#38bdf8', marginBottom: 3 }}>Vergi Dairesi (V.D.)</label>
                      <input
                        type="text"
                        value={tenantEditForm.tax_office || ''}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, tax_office: e.target.value })}
                        placeholder="Örn: Maslak V.D."
                        className="super-admin-input"
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Telefon</label>
                      <input
                        type="text"
                        value={tenantEditForm.phone}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, phone: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>İletişim E-posta</label>
                      <input
                        type="email"
                        value={tenantEditForm.contact_email}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, contact_email: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Web Sitesi</label>
                      <input
                        type="text"
                        value={tenantEditForm.website}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, website: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                  </div>

                  {/* Paket & Kira Bitiş Tarihi & Hatırlatıcı Mail (Maddeler 7, 10, 14) */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 10, padding: 10, borderRadius: 8, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#a78bfa', marginBottom: 3 }}>Tanımlı Paket</label>
                      <select
                        value={tenantEditForm.plan_id || ''}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, plan_id: e.target.value })}
                        className="super-admin-select"
                      >
                        <option value="">Paket Seçiniz...</option>
                        {plans.map((p) => (
                          <option key={p.id} value={p.id}>{p.name} ({p.monthly_price?.toLocaleString()} TRY/ay)</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#60a5fa', marginBottom: 3 }}>Paket Kira Bitiş Tarihi</label>
                      <input
                        type="date"
                        value={tenantEditForm.package_expiry_date ? tenantEditForm.package_expiry_date.split('T')[0] : ''}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, package_expiry_date: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', gap: 6 }}>
                      {/* Hoş Geldin Maili Gönder (Madde 1) */}
                      <button
                        type="button"
                        onClick={() => handleSendManualWelcome(selectedTenantDetails.tenant)}
                        disabled={processingId === 'welcome-' + selectedTenantDetails.tenant.id}
                        className="super-admin-btn-secondary"
                        style={{ height: 34, fontSize: '0.725rem', color: '#38bdf8', borderColor: 'rgba(56,189,248,0.3)', width: '100%', justifyContent: 'center' }}
                        title="Müşteriye Hoş Geldiniz e-postası gönder"
                      >
                        {processingId === 'welcome-' + selectedTenantDetails.tenant.id ? (
                          <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                        ) : (
                          <Mail style={{ width: 13, height: 13 }} />
                        )}
                        <span>Hoş Geldin Maili Gönder</span>
                      </button>

                      {/* Hatırlatıcı Mail Gönder */}
                      <button
                        type="button"
                        onClick={() => handleSendManualReminder(selectedTenantDetails.tenant)}
                        disabled={processingId === 'reminder-' + selectedTenantDetails.tenant.id}
                        className="super-admin-btn-secondary"
                        style={{ height: 34, fontSize: '0.725rem', color: '#f59e0b', borderColor: 'rgba(245,158,11,0.3)', width: '100%', justifyContent: 'center' }}
                        title="Paket süre dolum hatırlatma e-postası gönder"
                      >
                        {processingId === 'reminder-' + selectedTenantDetails.tenant.id ? (
                          <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                        ) : (
                          <Send style={{ width: 13, height: 13 }} />
                        )}
                        <span>Hatırlatıcı Mail Gönder</span>
                      </button>
                    </div>
                  </div>

                  {/* NACE Kodları Çoklu Seçim (Madde 13) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <label style={{ fontSize: '0.72rem', fontWeight: 700, color: '#38bdf8' }}>
                        Şirket Faaliyet NACE Kodları (Birden Fazla Seçilebilir)
                      </label>
                      <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                        {tenantEditForm.nace_codes?.length || 0} kod seçili
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, minHeight: 32, padding: 6, borderRadius: 6, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)' }}>
                      {(tenantEditForm.nace_codes || []).map((code) => (
                        <span key={code} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 999, background: 'rgba(56,189,248,0.2)', color: '#38bdf8', fontSize: '0.7rem', fontFamily: 'monospace' }}>
                          <span>{code}</span>
                          <button
                            type="button"
                            onClick={() => setTenantEditForm({
                              ...tenantEditForm,
                              nace_codes: tenantEditForm.nace_codes.filter(c => c !== code)
                            })}
                            style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', padding: 0 }}
                          >
                            ×
                          </button>
                        </span>
                      ))}
                      {(!tenantEditForm.nace_codes || tenantEditForm.nace_codes.length === 0) && (
                        <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Henüz NACE kodu seçilmedi. Aşağıdan arayarak ekleyebilirsiniz.</span>
                      )}
                    </div>

                    {/* NACE Arama */}
                    <input
                      type="text"
                      placeholder="NACE kodu veya sektör ara (Örn: 62.01, Yazılım, Danışmanlık)..."
                      value={detailNaceSearch}
                      onChange={async (e) => {
                        const val = e.target.value;
                        setDetailNaceSearch(val);
                        if (val.trim().length > 1) {
                          try {
                            const res = await api.searchNace(val, 8);
                            setDetailNaceResults(res || []);
                          } catch (_) {}
                        } else {
                          setDetailNaceResults([]);
                        }
                      }}
                      className="super-admin-input"
                      style={{ fontSize: '0.75rem' }}
                    />

                    {detailNaceResults.length > 0 && (
                      <div style={{ maxHeight: 120, overflowY: 'auto', borderRadius: 6, background: '#12182c', border: '1px solid rgba(255,255,255,0.1)', padding: 4 }}>
                        {detailNaceResults.map((n) => {
                          const isAlreadySelected = (tenantEditForm.nace_codes || []).includes(n.code);
                          return (
                            <div
                              key={n.id}
                              onClick={() => {
                                if (!isAlreadySelected) {
                                  setTenantEditForm({
                                    ...tenantEditForm,
                                    nace_codes: [...(tenantEditForm.nace_codes || []), n.code]
                                  });
                                }
                                setDetailNaceSearch('');
                                setDetailNaceResults([]);
                              }}
                              style={{ padding: '6px 8px', borderRadius: 4, cursor: isAlreadySelected ? 'default' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', background: isAlreadySelected ? 'rgba(255,255,255,0.02)' : 'transparent', color: isAlreadySelected ? '#64748b' : '#cbd5e1' }}
                            >
                              <span><strong style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{n.code}</strong> - {n.title}</span>
                              <span>{isAlreadySelected ? '✓ Eklendi' : '+ Ekle'}</span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* AI İle Şirket Manifestosu Oluşturma (Madde 13) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <label style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c084fc', display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Sparkles style={{ width: 13, height: 13 }} />
                        <span>RECOrion Ana LLM Tarafından Üretilen Kurumsal Manifesto</span>
                      </label>
                      <button
                        type="button"
                        onClick={handleGenerateManifestoForTenant}
                        disabled={isGeneratingDetailManifesto}
                        className="super-admin-btn-corporate"
                        style={{ fontSize: '0.7rem', padding: '4px 10px', background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)' }}
                      >
                        {isGeneratingDetailManifesto ? (
                          <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                        ) : (
                          <Sparkles style={{ width: 12, height: 12 }} />
                        )}
                        <span>{isGeneratingDetailManifesto ? 'LLM Yazıyor...' : '✨ AI ile Manifestoyu Yaz / Yenile'}</span>
                      </button>
                    </div>

                    <textarea
                      rows="4"
                      value={tenantEditForm.sector_manifesto || ''}
                      onChange={(e) => setTenantEditForm({ ...tenantEditForm, sector_manifesto: e.target.value })}
                      placeholder="Şirketin NACE kodları ve faaliyet alanına göre RECOrion LLM tarafından otomatik hazırlanan kurumsal vizyon ve manifesto metni..."
                      className="super-admin-input"
                      style={{ fontSize: '0.75rem', lineHeight: 1.5 }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Adres</label>
                    <textarea
                      rows="2"
                      value={tenantEditForm.address}
                      onChange={(e) => setTenantEditForm({ ...tenantEditForm, address: e.target.value })}
                      className="super-admin-input"
                    />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={() => setTenantDetailModalOpen(false)}
                      className="super-admin-btn-secondary"
                    >
                      Kapat
                    </button>
                    <button
                      type="submit"
                      disabled={processingId === 'save-tenant'}
                      className="super-admin-btn-corporate"
                      style={{
                        background: 'linear-gradient(135deg, #7134e2 0%, #314ccd 100%)',
                        boxShadow: '0 0 12px rgba(113, 52, 226, 0.4)',
                        fontWeight: 800,
                        padding: '8px 18px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6
                      }}
                      title="Şirket Bilgilerini Kaydet ve Ekranı Kapat"
                    >
                      {processingId === 'save-tenant' ? (
                        <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" />
                      ) : (
                        <Save style={{ width: 14, height: 14 }} />
                      )}
                      <span>Şirket Bilgilerini Kaydet</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setTenantDetailActiveTab('ADMIN')}
                      className="super-admin-btn-corporate"
                      style={{
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        boxShadow: '0 0 12px rgba(16, 185, 129, 0.3)',
                        fontWeight: 800,
                        padding: '8px 16px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6
                      }}
                      title="Yönetici (Admin) tanımlama bölümüne geç"
                    >
                      <User style={{ width: 14, height: 14 }} />
                      <span>Yönetici Tanımlamasına Geç →</span>
                    </button>
                  </div>
                </form>
                )}

                {/* 2. Şirket Admin Kullanıcısı & Güçlü Şifre */}
                {(tenantDetailActiveTab === 'ADMIN' || tenantDetailActiveTab === 'ALL') && (
                <div style={{
                  borderTop: tenantDetailActiveTab === 'ALL' ? '1px solid rgba(255,255,255,0.08)' : 'none',
                  paddingTop: tenantDetailActiveTab === 'ALL' ? 16 : 0,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <div style={{ fontSize: '0.825rem', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                        <User style={{ width: 15, height: 15 }} />
                        <span>2. Şirket Admin Kullanıcı Tanımlaması</span>
                      </div>
                      <div style={{ fontSize: '0.725rem', color: '#94a3b8' }}>
                        Şirketin sisteme ilk giriş yapacak yöneticisinin (Admin) kullanıcı bilgileri ve şifresi.
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {tenantDetailActiveTab === 'ADMIN' && (
                        <button
                          type="button"
                          onClick={() => setTenantDetailActiveTab('COMPANY')}
                          className="super-admin-btn-secondary"
                          style={{ fontSize: '0.725rem', padding: '6px 12px' }}
                        >
                          ← Şirket Bilgilerine Dön
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={handleGenerateTenantPassword}
                        disabled={processingId === 'gen-pass'}
                        className="super-admin-btn-corporate"
                        style={{ background: 'linear-gradient(135deg, #1261cd 0%, #146ceb 100%)', fontSize: '0.725rem' }}
                      >
                        <Lock style={{ width: 13, height: 13 }} />
                        <span>Güçlü Şifre Oluştur</span>
                      </button>
                    </div>
                  </div>

                  {generatedAdminPassword && (
                    <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ fontSize: '0.68rem', color: '#6ee7b7', fontWeight: 800 }}>Yeni Oluşturulan Güçlü Şifre:</div>
                        <div style={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '0.9rem', color: '#fff', marginTop: 2 }}>
                          {generatedAdminPassword}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(generatedAdminPassword, 'genpass')}
                        className="super-admin-btn-corporate"
                        style={{ padding: '4px 10px', fontSize: '0.725rem', background: '#10b981' }}
                      >
                        {copiedKey === 'genpass' ? <Check style={{ width: 12, height: 12 }} /> : <Copy style={{ width: 12, height: 12 }} />}
                        <span>Kopyala</span>
                      </button>
                    </div>
                  )}

                  <form onSubmit={handleSaveTenantAdmin} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Yönetici Adı Soyadı</label>
                        <input
                          type="text"
                          required
                          value={tenantAdminForm.display_name}
                          onChange={(e) => setTenantAdminForm({ ...tenantAdminForm, display_name: e.target.value })}
                          className="super-admin-input"
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Giriş E-postası</label>
                        <input
                          type="email"
                          required
                          value={tenantAdminForm.email}
                          onChange={(e) => setTenantAdminForm({ ...tenantAdminForm, email: e.target.value })}
                          className="super-admin-input"
                        />
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Telefon</label>
                        <input
                          type="text"
                          value={tenantAdminForm.phone}
                          onChange={(e) => setTenantAdminForm({ ...tenantAdminForm, phone: e.target.value })}
                          className="super-admin-input"
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', marginBottom: 3 }}>Manuel Şifre Ata</label>
                        <input
                          type="text"
                          value={tenantAdminForm.new_password}
                          onChange={(e) => setTenantAdminForm({ ...tenantAdminForm, new_password: e.target.value })}
                          placeholder="Otomatik yerine elle şifre girmek için..."
                          className="super-admin-input"
                        />
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 4 }}>
                      <button
                        type="button"
                        onClick={() => setTenantDetailModalOpen(false)}
                        className="super-admin-btn-secondary"
                      >
                        Kapat
                      </button>
                      <button
                        type="submit"
                        disabled={processingId === 'save-tenant-admin'}
                        className="super-admin-btn-corporate"
                        style={{
                          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                          boxShadow: '0 0 12px rgba(16,185,129,0.3)',
                          fontWeight: 800,
                          padding: '8px 18px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6
                        }}
                      >
                        {processingId === 'save-tenant-admin' ? (
                          <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" />
                        ) : (
                          <Save style={{ width: 14, height: 14 }} />
                        )}
                        <span>Yönetici Bilgilerini Kaydet</span>
                      </button>
                    </div>
                  </form>
                </div>
                )}

              </div>
            )}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 3. İZİN EKLEME / DÜZENLEME MODALI (Madde 4)               */}
      {/* ======================================================== */}
      {permissionModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff' }}>
                {editingPermission ? 'İzin Tanımını Düzenle' : 'Yeni İzin Tanımla'}
              </h3>
              <button onClick={() => setPermissionModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSavePermission} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Yetki Kodu</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingPermission}
                    value={permissionForm.code}
                    onChange={(e) => setPermissionForm({ ...permissionForm, code: e.target.value })}
                    placeholder="agent:deploy"
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Modül</label>
                  <select
                    value={permissionForm.module}
                    onChange={(e) => setPermissionForm({ ...permissionForm, module: e.target.value })}
                    className="super-admin-select"
                  >
                    {['PLATFORM', 'RBAC', 'AGENTS', 'PROJECTS', 'CHAT', 'MEMORY', 'BILLING'].map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>İzin Adı</label>
                <input
                  type="text"
                  required
                  value={permissionForm.name}
                  onChange={(e) => setPermissionForm({ ...permissionForm, name: e.target.value })}
                  placeholder="AI Personeli Başlatma"
                  className="super-admin-input"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Açıklama</label>
                <textarea
                  rows="3"
                  value={permissionForm.description}
                  onChange={(e) => setPermissionForm({ ...permissionForm, description: e.target.value })}
                  placeholder="Bu yetkiye sahip roller yapay zeka personellerini devreye alabilir."
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <button type="button" onClick={() => setPermissionModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>
                <button type="submit" className="super-admin-btn-corporate">
                  Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 4. PLAN MODALI (Madde 7)                                  */}
      {/* ======================================================== */}
      {planModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff' }}>
                {editingPlan ? 'Paketi Düzenle' : 'Yeni Kiralama Paketi Tanımla'}
              </h3>
              <button onClick={() => setPlanModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSavePlan} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Paket Kodu</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingPlan}
                    value={planForm.code}
                    onChange={(e) => setPlanForm({ ...planForm, code: e.target.value })}
                    placeholder="ENTERPRISE_CUSTOM"
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Paket Adı</label>
                  <input
                    type="text"
                    required
                    value={planForm.name}
                    onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                    placeholder="Kurumsal Paket"
                    className="super-admin-input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Aylık Fiyat (TRY)</label>
                  <input
                    type="number"
                    value={planForm.monthly_price}
                    onChange={(e) => setPlanForm({ ...planForm, monthly_price: Number(e.target.value) })}
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Aylık Kredi</label>
                  <input
                    type="number"
                    value={planForm.monthly_credits}
                    onChange={(e) => setPlanForm({ ...planForm, monthly_credits: Number(e.target.value) })}
                    className="super-admin-input"
                  />
                </div>
              </div>

              {/* Dinamik Limitler (Madde 15) */}
              <div style={{ padding: 12, borderRadius: 8, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#a78bfa', marginBottom: 8, textTransform: 'uppercase' }}>
                  Paket Kaynak ve Adetsel Limitleri (Madde 15)
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>AI Ajan Personel</label>
                    <input
                      type="number"
                      value={planForm.max_agents}
                      onChange={(e) => setPlanForm({ ...planForm, max_agents: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>İnsan Kullanıcı</label>
                    <input
                      type="number"
                      value={planForm.max_humans}
                      onChange={(e) => setPlanForm({ ...planForm, max_humans: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Eşzamanlı Proje</label>
                    <input
                      type="number"
                      value={planForm.max_projects || 3}
                      onChange={(e) => setPlanForm({ ...planForm, max_projects: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>İşlem Kredisi</label>
                    <input
                      type="number"
                      value={planForm.monthly_credits}
                      onChange={(e) => setPlanForm({ ...planForm, monthly_credits: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>MinIO Depolama (GB)</label>
                    <input
                      type="number"
                      value={planForm.storage_gb}
                      onChange={(e) => setPlanForm({ ...planForm, storage_gb: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                </div>
              </div>

              {/* Paket İçerisindeki EVREN LLM Modelleri Seçimi (Madde 15) */}
              <div style={{ padding: 12, borderRadius: 8, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase' }}>
                    Pakete Dahil Edilen EVREN LLM Modelleri ({planForm.allowed_models?.length || 0} Model Seçili)
                  </div>
                  <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Müşterinin kullanabileceği modeller</span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, maxHeight: 150, overflowY: 'auto' }}>
                  {models.map((m) => {
                    const isChecked = (planForm.allowed_models || []).includes(m.model_code);
                    return (
                      <label
                        key={m.id}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', borderRadius: 6,
                          background: isChecked ? 'rgba(56,189,248,0.15)' : 'rgba(0,0,0,0.3)',
                          border: isChecked ? '1px solid rgba(56,189,248,0.4)' : '1px solid rgba(255,255,255,0.04)',
                          cursor: 'pointer'
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            const cur = planForm.allowed_models || [];
                            if (e.target.checked) {
                              setPlanForm({ ...planForm, allowed_models: [...cur, m.model_code] });
                            } else {
                              setPlanForm({ ...planForm, allowed_models: cur.filter(x => x !== m.model_code) });
                            }
                          }}
                        />
                        <div style={{ overflow: 'hidden' }}>
                          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#fff', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>{m.display_name}</div>
                          <div style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: '#94a3b8' }}>{m.model_code}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Açıklama</label>
                <textarea
                  rows="2"
                  value={planForm.description}
                  onChange={(e) => setPlanForm({ ...planForm, description: e.target.value })}
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', gap: 20, padding: '4px 0' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={planForm.can_create_custom_titles}
                    onChange={(e) => setPlanForm({ ...planForm, can_create_custom_titles: e.target.checked })}
                  />
                  <span>Özel AI Ünvan Tanımlama İzni Ver</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={planForm.is_active}
                    onChange={(e) => setPlanForm({ ...planForm, is_active: e.target.checked })}
                  />
                  <span>Paket Aktif</span>
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <button type="button" onClick={() => setPlanModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>
                <button type="submit" className="super-admin-btn-corporate">
                  Paketi Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 5. EVREN MODEL MODALI (Madde 8)                            */}
      {/* ======================================================== */}
      {modelModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff' }}>
                {editingModel ? 'EVREN Modelini Düzenle' : 'Yeni EVREN Modeli Ekle'}
              </h3>
              <button onClick={() => setModelModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveModel} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Model Kodu</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingModel}
                    value={modelForm.model_code}
                    onChange={(e) => setModelForm({ ...modelForm, model_code: e.target.value })}
                    placeholder="deepseek-r1"
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Görünen İsim</label>
                  <input
                    type="text"
                    required
                    value={modelForm.display_name}
                    onChange={(e) => setModelForm({ ...modelForm, display_name: e.target.value })}
                    placeholder="DeepSeek R1 (Muhakeme)"
                    className="super-admin-input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Tür</label>
                  <select
                    value={modelForm.model_type}
                    onChange={(e) => setModelForm({ ...modelForm, model_type: e.target.value })}
                    className="super-admin-select"
                  >
                    {['CHAT', 'CODE', 'VISION', 'EMBEDDING', 'RERANKER', 'OCR', 'AUDIO'].map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Bağlam (Token)</label>
                  <input
                    type="number"
                    value={modelForm.context_window}
                    onChange={(e) => setModelForm({ ...modelForm, context_window: Number(e.target.value) })}
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Efor Katsayısı</label>
                  <input
                    type="number"
                    step="0.1"
                    value={modelForm.effort_coefficient}
                    onChange={(e) => setModelForm({ ...modelForm, effort_coefficient: Number(e.target.value) })}
                    className="super-admin-input"
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Durum</label>
                <select
                  value={modelForm.status}
                  onChange={(e) => setModelForm({ ...modelForm, status: e.target.value })}
                  className="super-admin-select"
                >
                  <option value="ACTIVE">ACTIVE (Aktif)</option>
                  <option value="INACTIVE">INACTIVE (Pasif)</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <button type="button" onClick={() => setModelModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>
                <button type="submit" className="super-admin-btn-corporate">
                  Modeli Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 6. NACE KODU MODALI (Madde 12)                            */}
      {/* ======================================================== */}
      {naceModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff' }}>
                {editingNace ? 'NACE Kodunu Düzenle' : 'Yeni NACE Kodu Tanımla'}
              </h3>
              <button onClick={() => setNaceModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveNace} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>NACE Kodu</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingNace}
                    value={naceForm.code}
                    onChange={(e) => setNaceForm({ ...naceForm, code: e.target.value })}
                    placeholder="62.01.01"
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Sektör Grubu</label>
                  <input
                    type="text"
                    required
                    value={naceForm.sector_group}
                    onChange={(e) => setNaceForm({ ...naceForm, sector_group: e.target.value })}
                    placeholder="Bilişim Teknolojileri"
                    className="super-admin-input"
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Faaliyet Alanı / Başlık</label>
                <input
                  type="text"
                  required
                  value={naceForm.title}
                  onChange={(e) => setNaceForm({ ...naceForm, title: e.target.value })}
                  placeholder="Bilgisayar programlama faaliyetleri"
                  className="super-admin-input"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Açıklama</label>
                <textarea
                  rows="3"
                  value={naceForm.description}
                  onChange={(e) => setNaceForm({ ...naceForm, description: e.target.value })}
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <button type="button" onClick={() => setNaceModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>
                <button type="submit" className="super-admin-btn-corporate">
                  NACE Kodunu Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 7. SEKTOREL ÜNVAN & PROMPT MODALI (Madde 13)              */}
      {/* ======================================================== */}
      {titleModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box" style={{ maxWidth: 680 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff' }}>
                  {editingTitle ? `'${titleForm.title}' Ünvan ve Prompt Düzenleme` : 'Yeni Sektörel Ünvan Tanımla'}
                </h3>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>AI ajan personelleri için sistem rol ve görev tanımı.</p>
              </div>
              <button onClick={() => setTitleModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveTitle} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Ünvan Kodu</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingTitle}
                    value={titleForm.code}
                    onChange={(e) => setTitleForm({ ...titleForm, code: e.target.value })}
                    placeholder="CHIEF_ARCHITECT"
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Ünvan Adı</label>
                  <input
                    type="text"
                    required
                    value={titleForm.title}
                    onChange={(e) => setTitleForm({ ...titleForm, title: e.target.value })}
                    placeholder="Baş Sistem Mimarı"
                    className="super-admin-input"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Sektör / Kategori</label>
                  <input
                    type="text"
                    required
                    value={titleForm.category}
                    onChange={(e) => setTitleForm({ ...titleForm, category: e.target.value })}
                    placeholder="YAZILIM"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Önerilen Model</label>
                  <input
                    type="text"
                    value={titleForm.recommended_model_code}
                    onChange={(e) => setTitleForm({ ...titleForm, recommended_model_code: e.target.value })}
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Otonomi Seviyesi</label>
                  <select
                    value={titleForm.autonomy_level}
                    onChange={(e) => setTitleForm({ ...titleForm, autonomy_level: e.target.value })}
                    className="super-admin-select"
                  >
                    <option value="L1">L1 (Yardımcı)</option>
                    <option value="L2">L2 (Yarı Otonom)</option>
                    <option value="L3">L3 (Tam Otonom)</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Ünvan Açıklaması</label>
                <input
                  type="text"
                  value={titleForm.description}
                  onChange={(e) => setTitleForm({ ...titleForm, description: e.target.value })}
                  placeholder="Sistem mimarisini kurgular ve kalite kapılarını denetler."
                  className="super-admin-input"
                />
              </div>

              {/* AI İLE ROL PROMPTU YENİDEN OLUŞTURMA (Madde 13) */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1' }}>
                    Temel Sistem Rol Promptu (Base Role Prompt)
                  </label>
                  {editingTitle && (
                    <button
                      type="button"
                      onClick={handleRegeneratePromptWithAI}
                      disabled={regeneratingPrompt}
                      className="super-admin-btn-corporate"
                      style={{ background: 'linear-gradient(135deg, #7134e2 0%, #ec4899 100%)', fontSize: '0.725rem', padding: '4px 10px' }}
                    >
                      <Sparkles style={{ width: 12, height: 12 }} className={regeneratingPrompt ? 'animate-spin' : ''} />
                      <span>{regeneratingPrompt ? 'AI Üretiyor...' : '✨ AI ile Rol Promptunu Yeniden Üret'}</span>
                    </button>
                  )}
                </div>
                <textarea
                  rows="7"
                  required
                  value={titleForm.base_role_prompt}
                  onChange={(e) => setTitleForm({ ...titleForm, base_role_prompt: e.target.value })}
                  placeholder="Sen RECOrion otonom mimarisinde görev alan Baş Mimarsın..."
                  className="super-admin-input"
                  style={{ fontFamily: 'monospace', fontSize: '0.75rem', lineHeight: 1.5 }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <button type="button" onClick={() => setTitleModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>
                <button type="submit" className="super-admin-btn-corporate">
                  Ünvanı Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 8. YENİ MÜŞTERİ / ŞİRKET EKLEME MODALI (Madde 9 & 13)    */}
      {/* ======================================================== */}
      {newTenantModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box" style={{ maxWidth: 780 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Building2 style={{ width: 20, height: 20, color: '#10b981' }} />
                  <span>Yeni Müşteri & Şirket Ekle (Süper Admin Kaydı)</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Şirket kartı oluşturulur, 1 yıllık kira paketi tanımlanır ve Hoş Geldiniz e-postası otomatik iletilir.
                </p>
              </div>
              <button onClick={() => setNewTenantModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveNewTenant} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
              {/* Kurumsal Bilgiler */}
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Şirket Ünvanı *</label>
                  <input
                    type="text"
                    required
                    value={newTenantForm.name}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, name: e.target.value })}
                    placeholder="Örn: Atlas Savunma Sanayi A.Ş."
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Vergi No (VKN) *</label>
                  <input
                    type="text"
                    required
                    value={newTenantForm.tax_id}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, tax_id: e.target.value })}
                    placeholder="10 Haneli VKN"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#38bdf8', marginBottom: 3 }}>Vergi Dairesi (Madde 12)</label>
                  <input
                    type="text"
                    value={newTenantForm.tax_office}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, tax_office: e.target.value })}
                    placeholder="Örn: Maslak V.D."
                    className="super-admin-input"
                  />
                </div>
              </div>

              {/* İletişim Bilgileri */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>İletişim E-posta *</label>
                  <input
                    type="email"
                    required
                    value={newTenantForm.contact_email}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, contact_email: e.target.value })}
                    placeholder="info@sirket.com"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Telefon</label>
                  <input
                    type="text"
                    value={newTenantForm.phone}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, phone: e.target.value })}
                    placeholder="+90 212 XXX XX XX"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Web Sitesi</label>
                  <input
                    type="text"
                    value={newTenantForm.website}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, website: e.target.value })}
                    placeholder="https://sirket.com"
                    className="super-admin-input"
                  />
                </div>
              </div>

              {/* Paket & Yönetici Bilgileri */}
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 10, padding: 10, borderRadius: 8, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#a78bfa', marginBottom: 3 }}>Kiralama Paketi (1 Yıl Başlatılır)</label>
                  <select
                    value={newTenantForm.plan_id}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, plan_id: e.target.value })}
                    className="super-admin-select"
                  >
                    {plans.map((p) => (
                      <option key={p.id} value={p.id}>{p.name} ({p.monthly_price?.toLocaleString()} TRY/ay)</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Yönetici Adı Soyadı</label>
                  <input
                    type="text"
                    value={newTenantForm.admin_name}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, admin_name: e.target.value })}
                    placeholder="Şirket Yöneticisi"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Yönetici Şifresi (Opsiyonel)</label>
                  <input
                    type="text"
                    value={newTenantForm.admin_password}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, admin_password: e.target.value })}
                    placeholder="Boş bırakılırsa güçlü şifre atanır"
                    className="super-admin-input"
                  />
                </div>
              </div>

              {/* NACE Kodları Çoklu Seçim (Madde 13) */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <label style={{ fontSize: '0.72rem', fontWeight: 700, color: '#38bdf8' }}>
                    Şirket Faaliyet NACE Kodları (Çoklu Seçim) (Madde 13)
                  </label>
                  <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                    {newTenantForm.nace_codes?.length || 0} kod seçildi
                  </span>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, minHeight: 32, padding: 6, borderRadius: 6, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  {(newTenantForm.nace_codes || []).map((code) => (
                    <span key={code} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 999, background: 'rgba(56,189,248,0.2)', color: '#38bdf8', fontSize: '0.7rem', fontFamily: 'monospace' }}>
                      <span>{code}</span>
                      <button
                        type="button"
                        onClick={() => setNewTenantForm({
                          ...newTenantForm,
                          nace_codes: newTenantForm.nace_codes.filter(c => c !== code)
                        })}
                        style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', padding: 0 }}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  {(!newTenantForm.nace_codes || newTenantForm.nace_codes.length === 0) && (
                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Aşağıdaki arama alanından NACE kodlarını seçebilirsiniz.</span>
                  )}
                </div>

                <input
                  type="text"
                  placeholder="NACE kodu veya sektör ara (Örn: 62.01, Bilişim, Danışmanlık)..."
                  value={newTenantNaceSearch}
                  onChange={async (e) => {
                    const val = e.target.value;
                    setNewTenantNaceSearch(val);
                    if (val.trim().length > 1) {
                      try {
                        const res = await api.searchNace(val, 8);
                        setNewTenantNaceResults(res || []);
                      } catch (_) {}
                    } else {
                      setNewTenantNaceResults([]);
                    }
                  }}
                  className="super-admin-input"
                  style={{ fontSize: '0.75rem' }}
                />

                {newTenantNaceResults.length > 0 && (
                  <div style={{ maxHeight: 110, overflowY: 'auto', borderRadius: 6, background: '#12182c', border: '1px solid rgba(255,255,255,0.1)', padding: 4 }}>
                    {newTenantNaceResults.map((n) => {
                      const isAlreadySelected = (newTenantForm.nace_codes || []).includes(n.code);
                      return (
                        <div
                          key={n.id}
                          onClick={() => {
                            if (!isAlreadySelected) {
                              setNewTenantForm({
                                ...newTenantForm,
                                nace_codes: [...(newTenantForm.nace_codes || []), n.code]
                              });
                            }
                            setNewTenantNaceSearch('');
                            setNewTenantNaceResults([]);
                          }}
                          style={{ padding: '6px 8px', borderRadius: 4, cursor: isAlreadySelected ? 'default' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', background: isAlreadySelected ? 'rgba(255,255,255,0.02)' : 'transparent', color: isAlreadySelected ? '#64748b' : '#cbd5e1' }}
                        >
                          <span><strong style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{n.code}</strong> - {n.title}</span>
                          <span>{isAlreadySelected ? '✓ Eklendi' : '+ Ekle'}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* AI İle Kurumsal Manifesto Üretimi (Madde 13) */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <label style={{ fontSize: '0.72rem', fontWeight: 700, color: '#c084fc', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Sparkles style={{ width: 13, height: 13 }} />
                    <span>RECOrion Ana LLM Tarafından Otomatik Yazılan Şirket Manifestosu</span>
                  </label>
                  <button
                    type="button"
                    onClick={handleGenerateManifestoForNewTenant}
                    disabled={isGeneratingNewTenantManifesto}
                    className="super-admin-btn-corporate"
                    style={{ fontSize: '0.7rem', padding: '4px 10px', background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)' }}
                  >
                    {isGeneratingNewTenantManifesto ? (
                      <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                    ) : (
                      <Sparkles style={{ width: 12, height: 12 }} />
                    )}
                    <span>{isGeneratingNewTenantManifesto ? 'LLM Yazıyor...' : '✨ RECOrion AI ile Manifesto Üret'}</span>
                  </button>
                </div>

                <textarea
                  rows="3"
                  value={newTenantManifesto}
                  onChange={(e) => setNewTenantManifesto(e.target.value)}
                  placeholder="Seçilen NACE kodlarına göre RECOrion LLM tarafından otomatik üretilen şirket vizyonu ve yapay zeka entegrasyon manifestosu (Kullanıcı dilediğince düzenleyebilir)..."
                  className="super-admin-input"
                  style={{ fontSize: '0.75rem', lineHeight: 1.5 }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Adres</label>
                <textarea
                  rows="2"
                  value={newTenantForm.address}
                  onChange={(e) => setNewTenantForm({ ...newTenantForm, address: e.target.value })}
                  placeholder="Şirket resmi adresi..."
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.08)', flexWrap: 'wrap' }}>
                <button type="button" onClick={() => setNewTenantModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>

                {/* 1. SADECE KAYDET & YÖNETİCİ TANIMLA */}
                <button
                  type="button"
                  onClick={(e) => handleSaveNewTenant(e, { activate: false, sendEmail: false })}
                  disabled={!!processingId}
                  className="super-admin-btn-secondary"
                  style={{
                    background: 'rgba(255,255,255,0.08)',
                    borderColor: 'rgba(255,255,255,0.2)',
                    color: '#e2e8f0',
                    fontWeight: 700
                  }}
                  title="Şirket bilgilerini kaydeder ve ardından doğrudan Yönetici Tanımlama ekranını açar"
                >
                  {processingId === 'create-new-tenant-draft' ? <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" /> : <Save style={{ width: 14, height: 14 }} />}
                  <span>Şirketi Kaydet & Yönetici Tanımla</span>
                </button>

                {/* 2. MÜŞTERİYİ KAYDET, PAKETİ BAŞLAT & YÖNETİCİ TANIMLAMAYA GEÇ */}
                <button
                  type="button"
                  onClick={(e) => handleSaveNewTenant(e, { activate: true, sendEmail: true })}
                  disabled={!!processingId}
                  className="super-admin-btn-corporate"
                  style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', fontWeight: 800 }}
                  title="Müşteriyi kaydeder, 1 yıllık paketi aktif eder ve doğrudan Yönetici Tanımlama ekranına geçer"
                >
                  {processingId === 'create-new-tenant-activate' ? <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" /> : <CheckCircle2 style={{ width: 14, height: 14 }} />}
                  <span>Şirketi Kaydet, Paketi Başlat & Yönetici Tanımlamaya Geç →</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 9. HTML E-POSTA ŞABLON EDİTÖRÜ MODALI (Madde 1)          */}
      {/* ======================================================== */}
      {templateModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box" style={{ maxWidth: 1340, width: '96%', maxHeight: '92vh', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Mail style={{ width: 22, height: 22, color: '#38bdf8' }} />
                  <span>{editingTemplate ? `'${templateForm.name}' Şablonunu Düzenle` : 'Yeni E-Posta Şablonu Tasarla'}</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Sürükle-bırak görsel blok editörü, canlı e-posta önizlemesi ve modal içi test gönderim altyapısı.
                </p>
              </div>

              {/* Mod Seçici (Görsel Builder vs HTML Kod) */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ display: 'flex', background: 'rgba(255,255,255,0.06)', padding: 3, borderRadius: 8, border: '1px solid rgba(255,255,255,0.08)' }}>
                  <button
                    type="button"
                    onClick={() => setTemplateEditorTab('BUILDER')}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      padding: '6px 12px', fontSize: '0.75rem', fontWeight: 700, borderRadius: 6, border: 'none', cursor: 'pointer',
                      background: templateEditorTab === 'BUILDER' ? '#7134e2' : 'transparent',
                      color: templateEditorTab === 'BUILDER' ? '#fff' : '#94a3b8'
                    }}
                  >
                    <Layers style={{ width: 14, height: 14 }} />
                    <span>🎨 Görsel Sürükle-Bırak</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setTemplateEditorTab('CODE')}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      padding: '6px 12px', fontSize: '0.75rem', fontWeight: 700, borderRadius: 6, border: 'none', cursor: 'pointer',
                      background: templateEditorTab === 'CODE' ? '#7134e2' : 'transparent',
                      color: templateEditorTab === 'CODE' ? '#fff' : '#94a3b8'
                    }}
                  >
                    <Code style={{ width: 14, height: 14 }} />
                    <span>💻 HTML Kaynak Kodu</span>
                  </button>
                </div>

                <button onClick={() => setTemplateModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                  <X style={{ width: 20, height: 20 }} />
                </button>
              </div>
            </div>

            <form onSubmit={handleSaveTemplate} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12, flex: 1, minHeight: 0, overflow: 'hidden' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.6fr 2.2fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Şablon Kodu *</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingTemplate}
                    value={templateForm.code}
                    onChange={(e) => setTemplateForm({ ...templateForm, code: e.target.value })}
                    placeholder="WELCOME_CUSTOMER"
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>Şablon Adı *</label>
                  <input
                    type="text"
                    required
                    value={templateForm.name}
                    onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}
                    placeholder="Kurumsal Hoş Geldiniz Maili"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 3 }}>E-Posta Konusu (Subject) *</label>
                  <input
                    type="text"
                    required
                    value={templateForm.subject}
                    onChange={(e) => setTemplateForm({ ...templateForm, subject: e.target.value })}
                    placeholder="RECDx | RECOrion Platformuna Hoş Geldiniz..."
                    className="super-admin-input"
                  />
                </div>
              </div>

              {/* Dinamik Değişken İpuçları */}
              <div style={{ padding: '6px 10px', borderRadius: 8, background: 'rgba(56,189,248,0.06)', border: '1px solid rgba(56,189,248,0.18)', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.68rem', fontWeight: 800, color: '#38bdf8' }}>Dinamik Değişkenler:</span>
                {['company_name', 'contact_name', 'login_email', 'password', 'plan_name', 'package_expiry_date', 'days_remaining', 'login_url'].map((v) => (
                  <button
                    type="button"
                    key={v}
                    onClick={() => {
                      if (templateEditorTab === 'CODE') {
                        setTemplateForm({ ...templateForm, html_content: templateForm.html_content + ` {{${v}}}` });
                      } else {
                        navigator.clipboard?.writeText(`{{${v}}}`);
                        alert(`'{{${v}}}' panoya kopyalandı! İstediğiniz blok alanına yapıştırabilirsiniz.`);
                      }
                    }}
                    style={{ fontSize: '0.62rem', fontFamily: 'monospace', padding: '2px 5px', borderRadius: 4, background: 'rgba(255,255,255,0.08)', color: '#a78bfa', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer' }}
                    title="Panoya kopyalamak veya içeriğe eklemek için tıklayın"
                  >
                    {`{{${v}}}`}
                  </button>
                ))}
              </div>

              {/* GÖRSEL BUILDER MODU (Madde 5) */}
              {templateEditorTab === 'BUILDER' ? (
                <div style={{ display: 'grid', gridTemplateColumns: '270px 1.4fr 1.1fr', gap: 12, flex: 1, minHeight: 440, maxHeight: '55vh', overflow: 'hidden' }}>
                  {/* Kolon 1: Bileşen Blokları Paleti */}
                  <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 12, display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', color: '#94a3b8', letterSpacing: 0.5, marginBottom: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span>Bileşen Blokları</span>
                      <span style={{ fontSize: '0.65rem', color: '#64748b' }}>Sürükle / Tıkla</span>
                    </div>

                    {EMAIL_PRESET_BLOCKS.map((preset) => (
                      <div
                        key={preset.type}
                        draggable={true}
                        onDragStart={(e) => {
                          e.dataTransfer.setData('text/plain', preset.type);
                          setDraggedPresetType(preset.type);
                        }}
                        onDragEnd={() => setDraggedPresetType(null)}
                        onClick={() => handleAddBlockToCanvas(preset.type)}
                        style={{
                          background: 'rgba(255,255,255,0.04)',
                          border: '1px solid rgba(255,255,255,0.08)',
                          borderRadius: 8,
                          padding: '8px 10px',
                          cursor: 'grab',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: 8,
                          transition: 'all 0.2s'
                        }}
                        title="Tuvale eklemek için tıklayın veya sürükleyin"
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <GripVertical style={{ width: 14, height: 14, color: '#64748b' }} />
                          <div>
                            <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#f1f5f9' }}>{preset.label}</div>
                            <div style={{ fontSize: '0.62rem', color: '#94a3b8', fontFamily: 'monospace' }}>{preset.type}</div>
                          </div>
                        </div>
                        <button
                          type="button"
                          style={{ width: 22, height: 22, borderRadius: 6, background: 'rgba(255,255,255,0.08)', border: 'none', color: '#cbd5e1', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
                        >
                          <Plus style={{ width: 12, height: 12 }} />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Kolon 2: Tasarım Tuvali (Canvas) */}
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      e.currentTarget.style.borderColor = '#38bdf8';
                    }}
                    onDragLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)';
                    }}
                    onDrop={(e) => {
                      e.preventDefault();
                      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)';
                      const type = e.dataTransfer.getData('text/plain') || draggedPresetType;
                      if (type) {
                        handleAddBlockToCanvas(type);
                      }
                    }}
                    style={{
                      background: 'rgba(15,23,42,0.4)',
                      border: '2px dashed rgba(255,255,255,0.12)',
                      borderRadius: 10,
                      padding: 12,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 10,
                      overflowY: 'auto'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#a78bfa' }}>
                        📋 Tuval Düzeni ({templateCanvasBlocks.length} Blok)
                      </span>
                      <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                        Oklarla veya sürükleyerek sıralayın
                      </span>
                    </div>

                    {templateCanvasBlocks.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b', fontSize: '0.8rem' }}>
                        Soldaki blokları buraya sürükleyin veya tıklayarak ekleyin.
                      </div>
                    ) : (
                      templateCanvasBlocks.map((block, idx) => (
                        <div
                          key={block.id}
                          draggable={true}
                          onDragStart={() => setDraggedBlockIdx(idx)}
                          onDragOver={(e) => e.preventDefault()}
                          onDrop={() => {
                            if (draggedBlockIdx !== null && draggedBlockIdx !== idx) {
                              const updated = [...templateCanvasBlocks];
                              const [moved] = updated.splice(draggedBlockIdx, 1);
                              updated.splice(idx, 0, moved);
                              setTemplateCanvasBlocks(updated);
                              setTemplateForm(prev => ({ ...prev, html_content: compileBlocksToHtml(updated) }));
                              setDraggedBlockIdx(null);
                            }
                          }}
                          style={{
                            background: 'rgba(30,41,59,0.85)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: 8,
                            padding: 10,
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 8,
                            cursor: 'move'
                          }}
                        >
                          {/* Blok Başlık Barı */}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                              <GripVertical style={{ width: 14, height: 14, color: '#94a3b8' }} />
                              <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '2px 6px', borderRadius: 4, background: 'rgba(113,52,226,0.25)', color: '#c4b5fd' }}>
                                {block.type}
                              </span>
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0' }}>
                                {EMAIL_PRESET_BLOCKS.find(p => p.type === block.type)?.label || block.type}
                              </span>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                              <button
                                type="button"
                                disabled={idx === 0}
                                onClick={() => handleMoveBlock(idx, -1)}
                                style={{ width: 22, height: 22, borderRadius: 4, background: 'rgba(255,255,255,0.06)', border: 'none', color: idx === 0 ? '#475569' : '#cbd5e1', cursor: idx === 0 ? 'default' : 'pointer' }}
                                title="Yukarı Taşı"
                              >
                                <ArrowUp style={{ width: 12, height: 12 }} />
                              </button>
                              <button
                                type="button"
                                disabled={idx === templateCanvasBlocks.length - 1}
                                onClick={() => handleMoveBlock(idx, 1)}
                                style={{ width: 22, height: 22, borderRadius: 4, background: 'rgba(255,255,255,0.06)', border: 'none', color: idx === templateCanvasBlocks.length - 1 ? '#475569' : '#cbd5e1', cursor: idx === templateCanvasBlocks.length - 1 ? 'default' : 'pointer' }}
                                title="Aşağı Taşı"
                              >
                                <ArrowDown style={{ width: 12, height: 12 }} />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleRemoveBlockFromCanvas(block.id)}
                                style={{ width: 22, height: 22, borderRadius: 4, background: 'rgba(239,68,68,0.15)', border: 'none', color: '#f87171', cursor: 'pointer' }}
                                title="Bloğu Kaldır"
                              >
                                <Trash2 style={{ width: 12, height: 12 }} />
                              </button>
                            </div>
                          </div>

                          {/* Blok İçerik Inputları */}
                          {block.type === 'HEADER' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              <input
                                type="text"
                                value={block.subtitle || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'subtitle', e.target.value)}
                                placeholder="Alt başlık / slogan..."
                                className="super-admin-input"
                                style={{ fontSize: '0.75rem', padding: '5px 8px' }}
                              />

                              {/* Logo Seçim Dialogu (Madde 1) */}
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)' }}>
                                <input
                                  type="file"
                                  id={`logo-upload-${block.id}`}
                                  accept="image/png, image/jpeg, image/jpg, image/webp, image/svg+xml"
                                  style={{ display: 'none' }}
                                  onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) {
                                      if (file.size > 3 * 1024 * 1024) {
                                        alert("Logo dosya boyutu 3MB'tan küçük olmalıdır.");
                                        return;
                                      }
                                      const reader = new FileReader();
                                      reader.onload = (ev) => {
                                        handleUpdateBlockField(block.id, 'logoUrl', ev.target.result);
                                      };
                                      reader.readAsDataURL(file);
                                    }
                                  }}
                                />
                                <label
                                  htmlFor={`logo-upload-${block.id}`}
                                  className="super-admin-btn-secondary"
                                  style={{ cursor: 'pointer', fontSize: '0.72rem', padding: '5px 10px', display: 'flex', alignItems: 'center', gap: 6, margin: 0, background: 'rgba(56,189,248,0.15)', color: '#38bdf8', borderColor: 'rgba(56,189,248,0.3)' }}
                                  title="Dosya Seçici Penceresi: PNG, JPG, SVG logo dosyası yükleyin"
                                >
                                  <ImageIcon style={{ width: 13, height: 13 }} />
                                  <span>{block.logoUrl ? '🖼️ Logoyu Değiştir (PNG, JPG)' : '📁 Logo Dosyası Seç (PNG, JPG)'}</span>
                                </label>

                                {block.logoUrl ? (
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                                    <div style={{ height: 26, maxWidth: 90, background: '#ffffff', borderRadius: 4, padding: '2px 4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                      <img
                                        src={block.logoUrl}
                                        alt="Seçilen Logo"
                                        style={{ maxHeight: 22, maxWidth: 80, objectFit: 'contain' }}
                                      />
                                    </div>
                                    <span style={{ fontSize: '0.68rem', color: '#34d399', fontWeight: 700 }}>✓ Logo Yüklendi</span>
                                    <button
                                      type="button"
                                      onClick={() => handleUpdateBlockField(block.id, 'logoUrl', '')}
                                      style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: '0.68rem', marginLeft: 'auto', fontWeight: 700 }}
                                      title="Logoyu kaldırıp varsayılan RECOrion başlığına dön"
                                    >
                                      Kaldır ✕
                                    </button>
                                  </div>
                                ) : (
                                  <span style={{ fontSize: '0.65rem', color: '#64748b' }}>Varsayılan RECOrion logosu devrede</span>
                                )}
                              </div>
                            </div>
                          )}
                          {block.type === 'IMAGE' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)' }}>
                                <input
                                  type="file"
                                  id={`img-upload-${block.id}`}
                                  accept="image/png, image/jpeg, image/jpg, image/webp, image/svg+xml"
                                  style={{ display: 'none' }}
                                  onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) {
                                      if (file.size > 4 * 1024 * 1024) {
                                        alert("Görsel dosya boyutu 4MB'tan küçük olmalıdır.");
                                        return;
                                      }
                                      const reader = new FileReader();
                                      reader.onload = (ev) => {
                                        handleUpdateBlockField(block.id, 'imageUrl', ev.target.result);
                                      };
                                      reader.readAsDataURL(file);
                                    }
                                  }}
                                />
                                <label
                                  htmlFor={`img-upload-${block.id}`}
                                  className="super-admin-btn-secondary"
                                  style={{ cursor: 'pointer', fontSize: '0.72rem', padding: '5px 10px', display: 'flex', alignItems: 'center', gap: 6, margin: 0, background: 'rgba(56,189,248,0.15)', color: '#38bdf8', borderColor: 'rgba(56,189,248,0.3)' }}
                                  title="PNG, JPG görsel seçin"
                                >
                                  <ImageIcon style={{ width: 13, height: 13 }} />
                                  <span>{block.imageUrl ? '🖼️ Görseli Değiştir' : '📁 Görsel Dosyası Seç (PNG, JPG)'}</span>
                                </label>

                                {block.imageUrl && (
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                                    <img
                                      src={block.imageUrl}
                                      alt="Önizleme"
                                      style={{ height: 26, maxWidth: 60, objectFit: 'contain', borderRadius: 4, background: '#fff', padding: 2 }}
                                    />
                                    <button
                                      type="button"
                                      onClick={() => handleUpdateBlockField(block.id, 'imageUrl', '')}
                                      style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: '0.68rem', marginLeft: 'auto', fontWeight: 700 }}
                                    >
                                      Kaldır ✕
                                    </button>
                                  </div>
                                )}
                              </div>
                              <input
                                type="text"
                                value={block.caption || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'caption', e.target.value)}
                                placeholder="Görsel alt yazısı / açıklama..."
                                className="super-admin-input"
                                style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                              />
                            </div>
                          )}
                          {block.type === 'GREETING' && (
                            <input
                              type="text"
                              value={block.text || ''}
                              onChange={(e) => handleUpdateBlockField(block.id, 'text', e.target.value)}
                              placeholder="Karşılama metni..."
                              className="super-admin-input"
                              style={{ fontSize: '0.75rem', padding: '5px 8px' }}
                            />
                          )}
                          {block.type === 'CONTENT' && (
                            <textarea
                              rows="2"
                              value={block.text || ''}
                              onChange={(e) => handleUpdateBlockField(block.id, 'text', e.target.value)}
                              placeholder="Duyuru veya açıklama paragrafı..."
                              className="super-admin-input"
                              style={{ fontSize: '0.75rem', padding: '5px 8px' }}
                            />
                          )}
                          {block.type === 'PACKAGE_INFO' && (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
                              <input
                                type="text"
                                value={block.planName || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'planName', e.target.value)}
                                placeholder="Paket Adı"
                                className="super-admin-input"
                                style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                              />
                              <input
                                type="text"
                                value={block.expiryDate || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'expiryDate', e.target.value)}
                                placeholder="Bitiş Tarihi"
                                className="super-admin-input"
                                style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                              />
                              <input
                                type="text"
                                value={block.daysRemaining || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'daysRemaining', e.target.value)}
                                placeholder="Kalan Gün"
                                className="super-admin-input"
                                style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                              />
                            </div>
                          )}
                          {block.type === 'CREDENTIALS' && (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                              <input
                                type="text"
                                value={block.loginEmail || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'loginEmail', e.target.value)}
                                placeholder="Kullanıcı / E-posta"
                                className="super-admin-input"
                                style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                              />
                              <input
                                type="text"
                                value={block.passwordText || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'passwordText', e.target.value)}
                                placeholder="Şifre"
                                className="super-admin-input"
                                style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                              />
                            </div>
                          )}
                          {block.type === 'BUTTON' && (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                              <input
                                type="text"
                                value={block.buttonText || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'buttonText', e.target.value)}
                                placeholder="Buton Metni"
                                className="super-admin-input"
                                style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                              />
                              <input
                                type="text"
                                value={block.buttonUrl || ''}
                                onChange={(e) => handleUpdateBlockField(block.id, 'buttonUrl', e.target.value)}
                                placeholder="Hedef URL"
                                className="super-admin-input"
                                style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                              />
                            </div>
                          )}
                          {block.type === 'FOOTER' && (
                            <textarea
                              rows="2"
                              value={block.footerText || ''}
                              onChange={(e) => handleUpdateBlockField(block.id, 'footerText', e.target.value)}
                              placeholder="Alt bilgi ve yasal metin..."
                              className="super-admin-input"
                              style={{ fontSize: '0.72rem', padding: '4px 6px' }}
                            />
                          )}
                        </div>
                      ))
                    )}
                  </div>

                  {/* Kolon 3: Canlı Önizleme */}
                  <div style={{ background: '#0b0f19', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 10, display: 'flex', flexDirection: 'column', gap: 6, minHeight: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 4 }}>
                      <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Eye style={{ width: 13, height: 13 }} />
                        <span>Canlı Görsel Önizleme</span>
                      </span>
                      <span style={{ fontSize: '0.62rem', color: '#64748b' }}>620px Responsive</span>
                    </div>
                    <div style={{ flex: 1, borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)', background: '#ffffff', minHeight: 0 }}>
                      <iframe
                        title="HTML Preview"
                        srcDoc={templateForm.html_content}
                        style={{ width: '100%', height: '100%', border: 'none' }}
                      />
                    </div>
                  </div>
                </div>
              ) : (
                /* HTML KOD EDİTÖRÜ MODU */
                <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 12, flex: 1, minHeight: 440, maxHeight: '55vh', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Code style={{ width: 13, height: 13, color: '#a78bfa' }} />
                      <span>HTML Kod Editörü</span>
                    </label>
                    <textarea
                      rows="18"
                      required
                      value={templateForm.html_content}
                      onChange={(e) => setTemplateForm({ ...templateForm, html_content: e.target.value })}
                      placeholder="<html><body>...</body></html>"
                      className="super-admin-input"
                      style={{ flex: 1, fontFamily: 'monospace', fontSize: '0.725rem', lineHeight: 1.4, whiteSpace: 'pre', background: '#0b0f19' }}
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Eye style={{ width: 13, height: 13, color: '#38bdf8' }} />
                      <span>Canlı E-Posta Önizlemesi (True Render)</span>
                    </label>
                    <div style={{ flex: 1, borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)', background: '#ffffff' }}>
                      <iframe
                        title="HTML Preview"
                        srcDoc={templateForm.html_content}
                        style={{ width: '100%', height: '100%', border: 'none' }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Alt Aksiyon Butonları & Madde 4 Modal İçi Test Gönder */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={templateForm.is_active}
                    onChange={(e) => setTemplateForm({ ...templateForm, is_active: e.target.checked })}
                  />
                  <span>Şablon Aktif</span>
                </label>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    type="button"
                    onClick={handleTestSendFromModal}
                    disabled={processingId === 'test-mail-modal'}
                    className="super-admin-btn-secondary"
                    style={{ background: 'rgba(56,189,248,0.15)', color: '#38bdf8', borderColor: 'rgba(56,189,248,0.3)', fontWeight: 700, padding: '7px 14px' }}
                    title="Şablonu kayıtlı bir adrese canlı test e-postası olarak gönderir"
                  >
                    {processingId === 'test-mail-modal' ? (
                      <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" />
                    ) : (
                      <Send style={{ width: 14, height: 14 }} />
                    )}
                    <span>Test E-postası Gönder</span>
                  </button>

                  <button type="button" onClick={() => setTemplateModalOpen(false)} className="super-admin-btn-secondary">
                    Vazgeç
                  </button>

                  <button type="submit" disabled={processingId === 'save-template'} className="super-admin-btn-corporate">
                    {processingId === 'save-template' ? <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" /> : <Check style={{ width: 14, height: 14 }} />}
                    <span>Şablonu Kaydet</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 10. ZAMANLAYICI (SCHEDULE) MODALI (Madde 2)               */}
      {/* ======================================================== */}
      {scheduleModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box" style={{ maxWidth: 640 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Clock style={{ width: 20, height: 20, color: '#fbbf24' }} />
                  <span>{editingSchedule ? `'${scheduleForm.name}' Zamanlama Kuralını Düzenle` : 'Yeni Bildirim Zamanlayıcısı Tanımla'}</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Kayıt anında veya paket bitimine 3 ay kala periyodik e-posta gönderim kuralı.
                </p>
              </div>
              <button onClick={() => setScheduleModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveSchedule} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Kural Adı *</label>
                <input
                  type="text"
                  required
                  value={scheduleForm.name}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, name: e.target.value })}
                  placeholder="Paket Bitimine 3 Ay Kala 15 Günde Bir Hatırlatıcı"
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Tetikleme Senaryosu *</label>
                  <select
                    value={scheduleForm.trigger_type}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, trigger_type: e.target.value })}
                    className="super-admin-select"
                  >
                    <option value="ON_REGISTRATION">Müşteri Kayıt Olduğunda (Tek Sefer)</option>
                    <option value="BEFORE_EXPIRATION_INTERVAL">Paket Bitişine 3 Ay Kala (Periyodik)</option>
                    <option value="CUSTOM_INTERVAL">Özel Gün Sıklığı</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>İletilecek Şablon *</label>
                  <select
                    value={scheduleForm.template_code}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, template_code: e.target.value })}
                    className="super-admin-select"
                  >
                    <option value="WELCOME_CUSTOMER">WELCOME_CUSTOMER (Hoş Geldiniz Şablonu)</option>
                    <option value="PACKAGE_EXPIRATION_REMINDER">PACKAGE_EXPIRATION_REMINDER (3 Ay Bitiş Hatırlatıcı)</option>
                    {emailTemplates.filter(t => !['WELCOME_CUSTOMER', 'PACKAGE_EXPIRATION_REMINDER'].includes(t.code)).map(t => (
                      <option key={t.id} value={t.code}>{t.code} - {t.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {scheduleForm.trigger_type !== 'ON_REGISTRATION' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, padding: 10, borderRadius: 8, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Kaç Gün Kala Başlasın?</label>
                    <input
                      type="number"
                      value={scheduleForm.target_lead_days}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, target_lead_days: Number(e.target.value) })}
                      placeholder="90 (3 Ay)"
                      className="super-admin-input"
                    />
                    <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Varsayılan: 90 gün (3 ay)</span>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: '#cbd5e1', marginBottom: 4 }}>Gönderim Sıklığı (Gün)?</label>
                    <input
                      type="number"
                      value={scheduleForm.frequency_days}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, frequency_days: Number(e.target.value) })}
                      placeholder="15 (15 Günde Bir)"
                      className="super-admin-input"
                    />
                    <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Varsayılan: 15 günde bir</span>
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={scheduleForm.is_active}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, is_active: e.target.checked })}
                  />
                  <span>Zamanlayıcı Aktif</span>
                </label>

                <div style={{ display: 'flex', gap: 10 }}>
                  <button type="button" onClick={() => setScheduleModalOpen(false)} className="super-admin-btn-secondary">
                    Vazgeç
                  </button>
                  <button type="submit" disabled={processingId === 'save-sched'} className="super-admin-btn-corporate">
                    {processingId === 'save-sched' ? <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" /> : <Check style={{ width: 14, height: 14 }} />}
                    <span>Zamanlayıcıyı Kaydet</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
