import React, { useState, useEffect, useRef } from 'react';
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
  ChevronDown,
  ChevronLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
  User,
  Settings,
  Tag,
  Briefcase,
  GraduationCap,
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
  Image as ImageIcon,
  PauseCircle,
  PlayCircle,
  Globe,
  Menu,
  Coins,
  Bot
} from 'lucide-react';
import { api } from '../api';
import { confirmDialog, notify, promptDialog, toast } from '../ui/feedback';
import ThemeToggle from '../ui/ThemeToggle';
import OdooProductPicker from './OdooProductPicker';
import CatalogAdmin from './catalog/CatalogAdmin';
import EmailTemplateBuilder from './email/EmailTemplateBuilder';
import { compileBlocksToHtml, htmlToBlocks } from './email/emailBlocks';
import { ModelSettingsPanel, PlatformAssistantPanel, PlatformUsagePanel, TenantCreditsModal } from './ai/PlatformAIPanels';
import PlatformDashboard, { HealthBadge, SystemHealthPanel, usePlatformHealth } from './dashboard/PlatformDashboard';
import LlmPricing from './ai/LlmPricing';

const TAB_SLUG_MAP = {
  DASHBOARD: 'dashboard',
  LEADS: 'leads',
  TENANTS: 'tenants',
  SECTORS: 'sectors',
  PROFESSIONS: 'professions',
  CATALOG: 'catalog',
  PERMISSIONS: 'permissions',
  ROLES: 'roles',
  PLANS: 'plans',
  EMAIL_TEMPLATES: 'email-templates',
  SCHEDULES: 'schedules',
  AI_MODEL_SETTINGS: 'ai-models',
  AI_ASSISTANT: 'ai-assistant',
  MODELS: 'models',
  LLM_PRICES: 'llm-prices'
};

const SLUG_TAB_MAP = {
  'dashboard': 'DASHBOARD',
  'leads': 'LEADS',
  'tenants': 'TENANTS',
  'sectors': 'SECTORS',
  'professions': 'PROFESSIONS',
  'catalog': 'CATALOG',
  'permissions': 'PERMISSIONS',
  'roles': 'ROLES',
  'plans': 'PLANS',
  'email-templates': 'EMAIL_TEMPLATES',
  'schedules': 'SCHEDULES',
  'ai-models': 'AI_MODEL_SETTINGS',
  'ai-assistant': 'AI_ASSISTANT',
  'models': 'MODELS',
  'llm-prices': 'LLM_PRICES'
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

export default function SuperAdminConsole({ 
  currentUser, 
  onLogout, 
  onSwitchToWorkspace, 
  onSwitchToCompanyAdmin,
  onGoToOfficialSite, 
  onUpdateCurrentUser 
}) {
  // Sol Menü Daraltma / Genişletme State'i (Madde 4)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  // Sol menü grupları açılıp kapanabilir; tercih bu tarayıcıda hatırlanır
  const [closedNavGroups, setClosedNavGroups] = useState(() => {
    try { return JSON.parse(localStorage.getItem('recorion_sa_nav_groups') || '{}'); } catch { return {}; }
  });
  const toggleNavGroup = (key) => setClosedNavGroups((prev) => {
    const next = { ...prev, [key]: !prev[key] };
    try { localStorage.setItem('recorion_sa_nav_groups', JSON.stringify(next)); } catch { /* depolama kapalı */ }
    return next;
  });
  // Tablet/telefonda sol menü açılır çekmece olarak çalışır
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const isSavingTenantRef = useRef(false);

  // Aktif Menü Sekmesi (URL Hash Senkronize)
  const [activeTab, setActiveTab] = useState(getTabFromHash);
  // ADIM 9.4: gerçek sistem durumu (başlık rozeti ve altyapı paneli)
  const platformHealth = usePlatformHealth(); 
  // 'DASHBOARD' | 'LEADS' | 'TENANTS' | 'EMAIL_TEMPLATES' | 'SCHEDULES' | 'PERMISSIONS' | 'MODELS' | 'PLANS' | 'NACE' | 'TITLES' | 'AI_MODEL_SETTINGS'

  const switchTab = (newTab, options = {}) => {
    setActiveTab(newTab);
    setMobileNavOpen(false);
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
  const [roleViewMode, setRoleViewMode] = useState('KANBAN');
  const [planViewMode, setPlanViewMode] = useState('KANBAN');
  const [modelViewMode, setModelViewMode] = useState('LIST');
  const [naceViewMode, setNaceViewMode] = useState('LIST');
  const [titleViewMode, setTitleViewMode] = useState('KANBAN');
  const [templateViewMode, setTemplateViewMode] = useState('KANBAN');
  const [scheduleViewMode, setScheduleViewMode] = useState('KANBAN');

  // E-Posta Şablonu Drag & Drop Builder State'leri (Madde 5)
  const [templateEditorTab, setTemplateEditorTab] = useState('BUILDER'); // 'BUILDER' | 'CODE'
  const [templateCanvasBlocks, setTemplateCanvasBlocks] = useState([]);

  // Ortak Segmentli Kanban / Liste Seçici Bileşeni (Madde 2)
  const renderViewModeToggle = (mode, setMode) => (
    <div style={{ display: 'flex', background: 'rgb(var(--rgb-ov) / 0.06)', padding: 3, borderRadius: 8, border: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
      <button
        type="button"
        onClick={() => setMode('KANBAN')}
        className="super-admin-btn-secondary"
        style={{
          padding: '5px 10px',
          fontSize: '0.75rem',
          border: 'none',
          background: mode === 'KANBAN' ? '#7134e2' : 'transparent',
          color: mode === 'KANBAN' ? '#fff' : 'var(--nt-94a3b8)'
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
          color: mode === 'LIST' ? '#fff' : 'var(--nt-94a3b8)'
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
  const [professions, setProfessions] = useState([]);
  const [systemSettings, setSystemSettings] = useState({ default_manifesto_model: 'deepseek-v4.1-flash' });
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [sectors, setSectors] = useState([]);

  // Arama & Filtre State'leri
  const [searchQuery, setSearchQuery] = useState('');
  const [professionsFilterSector, setProfessionsFilterSector] = useState('');
  const [professionSearch, setProfessionSearch] = useState('');
  const [professionViewMode, setProfessionViewMode] = useState('TABLE');
  const [permissionModuleFilter, setPermissionModuleFilter] = useState('ALL');

  // UI & Geri Bildirim
  const [loading, setLoading] = useState(false);
  // İşlem geri bildirimleri doğrudan ortak bildirim (toast) sistemiyle gösterilir.
  // (Önceden state'e yazılıyordu; ardından çağrılan loadAllData() mesajı aynı anda
  // sıfırladığı için başarı mesajları hiç görünmüyordu.) null ile çağrı etkisizdir.
  // Şifre içeren mesajlar okunup kopyalanabilsin diye daha uzun süre ekranda kalır.
  const setActionFeedback = (feedback) => {
    if (!feedback?.text) return;
    const type = ['success', 'error', 'warning', 'info'].includes(feedback.type) ? feedback.type : 'info';
    const duration = /şifre|sifre|password/i.test(feedback.text) ? 30000 : undefined;
    toast[type](feedback.text, { duration });
  };
  const [processingId, setProcessingId] = useState(null);
  const [creditTenant, setCreditTenant] = useState(null);
  const [syncingModels, setSyncingModels] = useState(false);
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

  // 2.1 Yetki Rolleri Detay / Ekleme Modal (Madde 1)
  const [roles, setRoles] = useState([]);
  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [roleForm, setRoleForm] = useState({
    name: '',
    description: '',
    permissions: [],
    is_system: true
  });
  const [rolePermissionSearch, setRolePermissionSearch] = useState('');
  const [rolePermissionModuleFilter, setRolePermissionModuleFilter] = useState('ALL');

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
    sectors: [],
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
    sectors: [],
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
    allowed_models: [],
    can_create_custom_titles: false,
    features: { can_change_llm: false, can_edit_role_prompt: false, can_upload_title_documents: false, ocr_enabled: false, max_documents_per_agent: 20 },
    odoo_product_id: '',
    is_active: true
  });

  // 4.1 E-Posta Şablonu Modal (Madde 1)
  const [templateModalOpen, setTemplateModalOpen] = useState(false);
  // Görsel editör blokları HTML ile eşleşiyor mu (HTML elle düzenlenince false olur)
  const [templateBlocksInSync, setTemplateBlocksInSync] = useState(true);
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

  // 6. Meslek Grubu Tanımı Modal (Madde 1)
  const [professionModalOpen, setProfessionModalOpen] = useState(false);
  const [editingProfession, setEditingProfession] = useState(null);
  const [professionForm, setProfessionForm] = useState({
    code: '',
    sector_code: '',
    name: '',
    description: '',
    is_active: true
  });

  // 7. Sektör Tanımlama Modal (Madde 1)
  const [sectorModalOpen, setSectorModalOpen] = useState(false);
  const [editingSector, setEditingSector] = useState(null);
  const [sectorViewMode, setSectorViewMode] = useState('TABLE');
  const [sectorForm, setSectorForm] = useState({
    code: '',
    name: '',
    description: '',
    icon: '',
    image_url: '',
    is_active: true
  });

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
        } else if (roleModalOpen) {
          setRoleModalOpen(false);
        } else if (modelModalOpen) {
          setModelModalOpen(false);
        } else if (professionModalOpen) {
          setProfessionModalOpen(false);
        } else if (sectorModalOpen) {
          setSectorModalOpen(false);
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
    roleModalOpen,
    modelModalOpen,
    professionModalOpen,
    sectorModalOpen,
    testEmailModalOpen
  ]);

  // ================= VERİLERİ YÜKLEME =================
  const loadAllData = async () => {
    setLoading(true);
    setActionFeedback(null);
    try {
      const [lData, tData, pData, rData, mData, plData, sData, etData, scData, secData, profData] = await Promise.all([
        api.getLeads().catch(() => []),
        api.getTenants().catch(() => []),
        api.getPermissions().catch(() => []),
        api.getSystemRoles().catch(() => []),
        api.getModels().catch(() => []),
        api.getPlans().catch(() => []),
        api.getSystemSettings().catch(() => ({ default_manifesto_model: 'deepseek-v3' })),
        api.getEmailTemplates().catch(() => []),
        api.getSchedules().catch(() => []),
        api.getSectors().catch(() => []),
        api.getProfessions().catch(() => [])
      ]);

      setLeads(lData || []);
      setTenants(tData || []);
      setPermissions(pData || []);
      setRoles(rData || []);
      setModels(mData || []);
      setPlans(plData || []);
      setSystemSettings(sData || { default_manifesto_model: 'deepseek-v3' });
      setEmailTemplates(etData || []);
      setSchedules(scData || []);
      setSectors(secData || []);
      setProfessions(profData || []);

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
    if (!(await confirmDialog({
      title: 'Başvuruyu Onayla',
      message: `'${lead.company_name}' şirketi 1 yıllık paketle aktifleştirilecek, Odoo siparişi onaylanacak ve ${lead.contact_email} adresine aktivasyon e-postası gönderilecek. Devam edilsin mi?`,
      confirmText: 'Onayla ve Aktif Et',
    }))) return;
    try {
      setProcessingId(lead.id);
      const res = await api.approveLead(lead.id);
      setActionFeedback({ type: res.activation_email_sent ? 'success' : 'warning', text: res.message });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Onay işlemi başarısız: ' + (err.message || '') });
    } finally {
      setProcessingId(null);
    }
  };

  const handleRejectLead = async (lead) => {
    const reason = await promptDialog({
      title: 'Başvuruyu Reddet',
      message: `'${lead.company_name}' başvurusu reddedilecek ve müşteriye aşağıdaki gerekçeyle e-posta gönderilecek. Odoo teklifi iptal edilir.`,
      defaultValue: '',
      confirmText: 'Reddet',
    });
    if (reason === null) return;
    if (reason.trim().length < 5) {
      toast.warning('Lütfen müşteriye iletilecek en az 5 karakterlik bir gerekçe yazın.');
      return;
    }
    try {
      setProcessingId(lead.id);
      const res = await api.rejectLead(lead.id, reason.trim());
      setActionFeedback({ type: 'success', text: res.message + (res.email_sent ? ' Müşteriye e-posta gönderildi.' : ' E-posta gönderilemedi.') });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Ret işlemi başarısız: ' + (err.message || '') });
    } finally {
      setProcessingId(null);
    }
  };

  const handleRetryLeadOdoo = async (lead) => {
    try {
      setProcessingId(lead.id);
      const res = await api.retryLeadOdooSync(lead.id);
      setActionFeedback(res.success
        ? { type: 'success', text: `Odoo senkronizasyonu tamamlandı${res.odoo_order_name ? `: ${res.odoo_order_name}` : ''}.` }
        : { type: 'error', text: `Odoo senkronizasyonu başarısız: ${res.odoo_sync_error || ''}` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Odoo senkronizasyonu başarısız: ' + (err.message || '') });
    } finally {
      setProcessingId(null);
    }
  };

  // Başvurunun Odoo durumu: senkron, işleniyor, hata (yeniden dene) veya kapalı
  const renderLeadOdoo = (lead) => {
    const status = lead.odoo_sync_status;
    if (lead.odoo_order_name) {
      return (
        <span style={{ display: 'inline-flex', flexDirection: 'column', gap: 2 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--ac-34d399)', fontWeight: 800 }}>{lead.odoo_order_name}</span>
          {lead.odoo_partner_name && (
            <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }} title="Siparişin açıldığı Odoo müşterisi">
              Odoo: {lead.odoo_partner_name}
            </span>
          )}
        </span>
      );
    }
    if (status === 'FAILED') {
      return (
        <button type="button" className="ui-btn ui-btn-ghost ui-btn-sm" onClick={() => handleRetryLeadOdoo(lead)}
                disabled={processingId === lead.id} title={lead.odoo_sync_error || 'Odoo hatası'}
                style={{ color: 'var(--ac-f87171)', padding: '2px 6px', minHeight: 0 }}>
          ⚠ Yeniden dene
        </button>
      );
    }
    if (status === 'SKIPPED') return <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Odoo: kapalı</span>;
    return <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Odoo: işleniyor…</span>;
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
        sectors: details.tenant.sectors || [],
        professions: details.tenant.professions || [],
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
        sectors: tenantEditForm.sectors || [],
        professions: tenantEditForm.professions || [],
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
      notify("Lütfen önce şirket adını giriniz.");
      return;
    }
    try {
      setIsGeneratingDetailManifesto(true);
      const res = await api.generateManifesto({
        company_name: tenantEditForm.name,
        sectors: tenantEditForm.sectors || [],
        professions: tenantEditForm.professions || [],
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
  const handleSyncEvrenModels = async () => {
    setSyncingModels(true);
    try {
      const res = await api.syncEvrenModels();
      setModels(await api.getModels());
      const parts = [`${res.updated.length} model güncellendi`];
      if (res.added.length) parts.push(`${res.added.length} yeni model PASİF olarak eklendi (${res.added.join(', ')}); katsayısını belirleyip aktifleştirin`);
      if (res.missing_in_evren.length) parts.push(`EVREN'de artık bulunmayan: ${res.missing_in_evren.join(', ')}`);
      toast.success(parts.join(' · '));
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSyncingModels(false);
    }
  };

  const handleToggleTenantStatus = async (t) => {
    const isCurrentlyActive = t.is_active;
    const confirmMsg = isCurrentlyActive
      ? `'${t.name}' şirketinin kartını PASİFE almak istediğinize emin misiniz?\n\nPasife alındığında şirket yöneticisi ve kullanıcıları sisteme giriş yapamayacaktır.`
      : `'${t.name}' şirketinin kartını tekrar AKTİFE almak istediğinize emin misiniz?\n\nAktife alındığında şirket kullanıcılarının sisteme erişimi açılacaktır.`;

    if (!(await confirmDialog({ message: confirmMsg }))) return;

    try {
      setProcessingId('toggle-status-' + t.id);
      const res = await api.toggleTenantStatus(t.id);
      const newStatus = res.is_active;
      setActionFeedback({
        type: 'success',
        text: `✓ ${res.message || `'${t.name}' şirket durumu başarıyla güncellendi.`}`
      });
      notify(`✓ İşlem Başarılı!\n\n${res.message || `'${t.name}' şirketi ${newStatus ? 'Aktif' : 'Pasif'} duruma getirildi.`}`);

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
      notify(`⚠️ Hata Alındı!\n\nŞirket durumu değiştirilemedi: ${err.message || 'Bilinmeyen hata'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Ana Şirket Kontrolü (RECDx Teknoloji & Dijital Dönüşüm Danışmanlığı LTD. Şirketi Silinemez)
  const isMainCompany = (tenant) => {
    if (!tenant) return false;
    const slug = (tenant.slug || '').toLowerCase();
    const name = (tenant.name || '').toLowerCase();
    return slug === 'recdx' || slug === 'recdx_hq' || name.includes('recdx teknoloji') || name.includes('dijital dönüşüm');
  };

  // Şirket Silme İşlemi (Madde 1: Departman, AI Ajan veya Proje yoksa silinebilir, Ana Şirket Silinemez)
  const handleDeleteTenant = async (t) => {
    if (!t?.id) return;
    if (isMainCompany(t)) {
      notify("⚠️ RECDx Teknoloji & Dijital Dönüşüm Danışmanlığı LTD. Şirketi sistemin ana şirketidir ve SİLİNEMEZ!");
      return;
    }
    const confirmText = `'${t.name}' şirketini sistemden kalıcı olarak SİLMEK istediğinize emin misiniz?\n\n⚠️ Dikkat: Bu işlem geri alınamaz!\n(Şirket içerisinde tanımlı departman, AI ajanı veya proje bulunması halinde silme işlemi engellenecektir.)`;
    if (!(await confirmDialog({ message: confirmText }))) return;

    try {
      setProcessingId('delete-tenant-' + t.id);
      const res = await api.deleteTenant(t.id);
      setActionFeedback({
        type: 'success',
        text: `✓ ${res.message || `'${t.name}' şirketi başarıyla silindi.`}`
      });
      notify(`✓ İşlem Başarılı!\n\n${res.message || `'${t.name}' şirketi sistemden silindi.`}`);

      // Eğer detay modalı açık ise kapat
      if (selectedTenantDetails?.tenant?.id === t.id) {
        setTenantDetailModalOpen(false);
        setSelectedTenantDetails(null);
      }

      await loadAllData();
    } catch (err) {
      setActionFeedback({
        type: 'error',
        text: 'Şirket silinemedi: ' + err.message
      });
      notify(`⚠️ Şirket Silinemedi!\n\nSebep: ${err.message || 'Bilinmeyen hata'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Manuel Paket Süre Dolum Hatırlatıcı Gönder (Madde 14)
  const handleSendManualReminder = async (t) => {
    if (!(await confirmDialog({ message: `'${t.name}' şirketine (${t.contact_email}) paket kullanım süresi hatırlatıcı e-postası göndermek istiyor musunuz?` }))) return;
    try {
      setProcessingId('reminder-' + t.id);
      const res = await api.sendManualReminder(t.id);
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
      notify(`✓ E-Posta Başarıyla Gönderildi!\n\n${res.message || `'${t.name}' şirketine hatırlatıcı e-postası başarıyla iletildi.`}`);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Hatırlatıcı e-postası gönderilemedi: ' + err.message });
      notify(`⚠️ E-Posta Gönderilemedi!\n\nHata Alındı: ${err.message || 'Bilinmeyen bir hata oluştu.'}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Kayıtlı Şirketler Ekranından Hızlı Onaylama
  const handleQuickApproveTenant = async (t) => {
    if (!(await confirmDialog({ message: `'${t.name}' şirketinin üyeliğini ve 1 yıllık kurumsal paketini onaylamak istiyor musunuz?` }))) return;
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
      notify(`✓ Zamanlayıcı E-Postaları Başarıyla Gönderildi!\n\n${res.message || 'Kural işletildi.'}`);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Zamanlayıcı çalıştırılamadı: ' + err.message });
      notify(`⚠️ Zamanlayıcı E-Postası Gönderilemedi!\n\nHata: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  // Sektör & Meslek Grubu Yardımcıları (Yeni Müşteri & Müşteri Düzenleme)
  const handleToggleSectorNewTenant = (sectorCode) => {
    const current = newTenantForm.sectors || [];
    const isSelected = current.includes(sectorCode);
    const updatedSectors = isSelected ? current.filter(s => s !== sectorCode) : [...current, sectorCode];
    // Sektör kaldırıldıysa ona ait seçili meslekleri de temizle
    const updatedProfessions = isSelected
      ? (newTenantForm.professions || []).filter(p => {
          const profObj = professions.find(pr => (typeof p === 'object' ? pr.code === p.code : pr.code === p));
          return profObj ? profObj.sector_code !== sectorCode : true;
        })
      : (newTenantForm.professions || []);

    setNewTenantForm(prev => ({
      ...prev,
      sectors: updatedSectors,
      professions: updatedProfessions
    }));
  };

  const handleToggleProfessionNewTenant = (profCode) => {
    const current = newTenantForm.professions || [];
    const isSelected = current.includes(profCode);
    setNewTenantForm(prev => ({
      ...prev,
      professions: isSelected ? current.filter(p => p !== profCode) : [...current, profCode]
    }));
  };

  const handleClearAllSectorsNewTenant = () => {
    setNewTenantForm(prev => ({
      ...prev,
      sectors: [],
      professions: []
    }));
  };

  const handleToggleSectorTenantEdit = (sectorCode) => {
    const current = tenantEditForm.sectors || [];
    const isSelected = current.includes(sectorCode);
    const updatedSectors = isSelected ? current.filter(s => s !== sectorCode) : [...current, sectorCode];
    const updatedProfessions = isSelected
      ? (tenantEditForm.professions || []).filter(p => {
          const profObj = professions.find(pr => (typeof p === 'object' ? pr.code === p.code : pr.code === p));
          return profObj ? profObj.sector_code !== sectorCode : true;
        })
      : (tenantEditForm.professions || []);

    setTenantEditForm(prev => ({
      ...prev,
      sectors: updatedSectors,
      professions: updatedProfessions
    }));
  };

  const handleToggleProfessionTenantEdit = (profCode) => {
    const current = tenantEditForm.professions || [];
    const isSelected = current.includes(profCode);
    setTenantEditForm(prev => ({
      ...prev,
      professions: isSelected ? current.filter(p => p !== profCode) : [...current, profCode]
    }));
  };

  const handleClearAllSectorsTenantEdit = () => {
    setTenantEditForm(prev => ({
      ...prev,
      sectors: [],
      professions: []
    }));
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
      sectors: [],
      professions: []
    });
    setNewTenantManifesto('');
    setNewTenantModalOpen(true);
  };

  const handleGenerateManifestoForNewTenant = async () => {
    if (!newTenantForm.name.trim()) {
      notify("Lütfen önce şirket adını giriniz.");
      return;
    }
    try {
      setIsGeneratingNewTenantManifesto(true);
      const res = await api.generateManifesto({
        company_name: newTenantForm.name,
        sectors: newTenantForm.sectors || [],
        professions: newTenantForm.professions || [],
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

  const handleSaveNewTenant = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (isSavingTenantRef.current) return;
    if (!newTenantForm.name.trim() || !newTenantForm.contact_email.trim()) {
      notify("Lütfen şirket adı ve e-posta adresini doldurunuz.");
      return;
    }

    // Madde 2: Resmi/Official kurumsal e-posta zorunluluğu (Gmail, Hotmail vb. engelleme)
    const publicMailDomains = [
      'gmail.com', 'googlemail.com', 'hotmail.com', 'hotmail.com.tr', 'outlook.com', 
      'outlook.com.tr', 'live.com', 'msn.com', 'yahoo.com', 'yahoo.com.tr', 'ymail.com', 
      'yandex.com', 'yandex.com.tr', 'ya.ru', 'icloud.com', 'mail.ru', 'proton.me', 
      'protonmail.com', 'zoho.com', 'gmx.com', 'aol.com'
    ];
    const emailParts = newTenantForm.contact_email.trim().toLowerCase().split('@');
    const domain = (emailParts[1] || '').trim();
    if (!domain || publicMailDomains.includes(domain) || publicMailDomains.some(d => domain.endsWith('.' + d))) {
      notify(`⚠️ Kurumsal / Official E-Posta Zorunluluğu!\n\nMüşteri kaydı için şirkete ait resmi (official) bir şirket e-posta adresi gereklidir.\nGenel/ücretsiz (${domain || 'geçersiz'}) e-posta sağlayıcıları kabul edilmemektedir.\nLütfen 'adsoyad@sirketiniz.com' veya 'info@sirketiniz.com' gibi bir kurumsal adres giriniz.`);
      return;
    }

    isSavingTenantRef.current = true;
    try {
      setProcessingId('create-new-tenant');
      const res = await api.adminCreateTenant({
        ...newTenantForm,
        sector_manifesto: newTenantManifesto,
        activate_package: false,
        send_welcome_email: false
      });
      const companyName = newTenantForm.name;
      const adminName = res.admin_name || newTenantForm.admin_name || 'Yetkili';
      const adminEmail = res.admin_email || newTenantForm.contact_email;

      // 1. Yeni müşteri modalını kapat
      setNewTenantModalOpen(false);

      // 2. Formu sıfırla
      setNewTenantForm({
        name: '',
        tax_id: '',
        tax_office: '',
        contact_email: '',
        phone: '',
        website: '',
        plan_id: '',
        admin_name: '',
        admin_password: '',
        sectors: [],
        nace_codes: [],
        address: ''
      });
      setNewTenantManifesto('');

      // 3. Verileri tazele
      await loadAllData();

      // 4. Kullanıcı İsteği: "bir daha kullanıcı ekleme ekranı açma"
      // İkinci modalı (handleOpenTenantDetails) KESİNLİKLE açmıyoruz!
      setActionFeedback({
        type: 'success',
        text: `✓ '${companyName}' kurumu ve yetkili yöneticisi (${adminName} - ${adminEmail}) başarıyla sisteme kaydedildi.`
      });
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Müşteri ekleme hatası: ' + err.message });
      notify(`⚠️ Müşteri Kaydedilemedi!\n\nHata: ${err.message || 'Bilinmeyen hata'}`);
    } finally {
      setProcessingId(null);
      isSavingTenantRef.current = false;
    }
  };

  // Müşteriye Manuel Hoş Geldiniz E-Postası Gönderme (Madde 1)
  const handleSendManualWelcome = async (t) => {
    if (!t?.id) return;
    try {
      setProcessingId('welcome-' + t.id);
      const res = await api.sendManualWelcome(t.id);
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
      notify(`✓ E-Posta Başarıyla Gönderildi!\n\n${res.message || `'${t.name}' şirketine kurumsal Hoş Geldiniz e-postası başarıyla iletildi.`}`);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Hoş geldiniz e-postası gönderilemedi: ' + err.message });
      notify(`⚠️ E-Posta Gönderilemedi!\n\nHata Alındı: ${err.message || 'Bilinmeyen bir hata oluştu.'}`);
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
      { id: 'b_5', type: 'CREDENTIALS', loginEmail: '{{login_email}}', passwordText: '{{password_instruction}}' },
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
      // Kayıtlı şablon: blok yapısı saklanmışsa görsel editörde, yoksa HTML olarak açılır.
      // (Önceden varsayılan bloklar yükleniyor ve ilk düzenlemede kayıtlı HTML'in üzerine yazılıyordu.)
      // Blok yapısı yoksa (HTML olarak kayıtlı şablon) HTML bloklara çevrilir; HTML, ilk görsel
      // düzenlemeye kadar değişmez. Kaydedilmeden hiçbir şey değişmez.
      const savedBlocks = Array.isArray(tmpl.builder_blocks) && tmpl.builder_blocks.length ? tmpl.builder_blocks : null;
      setTemplateCanvasBlocks(savedBlocks || htmlToBlocks(tmpl.html_content || ''));
      setTemplateBlocksInSync(!!savedBlocks);
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
        variables: ['company_name', 'contact_name', 'plan_name', 'package_expiry_date', 'days_remaining', 'login_email', 'password_instruction', 'action_url', 'login_url'],
        is_active: true
      });
      setTemplateCanvasBlocks(defaultBlocks);
      setTemplateBlocksInSync(true);
      setTemplateEditorTab('BUILDER');
    }
    setTemplateModalOpen(true);
  };

  const handleTestSendFromModal = async () => {
    const toEmail = (await promptDialog({ message: `'${templateForm.name || "E-Posta"}' şablonunu test etmek için alıcı e-posta adresi giriniz:`, defaultValue: currentUser?.email || 'cuneyterdil@recdx.com' }));
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
        notify(`✓ Test e-postası '${toEmail}' adresine başarıyla gönderildi!`);
      } else {
        if (!templateForm.code.trim() || !templateForm.name.trim() || !templateForm.subject.trim()) {
          notify("Lütfen önce şablon kodu, adı ve konusunu doldurunuz.");
          return;
        }
        const created = await api.createEmailTemplate(templateForm);
        setEditingTemplate(created);
        const res = await api.testSendEmailTemplate(created.id, { to_email: toEmail });
        setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
        notify(`✓ Şablon kaydedildi ve test e-postası '${toEmail}' adresine iletildi!`);
        await loadAllData();
      }
    } catch (err) {
      notify(`⚠️ Test e-postası iletilemedi:\n\n${err.message}`);
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
        await api.updateEmailTemplate(editingTemplate.id, { ...templateForm, builder_blocks: templateBlocksInSync && templateCanvasBlocks.length ? templateCanvasBlocks : null });
        setActionFeedback({ type: 'success', text: `✓ '${templateForm.name}' e-posta şablonu güncellendi.` });
      } else {
        await api.createEmailTemplate({ ...templateForm, builder_blocks: templateBlocksInSync && templateCanvasBlocks.length ? templateCanvasBlocks : null });
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
    if (!(await confirmDialog({ message: `'${tmpl.name}' (${tmpl.code}) e-posta şablonunu silmek istediğinize emin misiniz?\n\nNot: Bu şablon aktif zamanlayıcılarda veya sistem akışında kullanılmıyorsa silinebilir.`, danger: true, confirmText: 'Evet, devam et' }))) return;
    try {
      setProcessingId('del-tmpl-' + tmpl.id);
      await api.deleteEmailTemplate(tmpl.id);
      setActionFeedback({ type: 'success', text: `✓ '${tmpl.name}' şablonu silindi.` });
      await loadAllData();
    } catch (err) {
      notify(`⚠️ E-POSTA ŞABLONU SİLİNEMEZ!\n\n${err.message}`);
      setActionFeedback({ type: 'error', text: 'Şablon silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleTestSendTemplate = async (tmpl) => {
    const toEmail = (await promptDialog({ message: `'${tmpl.name}' şablonunu test etmek için alıcı e-posta adresi giriniz:`, defaultValue: currentUser?.email || 'cuneyterdil@recdx.com' }));
    if (!toEmail) return;
    try {
      setProcessingId('test-mail-' + tmpl.id);
      const res = await api.testSendEmailTemplate(tmpl.id, { to_email: toEmail });
      setActionFeedback({ type: 'success', text: `✓ ${res.message}` });
      notify(`✓ Test E-Postası Başarıyla Gönderildi!\n\nAlıcı: ${toEmail}\n${res.message || 'E-posta SMTP üzerinden başarıyla iletildi.'}`);
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Test e-postası gönderilemedi: ' + err.message });
      notify(`⚠️ Test E-Postası Gönderilemedi!\n\nHata Alındı: ${err.message || 'Bilinmeyen hata'}`);
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
    if (!(await confirmDialog({ message: `'${sched.name}' zamanlama kuralını silmek istediğinize emin misiniz?`, danger: true, confirmText: 'Evet, devam et' }))) return;
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
      notify(`✓ Yönetici ve Müşteri Kartı Güncellendi!\n\n${res.message || 'Yönetici bilgileri ve müşteri kartı başarıyla güncellendi.'}`);
      setTenantAdminForm(prev => ({ ...prev, new_password: '' }));
      setTenantEditForm(prev => ({
        ...prev,
        contact_email: tenantAdminForm.email,
        phone: tenantAdminForm.phone || prev.phone
      }));
      // Madde 1: Yönetici kaydedilince modal ekranı otomatik kapatılır
      setTenantDetailModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Yönetici güncelleme hatası: ' + err.message });
      notify(`⚠️ Yönetici Kaydedilemedi!\n\nHata: ${err.message || 'Bilinmeyen hata'}`);
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
    if (!(await confirmDialog({ message: `'${perm.name}' (${perm.code}) iznini silmek istediğinize emin misiniz?`, danger: true, confirmText: 'Evet, devam et' }))) return;
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

  // ================= 4.1 YETKİ ROLLERİ CRUD (Madde 1) =================
  const handleOpenRoleModal = (role = null) => {
    if (role) {
      setEditingRole(role);
      setRoleForm({
        name: role.name,
        description: role.description || '',
        permissions: [...(role.permissions || [])],
        is_system: role.is_system !== undefined ? role.is_system : true
      });
    } else {
      setEditingRole(null);
      setRoleForm({
        name: '',
        description: '',
        permissions: [],
        is_system: true
      });
    }
    setRolePermissionSearch('');
    setRolePermissionModuleFilter('ALL');
    setRoleModalOpen(true);
  };

  const handleTogglePermissionInRole = (permCode) => {
    setRoleForm(prev => {
      const current = prev.permissions || [];
      if (current.includes(permCode)) {
        return { ...prev, permissions: current.filter(c => c !== permCode) };
      } else {
        return { ...prev, permissions: [...current, permCode] };
      }
    });
  };

  const handleSelectAllPermissionsInCatalog = (listToSelect) => {
    const codesToAdd = listToSelect.map(p => p.code);
    setRoleForm(prev => {
      const merged = Array.from(new Set([...(prev.permissions || []), ...codesToAdd]));
      return { ...prev, permissions: merged };
    });
  };

  const handleDeselectAllPermissionsInCatalog = (listToDeselect) => {
    const codesToRemove = new Set(listToDeselect.map(p => p.code));
    setRoleForm(prev => ({
      ...prev,
      permissions: (prev.permissions || []).filter(c => !codesToRemove.has(c))
    }));
  };

  const handleSaveRole = async (e) => {
    e.preventDefault();
    if (!roleForm.name.trim()) {
      notify("Lütfen rol adını giriniz.");
      return;
    }
    try {
      setProcessingId('save-role');
      if (editingRole) {
        await api.updateSystemRole(editingRole.id, {
          name: roleForm.name,
          description: roleForm.description,
          permissions: roleForm.permissions,
          is_system: roleForm.is_system
        });
        setActionFeedback({ type: 'success', text: `✓ '${roleForm.name}' yetki rolü güncellendi.` });
      } else {
        await api.createSystemRole({
          name: roleForm.name,
          description: roleForm.description,
          permissions: roleForm.permissions,
          is_system: roleForm.is_system
        });
        setActionFeedback({ type: 'success', text: `✓ '${roleForm.name}' yetki rolü oluşturuldu.` });
      }
      setRoleModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Rol kaydedilemedi: ' + err.message });
      notify(`⚠️ Rol Kaydedilemedi!\n\nHata: ${err.message || 'Bilinmeyen hata'}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteRole = async (role) => {
    if (!(await confirmDialog({ message: `'${role.name}' yetki rolünü silmek istediğinize emin misiniz?`, danger: true, confirmText: 'Evet, devam et' }))) return;
    try {
      setProcessingId('del-role-' + role.id);
      await api.deleteSystemRole(role.id);
      setActionFeedback({ type: 'success', text: `✓ '${role.name}' yetki rolü silindi.` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Rol silinemedi: ' + err.message });
      notify(`⚠️ Rol Silinemedi!\n\nSebep: ${err.message || 'Bilinmeyen hata'}`);
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
        allowed_models: plan.allowed_models || [],
        can_create_custom_titles: !!plan.can_create_custom_titles,
        features: { ...{ can_change_llm: false, can_edit_role_prompt: false, can_upload_title_documents: false, ocr_enabled: false, max_documents_per_agent: 20 }, ...(plan.features || {}) },
        odoo_product_id: plan.odoo_product_id ?? '',
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
        allowed_models: [],
        can_create_custom_titles: false,
        features: { can_change_llm: false, can_edit_role_prompt: false, can_upload_title_documents: false, ocr_enabled: false, max_documents_per_agent: 20 },
        odoo_product_id: '',
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
        await api.updatePlan(editingPlan.id, { ...planForm, odoo_product_id: planForm.odoo_product_id === '' ? null : Number(planForm.odoo_product_id) });
        setActionFeedback({ type: 'success', text: `✓ '${planForm.name}' paketi güncellendi.` });
      } else {
        await api.createPlan({ ...planForm, odoo_product_id: planForm.odoo_product_id === '' ? null : Number(planForm.odoo_product_id) });
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
    if (!(await confirmDialog({ message: `'${plan.name}' (${plan.code}) kiralama paketini silmek istediğinize emin misiniz?\n\nNot: Bu paket hiçbir müşteri tarafından alınmamışsa silinebilir.`, danger: true, confirmText: 'Evet, devam et' }))) return;
    try {
      setProcessingId(plan.id);
      await api.deletePlan(plan.id);
      setActionFeedback({ type: 'success', text: `✓ '${plan.name}' paketi silindi.` });
      await loadAllData();
    } catch (err) {
      notify(`⚠️ KİRALAMA PAKETİ SİLİNEMEZ!\n\n${err.message}`);
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
    if (!(await confirmDialog({ message: `'${model.display_name}' modelini silmek istediğinize emin misiniz?`, danger: true, confirmText: 'Evet, devam et' }))) return;
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

  // ================= 8. MESLEK GRUBU TANIMLARI CRUD (Madde 1) =================
  const handleOpenProfessionModal = (prof = null) => {
    if (prof) {
      setEditingProfession(prof);
      setProfessionForm({
        code: prof.code || '',
        sector_code: prof.sector_code || '',
        name: prof.name || '',
        description: prof.description || '',
        is_active: prof.is_active !== undefined ? prof.is_active : true
      });
    } else {
      setEditingProfession(null);
      setProfessionForm({
        code: '',
        sector_code: professionsFilterSector || (sectors[0]?.code || ''),
        name: '',
        description: '',
        is_active: true
      });
    }
    setProfessionModalOpen(true);
  };

  const handleSaveProfession = async (e) => {
    e.preventDefault();
    if (!professionForm.code.trim() || !professionForm.name.trim() || !professionForm.sector_code.trim()) {
      notify("Lütfen Meslek Kodu, Sektör Kodu ve Meslek Tanım Adı alanlarını doldurunuz.");
      return;
    }
    try {
      setProcessingId('save-profession');
      if (editingProfession) {
        await api.updateProfession(editingProfession.code, {
          sector_code: professionForm.sector_code,
          name: professionForm.name,
          description: professionForm.description,
          is_active: professionForm.is_active
        });
        setActionFeedback({ type: 'success', text: `✓ '${professionForm.code}' meslek tanımı güncellendi.` });
      } else {
        await api.createProfession({
          code: professionForm.code.trim(),
          sector_code: professionForm.sector_code.trim(),
          name: professionForm.name.trim(),
          description: professionForm.description,
          is_active: professionForm.is_active
        });
        setActionFeedback({ type: 'success', text: `✓ '${professionForm.code}' yeni meslek tanımı eklendi.` });
      }
      setProfessionModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Meslek kaydedilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteProfession = async (prof) => {
    if (!(await confirmDialog({ message: `'${prof.code} - ${prof.name}' meslek tanımını silmek istediğinize emin misiniz?`, danger: true, confirmText: 'Evet, devam et' }))) return;
    try {
      setProcessingId(prof.code);
      await api.deleteProfession(prof.code);
      setActionFeedback({ type: 'success', text: `✓ '${prof.code}' meslek tanımı silindi.` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Meslek silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // ================= 9. SEKTÖR TANIMLAMA CRUD (Madde 1) =================
  const handleOpenSectorModal = (sec = null) => {
    if (sec) {
      setEditingSector(sec);
      setSectorForm({
        code: sec.code || '',
        name: sec.name || '',
        description: sec.description || '',
        icon: sec.icon || '',
        image_url: sec.image_url || '',
        is_active: sec.is_active !== undefined ? sec.is_active : true
      });
    } else {
      setEditingSector(null);
      setSectorForm({
        code: '',
        name: '',
        description: '',
        icon: '',
        image_url: '',
        is_active: true
      });
    }
    setSectorModalOpen(true);
  };

  const handleSaveSector = async (e) => {
    e.preventDefault();
    if (!sectorForm.code.trim() || !sectorForm.name.trim()) {
      notify("Lütfen Sektör Kodu ve Sektör Adı alanlarını doldurunuz.");
      return;
    }
    try {
      setProcessingId('save-sector');
      if (editingSector) {
        await api.updateSector(editingSector.code, {
          name: sectorForm.name,
          description: sectorForm.description,
          icon: sectorForm.icon || null,
          image_url: sectorForm.image_url || null,
          is_active: sectorForm.is_active
        });
        setActionFeedback({ type: 'success', text: `✓ '${sectorForm.code}' sektörü güncellendi.` });
      } else {
        await api.createSector({
          code: sectorForm.code.trim().toUpperCase(),
          name: sectorForm.name.trim(),
          description: sectorForm.description,
          icon: sectorForm.icon || null,
          image_url: sectorForm.image_url || null,
          is_active: sectorForm.is_active
        });
        setActionFeedback({ type: 'success', text: `✓ '${sectorForm.code}' yeni sektör oluşturuldu.` });
      }
      setSectorModalOpen(false);
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Sektör kaydedilemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeleteSector = async (sec) => {
    if (!(await confirmDialog({ message: `'${sec.code} - ${sec.name}' sektörünü ve bağlı meslek tanımlarını silmek istediğinize emin misiniz?`, danger: true, confirmText: 'Evet, devam et' }))) return;
    try {
      setProcessingId(sec.code);
      await api.deleteSector(sec.code);
      setActionFeedback({ type: 'success', text: `✓ '${sec.code}' sektörü silindi.` });
      await loadAllData();
    } catch (err) {
      setActionFeedback({ type: 'error', text: 'Sektör silinemedi: ' + err.message });
    } finally {
      setProcessingId(null);
    }
  };

  // Filtrelenmiş Listeler
  const filteredSectors = sectors.filter(s => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const codeMatch = s.code && s.code.toLowerCase().includes(q);
    const nameMatch = s.name && s.name.toLowerCase().includes(q);
    const descMatch = s.description && s.description.toLowerCase().includes(q);
    return codeMatch || nameMatch || descMatch;
  });

  const filteredProfessions = professions.filter(p => {
    if (professionsFilterSector && p.sector_code !== professionsFilterSector) return false;
    if (!professionSearch && !searchQuery) return true;
    const q = (professionSearch || searchQuery).toLowerCase();
    const codeMatch = p.code && p.code.toLowerCase().includes(q);
    const nameMatch = p.name && p.name.toLowerCase().includes(q);
    const secMatch = p.sector_code && p.sector_code.toLowerCase().includes(q);
    const descMatch = p.description && p.description.toLowerCase().includes(q);
    return codeMatch || nameMatch || secMatch || descMatch;
  });
  const filteredLeads = leads
    .filter(l => {
      if (leadApprovalFilter === 'PENDING') return l.status === 'PENDING';
      if (leadApprovalFilter === 'APPROVED') return l.status === 'APPROVED';
      if (leadApprovalFilter === 'REJECTED') return l.status === 'REJECTED';
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

  const filteredRoles = roles.filter(r => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const nameMatch = r.name && r.name.toLowerCase().includes(q);
    const descMatch = r.description && r.description.toLowerCase().includes(q);
    const permMatch = Array.isArray(r.permissions) && r.permissions.some(p => p.toLowerCase().includes(q));
    return nameMatch || descMatch || permMatch;
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
      <div className={`super-admin-mobile-backdrop ${mobileNavOpen ? 'open' : ''}`} onClick={() => setMobileNavOpen(false)} />
      <aside className={`super-admin-sidebar ${sidebarCollapsed ? 'collapsed' : ''} ${mobileNavOpen ? 'mobile-open' : ''}`}>
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
                    Operational Reasoning Intelligence Orchestration Network
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
          <button type="button" className="super-admin-nav-section-title super-admin-nav-group-toggle" onClick={() => toggleNavGroup('GENEL')} aria-expanded={!closedNavGroups.GENEL}>
            <span>Genel</span>
            <ChevronDown className={`super-admin-nav-group-chevron ${closedNavGroups.GENEL ? 'closed' : ''}`} />
          </button>
          {(sidebarCollapsed || !closedNavGroups.GENEL) && (
            <>

            {/* DASHBOARD (Madde 7) */}
            <button
              onClick={() => { switchTab('DASHBOARD'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'DASHBOARD' ? 'active' : ''}`}
              title="Dashboard (Genel Bakış)"
            >
              <div className="super-admin-nav-item-left">
                <LayoutDashboard style={{ width: 17, height: 17, color: 'var(--ac-a78bfa)' }} />
                {!sidebarCollapsed && <span>Dashboard (Genel Bakış)</span>}
              </div>
            </button>
            </>
          )}

          <button type="button" className="super-admin-nav-section-title super-admin-nav-group-toggle" onClick={() => toggleNavGroup('MUSTERILER')} aria-expanded={!closedNavGroups.MUSTERILER}>
            <span>Müşteriler</span>
            <ChevronDown className={`super-admin-nav-group-chevron ${closedNavGroups.MUSTERILER ? 'closed' : ''}`} />
          </button>
          {(sidebarCollapsed || !closedNavGroups.MUSTERILER) && (
            <>

            {/* BAŞVURU ONAY DURUM (Madde 8) */}
            <button
              onClick={() => { switchTab('LEADS'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'LEADS' ? 'active' : ''}`}
              title="Başvuru Onay Durum"
            >
              <div className="super-admin-nav-item-left">
                <Clock style={{ width: 17, height: 17, color: 'var(--ac-38bdf8)' }} />
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
                <Building2 style={{ width: 17, height: 17, color: 'var(--ac-818cf8)' }} />
                {!sidebarCollapsed && <span>Kayıtlı Şirketler</span>}
              </div>
              {!sidebarCollapsed && (
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{tenants.length}</span>
              )}
            </button>
            </>
          )}

          <button type="button" className="super-admin-nav-section-title super-admin-nav-group-toggle" onClick={() => toggleNavGroup('KATALOG')} aria-expanded={!closedNavGroups.KATALOG}>
            <span>Katalog</span>
            <ChevronDown className={`super-admin-nav-group-chevron ${closedNavGroups.KATALOG ? 'closed' : ''}`} />
          </button>
          {(sidebarCollapsed || !closedNavGroups.KATALOG) && (
            <>

            {/* SEKTÖR TANIMLARI (TİCARET BAKANLIĞI) */}
            <button
              onClick={() => { switchTab('SECTORS'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'SECTORS' ? 'active' : ''}`}
              title="Sektör Tanımları (Ticaret Bakanlığı)"
            >
              <div className="super-admin-nav-item-left">
                <Layers style={{ width: 17, height: 17, color: '#10b981' }} />
                {!sidebarCollapsed && <span>Sektör Tanımları</span>}
              </div>
              {!sidebarCollapsed && (
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{sectors.length}</span>
              )}
            </button>

            {/* MESLEK TANIMLARI (TİCARET BAKANLIĞI) */}
            <button
              onClick={() => { switchTab('PROFESSIONS'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'PROFESSIONS' ? 'active' : ''}`}
              title="Meslek Grubu Tanımları (Ticaret Bakanlığı)"
            >
              <div className="super-admin-nav-item-left">
                <Briefcase style={{ width: 17, height: 17, color: 'var(--ac-38bdf8)' }} />
                {!sidebarCollapsed && <span>Meslek Tanımları</span>}
              </div>
              {!sidebarCollapsed && (
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{professions.length}</span>
              )}
            </button>

            {/* DEPARTMAN & UNVAN KATALOĞU */}
            <button
              onClick={() => { switchTab('CATALOG'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'CATALOG' ? 'active' : ''}`}
              title="Departman & Unvan Kataloğu"
            >
              <div className="super-admin-nav-item-left">
                <Building2 style={{ width: 17, height: 17, color: 'var(--ac-a78bfa)' }} />
                {!sidebarCollapsed && <span>Departman & Unvan</span>}
              </div>
            </button>
            </>
          )}

          <button type="button" className="super-admin-nav-section-title super-admin-nav-group-toggle" onClick={() => toggleNavGroup('TICARIYETKI')} aria-expanded={!closedNavGroups.TICARIYETKI}>
            <span>Ticari & Yetki</span>
            <ChevronDown className={`super-admin-nav-group-chevron ${closedNavGroups.TICARIYETKI ? 'closed' : ''}`} />
          </button>
          {(sidebarCollapsed || !closedNavGroups.TICARIYETKI) && (
            <>

            {/* KİRALAMA PAKETLERİ */}
            <button
              onClick={() => { switchTab('PLANS'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'PLANS' ? 'active' : ''}`}
              title="Kiralama Paketleri"
            >
              <div className="super-admin-nav-item-left">
                <Package style={{ width: 17, height: 17, color: 'var(--ac-34d399)' }} />
                {!sidebarCollapsed && <span>Kiralama Paketleri</span>}
              </div>
              {!sidebarCollapsed && (
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{plans.length}</span>
              )}
            </button>

            {/* İZİN KATALOĞU */}
            <button
              onClick={() => { switchTab('PERMISSIONS'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'PERMISSIONS' ? 'active' : ''}`}
              title="İzin Kataloğu (RBAC)"
            >
              <div className="super-admin-nav-item-left">
                <KeyRound style={{ width: 17, height: 17, color: 'var(--ac-fbbf24)' }} />
                {!sidebarCollapsed && <span>İzin Kataloğu (RBAC)</span>}
              </div>
              {!sidebarCollapsed && (
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{permissions.length}</span>
              )}
            </button>

            {/* YETKİ ROLLERİ (Madde 1) */}
            <button
              onClick={() => { switchTab('ROLES'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'ROLES' ? 'active' : ''}`}
              title="Yetki Rolleri (RBAC)"
            >
              <div className="super-admin-nav-item-left">
                <ShieldCheck style={{ width: 17, height: 17, color: '#10b981' }} />
                {!sidebarCollapsed && <span>Yetki Rolleri</span>}
              </div>
              {!sidebarCollapsed && (
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{roles.length}</span>
              )}
            </button>
            </>
          )}

          <button type="button" className="super-admin-nav-section-title super-admin-nav-group-toggle" onClick={() => toggleNavGroup('ILETISIMOTOMASYON')} aria-expanded={!closedNavGroups.ILETISIMOTOMASYON}>
            <span>İletişim & Otomasyon</span>
            <ChevronDown className={`super-admin-nav-group-chevron ${closedNavGroups.ILETISIMOTOMASYON ? 'closed' : ''}`} />
          </button>
          {(sidebarCollapsed || !closedNavGroups.ILETISIMOTOMASYON) && (
            <>

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
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{emailTemplates.length}</span>
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
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{schedules.length}</span>
              )}
            </button>
            </>
          )}

          <button type="button" className="super-admin-nav-section-title super-admin-nav-group-toggle" onClick={() => toggleNavGroup('YAPAYZEKA')} aria-expanded={!closedNavGroups.YAPAYZEKA}>
            <span>Yapay Zeka</span>
            <ChevronDown className={`super-admin-nav-group-chevron ${closedNavGroups.YAPAYZEKA ? 'closed' : ''}`} />
          </button>
          {(sidebarCollapsed || !closedNavGroups.YAPAYZEKA) && (
            <>

            {/* GENEL AI MODELİ */}
            <button
              onClick={() => { switchTab('AI_MODEL_SETTINGS'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'AI_MODEL_SETTINGS' ? 'active' : ''}`}
              title="Genel AI Modeli (Manifesto)"
            >
              <div className="super-admin-nav-item-left">
                <Zap style={{ width: 17, height: 17, color: '#f43f5e' }} />
                {!sidebarCollapsed && <span>Genel AI Modelleri</span>}
              </div>
              {!sidebarCollapsed && (
                <span style={{ background: 'rgba(244,63,94,0.2)', color: '#f43f5e', fontSize: '0.6rem', padding: '2px 5px', borderRadius: 4, fontWeight: 700 }}>
                  ÇEKİRDEK
                </span>
              )}
            </button>

            {/* SÜPER YÖNETİCİ ASİSTANI */}
            <button
              onClick={() => { switchTab('AI_ASSISTANT'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'AI_ASSISTANT' ? 'active' : ''}`}
              title="Süper Yönetici Asistanı"
            >
              <div className="super-admin-nav-item-left">
                <Bot style={{ width: 17, height: 17, color: '#38bdf8' }} />
                {!sidebarCollapsed && <span>Yönetici Asistanı</span>}
              </div>
            </button>

            {/* EVREN MODELLERİ */}
            <button
              onClick={() => { switchTab('MODELS'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'MODELS' ? 'active' : ''}`}
              title="EVREN Modelleri"
            >
              <div className="super-admin-nav-item-left">
                <Cpu style={{ width: 17, height: 17, color: 'var(--ac-a78bfa)' }} />
                {!sidebarCollapsed && <span>EVREN Modelleri</span>}
              </div>
              {!sidebarCollapsed && (
                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontFamily: 'monospace' }}>{models.length}</span>
              )}
            </button>

            {/* LLM TL FİYATLARI (Adım 7.5.1) */}
            <button
              onClick={() => { switchTab('LLM_PRICES'); setSearchQuery(''); }}
              className={`super-admin-nav-item ${activeTab === 'LLM_PRICES' ? 'active' : ''}`}
              title="LLM TL Fiyatları"
            >
              <div className="super-admin-nav-item-left">
                <Coins style={{ width: 17, height: 17, color: '#facc15' }} />
                {!sidebarCollapsed && <span>LLM TL Fiyatları</span>}
              </div>
            </button>
            </>
          )}
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
              color: 'var(--ac-38bdf8)',
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              textDecoration: 'none',
              boxSizing: 'border-box',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            title="RECDx Resmi Web Sitesine Git (https://www.recdx.com - Yeni Sekmede Açılır)"
          >
            <Globe style={{ width: 15, height: 15, color: 'var(--ac-38bdf8)', flexShrink: 0 }} />
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
              color: 'var(--ac-f87171)',
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
          <button
            type="button"
            className="ui-icon-btn ui-show-tablet"
            onClick={() => setMobileNavOpen(true)}
            aria-label="Menüyü aç"
            title="Menü"
          >
            <Menu size={18} />
          </button>
          <div className="super-admin-header-title">
            <span>Ana Kontrol Merkezi</span>
            <span style={{ color: 'var(--nt-64748b)', fontSize: '0.8rem' }}>/</span>
            <span style={{ color: '#146ceb', fontSize: '0.825rem' }}>
              {activeTab === 'DASHBOARD' && 'Sistem Genel Bakış & Dashboard'}
              {activeTab === 'LEADS' && 'Başvuru Onay Durum Masası'}
              {activeTab === 'TENANTS' && 'Kayıtlı Kurumlar & Şirket Yönetimi'}
              {activeTab === 'EMAIL_TEMPLATES' && 'Kurumsal E-Posta Şablonları & HTML Editörü'}
              {activeTab === 'SCHEDULES' && 'Otomatik Zamanlayıcılar (Schedules)'}
              {activeTab === 'PERMISSIONS' && 'Sistem Yetki Kataloğu (RBAC)'}
              {activeTab === 'PLANS' && 'Kiralama Paketleri Yönetimi'}
              {activeTab === 'MODELS' && 'EVREN Model Kataloğu'}
              {activeTab === 'LLM_PRICES' && 'LLM TL Fiyatları'}
              {activeTab === 'AI_MODEL_SETTINGS' && 'Genel AI Modelleri & Yapay Zeka Kullanımı'}
              {activeTab === 'AI_ASSISTANT' && 'Süper Yönetici Asistanı'}
              {activeTab === 'CATALOG' && 'Departman & Unvan Kataloğu'}
              {activeTab === 'SECTORS' && 'Sektör Tanımları (Ticaret Bakanlığı)'}
              {activeTab === 'PROFESSIONS' && 'Meslek Grubu Tanımları (Ticaret Bakanlığı)'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            <ThemeToggle className="ui-hide-mobile" />
            <ThemeToggle compact className="ui-show-mobile-only" />
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
                <div style={{ fontSize: '0.785rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span>{currentUser?.display_name || 'Muhammed Cüneyt ERDİL'}</span>
                  <Settings style={{ width: 12, height: 12, opacity: 0.7 }} />
                </div>
                <div style={{ fontSize: '0.68rem', color: 'var(--nt-94a3b8)', fontFamily: 'monospace' }}>
                  {currentUser?.email || 'cuneyterdil@recdx.com'}
                </div>
              </div>
            </button>
          </div>
        </header>

        {/* GERİ BİLDİRİM BANNERI */}
        {/* İÇERİK GÖVDESİ */}
        <div className="super-admin-content">
          
          {/* TAB 0: DASHBOARD (GENEL BAKIŞ & METRİKLER - Madde 7) */}
          {activeTab === 'DASHBOARD' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* Sayfa Başlığı */}
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <LayoutDashboard style={{ width: 22, height: 22, color: 'var(--ac-a78bfa)' }} />
                    <span>Süper Yönetim Kontrol Paneli (Dashboard)</span>
                  </h2>
                  <p style={{ fontSize: '0.8rem', color: 'var(--nt-94a3b8)', marginTop: 4 }}>
                    RECOrion platformunun kurumsal başvuru, şirket, yapay zeka modelleri ve altyapı metrikleri.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <HealthBadge health={platformHealth.health} />
                </div>
              </div>

              {/* 3D KPI KARTLARI GRİDİ (Madde 7) */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 240px), 1fr))', gap: 18 }}>
                
                {/* KART 1: Aktif Edilmemiş Yeni Müşteri Sayısı (Tıklayınca Onaylanmamışlar Filtreli Açılır) */}
                <div 
                  onClick={() => { switchTab('LEADS'); setLeadApprovalFilter('PENDING'); setSearchQuery(''); }}
                  className="super-admin-kpi-card-3d glow-amber"
                  title="Onay bekleyen başvuruları görüntülemek için tıklayın"
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-fbbf24)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Bekleyen Başvurular
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--nt-cbd5e1)', marginTop: 2 }}>
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
                      color: 'var(--ac-fbbf24)' 
                    }}>
                      <Clock style={{ width: 22, height: 22 }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--nt-ffffff)', lineHeight: 1 }}>
                      {leads.filter(l => l.status === 'PENDING').length}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 700 }}>
                      Başvuru Onay Bekliyor
                    </span>
                  </div>

                  <div style={{ 
                    marginTop: 14, 
                    paddingTop: 12, 
                    borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    fontSize: '0.725rem',
                    color: 'var(--ac-fbbf24)'
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
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-c084fc)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Kurumsal Portföy
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--nt-cbd5e1)', marginTop: 2 }}>
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
                      color: 'var(--ac-a78bfa)' 
                    }}>
                      <Building2 style={{ width: 22, height: 22 }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--nt-ffffff)', lineHeight: 1 }}>
                      {tenants.length}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--ac-c084fc)', fontWeight: 700 }}>
                      Kayıtlı Kurum / Şirket
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.72rem', color: 'var(--nt-cbd5e1)', marginTop: 4 }}>
                    <span style={{ color: 'var(--ac-34d399)', fontWeight: 700 }}>{tenants.filter(t => t.is_active).length} Onaylı</span>
                    <span>•</span>
                    <span style={{ color: 'var(--ac-fbbf24)', fontWeight: 700 }}>{tenants.filter(t => !t.is_active).length} Onay Bekliyor</span>
                  </div>

                  <div style={{ 
                    marginTop: 14, 
                    paddingTop: 12, 
                    borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    fontSize: '0.725rem',
                    color: 'var(--ac-c084fc)'
                  }}>
                    <span style={{ fontWeight: 600 }}>Şirketler Listesini Aç</span>
                    <ArrowRight style={{ width: 14, height: 14 }} />
                  </div>
                </div>

                {/* KART 3: Onaylanmış & Aktif Müşteri Portföyü */}
                <div 
                  onClick={() => { switchTab('TENANTS'); setSearchQuery(''); }}
                  className="super-admin-kpi-card-3d glow-green"
                  style={{ borderColor: 'rgba(16, 185, 129, 0.3)' }}
                  title="Onaylanmış ve aktif müşterileri incelemek için tıklayın"
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-34d399)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Onaylanmış Portföy
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--nt-cbd5e1)', marginTop: 2 }}>
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
                      color: 'var(--ac-34d399)' 
                    }}>
                      <CheckCircle2 style={{ width: 22, height: 22 }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--nt-ffffff)', lineHeight: 1 }}>
                      {tenants.filter(t => t.is_active).length}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--ac-34d399)', fontWeight: 700 }}>
                      Aktif / Onaylı Müşteri
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.72rem', color: 'var(--nt-94a3b8)', marginTop: 4 }}>
                    <span style={{ color: 'var(--ac-34d399)', fontWeight: 700 }}>{leads.filter(l => l.status === 'APPROVED').length} Web Başvurusu</span>
                    <span>•</span>
                    <span>{Math.max(0, tenants.filter(t => t.is_active).length - leads.filter(l => l.status === 'APPROVED').length)} Doğrudan Kurumsal</span>
                  </div>

                  <div style={{ 
                    marginTop: 14, 
                    paddingTop: 12, 
                    borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    fontSize: '0.725rem',
                    color: 'var(--ac-34d399)'
                  }}>
                    <span style={{ fontWeight: 600 }}>Aktif Portföyü Gör</span>
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
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-38bdf8)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Yapay Zeka Altyapısı
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--nt-cbd5e1)', marginTop: 2 }}>
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
                      color: 'var(--ac-38bdf8)' 
                    }}>
                      <Cpu style={{ width: 22, height: 22 }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <span style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--nt-ffffff)', lineHeight: 1 }}>
                      {models.length}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--ac-38bdf8)', fontWeight: 700 }}>
                      LLM Muhakeme Motoru
                    </span>
                  </div>

                  <div style={{ 
                    marginTop: 14, 
                    paddingTop: 12, 
                    borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    fontSize: '0.725rem',
                    color: 'var(--ac-38bdf8)'
                  }}>
                    <span style={{ fontWeight: 600 }}>Model Kataloğuna Git</span>
                    <ArrowRight style={{ width: 14, height: 14 }} />
                  </div>
                </div>

              </div>

              {/* DASHBOARD ALT ALAN: Bekleyen Başvuru Özeti & Sistem Durumu */}
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
                
                {/* SOL: Bekleyen Yeni Başvurular Önizleme */}
                <div style={{ 
                  background: 'linear-gradient(180deg, var(--sf-101628) 0%, var(--sf-0d1222) 100%)',
                  borderRadius: 18,
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  padding: 20,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Clock style={{ width: 18, height: 18, color: '#f59e0b' }} />
                      <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--nt-ffffff)' }}>
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
                    <div style={{ padding: '36px 20px', textAlign: 'center', color: 'var(--nt-64748b)', fontSize: '0.85rem' }}>
                      <CheckCircle2 style={{ width: 36, height: 36, color: '#10b981', margin: '0 auto 8px', opacity: 0.8 }} />
                      <div>Şu anda onay bekleyen yeni başvuru bulunmuyor.</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--nt-475569)', marginTop: 4 }}>Tüm müşteri talepleri işleme alındı.</div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {leads.filter(l => l.status === 'PENDING').slice(0, 4).map((ld) => (
                        <div 
                          key={ld.id}
                          style={{
                            background: 'rgb(var(--rgb-ov) / 0.02)',
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
                            <div style={{ fontWeight: 800, color: 'var(--nt-ffffff)', fontSize: '0.85rem' }}>
                              {ld.company_name}
                            </div>
                            <div style={{ fontSize: '0.725rem', color: 'var(--nt-94a3b8)', display: 'flex', alignItems: 'center', gap: 12, marginTop: 4 }}>
                              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Mail style={{ width: 12, height: 12, color: 'var(--ac-818cf8)' }} />
                                {ld.contact_email}
                              </span>
                              <span style={{ color: 'var(--ac-38bdf8)', fontWeight: 600 }}>
                                {ld.plan_name || 'Paket Bilgisi'}
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

                {/* SAĞ: Altyapı ve entegrasyon durumu (ADIM 9.4: gerçek ölçüm) */}
                <SystemHealthPanel health={platformHealth.health} busy={platformHealth.busy} onRefresh={platformHealth.load} />

              </div>

              {/* Platform kullanımı ve LLM sağlığı (ADIM 9.4) */}
              <PlatformDashboard />

            </div>
          )}

          {/* TAB 1: LEADS & ODOO ONAY (Madde 8) */}
          {activeTab === 'LEADS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Clock style={{ width: 20, height: 20, color: 'var(--ac-38bdf8)' }} />
                    <span>Başvuru Onay Durum Masası</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
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
                    <button
                      type="button"
                      onClick={() => { setLeadApprovalFilter('REJECTED'); setLeadViewMode('LIST'); }}
                      className={`super-admin-toggle-3d-btn ${leadApprovalFilter === 'REJECTED' ? 'active' : ''}`}
                      title="Reddedilen Başvuruları Listele"
                    >
                      <X style={{ width: 15, height: 15 }} />
                      <span>Reddedilenler ({leads.filter(l => l.status === 'REJECTED').length})</span>
                    </button>
                  </div>

                  {renderViewModeToggle(leadViewMode, setLeadViewMode)}

                  <div style={{ width: 220, position: 'relative' }}>
                    <Search style={{ width: 14, height: 14, position: 'absolute', left: 10, top: 11, color: 'var(--nt-64748b)' }} />
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
                <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, alignItems: 'start' }}>
                  {/* Kolon 1: Onay Bekleyenler */}
                  <div style={{ background: 'rgb(var(--rgb-ov) / 0.02)', borderRadius: 14, border: '1px solid rgba(245,158,11,0.25)', padding: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.06)', marginBottom: 14 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Clock style={{ width: 16, height: 16, color: 'var(--ac-fbbf24)' }} />
                        <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--nt-ffffff)', margin: 0 }}>Onay Bekleyen Başvurular</h4>
                      </div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 800, background: 'rgba(245,158,11,0.2)', color: 'var(--ac-fbbf24)', padding: '2px 8px', borderRadius: 999 }}>
                        {leads.filter(l => l.status === 'PENDING').length}
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {leads.filter(l => l.status === 'PENDING').filter(l => !searchQuery || l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) || l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())).length === 0 ? (
                        <div style={{ padding: '28px', textAlign: 'center', color: 'var(--nt-64748b)', fontSize: '0.8rem' }}>
                          Onay bekleyen başvuru bulunmuyor.
                        </div>
                      ) : (
                        leads.filter(l => l.status === 'PENDING').filter(l => !searchQuery || l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) || l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())).map(lead => (
                          <div key={lead.id} className="super-admin-card" style={{ padding: 14, border: '1px solid rgba(245,158,11,0.25)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              {renderLeadOdoo(lead)}
                              <span style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--ac-fbbf24)', background: 'rgba(245,158,11,0.2)', padding: '2px 6px', borderRadius: 4 }}>
                                ⏳ Onay Bekliyor
                              </span>
                            </div>
                            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--nt-ffffff)', margin: '8px 0 4px 0' }}>{lead.company_name}</h4>
                            <div style={{ fontSize: '0.725rem', color: 'var(--nt-94a3b8)', display: 'flex', flexDirection: 'column', gap: 3 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Mail style={{ width: 12, height: 12, color: 'var(--ac-818cf8)' }} />
                                <span>{lead.contact_email}</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Phone style={{ width: 12, height: 12 }} />
                                <span>{lead.phone || '-'}</span>
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12, paddingTop: 10, borderTop: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ac-a78bfa)' }}>
                                {lead.plan_name || 'Paket seçilmemiş'}
                              </span>
                              <div style={{ display: 'flex', gap: 6 }}>
                              <button
                                type="button"
                                onClick={() => handleRejectLead(lead)}
                                disabled={processingId === lead.id}
                                className="ui-btn ui-btn-ghost ui-btn-sm"
                                style={{ color: 'var(--ac-f87171)' }}
                              >
                                Reddet
                              </button>
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
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Kolon 2: Onaylananlar */}
                  <div style={{ background: 'rgb(var(--rgb-ov) / 0.02)', borderRadius: 14, border: '1px solid rgba(16,185,129,0.25)', padding: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.06)', marginBottom: 14 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <CheckCircle2 style={{ width: 16, height: 16, color: 'var(--ac-34d399)' }} />
                        <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--nt-ffffff)', margin: 0 }}>Onaylanan ve Aktif Başvurular</h4>
                      </div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 800, background: 'rgba(16,185,129,0.2)', color: 'var(--ac-34d399)', padding: '2px 8px', borderRadius: 999 }}>
                        {leads.filter(l => l.status === 'APPROVED').length}
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {leads.filter(l => l.status === 'APPROVED').filter(l => !searchQuery || l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) || l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())).length === 0 ? (
                        <div style={{ padding: '28px', textAlign: 'center', color: 'var(--nt-64748b)', fontSize: '0.8rem' }}>
                          Henüz onaylanmış başvuru bulunmuyor.
                        </div>
                      ) : (
                        leads.filter(l => l.status === 'APPROVED').filter(l => !searchQuery || l.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) || l.contact_email?.toLowerCase().includes(searchQuery.toLowerCase())).map(lead => (
                          <div key={lead.id} className="super-admin-card" style={{ padding: 14, border: '1px solid rgba(16,185,129,0.25)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span style={{ fontFamily: 'monospace', fontSize: '0.7rem', color: 'var(--ac-34d399)', fontWeight: 800 }}>
                                {lead.odoo_order_name || 'Odoo: Onaylandı'}
                              </span>
                              <span style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--ac-34d399)', background: 'rgba(16,185,129,0.2)', padding: '2px 6px', borderRadius: 4 }}>
                                ✓ Aktif
                              </span>
                            </div>
                            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--nt-ffffff)', margin: '8px 0 4px 0' }}>{lead.company_name}</h4>
                            <div style={{ fontSize: '0.725rem', color: 'var(--nt-94a3b8)', display: 'flex', flexDirection: 'column', gap: 3 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Mail style={{ width: 12, height: 12, color: 'var(--ac-818cf8)' }} />
                                <span>{lead.contact_email}</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Phone style={{ width: 12, height: 12 }} />
                                <span>{lead.phone || '-'}</span>
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12, paddingTop: 10, borderTop: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ac-a78bfa)' }}>
                                {lead.plan_name || 'Paket'}
                              </span>
                              <span style={{ fontSize: '0.72rem', color: 'var(--ac-6ee7b7)', fontWeight: 700 }}>
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
                        <th>İletişim</th>
                        <th>Seçilen Paket</th>
                        <th>Odoo Sipariş No</th>
                        <th>Durum</th>
                        <th className="ui-sticky-right" style={{ textAlign: 'right' }}>Aksiyon</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredLeads.length === 0 ? (
                        <tr>
                          <td colSpan="6" style={{ textAlign: 'center', padding: '36px', color: 'var(--nt-64748b)' }}>
                            {leadApprovalFilter === 'PENDING'
                              ? 'Şu anda onay bekleyen müşteri başvurusu bulunmuyor.'
                              : 'Henüz onaylanmış müşteri başvurusu bulunmuyor.'}
                          </td>
                        </tr>
                      ) : (
                        filteredLeads.map((lead) => (
                          <tr key={lead.id}>
                            <td>
                              <div style={{ fontWeight: 800, color: 'var(--nt-ffffff)' }}>{lead.company_name}</div>
                              <div style={{ fontSize: '0.725rem', color: 'var(--nt-94a3b8)', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                                <Mail style={{ width: 12, height: 12, color: 'var(--ac-818cf8)' }} />
                                <span>{lead.contact_email}</span>
                              </div>
                            </td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Phone style={{ width: 12, height: 12 }} />
                                <span>{lead.phone || '-'}</span>
                              </div>
                            </td>
                            <td>
                              <span style={{ fontWeight: 700, color: 'var(--nt-ffffff)' }}>
                                {lead.plan_name || 'Paket seçilmemiş'}
                              </span>
                            </td>
                            <td>
                              {renderLeadOdoo(lead)}
                            </td>
                            <td>
                              {lead.status === 'REJECTED' ? (
                                <span title={lead.rejection_reason || ''} style={{ background: 'rgba(239,68,68,0.15)', color: 'var(--ac-f87171)', border: '1px solid rgba(239,68,68,0.3)', padding: '3px 8px', borderRadius: 999, fontSize: '0.7rem', fontWeight: 800 }}>
                                  ✕ Reddedildi
                                </span>
                              ) : lead.status === 'APPROVED' ? (
                                <span style={{ background: 'rgba(16,185,129,0.2)', color: 'var(--ac-6ee7b7)', border: '1px solid rgba(16,185,129,0.3)', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800 }}>
                                  ✓ Onaylandı & Aktif
                                </span>
                              ) : (
                                <span style={{ background: 'rgba(245,158,11,0.2)', color: 'var(--ac-fcd34d)', border: '1px solid rgba(245,158,11,0.3)', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800 }}>
                                  ⏳ Onay Bekliyor
                                </span>
                              )}
                            </td>
                            <td className="ui-sticky-right" style={{ textAlign: 'right' }}>
                              {lead.status === 'REJECTED' ? (
                                <span style={{ fontSize: '0.725rem', color: 'var(--nt-64748b)' }}>{lead.rejection_reason || 'Reddedildi'}</span>
                              ) : lead.status !== 'APPROVED' ? (
                                <div style={{ display: 'inline-flex', gap: 6 }}>
                                <button
                                  type="button"
                                  onClick={() => handleRejectLead(lead)}
                                  disabled={processingId === lead.id}
                                  className="ui-btn ui-btn-ghost ui-btn-sm"
                                  style={{ color: 'var(--ac-f87171)' }}
                                >
                                  Reddet
                                </button>
                                <button
                                  onClick={() => handleApproveLead(lead)}
                                  disabled={processingId === lead.id}
                                  className="super-admin-btn-corporate"
                                  style={{ padding: '6px 12px', fontSize: '0.725rem' }}
                                >
                                  {processingId === lead.id ? <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" /> : <CheckCircle2 style={{ width: 12, height: 12 }} />}
                                  <span>Onayla & Aktif Et</span>
                                </button>
                                </div>
                              ) : (
                                <span style={{ fontSize: '0.725rem', color: 'var(--nt-64748b)' }}>Aktivasyon Tamamlandı</span>
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
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Building2 style={{ width: 20, height: 20, color: 'var(--ac-818cf8)' }} />
                    <span>Kayıtlı Kurumlar ve Şirketler (Tenants)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
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
                  <div style={{ display: 'flex', background: 'rgb(var(--rgb-ov) / 0.06)', padding: 3, borderRadius: 8, border: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                    <button
                      onClick={() => setTenantStatusFilter('ALL')}
                      className="super-admin-btn-secondary"
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.75rem',
                        border: 'none',
                        background: tenantStatusFilter === 'ALL' ? '#7134e2' : 'transparent',
                        color: tenantStatusFilter === 'ALL' ? '#fff' : 'var(--nt-94a3b8)'
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
                        color: tenantStatusFilter === 'APPROVED' ? 'var(--ac-34d399)' : 'var(--nt-94a3b8)'
                      }}
                      title="Aktif Durumdaki Şirketleri Listele"
                    >
                      <CheckCircle2 style={{ width: 13, height: 13, color: 'var(--ac-34d399)' }} />
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
                        color: tenantStatusFilter === 'PENDING' ? 'var(--ac-f87171)' : 'var(--nt-94a3b8)'
                      }}
                      title="Pasife Alınmış veya Onay Bekleyen Şirketleri Listele"
                    >
                      <PauseCircle style={{ width: 13, height: 13, color: 'var(--ac-f87171)' }} />
                      <span>Pasif / Bekleyen ({tenants.filter(t => !t.is_active).length})</span>
                    </button>
                  </div>

                  {/* Kanban / Liste Format Butonları (Madde 8) */}
                  <div style={{ display: 'flex', background: 'rgb(var(--rgb-ov) / 0.06)', padding: 3, borderRadius: 8, border: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                    <button
                      onClick={() => setTenantViewMode('KANBAN')}
                      className="super-admin-btn-secondary"
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.75rem',
                        border: 'none',
                        background: tenantViewMode === 'KANBAN' ? '#7134e2' : 'transparent',
                        color: tenantViewMode === 'KANBAN' ? '#fff' : 'var(--nt-94a3b8)'
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
                        color: tenantViewMode === 'LIST' ? '#fff' : 'var(--nt-94a3b8)'
                      }}
                      title="Liste Tablo Görünümü"
                    >
                      <List style={{ width: 14, height: 14 }} />
                      <span>Liste</span>
                    </button>
                  </div>

                  {/* Arama */}
                  <div style={{ width: 240, position: 'relative' }}>
                    <Search style={{ width: 14, height: 14, position: 'absolute', left: 10, top: 11, color: 'var(--nt-64748b)' }} />
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
                          <div style={{ width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(135deg, rgba(113,52,226,0.4), rgba(20,108,235,0.4))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, color: 'var(--nt-ffffff)', border: '1px solid rgb(var(--rgb-ov) / 0.1)' }}>
                            {t.name.slice(0, 2).toUpperCase()}
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            {/* Satın Alma Onay İkonu */}
                            {t.is_active ? (
                              <span style={{
                                padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800,
                                background: 'rgba(16,185,129,0.2)', color: 'var(--ac-6ee7b7)', border: '1px solid rgba(16,185,129,0.3)',
                                display: 'flex', alignItems: 'center', gap: 4
                              }}>
                                <CheckCircle2 style={{ width: 12, height: 12 }} />
                                <span>AKTİF</span>
                              </span>
                            ) : (
                              <span style={{
                                padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800,
                                background: 'rgba(239,68,68,0.2)', color: 'var(--ac-fca5a5)', border: '1px solid rgba(239,68,68,0.3)',
                                display: 'flex', alignItems: 'center', gap: 4
                              }}>
                                <PauseCircle style={{ width: 12, height: 12 }} />
                                <span>PASİF</span>
                              </span>
                            )}
                          </div>
                        </div>

                        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--nt-ffffff)', marginTop: 12 }}>{t.name}</h3>

                        {/* Açıklamalı Slug / Sistem Kimliği Etiketi (Madde 10 - Kullanıcı Sorusu Cevabı) */}
                        <div style={{ 
                          fontSize: '0.7rem', color: 'var(--nt-94a3b8)', background: 'rgb(var(--rgb-ov) / 0.03)', 
                          padding: '4px 8px', borderRadius: 6, marginTop: 4, display: 'flex', alignItems: 'center', gap: 6 
                        }}>
                          <Tag style={{ width: 12, height: 12, color: 'var(--ac-38bdf8)' }} />
                          <span><strong>🔑 Sistem Kimliği / URL:</strong> <code style={{ color: 'var(--ac-38bdf8)' }}>{t.slug}</code></span>
                        </div>

                        {/* Faaliyet Sektörleri Rozetleri (Madde 1) */}
                        {t.sectors && t.sectors.length > 0 && (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                            {t.sectors.map((secName, sIdx) => {
                              const sObj = sectors.find(s => s.name === secName || s.code === secName);
                              return (
                                <span
                                  key={sIdx}
                                  style={{
                                    padding: '2px 7px',
                                    borderRadius: 6,
                                    fontSize: '0.675rem',
                                    fontWeight: 700,
                                    background: 'rgba(99,102,241,0.2)',
                                    border: '1px solid rgba(129,140,248,0.4)',
                                    color: 'var(--ac-c7d2fe)',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 4
                                  }}
                                >
                                  <span>{sObj?.icon || '📁'}</span>
                                  <span>{secName}</span>
                                </span>
                              );
                            })}
                          </div>
                        )}

                        {/* Paket & Bitiş Tarihi Bilgileri (Madde 10) */}
                        <div style={{ marginTop: 10, padding: '8px 10px', borderRadius: 8, background: 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))', border: '1px solid rgb(var(--rgb-ov) / 0.06)', display: 'flex', flexDirection: 'column', gap: 5 }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                            <span style={{ color: 'var(--nt-94a3b8)', display: 'flex', alignItems: 'center', gap: 5 }}>
                              <Package style={{ width: 13, height: 13, color: 'var(--ac-a78bfa)' }} /> Paket:
                            </span>
                            <span style={{ color: 'var(--nt-ffffff)', fontWeight: 700 }}>{t.plan_name || 'Standart Kiralama'}</span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                            <span style={{ color: 'var(--nt-94a3b8)', display: 'flex', alignItems: 'center', gap: 5 }}>
                              <Calendar style={{ width: 13, height: 13, color: 'var(--ac-60a5fa)' }} /> Kira Bitiş:
                            </span>
                            <span style={{ color: !t.is_active ? 'var(--ac-fbbf24)' : (t.is_warning_3_months ? 'var(--ac-f87171)' : 'var(--nt-cbd5e1)'), fontWeight: 700 }}>
                              {!t.is_active ? 'Onay Bekliyor / Pasif' : (t.package_expiry_date ? new Date(t.package_expiry_date).toLocaleDateString('tr-TR') : '1 Yıl')}
                            </span>
                          </div>
                        </div>

                        {/* 3 Ay Bitiş Uyarısı Banner (Madde 10) */}
                        {t.is_active && t.is_warning_3_months && (
                          <div style={{
                            marginTop: 10, padding: '7px 10px', borderRadius: 8,
                            background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)',
                            display: 'flex', alignItems: 'center', gap: 6, color: 'var(--ac-fca5a5)', fontSize: '0.72rem', fontWeight: 700
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
                            display: 'flex', alignItems: 'center', gap: 6, color: 'var(--ac-fca5a5)', fontSize: '0.72rem', fontWeight: 700
                          }}>
                            <PauseCircle style={{ width: 14, height: 14, color: 'var(--ac-f87171)', flexShrink: 0 }} />
                            <span>⏸️ Şirket Kartı Pasif Durumda (Girişler Kapalı)</span>
                          </div>
                        )}

                        {/* İletişim Detayları */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 12, fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Mail style={{ width: 13, height: 13, color: 'var(--ac-818cf8)' }} />
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.contact_email || 'E-posta yok'}</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Phone style={{ width: 13, height: 13, color: 'var(--ac-34d399)' }} />
                            <span>{t.phone || 'Telefon yok'}</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <CreditCard style={{ width: 13, height: 13, color: 'var(--ac-fbbf24)' }} />
                            <span>VKN: {t.tax_id || '-'} {t.tax_office ? `(${t.tax_office} V.D.)` : ''}</span>
                          </div>
                        </div>
                      </div>

                      {/* Kart Altı Aksiyon Butonları (Madde 10 & 14 & Madde 4) */}
                      {/* Kart Altı Aksiyon Butonları (Madde 1 & 10 & 14) */}
                      <div 
                        className="super-admin-card-actions"
                        style={{ 
                          display: 'flex', 
                          flexWrap: 'wrap', 
                          alignItems: 'center', 
                          gap: 6, 
                          marginTop: 16, 
                          paddingTop: 12, 
                          borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                          width: '100%',
                          overflowX: 'auto',
                          scrollbarWidth: 'thin'
                        }}
                      >
                        <button
                          onClick={() => setCreditTenant(t)}
                          className="super-admin-btn-secondary"
                          style={{ flex: '1 1 calc(50% - 6px)', minWidth: '85px', justifyContent: 'center', padding: '6px 8px', fontSize: '0.72rem', whiteSpace: 'nowrap' }}
                          title="Kredi durumu ve ek kredi yükleme"
                        >
                          <Coins style={{ width: 13, height: 13, color: '#facc15' }} />
                          <span>Kredi</span>
                        </button>
                        {/* Müşteri Kartını Pasife Al / Aktife Al Butonu (Madde 3: Yalnızca Kayıtlı Şirketler Listesinden Yapılır) */}
                        <button
                          onClick={() => handleToggleTenantStatus(t)}
                          disabled={processingId === 'toggle-status-' + t.id}
                          className="super-admin-btn-secondary"
                          style={{
                            flex: '1 1 calc(50% - 6px)',
                            minWidth: '85px',
                            justifyContent: 'center',
                            padding: '6px 8px', 
                            fontSize: '0.72rem',
                            whiteSpace: 'nowrap',
                            color: t.is_active ? 'var(--ac-f87171)' : 'var(--ac-34d399)',
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

                        {/* Şirketi Sil Butonu (Madde 1: Ana Şirket Silinemez) */}
                        {!isMainCompany(t) ? (
                          <button
                            onClick={() => handleDeleteTenant(t)}
                            disabled={processingId === 'delete-tenant-' + t.id}
                            className="super-admin-btn-secondary"
                            style={{
                              padding: '6px 8px',
                              fontSize: '0.72rem',
                              color: 'var(--ac-f87171)',
                              borderColor: 'rgba(239,68,68,0.35)',
                              background: 'rgba(239,68,68,0.08)',
                              justifyContent: 'center'
                            }}
                            title="Şirketi Kalıcı Olarak Sil (Departman, AI ajanı veya proje yoksa silinebilir)"
                          >
                            {processingId === 'delete-tenant-' + t.id ? (
                              <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                            ) : (
                              <Trash2 style={{ width: 13, height: 13 }} />
                            )}
                            <span>Sil</span>
                          </button>
                        ) : (
                          <span
                            style={{
                              padding: '6px 8px',
                              fontSize: '0.70rem',
                              fontWeight: 600,
                              color: 'var(--ac-38bdf8)',
                              background: 'rgba(56, 189, 248, 0.08)',
                              border: '1px solid rgba(56, 189, 248, 0.25)',
                              borderRadius: '6px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '4px'
                            }}
                            title="Ana sistem şirketi silinemez"
                          >
                            🛡️ Ana Şirket
                          </span>
                        )}

                        <button
                          onClick={() => handleOpenTenantDetails(t)}
                          className="super-admin-btn-corporate"
                          style={{ 
                            flex: '1 1 calc(50% - 6px)', 
                            minWidth: '105px',
                            justifyContent: 'center', 
                            fontSize: '0.72rem', 
                            padding: '6px 8px',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          <Edit style={{ width: 13, height: 13 }} />
                          <span>Detay & Yönetim</span>
                        </button>

                        {/* Manuel Hoş Geldin Mail Gönder */}
                        <button
                          onClick={() => handleSendManualWelcome(t)}
                          disabled={processingId === 'welcome-' + t.id}
                          className="super-admin-btn-secondary"
                          style={{ 
                            flex: '1 1 calc(50% - 6px)', 
                            minWidth: '100px',
                            justifyContent: 'center',
                            padding: '6px 8px', 
                            fontSize: '0.72rem', 
                            whiteSpace: 'nowrap',
                            color: 'var(--ac-38bdf8)', 
                            borderColor: 'rgba(56,189,248,0.3)' 
                          }}
                          title="Hoş Geldiniz E-postası Gönder"
                        >
                          {processingId === 'welcome-' + t.id ? (
                            <RefreshCw style={{ width: 13, height: 13 }} className="animate-spin" />
                          ) : (
                            <Mail style={{ width: 13, height: 13 }} />
                          )}
                          <span>Hoş Geldin Maili</span>
                        </button>

                        {/* Manuel Hatırlatıcı Mail Gönder */}
                        {t.is_active && (
                          <button
                            onClick={() => handleSendManualReminder(t)}
                            disabled={processingId === 'reminder-' + t.id}
                            className="super-admin-btn-secondary"
                            style={{ 
                              flex: '1 1 calc(50% - 6px)', 
                              minWidth: '95px',
                              justifyContent: 'center',
                              padding: '6px 8px', 
                              fontSize: '0.72rem', 
                              whiteSpace: 'nowrap',
                              color: '#f59e0b', 
                              borderColor: 'rgba(245,158,11,0.3)' 
                            }}
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

                        {onSwitchToCompanyAdmin && (
                          <button
                            onClick={() => onSwitchToCompanyAdmin(t)}
                            className="super-admin-btn-secondary"
                            title="Şirket Yönetim Paneline Geç (Departmanlar, Ünvanlar, AI Ajanlar)"
                            style={{ flex: '0 0 auto', padding: '6px 8px', justifyContent: 'center', color: 'var(--ac-c084fc)', borderColor: 'rgba(113,52,226,0.4)', background: 'rgba(113,52,226,0.1)' }}
                          >
                            <Building2 style={{ width: 14, height: 14 }} />
                          </button>
                        )}

                        {onSwitchToWorkspace && (
                          <button
                            onClick={() => onSwitchToWorkspace(t)}
                            className="super-admin-btn-secondary"
                            title="Şirket Çalışma Alanına Geç"
                            style={{ flex: '0 0 auto', padding: '6px 8px', justifyContent: 'center' }}
                          >
                            <ChevronRight style={{ width: 15, height: 15 }} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* LİSTE FORMAT GÖRÜNÜMÜ (Madde 11 & Madde 2) */}
              {tenantViewMode === 'LIST' && (
                <div 
                  className="super-admin-table-container"
                  style={{
                    overflowX: 'auto',
                    maxWidth: '100%',
                    scrollbarWidth: 'thin'
                  }}
                >
                  <table className="super-admin-table" style={{ minWidth: '1550px' }}>
                    <thead>
                      <tr>
                        <th style={{ whiteSpace: 'nowrap' }}>Durum</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 180 }}>Firma Adı & Kimlik</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 140 }}>Vergi No / Dairesi</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 120 }}>Telefon</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 160 }}>Web Adres</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 130 }}>Yönetici Adı</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 160 }}>Email</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 120 }}>Aldığı Paket</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 120 }}>Kira Bitiş Tarihi</th>
                        <th style={{ whiteSpace: 'nowrap', minWidth: 130 }}>3 Ay Uyarısı</th>
                        <th style={{ textAlign: 'right', whiteSpace: 'nowrap', minWidth: 240 }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTenants.length === 0 ? (
                        <tr>
                          <td colSpan="11" style={{ textAlign: 'center', padding: '30px', color: 'var(--nt-94a3b8)' }}>
                            Aramaya uygun şirket kaydı bulunamadı.
                          </td>
                        </tr>
                      ) : (
                        filteredTenants.map((t) => (
                          <tr key={t.id} style={t.is_warning_3_months ? { background: 'rgba(239,68,68,0.06)' } : {}}>
                            {/* 1. Onay & Aktiflik Durumu İkonu */}
                            <td style={{ whiteSpace: 'nowrap' }}>
                              {t.is_active ? (
                                <span style={{ background: 'rgba(16,185,129,0.2)', color: 'var(--ac-6ee7b7)', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                  <CheckCircle2 style={{ width: 12, height: 12 }} /> Aktif
                                </span>
                              ) : (
                                <span style={{ background: 'rgba(239,68,68,0.2)', color: 'var(--ac-fca5a5)', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                  <PauseCircle style={{ width: 12, height: 12 }} /> Pasif
                                </span>
                              )}
                            </td>

                            {/* 2. Firma Adı, Slug & Sektörler (Madde 1) */}
                            <td style={{ whiteSpace: 'nowrap' }}>
                              <div style={{ fontWeight: 800, color: 'var(--nt-ffffff)' }}>{t.name}</div>
                              <div style={{ fontSize: '0.68rem', color: 'var(--ac-38bdf8)', fontFamily: 'monospace' }}>
                                URL: {t.slug}
                              </div>
                              {t.sectors && t.sectors.length > 0 && (
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginTop: 4 }}>
                                  {t.sectors.map((secName, sIdx) => {
                                    const sObj = sectors.find(s => s.name === secName || s.code === secName);
                                    return (
                                      <span
                                        key={sIdx}
                                        style={{
                                          padding: '1px 6px',
                                          borderRadius: 4,
                                          fontSize: '0.65rem',
                                          fontWeight: 700,
                                          background: 'rgba(99,102,241,0.2)',
                                          border: '1px solid rgba(129,140,248,0.3)',
                                          color: 'var(--ac-c7d2fe)',
                                          display: 'inline-flex',
                                          alignItems: 'center',
                                          gap: 3
                                        }}
                                      >
                                        <span>{sObj?.icon || '📁'}</span>
                                        <span>{secName}</span>
                                      </span>
                                    );
                                  })}
                                </div>
                              )}
                            </td>

                            {/* 3. Vergi No / Dairesi (Madde 12) */}
                            <td style={{ whiteSpace: 'nowrap' }}>
                              <div style={{ fontFamily: 'monospace', color: 'var(--nt-cbd5e1)' }}>{t.tax_id || '-'}</div>
                              <div style={{ fontSize: '0.68rem', color: 'var(--nt-94a3b8)' }}>{t.tax_office ? `${t.tax_office} V.D.` : 'V.D. Yok'}</div>
                            </td>

                            {/* 4. Telefon */}
                            <td style={{ fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', whiteSpace: 'nowrap' }}>{t.phone || '-'}</td>

                            {/* 5. Web Adres */}
                            <td style={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                              {t.website ? (
                                <a href={t.website.startsWith('http') ? t.website : `https://${t.website}`} target="_blank" rel="noreferrer" style={{ color: 'var(--ac-60a5fa)', display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none' }}>
                                  <span>{t.website.replace('https://', '').replace('http://', '')}</span>
                                  <ExternalLink style={{ width: 11, height: 11 }} />
                                </a>
                              ) : '-'}
                            </td>

                            {/* 6. Yönetici Adı */}
                            <td style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--nt-e2e8f0)', whiteSpace: 'nowrap' }}>{t.admin_name || '-'}</td>

                            {/* 7. Email */}
                            <td style={{ fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', whiteSpace: 'nowrap' }}>{t.contact_email || '-'}</td>

                            {/* 8. Aldığı Paket */}
                            <td style={{ whiteSpace: 'nowrap' }}>
                              <span style={{ background: 'rgba(113,52,226,0.2)', color: 'var(--ac-c084fc)', padding: '2px 7px', borderRadius: 6, fontSize: '0.72rem', fontWeight: 700 }}>
                                {t.plan_name || 'Standart'}
                              </span>
                            </td>

                            {/* 9. Kira Bitiş Tarihi */}
                            <td style={{ fontSize: '0.75rem', fontWeight: 700, color: !t.is_active ? 'var(--ac-fbbf24)' : (t.is_warning_3_months ? 'var(--ac-f87171)' : 'var(--nt-ffffff)'), whiteSpace: 'nowrap' }}>
                              {!t.is_active ? 'Onay Bekliyor / Pasif' : (t.package_expiry_date ? new Date(t.package_expiry_date).toLocaleDateString('tr-TR') : '1 Yıl')}
                            </td>

                            {/* 10. 3 Ay Uyarısı */}
                            <td style={{ whiteSpace: 'nowrap' }}>
                              {!t.is_active ? (
                                <span style={{ color: 'var(--ac-fca5a5)', fontSize: '0.72rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                  <PauseCircle style={{ width: 12, height: 12 }} /> Pasif Durumda
                                </span>
                              ) : t.is_warning_3_months ? (
                                <span style={{ background: 'rgba(239,68,68,0.2)', color: 'var(--ac-fca5a5)', padding: '3px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                  <AlertTriangle style={{ width: 12, height: 12 }} />
                                  <span>3 Ay Kaldı ({t.days_remaining}g)</span>
                                </span>
                              ) : (
                                <span style={{ color: 'var(--nt-64748b)', fontSize: '0.72rem' }}>Normal ({t.days_remaining}g)</span>
                              )}
                            </td>

                            {/* 11. İşlemler */}
                            <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                                <button
                                  onClick={() => setCreditTenant(t)}
                                  className="super-admin-btn-secondary"
                                  style={{ padding: '5px 8px', fontSize: '0.72rem' }}
                                  title="Kredi durumu ve ek kredi yükleme"
                                >
                                  <Coins style={{ width: 12, height: 12, color: '#facc15' }} />
                                </button>
                                {/* Müşteri Kartını Pasife Al / Aktife Al Butonu (Madde 3: Yalnızca Kayıtlı Şirketler Listesinden Yapılır) */}
                                <button
                                  onClick={() => handleToggleTenantStatus(t)}
                                  disabled={processingId === 'toggle-status-' + t.id}
                                  className="super-admin-btn-secondary"
                                  style={{
                                    padding: '5px 8px',
                                    fontSize: '0.72rem',
                                    color: t.is_active ? 'var(--ac-f87171)' : 'var(--ac-34d399)',
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

                                {/* Şirketi Sil Butonu (Madde 1: Ana Şirket Silinemez) */}
                                {!isMainCompany(t) ? (
                                  <button
                                    onClick={() => handleDeleteTenant(t)}
                                    disabled={processingId === 'delete-tenant-' + t.id}
                                    className="super-admin-btn-secondary"
                                    style={{
                                      padding: '5px 8px',
                                      fontSize: '0.72rem',
                                      color: 'var(--ac-f87171)',
                                      borderColor: 'rgba(239,68,68,0.35)',
                                      background: 'rgba(239,68,68,0.08)'
                                    }}
                                    title="Şirketi Kalıcı Olarak Sil (Departman, AI ajan veya proje yoksa silinebilir)"
                                  >
                                    {processingId === 'delete-tenant-' + t.id ? (
                                      <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                                    ) : (
                                      <Trash2 style={{ width: 12, height: 12 }} />
                                    )}
                                    <span>Sil</span>
                                  </button>
                                ) : (
                                  <span
                                    style={{
                                      padding: '5px 8px',
                                      fontSize: '0.70rem',
                                      fontWeight: 600,
                                      color: 'var(--ac-38bdf8)',
                                      background: 'rgba(56, 189, 248, 0.08)',
                                      border: '1px solid rgba(56, 189, 248, 0.25)',
                                      borderRadius: '6px',
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: '4px'
                                    }}
                                    title="Ana sistem şirketi silinemez"
                                  >
                                    🛡️ Ana Şirket
                                  </span>
                                )}

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
                                  style={{ padding: '5px 8px', fontSize: '0.72rem', color: 'var(--ac-38bdf8)' }}
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

                                {onSwitchToCompanyAdmin && (
                                  <button
                                    onClick={() => onSwitchToCompanyAdmin(t)}
                                    className="super-admin-btn-secondary"
                                    style={{ padding: '5px 8px', color: 'var(--ac-c084fc)', borderColor: 'rgba(113,52,226,0.4)', background: 'rgba(113,52,226,0.1)' }}
                                    title="Şirket Yönetim Paneline Geç (Departmanlar, Ünvanlar, AI Ajanlar)"
                                  >
                                    <Building2 style={{ width: 13, height: 13 }} />
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
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <KeyRound style={{ width: 20, height: 20, color: 'var(--ac-fbbf24)' }} />
                    <span>Sistem Yetki ve İzin Kataloğu (RBAC)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
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
                          <span style={{ background: 'rgba(20,108,235,0.2)', color: 'var(--ac-60a5fa)', padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.68rem', fontWeight: 700 }}>
                            {perm.module}
                          </span>
                          <span style={{ fontFamily: 'monospace', fontWeight: 800, color: 'var(--ac-a78bfa)', fontSize: '0.75rem' }}>
                            {perm.code}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--nt-ffffff)', margin: '6px 0 4px 0' }}>{perm.name}</h4>
                        <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: '4px 0 10px 0', lineHeight: 1.4 }}>{perm.description || '-'}</p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
                          {(perm.default_for_roles || []).map((r, i) => (
                            <span key={i} style={{ background: 'rgb(var(--rgb-ov) / 0.06)', color: 'var(--nt-cbd5e1)', padding: '2px 6px', borderRadius: 4, fontSize: '0.65rem' }}>
                              {r}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6, marginTop: 14, paddingTop: 10, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
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
                          style={{ padding: '5px 8px', color: 'var(--ac-f87171)' }}
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
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: 'var(--ac-a78bfa)' }}>{perm.code}</td>
                          <td>
                            <span style={{ background: 'rgba(20,108,235,0.2)', color: 'var(--ac-60a5fa)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.68rem' }}>
                              {perm.module}
                            </span>
                          </td>
                          <td>
                            <div style={{ fontWeight: 700, color: 'var(--nt-ffffff)' }}>{perm.name}</div>
                            <div style={{ fontSize: '0.725rem', color: 'var(--nt-94a3b8)' }}>{perm.description || '-'}</div>
                          </td>
                          <td>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                              {perm.default_for_roles && perm.default_for_roles.map((r, i) => (
                                <span key={i} style={{ background: 'rgb(var(--rgb-ov) / 0.06)', padding: '2px 5px', borderRadius: 4, fontSize: '0.65rem' }}>
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
                              style={{ padding: '5px 8px', color: 'var(--ac-f87171)' }}
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

          {/* TAB 3.5: YETKİ ROLLERİ YÖNETİMİ (Madde 1) */}
          {activeTab === 'ROLES' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Sayfa Başlığı ve İşlemler */}
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <ShieldCheck style={{ width: 20, height: 20, color: '#10b981' }} />
                    <span>Yetki Rolleri Yönetimi (RBAC Roles)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
                    Kullanıcı ve aktörlerin sistem üzerindeki Yetki Rollerini tanımlayın, İzin Kataloğundan yetkileri çoklu olarak eşleştirin.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    onClick={() => handleOpenRoleModal(null)}
                    className="super-admin-btn-corporate"
                    style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', boxShadow: '0 0 14px rgba(16,185,129,0.35)' }}
                  >
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>Yeni Rol Tanımla</span>
                  </button>

                  {renderViewModeToggle(roleViewMode, setRoleViewMode)}

                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Rol adı veya izin ara..."
                    className="super-admin-input"
                    style={{ width: 220 }}
                  />
                </div>
              </div>

              {/* KPI Özet Kartları */}
              <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                <div style={{ background: 'rgb(var(--rgb-ov) / 0.02)', border: '1px solid rgb(var(--rgb-ov) / 0.06)', borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 38, height: 38, borderRadius: 8, background: 'rgba(16,185,129,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#10b981' }}>
                    <ShieldCheck style={{ width: 20, height: 20 }} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)', fontWeight: 600 }}>Tanımlı Yetki Rolü</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 900, color: 'var(--nt-ffffff)', fontFamily: 'monospace' }}>{roles.length}</div>
                  </div>
                </div>

                <div style={{ background: 'rgb(var(--rgb-ov) / 0.02)', border: '1px solid rgb(var(--rgb-ov) / 0.06)', borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 38, height: 38, borderRadius: 8, background: 'rgba(129,140,248,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ac-818cf8)' }}>
                    <Layers style={{ width: 20, height: 20 }} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)', fontWeight: 600 }}>Sistem / Global Roller</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 900, color: 'var(--ac-818cf8)', fontFamily: 'monospace' }}>
                      {roles.filter(r => r.is_system).length}
                    </div>
                  </div>
                </div>

                <div style={{ background: 'rgb(var(--rgb-ov) / 0.02)', border: '1px solid rgb(var(--rgb-ov) / 0.06)', borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 38, height: 38, borderRadius: 8, background: 'rgba(245,158,11,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
                    <KeyRound style={{ width: 20, height: 20 }} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)', fontWeight: 600 }}>İzin Kataloğu Havuzu</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 900, color: 'var(--ac-fbbf24)', fontFamily: 'monospace' }}>
                      {permissions.length} İzin
                    </div>
                  </div>
                </div>

                <div style={{ background: 'rgb(var(--rgb-ov) / 0.02)', border: '1px solid rgb(var(--rgb-ov) / 0.06)', borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 38, height: 38, borderRadius: 8, background: 'rgba(56,189,248,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ac-38bdf8)' }}>
                    <User style={{ width: 20, height: 20 }} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)', fontWeight: 600 }}>Atanmış Aktör / Personel</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 900, color: 'var(--ac-38bdf8)', fontFamily: 'monospace' }}>
                      {roles.reduce((acc, r) => acc + (r.actor_count || 0), 0)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Rol Kartları (KANBAN Görünümü) */}
              {roleViewMode === 'KANBAN' ? (
                <div className="super-admin-card-grid">
                  {filteredRoles.map((role) => {
                    const rolePerms = role.permissions || [];
                    return (
                      <div
                        key={role.id}
                        className="super-admin-card"
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          border: role.is_system ? '1px solid rgba(16,185,129,0.3)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                          background: 'linear-gradient(180deg, rgb(var(--rgb-ov) / 0.02) 0%, rgb(var(--rgb-shade) / calc(0.25 * var(--shade-k))) 100%)'
                        }}
                      >
                        <div>
                          {/* Başlık & Rozetler */}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                            <span
                              style={{
                                fontSize: '0.675rem',
                                fontWeight: 800,
                                padding: '2px 8px',
                                borderRadius: 4,
                                background: role.is_system ? 'rgba(16,185,129,0.2)' : 'rgba(129,140,248,0.2)',
                                color: role.is_system ? 'var(--ac-34d399)' : 'var(--ac-a78bfa)',
                                border: role.is_system ? '1px solid rgba(16,185,129,0.3)' : '1px solid rgba(129,140,248,0.3)'
                              }}
                            >
                              {role.is_system ? '🛡️ SİSTEM ROLÜ' : '🏢 ÖZEL ROL'}
                            </span>

                            <span
                              style={{
                                fontSize: '0.68rem',
                                color: role.actor_count > 0 ? 'var(--ac-38bdf8)' : 'var(--nt-64748b)',
                                fontWeight: 700,
                                display: 'flex',
                                alignItems: 'center',
                                gap: 4
                              }}
                            >
                              <User style={{ width: 12, height: 12 }} />
                              <span>{role.actor_count > 0 ? `${role.actor_count} Aktör` : 'Atanmamış'}</span>
                            </span>
                          </div>

                          {/* Rol Adı & Açıklaması */}
                          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)', marginBottom: 6, lineHeight: 1.3 }}>
                            {role.name}
                          </h3>
                          <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', lineHeight: 1.45, minHeight: 38, marginBottom: 14 }}>
                            {role.description || 'Bu yetki rolü için henüz bir açıklama girilmemiş.'}
                          </p>

                          {/* İzin Kataloğu Yetkileri */}
                          <div style={{ borderTop: '1px solid rgb(var(--rgb-ov) / 0.06)', paddingTop: 10, marginTop: 10 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                İzin Kataloğu Yetkileri
                              </span>
                              <span
                                style={{
                                  fontSize: '0.68rem',
                                  fontWeight: 800,
                                  color: rolePerms.length > 0 ? '#10b981' : 'var(--ac-f87171)',
                                  background: rolePerms.length > 0 ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                                  padding: '1px 6px',
                                  borderRadius: 4
                                }}
                              >
                                {rolePerms.length} İzin Seçili
                              </span>
                            </div>

                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, minHeight: 48, maxHeight: 90, overflowY: 'auto' }}>
                              {rolePerms.length === 0 ? (
                                <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontStyle: 'italic' }}>
                                  Henüz izin kataloğundan yetki seçilmedi.
                                </span>
                              ) : (
                                <>
                                  {rolePerms.slice(0, 6).map((code) => {
                                    const pObj = permissions.find(p => p.code === code);
                                    return (
                                      <span
                                        key={code}
                                        style={{
                                          fontSize: '0.65rem',
                                          fontFamily: 'monospace',
                                          padding: '2px 6px',
                                          borderRadius: 4,
                                          background: 'rgb(var(--rgb-ov) / 0.06)',
                                          color: 'var(--nt-e2e8f0)',
                                          border: '1px solid rgb(var(--rgb-ov) / 0.08)'
                                        }}
                                        title={pObj?.name || code}
                                      >
                                        {code}
                                      </span>
                                    );
                                  })}
                                  {rolePerms.length > 6 && (
                                    <span
                                      style={{
                                        fontSize: '0.65rem',
                                        fontWeight: 700,
                                        padding: '2px 6px',
                                        borderRadius: 4,
                                        background: 'rgba(16,185,129,0.15)',
                                        color: 'var(--ac-34d399)',
                                        border: '1px solid rgba(16,185,129,0.3)'
                                      }}
                                    >
                                      +{rolePerms.length - 6} diğer izin
                                    </span>
                                  )}
                                </>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Kart Aksiyonları */}
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 8,
                            marginTop: 16,
                            paddingTop: 12,
                            borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)'
                          }}
                        >
                          <button
                            onClick={() => handleOpenRoleModal(role)}
                            className="super-admin-btn-secondary"
                            style={{ flex: 1, justifyContent: 'center' }}
                          >
                            <Edit style={{ width: 13, height: 13 }} />
                            <span>Düzenle & İzinler</span>
                          </button>
                          <button
                            onClick={() => handleDeleteRole(role)}
                            className="super-admin-btn-secondary"
                            style={{ color: 'var(--ac-f87171)' }}
                            title="Rolü Sil"
                          >
                            <Trash2 style={{ width: 13, height: 13 }} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                /* TABLO GÖRÜNÜMÜ */
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th>Rol Adı & Kapsam</th>
                        <th>Rol Açıklaması</th>
                        <th>Seçili İzin Kataloğu Yetkileri</th>
                        <th>Bağlı Aktörler</th>
                        <th>Oluşturulma Tarihi</th>
                        <th style={{ textAlign: 'right' }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredRoles.map((role) => {
                        const rolePerms = role.permissions || [];
                        return (
                          <tr key={role.id}>
                            <td>
                              <div style={{ fontWeight: 800, color: 'var(--nt-ffffff)', fontSize: '0.85rem' }}>{role.name}</div>
                              <span
                                style={{
                                  fontSize: '0.62rem',
                                  fontWeight: 800,
                                  padding: '1px 6px',
                                  borderRadius: 4,
                                  background: role.is_system ? 'rgba(16,185,129,0.2)' : 'rgba(129,140,248,0.2)',
                                  color: role.is_system ? 'var(--ac-34d399)' : 'var(--ac-a78bfa)'
                                }}
                              >
                                {role.is_system ? 'SİSTEM ROLÜ' : 'ÖZEL ROL'}
                              </span>
                            </td>
                            <td>
                              <div style={{ fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', maxWidth: 260, lineHeight: 1.4 }}>
                                {role.description || '-'}
                              </div>
                            </td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', maxWidth: 380 }}>
                                <span
                                  style={{
                                    fontSize: '0.68rem',
                                    fontWeight: 800,
                                    padding: '2px 6px',
                                    borderRadius: 4,
                                    background: 'rgba(16,185,129,0.15)',
                                    color: 'var(--ac-34d399)'
                                  }}
                                >
                                  {rolePerms.length} İzin
                                </span>
                                {rolePerms.slice(0, 4).map(code => (
                                  <span key={code} style={{ fontSize: '0.65rem', fontFamily: 'monospace', background: 'rgb(var(--rgb-ov) / 0.06)', padding: '2px 5px', borderRadius: 4, color: 'var(--nt-94a3b8)' }}>
                                    {code}
                                  </span>
                                ))}
                                {rolePerms.length > 4 && (
                                  <span style={{ fontSize: '0.65rem', color: 'var(--nt-64748b)' }}>+{rolePerms.length - 4} diğer</span>
                                )}
                              </div>
                            </td>
                            <td>
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: role.actor_count > 0 ? 'var(--ac-38bdf8)' : 'var(--nt-64748b)' }}>
                                {role.actor_count || 0} Aktör
                              </span>
                            </td>
                            <td>
                              <span style={{ fontSize: '0.72rem', color: 'var(--nt-94a3b8)', fontFamily: 'monospace' }}>
                                {role.created_at ? new Date(role.created_at).toLocaleDateString('tr-TR') : '-'}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <button
                                onClick={() => handleOpenRoleModal(role)}
                                className="super-admin-btn-secondary"
                                style={{ padding: '5px 8px', marginRight: 6 }}
                                title="Düzenle & İzinler"
                              >
                                <Edit style={{ width: 13, height: 13 }} />
                              </button>
                              <button
                                onClick={() => handleDeleteRole(role)}
                                className="super-admin-btn-secondary"
                                style={{ padding: '5px 8px', color: 'var(--ac-f87171)' }}
                                title="Sil"
                              >
                                <Trash2 style={{ width: 13, height: 13 }} />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
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
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Package style={{ width: 20, height: 20, color: 'var(--ac-34d399)' }} />
                    <span>Kiralama Paketleri Yönetimi</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
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
                          <span style={{ fontFamily: 'monospace', fontWeight: 800, fontSize: '0.75rem', background: 'rgba(113,52,226,0.2)', color: 'var(--ac-c084fc)', padding: '2px 8px', borderRadius: 4 }}>
                            {p.code}
                          </span>
                          <span style={{ fontSize: '0.68rem', fontWeight: 800, color: p.is_active ? 'var(--ac-34d399)' : 'var(--ac-f87171)' }}>
                            {p.is_active ? 'AKTİF' : 'PASİF'}
                          </span>
                        </div>

                        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--nt-ffffff)', marginTop: 10 }}>{p.name}</h3>
                        <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', marginTop: 4 }}>{p.description}</p>

                        <div style={{ marginTop: 16, marginBottom: 16 }}>
                          <span style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--nt-ffffff)' }}>
                            {Number(p.monthly_price).toLocaleString('tr-TR')}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', marginLeft: 4 }}>{p.currency} / ay</span>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)', paddingTop: 12 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>İnsan Kullanıcı:</span>
                            <b>{p.max_humans}</b>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>AI Ajan Personel:</span>
                            <b>{p.max_agents}</b>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>Aylık Kredi:</span>
                            <b>{p.monthly_credits}</b>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>Özel AI Ünvan Tanımlama:</span>
                            <b style={{ color: p.can_create_custom_titles ? 'var(--ac-34d399)' : 'var(--nt-64748b)' }}>
                              {p.can_create_custom_titles ? 'Evet' : 'Hayır'}
                            </b>
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 18, paddingTop: 14, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
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
                          style={{ color: 'var(--ac-f87171)' }}
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
                            <div style={{ fontWeight: 800, color: 'var(--nt-ffffff)' }}>{p.name}</div>
                            <div style={{ fontFamily: 'monospace', fontSize: '0.725rem', color: 'var(--ac-a78bfa)' }}>{p.code}</div>
                          </td>
                          <td>
                            <span style={{ fontWeight: 800, color: 'var(--ac-38bdf8)' }}>{Number(p.monthly_price).toLocaleString('tr-TR')} {p.currency}</span>
                            <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)' }}> / ay</span>
                          </td>
                          <td>
                            <span style={{ fontSize: '0.75rem', color: 'var(--nt-cbd5e1)' }}>
                              {p.max_humans} İnsan | {p.max_agents} Ajan | {p.monthly_credits} Kredi
                            </span>
                          </td>
                          <td>
                            <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--nt-cbd5e1)' }}>{p.storage_gb} GB</span>
                          </td>
                          <td>
                            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: p.can_create_custom_titles ? 'var(--ac-34d399)' : 'var(--nt-64748b)' }}>
                              {p.can_create_custom_titles ? '✓ İzinli' : '✗ Kapalı'}
                            </span>
                          </td>
                          <td>
                            <span style={{
                              fontSize: '0.68rem', fontWeight: 800, padding: '2px 8px', borderRadius: 999,
                              background: p.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                              color: p.is_active ? 'var(--ac-34d399)' : 'var(--ac-f87171)'
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
                              style={{ padding: '5px 8px', color: 'var(--ac-f87171)' }}
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
            <div className="ai-stack">
              <ModelSettingsPanel />
              <PlatformUsagePanel />
            </div>
          )}

          {activeTab === 'AI_ASSISTANT' && <PlatformAssistantPanel />}

          {activeTab === 'LLM_PRICES' && <LlmPricing />}

          {activeTab === 'CATALOG' && <CatalogAdmin />}

          {/* TAB 6: EVREN MODELLERİ (Madde 8) */}
          {activeTab === 'MODELS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Cpu style={{ width: 20, height: 20, color: 'var(--ac-a78bfa)' }} />
                    <span>EVREN Modelleri Kataloğu</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
                    TÜBİTAK BİLGEM EVREN modelleri ve sisteme yeni eklenebilecek modellerin yönetimi.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button onClick={handleSyncEvrenModels} disabled={syncingModels} className="super-admin-btn-secondary" title="EVREN model kataloğunu çek: bağlam, çıktı sınırı ve fiyat bilgilerini güncelle, yeni modelleri pasif ekle">
                    <RefreshCw style={{ width: 14, height: 14 }} className={syncingModels ? 'animate-spin' : ''} />
                    <span>EVREN'den Modelleri Çek</span>
                  </button>
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
                          <span style={{ background: 'rgb(var(--rgb-ov) / 0.06)', padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.68rem', color: 'var(--nt-cbd5e1)' }}>
                            {m.model_type}
                          </span>
                          <span style={{
                            padding: '2px 6px', borderRadius: 4, fontSize: '0.68rem', fontWeight: 800,
                            background: m.status === 'ACTIVE' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                            color: m.status === 'ACTIVE' ? 'var(--ac-6ee7b7)' : 'var(--ac-fca5a5)'
                          }}>
                            {m.status}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--ac-38bdf8)', margin: '4px 0 2px 0' }}>{m.display_name}</h4>
                        <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--nt-94a3b8)', marginBottom: 12 }}>{m.model_code}</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', borderTop: '1px solid rgb(var(--rgb-ov) / 0.06)', paddingTop: 10 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>Bağlam Penceresi:</span>
                            <b style={{ fontFamily: 'monospace' }}>{m.context_window?.toLocaleString()} token</b>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>Efor Katsayısı:</span>
                            <b style={{ fontFamily: 'monospace' }}>{m.effort_coefficient}x</b>
                          </div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6, marginTop: 14, paddingTop: 10, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
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
                          style={{ padding: '5px 8px', color: 'var(--ac-f87171)' }}
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
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: 'var(--nt-ffffff)' }}>{m.model_code}</td>
                          <td style={{ fontWeight: 700, color: 'var(--ac-38bdf8)' }}>{m.display_name}</td>
                          <td>
                            <span style={{ background: 'rgb(var(--rgb-ov) / 0.06)', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.68rem' }}>
                              {m.model_type}
                            </span>
                          </td>
                          <td style={{ fontFamily: 'monospace' }}>{m.context_window.toLocaleString()} token</td>
                          <td style={{ fontFamily: 'monospace' }}>{m.effort_coefficient}x</td>
                          <td>
                            <span style={{
                              padding: '2px 6px', borderRadius: 4, fontSize: '0.68rem', fontWeight: 800,
                              background: m.status === 'ACTIVE' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                              color: m.status === 'ACTIVE' ? 'var(--ac-6ee7b7)' : 'var(--ac-fca5a5)'
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
                              style={{ padding: '5px 8px', color: 'var(--ac-f87171)' }}
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

          {/* ======================================================== */}
          {/* TAB: SEKTÖR TANIMLAMA MODÜLÜ (TİCARET BAKANLIĞI)        */}
          {/* ======================================================== */}
          {activeTab === 'SECTORS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Layers style={{ width: 20, height: 20, color: '#10b981' }} />
                    <span>Sektör Tanımları (Ticaret Bakanlığı)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
                    T.C. Ticaret Bakanlığı resmi sektör kataloğu ve bağlı meslek grupları yönetim modülü.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button onClick={() => handleOpenSectorModal(null)} className="super-admin-btn-corporate">
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>Yeni Sektör Ekle</span>
                  </button>
                  {renderViewModeToggle(sectorViewMode, setSectorViewMode)}
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Sektör kodu veya adı ara..."
                    className="super-admin-input"
                    style={{ width: 250 }}
                  />
                </div>
              </div>

              {sectorViewMode === 'KANBAN' ? (
                <div className="super-admin-card-grid">
                  {filteredSectors.map((sec) => {
                    const profCount = professions.filter(p => p.sector_code === sec.code).length;
                    return (
                      <div key={sec.code} className="super-admin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                              {sec.image_url ? (
                                <img
                                  src={sec.image_url}
                                  alt={sec.name}
                                  style={{ width: 36, height: 36, borderRadius: 8, objectFit: 'cover', border: '1px solid rgb(var(--rgb-ov) / 0.12)' }}
                                />
                              ) : (
                                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgb(var(--rgb-ov) / 0.06)', border: '1px solid rgb(var(--rgb-ov) / 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.35rem' }}>
                                  {sec.icon || '🏢'}
                                </div>
                              )}
                              <span style={{ fontSize: '0.85rem', fontFamily: 'monospace', fontWeight: 800, padding: '4px 10px', borderRadius: 6, background: 'rgba(16, 185, 129, 0.15)', color: 'var(--ac-34d399)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                                Sektör Kodu: {sec.code}
                              </span>
                            </div>
                            <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '2px 8px', borderRadius: 4, background: sec.is_active ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: sec.is_active ? 'var(--ac-4ade80)' : 'var(--ac-f87171)' }}>
                              {sec.is_active ? '● Aktif' : '○ Pasif'}
                            </span>
                          </div>

                          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)', marginBottom: 6 }}>{sec.name}</h3>
                          <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', lineHeight: 1.4, marginBottom: 12 }}>
                            {sec.description || 'T.C. Ticaret Bakanlığı ana sektör tanımı.'}
                          </p>

                          <div style={{ padding: '8px 12px', borderRadius: 8, background: 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))', border: '1px solid rgb(var(--rgb-ov) / 0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>Bağlı Meslek Sayısı:</span>
                            <button
                              onClick={() => {
                                setProfessionsFilterSector(sec.code);
                                setProfessionSearch('');
                                setSearchQuery('');
                                switchTab('PROFESSIONS');
                              }}
                              style={{ background: 'transparent', border: 'none', color: 'var(--ac-38bdf8)', fontWeight: 800, fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'underline' }}
                            >
                              {profCount} Meslek Tanımı →
                            </button>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                          <button
                            onClick={() => handleOpenSectorModal(sec)}
                            className="super-admin-btn-corporate"
                            style={{ flex: 1, justifyContent: 'center', fontSize: '0.785rem', padding: '6px 10px' }}
                          >
                            <Edit style={{ width: 13, height: 13 }} />
                            <span>Düzenle</span>
                          </button>
                          <button
                            onClick={() => handleDeleteSector(sec)}
                            className="super-admin-btn-secondary"
                            style={{ padding: '6px 8px', color: 'var(--ac-f87171)' }}
                            title="Sektörü Sil"
                          >
                            <Trash2 style={{ width: 13, height: 13 }} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th style={{ width: 110 }}>Sektör Kodu</th>
                        <th>Sektör Adı & İkon</th>
                        <th>Açıklama</th>
                        <th style={{ width: 150 }}>Bağlı Meslek Sayısı</th>
                        <th style={{ width: 90 }}>Durum</th>
                        <th style={{ textAlign: 'right', width: 110 }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredSectors.map((sec) => {
                        const profCount = professions.filter(p => p.sector_code === sec.code).length;
                        return (
                          <tr key={sec.code}>
                            <td style={{ fontFamily: 'monospace', fontWeight: 800, color: 'var(--ac-34d399)', fontSize: '0.9rem' }}>{sec.code}</td>
                            <td style={{ fontWeight: 800, color: 'var(--nt-ffffff)' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                {sec.image_url ? (
                                  <img src={sec.image_url} alt={sec.name} style={{ width: 28, height: 28, borderRadius: 6, objectFit: 'cover', border: '1px solid rgb(var(--rgb-ov) / 0.1)' }} />
                                ) : (
                                  <span style={{ fontSize: '1.25rem', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, borderRadius: 6, background: 'rgb(var(--rgb-ov) / 0.05)' }}>
                                    {sec.icon || '🏢'}
                                  </span>
                                )}
                                <span>{sec.name}</span>
                              </div>
                            </td>
                            <td style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)' }}>{sec.description || '-'}</td>
                            <td>
                              <button
                                onClick={() => {
                                  setProfessionsFilterSector(sec.code);
                                  setProfessionSearch('');
                                  setSearchQuery('');
                                  switchTab('PROFESSIONS');
                                }}
                                style={{
                                  background: 'rgba(56, 189, 248, 0.1)',
                                  border: '1px solid rgba(56, 189, 248, 0.3)',
                                  color: 'var(--ac-38bdf8)',
                                  padding: '3px 8px',
                                  borderRadius: 6,
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                  cursor: 'pointer'
                                }}
                              >
                                {profCount} Meslek Tanımı →
                              </button>
                            </td>
                            <td>
                              <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '2px 8px', borderRadius: 4, background: sec.is_active ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: sec.is_active ? 'var(--ac-4ade80)' : 'var(--ac-f87171)' }}>
                                {sec.is_active ? 'Aktif' : 'Pasif'}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <button
                                onClick={() => handleOpenSectorModal(sec)}
                                className="super-admin-btn-secondary"
                                style={{ padding: '5px 8px', marginRight: 4 }}
                                title="Düzenle"
                              >
                                <Edit style={{ width: 12, height: 12 }} />
                              </button>
                              <button
                                onClick={() => handleDeleteSector(sec)}
                                className="super-admin-btn-secondary"
                                style={{ padding: '5px 8px', color: 'var(--ac-f87171)' }}
                                title="Sil"
                              >
                                <Trash2 style={{ width: 12, height: 12 }} />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB: MESLEK GRUBU TANIMLAMA MODÜLÜ (TİCARET BAKANLIĞI)    */}
          {/* ======================================================== */}
          {activeTab === 'PROFESSIONS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="super-admin-page-header">
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Briefcase style={{ width: 20, height: 20, color: 'var(--ac-38bdf8)' }} />
                    <span>Meslek Grubu Tanımları (Ticaret Bakanlığı)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
                    T.C. Ticaret Bakanlığı sektörlerine bağlı 184 resmi meslek grubu tanımı ve yönetimi.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button onClick={() => handleOpenProfessionModal(null)} className="super-admin-btn-corporate">
                    <Plus style={{ width: 14, height: 14 }} />
                    <span>Yeni Meslek Ekle</span>
                  </button>
                  {renderViewModeToggle(professionViewMode, setProfessionViewMode)}
                  <input
                    type="text"
                    value={professionSearch}
                    onChange={(e) => setProfessionSearch(e.target.value)}
                    placeholder="Meslek kodu veya adı ara..."
                    className="super-admin-input"
                    style={{ width: 220 }}
                  />
                </div>
              </div>

              {/* Sektöre Göre Filtreleme Barı */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center', background: 'rgb(var(--rgb-ov) / 0.02)', padding: '10px 14px', borderRadius: 10, border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--nt-94a3b8)', textTransform: 'uppercase', marginRight: 4 }}>
                  Sektör Filtresi:
                </span>
                <button
                  onClick={() => setProfessionsFilterSector('')}
                  className="super-admin-btn-secondary"
                  style={!professionsFilterSector ? { background: 'var(--ac-38bdf8)', color: '#0f172a', borderColor: 'var(--ac-38bdf8)', fontWeight: 800 } : { fontSize: '0.725rem' }}
                >
                  TÜM SEKTÖRLER ({professions.length})
                </button>
                {sectors.map((sec) => {
                  const count = professions.filter(p => p.sector_code === sec.code).length;
                  const isSelected = professionsFilterSector === sec.code;
                  return (
                    <button
                      key={sec.code}
                      onClick={() => setProfessionsFilterSector(sec.code)}
                      className="super-admin-btn-secondary"
                      style={isSelected ? { background: '#10b981', color: '#fff', borderColor: '#10b981', fontWeight: 800 } : { fontSize: '0.725rem' }}
                    >
                      {sec.code} - {sec.name} ({count})
                    </button>
                  );
                })}
              </div>

              {professionViewMode === 'KANBAN' ? (
                <div className="super-admin-card-grid">
                  {filteredProfessions.map((prof) => {
                    const parentSector = sectors.find(s => s.code === prof.sector_code);
                    return (
                      <div key={prof.code} className="super-admin-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                            <span style={{ fontFamily: 'monospace', fontWeight: 800, color: 'var(--ac-38bdf8)', background: 'rgba(56,189,248,0.15)', padding: '2px 8px', borderRadius: 6, fontSize: '0.8rem' }}>
                              {prof.code}
                            </span>
                            <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', color: 'var(--ac-34d399)', background: 'rgba(16,185,129,0.15)', padding: '2px 8px', borderRadius: 4, fontWeight: 700 }}>
                              Sektör: {prof.sector_code} {parentSector ? `(${parentSector.name})` : ''}
                            </span>
                          </div>
                          <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--nt-ffffff)', margin: '6px 0 4px 0' }}>{prof.name}</h4>
                          <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: '4px 0 8px 0', lineHeight: 1.4 }}>{prof.description || '-'}</p>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6, marginTop: 12, paddingTop: 10, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                          <button
                            onClick={() => handleOpenProfessionModal(prof)}
                            className="super-admin-btn-secondary"
                            style={{ padding: '5px 8px' }}
                            title="Düzenle"
                          >
                            <Edit style={{ width: 12, height: 12 }} />
                            <span style={{ fontSize: '0.72rem', marginLeft: 4 }}>Düzenle</span>
                          </button>
                          <button
                            onClick={() => handleDeleteProfession(prof)}
                            className="super-admin-btn-secondary"
                            style={{ padding: '5px 8px', color: 'var(--ac-f87171)' }}
                            title="Sil"
                          >
                            <Trash2 style={{ width: 12, height: 12 }} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="super-admin-table-container">
                  <table className="super-admin-table">
                    <thead>
                      <tr>
                        <th style={{ width: 120 }}>Meslek Kodu</th>
                        <th style={{ width: 130 }}>Sektör Kodu</th>
                        <th style={{ width: 220 }}>Sektör Adı</th>
                        <th>Meslek Tanım Adı</th>
                        <th>Açıklama</th>
                        <th style={{ width: 80 }}>Durum</th>
                        <th style={{ textAlign: 'right', width: 90 }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredProfessions.map((prof) => {
                        const parentSector = sectors.find(s => s.code === prof.sector_code);
                        return (
                          <tr key={prof.code}>
                            <td style={{ fontFamily: 'monospace', fontWeight: 800, color: 'var(--ac-38bdf8)' }}>{prof.code}</td>
                            <td style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--ac-34d399)' }}>{prof.sector_code}</td>
                            <td style={{ fontWeight: 600, color: 'var(--nt-cbd5e1)', fontSize: '0.785rem' }}>{parentSector?.name || '-'}</td>
                            <td style={{ fontWeight: 700, color: 'var(--nt-ffffff)' }}>{prof.name}</td>
                            <td style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>{prof.description || '-'}</td>
                            <td>
                              <span style={{ fontSize: '0.68rem', fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: prof.is_active ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: prof.is_active ? 'var(--ac-4ade80)' : 'var(--ac-f87171)' }}>
                                {prof.is_active ? 'Aktif' : 'Pasif'}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <button
                                onClick={() => handleOpenProfessionModal(prof)}
                                className="super-admin-btn-secondary"
                                style={{ padding: '5px 7px', marginRight: 4 }}
                                title="Düzenle"
                              >
                                <Edit style={{ width: 12, height: 12 }} />
                              </button>
                              <button
                                onClick={() => handleDeleteProfession(prof)}
                                className="super-admin-btn-secondary"
                                style={{ padding: '5px 7px', color: 'var(--ac-f87171)' }}
                                title="Sil"
                              >
                                <Trash2 style={{ width: 12, height: 12 }} />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
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
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Mail style={{ width: 20, height: 20, color: 'var(--ac-38bdf8)' }} />
                    <span>HTML E-Posta Şablonları & Canlı Editör</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
                    RECDx kurumsal logosunu içeren Hoş Geldiniz, 3 Ay Bitiş Hatırlatıcı ve özel e-posta şablonları.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    onClick={() => handleOpenTemplateModal(null)}
                    className="super-admin-btn-corporate"
                    style={{ background: 'linear-gradient(135deg, var(--ac-38bdf8) 0%, #1d4ed8 100%)' }}
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
                          <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: 'rgba(56,189,248,0.2)', color: 'var(--ac-38bdf8)' }}>
                            {tmpl.code}
                          </span>
                          <span style={{
                            padding: '2px 7px', borderRadius: 999, fontSize: '0.65rem', fontWeight: 800,
                            background: tmpl.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                            color: tmpl.is_active ? 'var(--ac-6ee7b7)' : 'var(--ac-fca5a5)'
                          }}>
                            {tmpl.is_active ? 'AKTİF' : 'PASİF'}
                          </span>
                        </div>

                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)', marginTop: 10 }}>{tmpl.name}</h3>
                        <div style={{ fontSize: '0.785rem', color: 'var(--nt-cbd5e1)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                          <strong style={{ color: 'var(--nt-94a3b8)' }}>Konu:</strong> {tmpl.subject}
                        </div>

                        {/* Değişken Rozetleri */}
                        <div style={{ marginTop: 12 }}>
                          <div style={{ fontSize: '0.68rem', color: 'var(--nt-94a3b8)', marginBottom: 4, fontWeight: 700 }}>DİNAMİK DEĞİŞKENLER:</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            {(tmpl.variables || []).map((v, i) => (
                              <span key={i} style={{ fontSize: '0.65rem', fontFamily: 'monospace', padding: '2px 6px', borderRadius: 4, background: 'rgb(var(--rgb-ov) / 0.06)', color: 'var(--ac-a78bfa)' }}>
                                {`{{${v}}}`}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* HTML Önizleme Kutusu */}
                        <div style={{ marginTop: 14, borderRadius: 8, overflow: 'hidden', border: '1px solid rgb(var(--rgb-ov) / 0.08)', height: 110, background: 'var(--sf-0b0f19)', position: 'relative' }}>
                          <iframe
                            title={tmpl.name}
                            srcDoc={tmpl.html_content}
                            sandbox=""
                            style={{ width: '100%', height: '100%', border: 'none', pointerEvents: 'none', transform: 'scale(0.7)', transformOrigin: 'top left', width: '142%', height: '142%' }}
                          />
                        </div>
                      </div>

                      {/* Aksiyon Butonları */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
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
                          style={{ padding: '6px 10px', fontSize: '0.75rem', color: 'var(--ac-38bdf8)' }}
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
                          style={{ color: 'var(--ac-f87171)', padding: '6px 8px' }}
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
                          <td style={{ fontFamily: 'monospace', fontWeight: 800, color: 'var(--ac-38bdf8)' }}>{tmpl.code}</td>
                          <td style={{ fontWeight: 700, color: 'var(--nt-ffffff)' }}>{tmpl.name}</td>
                          <td style={{ fontSize: '0.8rem', color: 'var(--nt-cbd5e1)' }}>{tmpl.subject}</td>
                          <td>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                              {(tmpl.variables || []).slice(0, 4).map((v, i) => (
                                <span key={i} style={{ fontSize: '0.62rem', fontFamily: 'monospace', padding: '1px 5px', borderRadius: 3, background: 'rgb(var(--rgb-ov) / 0.06)', color: 'var(--ac-a78bfa)' }}>
                                  {`{{${v}}}`}
                                </span>
                              ))}
                              {(tmpl.variables || []).length > 4 && (
                                <span style={{ fontSize: '0.62rem', color: 'var(--nt-64748b)' }}>+{tmpl.variables.length - 4}</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <span style={{
                              padding: '2px 7px', borderRadius: 999, fontSize: '0.65rem', fontWeight: 800,
                              background: tmpl.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                              color: tmpl.is_active ? 'var(--ac-6ee7b7)' : 'var(--ac-fca5a5)'
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
                              style={{ padding: '5px 7px', marginRight: 4, color: 'var(--ac-38bdf8)' }}
                              title="Test E-postası Gönder"
                            >
                              {processingId === 'test-mail-' + tmpl.id ? <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" /> : <Send style={{ width: 12, height: 12 }} />}
                            </button>
                            <button
                              onClick={() => handleDeleteTemplate(tmpl)}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', color: 'var(--ac-f87171)' }}
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
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Clock style={{ width: 20, height: 20, color: 'var(--ac-fbbf24)' }} />
                    <span>Otomatik Bildirim Zamanlayıcıları (Notification Schedules)</span>
                  </h2>
                  <p style={{ fontSize: '0.785rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
                    Kayıt sonrası tek seferlik gönderim ve paket bitişine 3 ay kala 15 günde bir periyodik hatırlatma kuralları.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    onClick={() => handleOpenScheduleModal(null)}
                    className="super-admin-btn-corporate"
                    style={{ background: 'linear-gradient(135deg, var(--ac-fbbf24) 0%, #d97706 100%)', color: '#000', fontWeight: 800 }}
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
                          <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: 'rgba(251,191,36,0.2)', color: 'var(--ac-fbbf24)' }}>
                            {sch.trigger_type}
                          </span>
                          <span style={{
                            padding: '2px 7px', borderRadius: 999, fontSize: '0.65rem', fontWeight: 800,
                            background: sch.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                            color: sch.is_active ? 'var(--ac-6ee7b7)' : 'var(--ac-fca5a5)'
                          }}>
                            {sch.is_active ? 'AKTİF' : 'PASİF'}
                          </span>
                        </div>

                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)', marginTop: 10 }}>{sch.name}</h3>

                        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8, fontSize: '0.785rem', color: 'var(--nt-cbd5e1)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 6, background: 'rgb(var(--rgb-ov) / 0.03)' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>Bağlı Şablon:</span>
                            <span style={{ fontFamily: 'monospace', color: 'var(--ac-38bdf8)', fontWeight: 700 }}>{sch.template_code}</span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 6, background: 'rgb(var(--rgb-ov) / 0.03)' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>Çalışma Mantığı:</span>
                            <span style={{ color: 'var(--nt-ffffff)', fontWeight: 700 }}>
                              {sch.trigger_type === 'ON_REGISTRATION'
                                ? 'Kayıt anında tek sefer gönder'
                                : `${sch.target_lead_days || 90} gün kala, her ${sch.frequency_days || 15} günde bir`}
                            </span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: 6, background: 'rgb(var(--rgb-ov) / 0.03)' }}>
                            <span style={{ color: 'var(--nt-94a3b8)' }}>Son Gönderim:</span>
                            <span style={{ color: 'var(--ac-a78bfa)' }}>
                              {sch.last_run_at ? new Date(sch.last_run_at).toLocaleString('tr-TR') : 'Henüz tetiklenmedi'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Aksiyon Butonları */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 16, paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                        <button
                          onClick={() => handleTriggerSchedule(sch)}
                          disabled={processingId === 'sched-' + sch.id}
                          className="super-admin-btn-corporate"
                          style={{ flex: 1, justifyContent: 'center', fontSize: '0.75rem', padding: '6px 10px', background: 'linear-gradient(135deg, var(--ac-fbbf24) 0%, #d97706 100%)', color: '#000', fontWeight: 800 }}
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
                          style={{ color: 'var(--ac-f87171)', padding: '6px 8px' }}
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
                            <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', fontWeight: 800, padding: '3px 8px', borderRadius: 6, background: 'rgba(251,191,36,0.2)', color: 'var(--ac-fbbf24)' }}>
                              {sch.trigger_type}
                            </span>
                          </td>
                          <td style={{ fontWeight: 700, color: 'var(--nt-ffffff)' }}>{sch.name}</td>
                          <td style={{ fontFamily: 'monospace', color: 'var(--ac-38bdf8)', fontWeight: 700 }}>{sch.template_code}</td>
                          <td style={{ fontSize: '0.8rem', color: 'var(--nt-cbd5e1)' }}>
                            {sch.trigger_type === 'ON_REGISTRATION'
                              ? 'Kayıt anında tek sefer gönderim'
                              : `${sch.target_lead_days || 90} gün kala, her ${sch.frequency_days || 15} günde bir`}
                          </td>
                          <td style={{ fontSize: '0.75rem', color: 'var(--ac-a78bfa)' }}>
                            {sch.last_run_at ? new Date(sch.last_run_at).toLocaleString('tr-TR') : 'Henüz çalışmadı'}
                          </td>
                          <td>
                            <span style={{
                              padding: '2px 7px', borderRadius: 999, fontSize: '0.65rem', fontWeight: 800,
                              background: sch.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
                              color: sch.is_active ? 'var(--ac-6ee7b7)' : 'var(--ac-fca5a5)'
                            }}>
                              {sch.is_active ? 'AKTİF' : 'PASİF'}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              onClick={() => handleTriggerSchedule(sch)}
                              disabled={processingId === 'sched-' + sch.id}
                              className="super-admin-btn-secondary"
                              style={{ padding: '5px 7px', marginRight: 4, color: 'var(--ac-fbbf24)' }}
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
                              style={{ padding: '5px 7px', color: 'var(--ac-f87171)' }}
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <User style={{ width: 18, height: 18 }} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--nt-ffffff)' }}>Süper Admin Profil Bilgileri</h3>
                  <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>Ad, telefon, e-posta, adres ve şifre güncelleyin.</p>
                </div>
              </div>
              <button onClick={() => setProfileModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Ad Soyad</label>
                <input
                  type="text"
                  required
                  value={profileForm.display_name}
                  onChange={(e) => setProfileForm({ ...profileForm, display_name: e.target.value })}
                  className="super-admin-input"
                />
              </div>

              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Telefon</label>
                  <input
                    type="text"
                    value={profileForm.phone}
                    onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                    placeholder="+90 5XX XXX XX XX"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>E-posta</label>
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
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Adres</label>
                <textarea
                  rows="3"
                  value={profileForm.address}
                  onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
                  placeholder="Maslak Teknopark, Sarıyer / İstanbul"
                  className="super-admin-input"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Yeni Şifre (İsteğe Bağlı)</label>
                <input
                  type="password"
                  value={profileForm.new_password}
                  onChange={(e) => setProfileForm({ ...profileForm, new_password: e.target.value })}
                  placeholder="Değiştirmek istemiyorsanız boş bırakın"
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)' }}>{tenantEditForm.name || 'Şirket Detayları'}</h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>Şirket bilgileri, onaylama ve Şirket Admin kullanıcısı.</p>
              </div>
              <button onClick={() => setTenantDetailModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            {/* Sekme Butonları: 1. Kurumsal Bilgiler | 2. Yönetici Tanımlaması */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)', paddingBottom: 10, flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => setTenantDetailActiveTab('COMPANY')}
                className="super-admin-btn-secondary"
                style={{
                  padding: '7px 14px',
                  fontSize: '0.785rem',
                  fontWeight: 700,
                  background: tenantDetailActiveTab === 'COMPANY' ? '#7134e2' : 'rgb(var(--rgb-ov) / 0.05)',
                  color: tenantDetailActiveTab === 'COMPANY' ? '#fff' : 'var(--nt-94a3b8)',
                  borderColor: tenantDetailActiveTab === 'COMPANY' ? '#7134e2' : 'rgb(var(--rgb-ov) / 0.1)'
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
                  background: tenantDetailActiveTab === 'ADMIN' ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'rgb(var(--rgb-ov) / 0.05)',
                  color: tenantDetailActiveTab === 'ADMIN' ? '#fff' : 'var(--nt-94a3b8)',
                  borderColor: tenantDetailActiveTab === 'ADMIN' ? '#10b981' : 'rgb(var(--rgb-ov) / 0.1)',
                  boxShadow: tenantDetailActiveTab === 'ADMIN' ? '0 0 12px rgba(16,185,129,0.3)' : 'none'
                }}
              >
                <User style={{ width: 14, height: 14 }} />
                <span>2. Şirket Yöneticisi Tanımlaması</span>
                {justCreatedTenantAlert && (
                  <span style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--ac-34d399)', display: 'inline-block' }} />
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
                  background: tenantDetailActiveTab === 'ALL' ? 'rgb(var(--rgb-ov) / 0.15)' : 'transparent',
                  color: tenantDetailActiveTab === 'ALL' ? 'var(--nt-ffffff)' : 'var(--nt-64748b)',
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
                color: 'var(--ac-6ee7b7)',
                fontSize: '0.785rem',
                fontWeight: 700
              }}>
                <CheckCircle2 style={{ width: 16, height: 16, color: 'var(--ac-34d399)', flexShrink: 0 }} />
                <span>{justCreatedTenantAlert}</span>
              </div>
            )}

            {tenantDetailLoading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--nt-94a3b8)' }}>Yükleniyor...</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20, marginTop: 16 }}>
                
                {/* 1. Şirket Bilgileri */}
                {(tenantDetailActiveTab === 'COMPANY' || tenantDetailActiveTab === 'ALL') && (
                <form onSubmit={handleSaveTenantDetails} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, padding: '8px 12px', borderRadius: 8, background: 'rgb(var(--rgb-ov) / 0.03)', border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-a78bfa)', textTransform: 'uppercase' }}>
                        1. Kurumsal Bilgiler & Durum:
                      </span>
                      {tenantEditForm.is_active ? (
                        <span style={{ padding: '2px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, background: 'rgba(16,185,129,0.2)', color: 'var(--ac-6ee7b7)', border: '1px solid rgba(16,185,129,0.3)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <CheckCircle2 style={{ width: 11, height: 11 }} /> AKTİF
                        </span>
                      ) : (
                        <span style={{ padding: '2px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 800, background: 'rgba(239,68,68,0.2)', color: 'var(--ac-fca5a5)', border: '1px solid rgba(239,68,68,0.3)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <PauseCircle style={{ width: 11, height: 11 }} /> PASİF
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--nt-94a3b8)' }}>
                        Sistem Kimliği: <code style={{ color: 'var(--ac-38bdf8)' }}>{selectedTenantDetails?.tenant?.slug}</code>
                      </span>
                      {selectedTenantDetails?.tenant && !isMainCompany(selectedTenantDetails.tenant) && (
                        <button
                          type="button"
                          onClick={() => handleDeleteTenant(selectedTenantDetails.tenant)}
                          disabled={processingId === 'delete-tenant-' + selectedTenantDetails.tenant.id}
                          className="super-admin-btn-secondary"
                          style={{
                            padding: '4px 10px',
                            fontSize: '0.72rem',
                            color: 'var(--ac-f87171)',
                            borderColor: 'rgba(239,68,68,0.35)',
                            background: 'rgba(239,68,68,0.08)'
                          }}
                          title="Şirketi Kalıcı Olarak Sil (Departman, AI ajanı veya proje yoksa silinebilir)"
                        >
                          {processingId === 'delete-tenant-' + selectedTenantDetails.tenant.id ? (
                            <RefreshCw style={{ width: 12, height: 12 }} className="animate-spin" />
                          ) : (
                            <Trash2 style={{ width: 12, height: 12 }} />
                          )}
                          <span>Şirketi Sil</span>
                        </button>
                      )}
                      {selectedTenantDetails?.tenant && isMainCompany(selectedTenantDetails.tenant) && (
                        <span
                          style={{
                            padding: '4px 10px',
                            fontSize: '0.72rem',
                            fontWeight: 600,
                            color: 'var(--ac-38bdf8)',
                            background: 'rgba(56, 189, 248, 0.08)',
                            border: '1px solid rgba(56, 189, 248, 0.25)',
                            borderRadius: '6px',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                          title="Ana sistem şirketi silinemez"
                        >
                          🛡️ Ana Şirket (Silinemez)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Madde 3: Aktif / Pasif Yapma İşlemi Sadece Kayıtlı Müşteri Listesinden yapılmalı */}
                  <div style={{
                    padding: '8px 12px',
                    borderRadius: 8,
                    background: tenantEditForm.is_active ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                    border: `1px solid ${tenantEditForm.is_active ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.74rem', fontWeight: 700, color: tenantEditForm.is_active ? 'var(--ac-6ee7b7)' : 'var(--ac-fca5a5)' }}>
                      {tenantEditForm.is_active ? <CheckCircle2 style={{ width: 14, height: 14 }} /> : <PauseCircle style={{ width: 14, height: 14 }} />}
                      <span>Şirket Kartı Durumu: <strong>{tenantEditForm.is_active ? 'AKTİF' : 'PASİF'}</strong> (Aktif / Pasif yapma işlemi yalnızca Kayıtlı Müşteri Listesinden yapılabilir)</span>
                    </div>
                    <span style={{ fontSize: '0.68rem', color: 'var(--nt-94a3b8)' }}>
                      {tenantEditForm.is_active ? '✓ Sistem Girişleri Açık' : '⏸️ Girişler Kapalı'}
                    </span>
                  </div>

                  <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 10 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Şirket Ünvanı</label>
                      <input
                        type="text"
                        value={tenantEditForm.name}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, name: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Vergi No (VKN)</label>
                      <input
                        type="text"
                        value={tenantEditForm.tax_id}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, tax_id: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--ac-38bdf8)', marginBottom: 3 }}>Vergi Dairesi (V.D.)</label>
                      <input
                        type="text"
                        value={tenantEditForm.tax_office || ''}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, tax_office: e.target.value })}
                        placeholder="Örn: Maslak V.D."
                        className="super-admin-input"
                      />
                    </div>
                  </div>

                  <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Telefon</label>
                      <input
                        type="text"
                        value={tenantEditForm.phone}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, phone: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>İletişim E-posta</label>
                      <input
                        type="email"
                        value={tenantEditForm.contact_email}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, contact_email: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Web Sitesi</label>
                      <input
                        type="text"
                        value={tenantEditForm.website}
                        onChange={(e) => setTenantEditForm({ ...tenantEditForm, website: e.target.value })}
                        className="super-admin-input"
                      />
                    </div>
                  </div>

                  {/* Paket & Kira Bitiş Tarihi & Hatırlatıcı Mail (Maddeler 7, 10, 14) */}
                  <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 10, padding: 10, borderRadius: 8, background: 'rgb(var(--rgb-ov) / 0.03)', border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--ac-a78bfa)', marginBottom: 3 }}>Tanımlı Paket</label>
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
                      <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--ac-60a5fa)', marginBottom: 3 }}>Paket Kira Bitiş Tarihi</label>
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
                        style={{ height: 34, fontSize: '0.725rem', color: 'var(--ac-38bdf8)', borderColor: 'rgba(56,189,248,0.3)', width: '100%', justifyContent: 'center' }}
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

                  {/* Sektörler ve Meslek Grupları Seçimi (Madde 2 - T.C. Ticaret Bakanlığı) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 12, borderRadius: 10, background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.2)' }}>
                    {/* 1. SEKTÖR SEÇİMİ */}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <label style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-818cf8)', display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Briefcase style={{ width: 14, height: 14 }} />
                          <span>Faaliyet Sektörleri (T.C. Ticaret Bakanlığı)</span>
                        </label>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)' }}>
                            {tenantEditForm.sectors?.length || 0} sektör seçili
                          </span>
                          {tenantEditForm.sectors?.length > 0 && (
                            <button
                              type="button"
                              onClick={handleClearAllSectorsTenantEdit}
                              style={{
                                background: 'rgba(239,68,68,0.15)',
                                border: '1px solid rgba(239,68,68,0.3)',
                                color: 'var(--ac-f87171)',
                                padding: '2px 8px',
                                borderRadius: 6,
                                fontSize: '0.675rem',
                                fontWeight: 700,
                                cursor: 'pointer'
                              }}
                            >
                              Temizle ✕
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Seçili Sektör Rozetleri */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, minHeight: 34, padding: 6, borderRadius: 6, background: 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))', border: '1px solid rgb(var(--rgb-ov) / 0.06)', marginBottom: 8 }}>
                        {(tenantEditForm.sectors || []).map((secCode) => {
                          const secObj = sectors.find(s => s.code === secCode || s.name === secCode);
                          return (
                            <span
                              key={secCode}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 6,
                                padding: '3px 10px',
                                borderRadius: 999,
                                background: 'linear-gradient(135deg, rgba(99,102,241,0.25) 0%, rgba(168,85,247,0.25) 100%)',
                                border: '1px solid rgba(129,140,248,0.4)',
                                color: 'var(--ac-c7d2fe)',
                                fontSize: '0.72rem',
                                fontWeight: 700
                              }}
                            >
                              <span>{secObj?.icon || '📁'}</span>
                              <span style={{ fontFamily: 'monospace', fontWeight: 800 }}>[{secObj?.code || secCode}]</span>
                              <span>{secObj?.name || secCode}</span>
                              <button
                                type="button"
                                onClick={() => handleToggleSectorTenantEdit(secCode)}
                                style={{ background: 'none', border: 'none', color: 'var(--ac-f87171)', cursor: 'pointer', padding: 0, fontWeight: 800, fontSize: '0.85rem', lineHeight: 1 }}
                                title="Sektörü kaldır"
                              >
                                ×
                              </button>
                            </span>
                          );
                        })}
                        {(!tenantEditForm.sectors || tenantEditForm.sectors.length === 0) && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--nt-64748b)', display: 'flex', alignItems: 'center' }}>
                            Henüz sektör seçilmedi. Aşağıdaki butonlardan veya açılır kutudan sektör(ler) seçiniz.
                          </span>
                        )}
                      </div>

                      {/* Sektör Seçim Listesi (Açılır Kutu + Butonlar) */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <select
                          value=""
                          onChange={(e) => {
                            const selCode = e.target.value;
                            if (!selCode) return;
                            handleToggleSectorTenantEdit(selCode);
                          }}
                          className="super-admin-select"
                          style={{ fontSize: '0.75rem', borderColor: 'rgba(129,140,248,0.3)' }}
                        >
                          <option value="">+ Açılır Listeden Sektör Seçiniz...</option>
                          {sectors.map((s) => {
                            const isSelected = (tenantEditForm.sectors || []).includes(s.code);
                            return (
                              <option key={s.code} value={s.code} disabled={isSelected}>
                                {s.icon || '📁'} [{s.code}] {s.name} {isSelected ? '(Seçildi)' : ''}
                              </option>
                            );
                          })}
                        </select>

                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, maxHeight: 85, overflowY: 'auto' }}>
                          {sectors.map((s) => {
                            const isSelected = (tenantEditForm.sectors || []).includes(s.code);
                            return (
                              <button
                                key={s.code}
                                type="button"
                                onClick={() => handleToggleSectorTenantEdit(s.code)}
                                style={{
                                  padding: '3px 8px',
                                  borderRadius: 6,
                                  fontSize: '0.675rem',
                                  fontWeight: isSelected ? 800 : 500,
                                  cursor: 'pointer',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 4,
                                  background: isSelected ? 'rgba(99,102,241,0.3)' : 'rgb(var(--rgb-ov) / 0.03)',
                                  border: isSelected ? '1px solid rgba(129,140,248,0.6)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                                  color: isSelected ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                                  transition: 'all 0.15s'
                                }}
                              >
                                <span>{s.icon || '📁'}</span>
                                <span>[{s.code}] {s.name}</span>
                                <span>{isSelected ? '✓' : '+'}</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    </div>

                    {/* 2. MESLEK GRUPLARI SEÇİMİ (Seçili sektörlere göre filtreli) */}
                    <div style={{ paddingTop: 10, borderTop: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <label style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-38bdf8)', display: 'flex', alignItems: 'center', gap: 6 }}>
                          <GraduationCap style={{ width: 14, height: 14 }} />
                          <span>Meslek Grupları (Seçili Sektörlere Göre Filtrelenir)</span>
                        </label>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)' }}>
                            {tenantEditForm.professions?.length || 0} meslek seçili
                          </span>
                          {tenantEditForm.professions?.length > 0 && (
                            <button
                              type="button"
                              onClick={() => setTenantEditForm({ ...tenantEditForm, professions: [] })}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--ac-f87171)',
                                fontSize: '0.675rem',
                                cursor: 'pointer',
                                fontWeight: 600
                              }}
                            >
                              Temizle ✕
                            </button>
                          )}
                        </div>
                      </div>

                      {(!tenantEditForm.sectors || tenantEditForm.sectors.length === 0) ? (
                        <div style={{ padding: '8px 12px', borderRadius: 6, background: 'rgba(234, 179, 8, 0.08)', border: '1px solid rgba(234, 179, 8, 0.25)', color: '#fde047', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                          <AlertCircle style={{ width: 15, height: 15, flexShrink: 0 }} />
                          <span>Lütfen önce yukarıdan en az bir <strong>Faaliyet Sektörü</strong> seçiniz. Seçtiğiniz sektör(ler)e ait resmi meslek grupları otomatik olarak burada listelenecektir.</span>
                        </div>
                      ) : (
                        <>
                          {/* Seçili Meslekler Etiketleri (Chips) */}
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, minHeight: 34, padding: 6, borderRadius: 6, background: 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))', border: '1px solid rgb(var(--rgb-ov) / 0.06)', marginBottom: 8 }}>
                            {(tenantEditForm.professions || []).map((pItem) => {
                              const pCode = typeof pItem === 'object' ? pItem.code : pItem;
                              const profObj = professions.find(pr => pr.code === pCode);
                              const pName = profObj ? profObj.name : (typeof pItem === 'object' ? pItem.name : pCode);
                              const pSector = profObj ? profObj.sector_code : '';
                              return (
                                <span key={pCode} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 999, background: 'rgba(56,189,248,0.2)', border: '1px solid rgba(56,189,248,0.4)', color: 'var(--ac-38bdf8)', fontSize: '0.7rem' }}>
                                  <span style={{ fontFamily: 'monospace', fontWeight: 800 }}>[{pCode}]</span>
                                  <span>{pName}</span>
                                  {pSector && <span style={{ opacity: 0.6, fontSize: '0.65rem' }}>({pSector})</span>}
                                  <button
                                    type="button"
                                    onClick={() => handleToggleProfessionTenantEdit(pCode)}
                                    style={{ background: 'none', border: 'none', color: 'var(--ac-38bdf8)', cursor: 'pointer', padding: 0, fontWeight: 800 }}
                                  >
                                    ×
                                  </button>
                                </span>
                              );
                            })}
                            {(!tenantEditForm.professions || tenantEditForm.professions.length === 0) && (
                              <span style={{ fontSize: '0.72rem', color: 'var(--nt-64748b)', display: 'flex', alignItems: 'center' }}>
                                Seçili sektör(ler)e ait meslek grubu seçilmedi. Aşağıdan seçebilirsiniz (opsiyonel).
                              </span>
                            )}
                          </div>

                          {/* Meslek Grubu Açılır Listesi (Sadece Seçili Sektörler) */}
                          <select
                            value=""
                            onChange={(e) => {
                              const val = e.target.value;
                              if (val) handleToggleProfessionTenantEdit(val);
                            }}
                            className="super-admin-select"
                            style={{ fontSize: '0.75rem', borderColor: 'rgba(56,189,248,0.3)' }}
                          >
                            <option value="">+ Seçili Sektörlere Bağlı Meslek Grubu Ekle ({professions.filter(pr => (tenantEditForm.sectors || []).includes(pr.sector_code)).length} meslek mevcut)...</option>
                            {professions
                              .filter(pr => (tenantEditForm.sectors || []).includes(pr.sector_code))
                              .map(pr => {
                                const isAlreadySelected = (tenantEditForm.professions || []).some(p => (typeof p === 'object' ? p.code : p) === pr.code);
                                return (
                                  <option key={pr.code} value={pr.code} disabled={isAlreadySelected}>
                                    [{pr.code}] {pr.name} (Sektör: {pr.sector_code}) {isAlreadySelected ? '✓' : ''}
                                  </option>
                                );
                              })}
                          </select>
                        </>
                      )}
                    </div>
                  </div>

                  {/* AI İle Şirket Manifestosu Oluşturma (Madde 13) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ac-c084fc)', display: 'flex', alignItems: 'center', gap: 6 }}>
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
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Adres</label>
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
                  borderTop: tenantDetailActiveTab === 'ALL' ? '1px solid rgb(var(--rgb-ov) / 0.08)' : 'none',
                  paddingTop: tenantDetailActiveTab === 'ALL' ? 16 : 0,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <div style={{ fontSize: '0.825rem', fontWeight: 800, color: 'var(--ac-38bdf8)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                        <User style={{ width: 15, height: 15 }} />
                        <span>2. Şirket Admin Kullanıcı Tanımlaması</span>
                      </div>
                      <div style={{ fontSize: '0.725rem', color: 'var(--nt-94a3b8)' }}>
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
                        <div style={{ fontSize: '0.68rem', color: 'var(--ac-6ee7b7)', fontWeight: 800 }}>Yeni Oluşturulan Güçlü Şifre:</div>
                        <div style={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '0.9rem', color: 'var(--nt-ffffff)', marginTop: 2 }}>
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
                    <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Yönetici Adı Soyadı</label>
                        <input
                          type="text"
                          required
                          value={tenantAdminForm.display_name}
                          onChange={(e) => setTenantAdminForm({ ...tenantAdminForm, display_name: e.target.value })}
                          className="super-admin-input"
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Giriş E-postası</label>
                        <input
                          type="email"
                          required
                          value={tenantAdminForm.email}
                          onChange={(e) => setTenantAdminForm({ ...tenantAdminForm, email: e.target.value })}
                          className="super-admin-input"
                        />
                      </div>
                    </div>

                    <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Telefon</label>
                        <input
                          type="text"
                          value={tenantAdminForm.phone}
                          onChange={(e) => setTenantAdminForm({ ...tenantAdminForm, phone: e.target.value })}
                          className="super-admin-input"
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-94a3b8)', marginBottom: 3 }}>Manuel Şifre Ata</label>
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--nt-ffffff)' }}>
                {editingPermission ? 'İzin Tanımını Düzenle' : 'Yeni İzin Tanımla'}
              </h3>
              <button onClick={() => setPermissionModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSavePermission} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Yetki Kodu</label>
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
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Modül</label>
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
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>İzin Adı</label>
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
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Açıklama</label>
                <textarea
                  rows="3"
                  value={permissionForm.description}
                  onChange={(e) => setPermissionForm({ ...permissionForm, description: e.target.value })}
                  placeholder="Bu yetkiye sahip roller yapay zeka personellerini devreye alabilir."
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
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
      {/* 3.1 YETKİ ROLÜ EKLEME / DÜZENLEME MODALI (Madde 1)       */}
      {/* ======================================================== */}
      {roleModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box" style={{ maxWidth: 880, maxHeight: '92vh', display: 'flex', flexDirection: 'column' }}>
            {/* Modal Başlığı */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <ShieldCheck style={{ width: 20, height: 20, color: '#10b981' }} />
                  <span>{editingRole ? `Yetki Rolünü Düzenle: ${editingRole.name}` : 'Yeni Yetki Rolü Tanımla (RBAC)'}</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', marginTop: 2 }}>
                  Kullanıcı ve aktör yetki sınırlarını belirleyin, İzin Kataloğundan çoklu yetkileri seçin.
                </p>
              </div>
              <button onClick={() => setRoleModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveRole} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 14, overflowY: 'auto', paddingRight: 4 }}>
              {/* 1. Rol Adı & Sistem Rolü Toggle */}
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                    Rol Adı *
                  </label>
                  <input
                    type="text"
                    required
                    value={roleForm.name}
                    onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })}
                    placeholder="Örn: Operasyon ve Müşteri Destek Yöneticisi"
                    className="super-admin-input"
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                    Rol Türü / Kapsamı
                  </label>
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      height: 38,
                      padding: '0 12px',
                      background: 'rgb(var(--rgb-ov) / 0.03)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                      borderRadius: 6,
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      color: roleForm.is_system ? 'var(--ac-34d399)' : 'var(--nt-94a3b8)',
                      fontWeight: 700
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={roleForm.is_system}
                      onChange={(e) => setRoleForm({ ...roleForm, is_system: e.target.checked })}
                    />
                    <span>Sistem / Global Rol Olarak Tanımla</span>
                  </label>
                </div>
              </div>

              {/* 2. Rol Açıklaması */}
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                  Rol Açıklaması
                </label>
                <textarea
                  rows="2"
                  value={roleForm.description}
                  onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                  placeholder="Bu yetki rolünün sistem ve kurum genelindeki sorumlulukları, yetki çerçevesi..."
                  className="super-admin-input"
                />
              </div>

              {/* 3. İZİN KATALOĞUNDAN ÇOKLU SEÇİM ALANI */}
              <div
                style={{
                  background: 'rgb(var(--rgb-shade) / calc(0.25 * var(--shade-k)))',
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  borderRadius: 8,
                  padding: 12,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10
                }}
              >
                {/* İzin Başlığı, Sayaç ve Hızlı Eylemler */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <KeyRound style={{ width: 16, height: 16, color: 'var(--ac-fbbf24)' }} />
                    <span style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--nt-ffffff)' }}>
                      İzin Kataloğu Yetkileri (Çoklu Seçim)
                    </span>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 800,
                        padding: '2px 8px',
                        borderRadius: 999,
                        background: roleForm.permissions.length > 0 ? 'rgba(16,185,129,0.2)' : 'rgb(var(--rgb-ov) / 0.06)',
                        color: roleForm.permissions.length > 0 ? 'var(--ac-34d399)' : 'var(--nt-94a3b8)',
                        border: roleForm.permissions.length > 0 ? '1px solid rgba(16,185,129,0.3)' : '1px solid rgb(var(--rgb-ov) / 0.08)'
                      }}
                    >
                      {roleForm.permissions.length} / {permissions.length} İzin Seçildi
                    </span>
                  </div>

                  {/* Hızlı Seçim Butonları */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <button
                      type="button"
                      onClick={() => {
                        const matching = permissions.filter(p => {
                          const matchMod = rolePermissionModuleFilter === 'ALL' || p.module === rolePermissionModuleFilter;
                          const matchQ = !rolePermissionSearch ||
                            p.code.toLowerCase().includes(rolePermissionSearch.toLowerCase()) ||
                            p.name.toLowerCase().includes(rolePermissionSearch.toLowerCase());
                          return matchMod && matchQ;
                        });
                        handleSelectAllPermissionsInCatalog(matching);
                      }}
                      className="super-admin-btn-secondary"
                      style={{ fontSize: '0.68rem', padding: '3px 8px' }}
                    >
                      ✓ Listelenenleri Seç
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSelectAllPermissionsInCatalog(permissions)}
                      className="super-admin-btn-secondary"
                      style={{ fontSize: '0.68rem', padding: '3px 8px' }}
                    >
                      Tümünü Seç ({permissions.length})
                    </button>
                    {roleForm.permissions.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setRoleForm({ ...roleForm, permissions: [] })}
                        className="super-admin-btn-secondary"
                        style={{ fontSize: '0.68rem', padding: '3px 8px', color: 'var(--ac-f87171)' }}
                      >
                        Temizle
                      </button>
                    )}
                  </div>
                </div>

                {/* Filtreleme ve Arama Çubuğu */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <input
                    type="text"
                    value={rolePermissionSearch}
                    onChange={(e) => setRolePermissionSearch(e.target.value)}
                    placeholder="İzin ara (örn: role:create, agent, chat)..."
                    className="super-admin-input"
                    style={{ flex: 1, minWidth: 200, fontSize: '0.75rem', height: 32 }}
                  />

                  {/* Modül Butonları */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {['ALL', 'PLATFORM', 'RBAC', 'AGENTS', 'PROJECTS', 'CHAT', 'MEMORY', 'BILLING'].map((mod) => (
                      <button
                        key={mod}
                        type="button"
                        onClick={() => setRolePermissionModuleFilter(mod)}
                        style={{
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          padding: '3px 7px',
                          borderRadius: 4,
                          border: rolePermissionModuleFilter === mod ? '1px solid #10b981' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                          background: rolePermissionModuleFilter === mod ? 'rgba(16,185,129,0.2)' : 'rgb(var(--rgb-ov) / 0.03)',
                          color: rolePermissionModuleFilter === mod ? 'var(--ac-34d399)' : 'var(--nt-94a3b8)',
                          cursor: 'pointer'
                        }}
                      >
                        {mod === 'ALL' ? 'TÜMÜ' : mod}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Seçili İzinlerin Önizleme Şeridi */}
                {roleForm.permissions.length > 0 && (
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: 4,
                      padding: '6px 8px',
                      background: 'rgba(16,185,129,0.04)',
                      border: '1px solid rgba(16,185,129,0.15)',
                      borderRadius: 6,
                      maxHeight: 70,
                      overflowY: 'auto'
                    }}
                  >
                    {roleForm.permissions.map((code) => {
                      const pObj = permissions.find(p => p.code === code);
                      return (
                        <span
                          key={code}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            padding: '2px 6px',
                            borderRadius: 4,
                            background: 'rgba(16,185,129,0.18)',
                            color: 'var(--ac-34d399)',
                            fontSize: '0.68rem',
                            fontFamily: 'monospace'
                          }}
                          title={pObj?.name || code}
                        >
                          <span>{code}</span>
                          <button
                            type="button"
                            onClick={() => handleTogglePermissionInRole(code)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: 'var(--ac-34d399)',
                              cursor: 'pointer',
                              padding: 0,
                              fontWeight: 900,
                              lineHeight: 1
                            }}
                          >
                            ×
                          </button>
                        </span>
                      );
                    })}
                  </div>
                )}

                {/* İzin Kataloğu Seçim Listesi (Kompakt Grid) */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 260px), 1fr))',
                    gap: 6,
                    maxHeight: 280,
                    overflowY: 'auto',
                    padding: 4,
                    background: 'rgb(var(--rgb-shade) / calc(0.2 * var(--shade-k)))',
                    borderRadius: 6,
                    border: '1px solid rgb(var(--rgb-ov) / 0.04)'
                  }}
                >
                  {permissions
                    .filter(p => {
                      const matchMod = rolePermissionModuleFilter === 'ALL' || p.module === rolePermissionModuleFilter;
                      const matchQ = !rolePermissionSearch ||
                        p.code.toLowerCase().includes(rolePermissionSearch.toLowerCase()) ||
                        p.name.toLowerCase().includes(rolePermissionSearch.toLowerCase()) ||
                        (p.description && p.description.toLowerCase().includes(rolePermissionSearch.toLowerCase()));
                      return matchMod && matchQ;
                    })
                    .map((p) => {
                      const isSelected = roleForm.permissions.includes(p.code);
                      return (
                        <div
                          key={p.id || p.code}
                          onClick={() => handleTogglePermissionInRole(p.code)}
                          style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: 8,
                            padding: '8px 10px',
                            borderRadius: 6,
                            cursor: 'pointer',
                            background: isSelected ? 'rgba(16,185,129,0.12)' : 'rgb(var(--rgb-ov) / 0.02)',
                            border: isSelected ? '1px solid rgba(16,185,129,0.45)' : '1px solid rgb(var(--rgb-ov) / 0.05)',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {}} // parent onClick handles toggle
                            style={{ marginTop: 2, cursor: 'pointer' }}
                          />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 4, marginBottom: 2 }}>
                              <span style={{ fontSize: '0.62rem', fontWeight: 800, padding: '1px 5px', borderRadius: 3, background: 'rgb(var(--rgb-ov) / 0.08)', color: 'var(--ac-a78bfa)' }}>
                                {p.module}
                              </span>
                              <span style={{ fontSize: '0.65rem', fontFamily: 'monospace', fontWeight: 700, color: isSelected ? 'var(--ac-34d399)' : 'var(--nt-cbd5e1)' }}>
                                {p.code}
                              </span>
                            </div>
                            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-ffffff)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {p.name}
                            </div>
                            {p.description && (
                              <div style={{ fontSize: '0.65rem', color: 'var(--nt-94a3b8)', marginTop: 2, lineHeight: 1.25, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                {p.description}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>

              {/* Modal Butonları */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                <button
                  type="button"
                  onClick={() => setRoleModalOpen(false)}
                  className="super-admin-btn-secondary"
                >
                  Vazgeç
                </button>
                <button
                  type="submit"
                  disabled={processingId === 'save-role'}
                  className="super-admin-btn-corporate"
                  style={{
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    boxShadow: '0 0 14px rgba(16,185,129,0.35)',
                    padding: '8px 20px',
                    fontWeight: 800
                  }}
                >
                  {processingId === 'save-role' ? (
                    <>
                      <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" />
                      <span>Kaydediliyor...</span>
                    </>
                  ) : (
                    <>
                      <Save style={{ width: 14, height: 14 }} />
                      <span>{editingRole ? 'Değişiklikleri Kaydet' : 'Yetki Rolünü Oluştur'}</span>
                    </>
                  )}
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--nt-ffffff)' }}>
                {editingPlan ? 'Paketi Düzenle' : 'Yeni Kiralama Paketi Tanımla'}
              </h3>
              <button onClick={() => setPlanModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSavePlan} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Paket Kodu</label>
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
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Paket Adı</label>
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

              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Aylık Fiyat (TRY)</label>
                  <input
                    type="number"
                    value={planForm.monthly_price}
                    onChange={(e) => setPlanForm({ ...planForm, monthly_price: Number(e.target.value) })}
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Aylık Kredi</label>
                  <input
                    type="number"
                    value={planForm.monthly_credits}
                    onChange={(e) => setPlanForm({ ...planForm, monthly_credits: Number(e.target.value) })}
                    className="super-admin-input"
                  />
                </div>
              </div>

              {/* Dinamik Limitler (Madde 15) */}
              <div style={{ padding: 12, borderRadius: 8, background: 'rgb(var(--rgb-ov) / 0.03)', border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-a78bfa)', marginBottom: 8, textTransform: 'uppercase' }}>
                  Paket Kaynak ve Adetsel Limitleri
                </div>
                <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>AI Ajan Personel</label>
                    <input
                      type="number"
                      value={planForm.max_agents}
                      onChange={(e) => setPlanForm({ ...planForm, max_agents: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>İnsan Kullanıcı</label>
                    <input
                      type="number"
                      value={planForm.max_humans}
                      onChange={(e) => setPlanForm({ ...planForm, max_humans: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Eşzamanlı Proje</label>
                    <input
                      type="number"
                      value={planForm.max_projects || 3}
                      onChange={(e) => setPlanForm({ ...planForm, max_projects: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>İşlem Kredisi</label>
                    <input
                      type="number"
                      value={planForm.monthly_credits}
                      onChange={(e) => setPlanForm({ ...planForm, monthly_credits: Number(e.target.value) })}
                      className="super-admin-input"
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>MinIO Depolama (GB)</label>
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
              <div style={{ padding: 12, borderRadius: 8, background: 'rgb(var(--rgb-ov) / 0.03)', border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-38bdf8)', textTransform: 'uppercase' }}>
                    Pakete Dahil Edilen EVREN LLM Modelleri ({planForm.allowed_models?.length || 0} Model Seçili)
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)' }}>Müşterinin kullanabileceği modeller</span>
                </div>
                
                <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, maxHeight: 150, overflowY: 'auto' }}>
                  {models.map((m) => {
                    const isChecked = (planForm.allowed_models || []).includes(m.model_code);
                    return (
                      <label
                        key={m.id}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', borderRadius: 6,
                          background: isChecked ? 'rgba(56,189,248,0.15)' : 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))',
                          border: isChecked ? '1px solid rgba(56,189,248,0.4)' : '1px solid rgb(var(--rgb-ov) / 0.04)',
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
                          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-ffffff)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>{m.display_name}</div>
                          <div style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: 'var(--nt-94a3b8)' }}>{m.model_code}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Açıklama</label>
                <textarea
                  rows="2"
                  value={planForm.description}
                  onChange={(e) => setPlanForm({ ...planForm, description: e.target.value })}
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', gap: 20, padding: '4px 0' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={planForm.can_create_custom_titles}
                    onChange={(e) => setPlanForm({ ...planForm, can_create_custom_titles: e.target.checked })}
                  />
                  <span>Özel AI Ünvan Tanımlama İzni Ver</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={planForm.is_active}
                    onChange={(e) => setPlanForm({ ...planForm, is_active: e.target.checked })}
                  />
                  <span>Paket Aktif</span>
                </label>
              </div>

              {/* Paket izinleri (#241) ve Odoo ürün eşleşmesi */}
              <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 12, padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--text-main)' }}>Paket İzinleri</div>
                <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {[
                    ['can_change_llm', 'AI personelin LLM modelini değiştirebilir'],
                    ['can_edit_role_prompt', 'Ünvan rol promptunu değiştirebilir'],
                    ['can_upload_title_documents', 'Ünvanlara bilgi dokümanı yükleyebilir'],
                    ['ocr_enabled', 'Taranmış belgelerde OCR kullanabilir'],
                  ].map(([key, label]) => (
                    <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={!!planForm.features?.[key]}
                        onChange={(e) => setPlanForm({ ...planForm, features: { ...planForm.features, [key]: e.target.checked } })}
                      />
                      <span>{label}</span>
                    </label>
                  ))}
                </div>
                <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                    AI personel başına en fazla öğrenme kaynağı
                    <input
                      type="number"
                      min="0"
                      value={planForm.features?.max_documents_per_agent ?? 20}
                      onChange={(e) => setPlanForm({ ...planForm, features: { ...planForm.features, max_documents_per_agent: Number(e.target.value) } })}
                      className="super-admin-input"
                      style={{ marginTop: 4 }}
                    />
                  </label>
                  <OdooProductPicker
                    value={planForm.odoo_product_id}
                    planPrice={planForm.monthly_price}
                    onChange={(id) => setPlanForm({ ...planForm, odoo_product_id: id })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--nt-ffffff)' }}>
                {editingModel ? 'EVREN Modelini Düzenle' : 'Yeni EVREN Modeli Ekle'}
              </h3>
              <button onClick={() => setModelModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveModel} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Model Kodu</label>
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
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Görünen İsim</label>
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

              <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Tür</label>
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
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Bağlam (Token)</label>
                  <input
                    type="number"
                    value={modelForm.context_window}
                    onChange={(e) => setModelForm({ ...modelForm, context_window: Number(e.target.value) })}
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Efor Katsayısı</label>
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
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Durum</label>
                <select
                  value={modelForm.status}
                  onChange={(e) => setModelForm({ ...modelForm, status: e.target.value })}
                  className="super-admin-select"
                >
                  <option value="ACTIVE">ACTIVE (Aktif)</option>
                  <option value="INACTIVE">INACTIVE (Pasif)</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
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
      {/* MESLEK GRUBU TANIMLAMA MODALI (TİCARET BAKANLIĞI)        */}
      {/* ======================================================== */}
      {professionModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--nt-ffffff)' }}>
                  {editingProfession ? `'${professionForm.code}' Meslek Tanımını Düzenle` : 'Yeni Meslek Grubu Tanımla'}
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>T.C. Ticaret Bakanlığı resmi meslek grubu tanımı.</p>
              </div>
              <button onClick={() => setProfessionModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveProfession} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                    Meslek Kodu *
                  </label>
                  <input
                    type="text"
                    required
                    disabled={!!editingProfession}
                    value={professionForm.code}
                    onChange={(e) => setProfessionForm({ ...professionForm, code: e.target.value })}
                    placeholder="Örn: A.01, B.05..."
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace', fontWeight: 700 }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                    Bağlı Olduğu Sektör *
                  </label>
                  <select
                    required
                    value={professionForm.sector_code}
                    onChange={(e) => setProfessionForm({ ...professionForm, sector_code: e.target.value })}
                    className="super-admin-input"
                    style={{ background: 'var(--sf-1e293b)', color: 'var(--nt-ffffff)', cursor: 'pointer' }}
                  >
                    <option value="">-- Sektör Seçiniz --</option>
                    {sectors.map((sec) => (
                      <option key={sec.code} value={sec.code}>
                        {sec.code} - {sec.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                  Meslek Tanım Adı *
                </label>
                <input
                  type="text"
                  required
                  value={professionForm.name}
                  onChange={(e) => setProfessionForm({ ...professionForm, name: e.target.value })}
                  placeholder="Örn: Kerestecilik, Marangozluk, Yazılım Geliştirme..."
                  className="super-admin-input"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                  Açıklama (Opsiyonel)
                </label>
                <textarea
                  rows="3"
                  value={professionForm.description}
                  onChange={(e) => setProfessionForm({ ...professionForm, description: e.target.value })}
                  placeholder="Meslek grubunun kapsamı ve faaliyet detayları..."
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={professionForm.is_active}
                    onChange={(e) => setProfessionForm({ ...professionForm, is_active: e.target.checked })}
                  />
                  <span style={{ fontWeight: 700 }}>Meslek Tanımı Aktif</span>
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 14, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                <button type="button" onClick={() => setProfessionModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>
                <button type="submit" disabled={processingId === 'save-profession'} className="super-admin-btn-corporate">
                  {processingId === 'save-profession' ? <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" /> : <Save style={{ width: 14, height: 14 }} />}
                  <span>{editingProfession ? 'Değişiklikleri Kaydet' : 'Meslek Tanımını Kaydet'}</span>
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Building2 style={{ width: 20, height: 20, color: '#10b981' }} />
                  <span>Yeni Müşteri & Şirket Ekle (Süper Admin Kaydı)</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                  Şirket kartı oluşturulur, 1 yıllık kira paketi tanımlanır ve Hoş Geldiniz e-postası otomatik iletilir.
                </p>
              </div>
              <button onClick={() => setNewTenantModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveNewTenant} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
              {/* Kurumsal Bilgiler */}
              <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Şirket Ünvanı *</label>
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
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Vergi No (VKN) *</label>
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
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--ac-38bdf8)', marginBottom: 3 }}>Vergi Dairesi</label>
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
              <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Kurumsal / Official E-posta *</label>
                  <input
                    type="email"
                    required
                    value={newTenantForm.contact_email}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, contact_email: e.target.value })}
                    placeholder="yetkili@sirketiniz.com"
                    className="super-admin-input"
                  />
                  <div style={{ fontSize: '0.65rem', color: 'var(--nt-94a3b8)', marginTop: 3 }}>
                    * Resmi şirket e-posta adresi zorunludur (Gmail, Hotmail vb. kabul edilmez).
                  </div>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Telefon</label>
                  <input
                    type="text"
                    value={newTenantForm.phone}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, phone: e.target.value })}
                    placeholder="+90 212 XXX XX XX"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Web Sitesi</label>
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
              <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 10, padding: 10, borderRadius: 8, background: 'rgb(var(--rgb-ov) / 0.03)', border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--ac-a78bfa)', marginBottom: 3 }}>Kiralama Paketi (1 Yıl Başlatılır)</label>
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
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Yönetici Adı Soyadı</label>
                  <input
                    type="text"
                    value={newTenantForm.admin_name}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, admin_name: e.target.value })}
                    placeholder="Şirket Yöneticisi"
                    className="super-admin-input"
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Yönetici Şifresi (Opsiyonel)</label>
                  <input
                    type="text"
                    value={newTenantForm.admin_password}
                    onChange={(e) => setNewTenantForm({ ...newTenantForm, admin_password: e.target.value })}
                    placeholder="Boş bırakılırsa yönetici şifresini e-postadaki bağlantıdan kendisi belirler"
                    className="super-admin-input"
                  />
                </div>
              </div>

              {/* Sektörler ve Meslek Grupları Seçimi (Madde 2 - T.C. Ticaret Bakanlığı) */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 12, borderRadius: 10, background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.2)' }}>
                {/* 1. SEKTÖR SEÇİMİ */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                    <label style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-818cf8)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Briefcase style={{ width: 14, height: 14 }} />
                      <span>Faaliyet Sektörleri (T.C. Ticaret Bakanlığı) *</span>
                    </label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)' }}>
                        {newTenantForm.sectors?.length || 0} sektör seçili
                      </span>
                      {newTenantForm.sectors?.length > 0 && (
                        <button
                          type="button"
                          onClick={handleClearAllSectorsNewTenant}
                          style={{
                            background: 'rgba(239,68,68,0.15)',
                            border: '1px solid rgba(239,68,68,0.3)',
                            color: 'var(--ac-f87171)',
                            padding: '2px 8px',
                            borderRadius: 6,
                            fontSize: '0.675rem',
                            fontWeight: 700,
                            cursor: 'pointer'
                          }}
                        >
                          Temizle ✕
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Seçili Sektörler Etiketleri (Chips) */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, minHeight: 34, padding: 6, borderRadius: 6, background: 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))', border: '1px solid rgb(var(--rgb-ov) / 0.06)', marginBottom: 8 }}>
                    {(newTenantForm.sectors || []).map((secCode) => {
                      const secObj = sectors.find(s => s.code === secCode || s.name === secCode);
                      return (
                        <span
                          key={secCode}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 6,
                            padding: '3px 10px',
                            borderRadius: 999,
                            background: 'linear-gradient(135deg, rgba(99,102,241,0.25) 0%, rgba(168,85,247,0.25) 100%)',
                            border: '1px solid rgba(129,140,248,0.4)',
                            color: 'var(--ac-c7d2fe)',
                            fontSize: '0.72rem',
                            fontWeight: 700
                          }}
                        >
                          <span>{secObj?.icon || '📁'}</span>
                          <span style={{ fontFamily: 'monospace', fontWeight: 800 }}>[{secObj?.code || secCode}]</span>
                          <span>{secObj?.name || secCode}</span>
                          <button
                            type="button"
                            onClick={() => handleToggleSectorNewTenant(secCode)}
                            style={{ background: 'none', border: 'none', color: 'var(--ac-f87171)', cursor: 'pointer', padding: 0, fontWeight: 800, fontSize: '0.85rem', lineHeight: 1 }}
                            title="Sektörü kaldır"
                          >
                            ×
                          </button>
                        </span>
                      );
                    })}
                    {(!newTenantForm.sectors || newTenantForm.sectors.length === 0) && (
                      <span style={{ fontSize: '0.72rem', color: 'var(--nt-64748b)', display: 'flex', alignItems: 'center' }}>
                        Henüz sektör seçilmedi. Aşağıdaki butonlardan veya açılır kutudan sektör(ler) seçiniz.
                      </span>
                    )}
                  </div>

                  {/* Açılır Kutu + Hızlı Sektör Butonları */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <select
                      value=""
                      onChange={(e) => {
                        const selCode = e.target.value;
                        if (!selCode) return;
                        handleToggleSectorNewTenant(selCode);
                      }}
                      className="super-admin-select"
                      style={{ fontSize: '0.75rem', borderColor: 'rgba(129,140,248,0.3)' }}
                    >
                      <option value="">+ Açılır Listeden Sektör Seçiniz...</option>
                      {sectors.map((s) => {
                        const isSelected = (newTenantForm.sectors || []).includes(s.code);
                        return (
                          <option key={s.code} value={s.code} disabled={isSelected}>
                            {s.icon || '📁'} [{s.code}] {s.name} {isSelected ? '(Seçildi)' : ''}
                          </option>
                        );
                      })}
                    </select>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, maxHeight: 85, overflowY: 'auto' }}>
                      {sectors.map((s) => {
                        const isSelected = (newTenantForm.sectors || []).includes(s.code);
                        return (
                          <button
                            key={s.code}
                            type="button"
                            onClick={() => handleToggleSectorNewTenant(s.code)}
                            style={{
                              padding: '3px 8px',
                              borderRadius: 6,
                              fontSize: '0.675rem',
                              fontWeight: isSelected ? 800 : 500,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 4,
                              background: isSelected ? 'rgba(99,102,241,0.3)' : 'rgb(var(--rgb-ov) / 0.03)',
                              border: isSelected ? '1px solid rgba(129,140,248,0.6)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                              color: isSelected ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                              transition: 'all 0.15s'
                            }}
                          >
                            <span>{s.icon || '📁'}</span>
                            <span>[{s.code}] {s.name}</span>
                            <span>{isSelected ? '✓' : '+'}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* 2. MESLEK GRUPLARI SEÇİMİ (Seçili sektörlere göre filtreli) */}
                <div style={{ paddingTop: 10, borderTop: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                    <label style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--ac-38bdf8)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <GraduationCap style={{ width: 14, height: 14 }} />
                      <span>Meslek Grupları (Seçili Sektörlere Göre Filtrelenir)</span>
                    </label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)' }}>
                        {newTenantForm.professions?.length || 0} meslek seçili
                      </span>
                      {newTenantForm.professions?.length > 0 && (
                        <button
                          type="button"
                          onClick={() => setNewTenantForm({ ...newTenantForm, professions: [] })}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--ac-f87171)',
                            fontSize: '0.675rem',
                            cursor: 'pointer',
                            fontWeight: 600
                          }}
                        >
                          Temizle ✕
                        </button>
                      )}
                    </div>
                  </div>

                  {(!newTenantForm.sectors || newTenantForm.sectors.length === 0) ? (
                    <div style={{ padding: '8px 12px', borderRadius: 6, background: 'rgba(234, 179, 8, 0.08)', border: '1px solid rgba(234, 179, 8, 0.25)', color: '#fde047', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                      <AlertCircle style={{ width: 15, height: 15, flexShrink: 0 }} />
                      <span>Lütfen önce yukarıdan en az bir <strong>Faaliyet Sektörü</strong> seçiniz. Seçtiğiniz sektör(ler)e ait resmi meslek grupları otomatik olarak burada listelenecektir.</span>
                    </div>
                  ) : (
                    <>
                      {/* Seçili Meslekler Etiketleri (Chips) */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, minHeight: 34, padding: 6, borderRadius: 6, background: 'rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))', border: '1px solid rgb(var(--rgb-ov) / 0.06)', marginBottom: 8 }}>
                        {(newTenantForm.professions || []).map((pItem) => {
                          const pCode = typeof pItem === 'object' ? pItem.code : pItem;
                          const profObj = professions.find(pr => pr.code === pCode);
                          const pName = profObj ? profObj.name : (typeof pItem === 'object' ? pItem.name : pCode);
                          const pSector = profObj ? profObj.sector_code : '';
                          return (
                            <span key={pCode} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px', borderRadius: 999, background: 'rgba(56,189,248,0.2)', border: '1px solid rgba(56,189,248,0.4)', color: 'var(--ac-38bdf8)', fontSize: '0.7rem' }}>
                              <span style={{ fontFamily: 'monospace', fontWeight: 800 }}>[{pCode}]</span>
                              <span>{pName}</span>
                              {pSector && <span style={{ opacity: 0.6, fontSize: '0.65rem' }}>({pSector})</span>}
                              <button
                                type="button"
                                onClick={() => handleToggleProfessionNewTenant(pCode)}
                                style={{ background: 'none', border: 'none', color: 'var(--ac-38bdf8)', cursor: 'pointer', padding: 0, fontWeight: 800 }}
                              >
                                ×
                              </button>
                            </span>
                          );
                        })}
                        {(!newTenantForm.professions || newTenantForm.professions.length === 0) && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--nt-64748b)', display: 'flex', alignItems: 'center' }}>
                            Seçili sektör(ler)e ait meslek grubu seçilmedi. Aşağıdan seçebilirsiniz (opsiyonel).
                          </span>
                        )}
                      </div>

                      {/* Meslek Grubu Açılır Listesi (Sadece Seçili Sektörler) */}
                      <select
                        value=""
                        onChange={(e) => {
                          const val = e.target.value;
                          if (val) handleToggleProfessionNewTenant(val);
                        }}
                        className="super-admin-select"
                        style={{ fontSize: '0.75rem', borderColor: 'rgba(56,189,248,0.3)' }}
                      >
                        <option value="">+ Seçili Sektörlere Bağlı Meslek Grubu Ekle ({professions.filter(pr => (newTenantForm.sectors || []).includes(pr.sector_code)).length} meslek mevcut)...</option>
                        {professions
                          .filter(pr => (newTenantForm.sectors || []).includes(pr.sector_code))
                          .map(pr => {
                            const isAlreadySelected = (newTenantForm.professions || []).some(p => (typeof p === 'object' ? p.code : p) === pr.code);
                            return (
                              <option key={pr.code} value={pr.code} disabled={isAlreadySelected}>
                                [{pr.code}] {pr.name} (Sektör: {pr.sector_code}) {isAlreadySelected ? '✓' : ''}
                              </option>
                            );
                          })}
                      </select>
                    </>
                  )}
                </div>
              </div>

              {/* AI İle Kurumsal Manifesto Üretimi (Madde 13) */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ac-c084fc)', display: 'flex', alignItems: 'center', gap: 6 }}>
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
                    <span>{isGeneratingNewTenantManifesto ? 'LLM Yazıyor...' : '✨ RECAi ile Manifesto Üret'}</span>
                  </button>
                </div>

                <textarea
                  rows="3"
                  value={newTenantManifesto}
                  onChange={(e) => setNewTenantManifesto(e.target.value)}
                  placeholder="Seçilen sektör ve meslek gruplarına göre RECOrion LLM tarafından otomatik üretilen şirket vizyonu ve yapay zeka entegrasyon manifestosu (Kullanıcı dilediğince düzenleyebilir)..."
                  className="super-admin-input"
                  style={{ fontSize: '0.75rem', lineHeight: 1.5 }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Adres</label>
                <textarea
                  rows="2"
                  value={newTenantForm.address}
                  onChange={(e) => setNewTenantForm({ ...newTenantForm, address: e.target.value })}
                  placeholder="Şirket resmi adresi..."
                  className="super-admin-input"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10, paddingTop: 14, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)', flexWrap: 'wrap' }}>
                <button type="button" onClick={() => setNewTenantModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>

                {/* MÜŞTERİYİ VE YÖNETİCİYİ KAYDET (Tek Adımda Kayıt) */}
                <button
                  type="button"
                  onClick={handleSaveNewTenant}
                  disabled={!!processingId}
                  className="super-admin-btn-corporate"
                  style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', fontWeight: 800 }}
                  title="Şirket ve yetkili yönetici kullanıcısı tek adımda doğrudan sisteme kaydedilir"
                >
                  {processingId === 'create-new-tenant' ? <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" /> : <CheckCircle2 style={{ width: 14, height: 14 }} />}
                  <span>Müşteriyi ve Yöneticiyi Kaydet</span>
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
          <div className="super-admin-modal-box" style={{ maxWidth: 1360, width: '96%', maxHeight: '92vh', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Mail style={{ width: 22, height: 22, color: 'var(--ac-38bdf8)' }} />
                  <span>{editingTemplate ? `'${templateForm.name}' Şablonunu Düzenle` : 'Yeni E-Posta Şablonu Tasarla'}</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                  Sürükle-bırak görsel blok editörü, canlı e-posta önizlemesi ve modal içi test gönderim altyapısı.
                </p>
              </div>

              {/* Mod Seçici (Görsel Builder vs HTML Kod) */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ display: 'flex', background: 'rgb(var(--rgb-ov) / 0.06)', padding: 3, borderRadius: 8, border: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                  <button
                    type="button"
                    onClick={async () => {
                      // HTML elle düzenlendiyse görsel editör bloklarını güncel HTML'den yeniden oluştur
                      if (!templateBlocksInSync && templateForm.html_content?.trim()) {
                        setTemplateCanvasBlocks(htmlToBlocks(templateForm.html_content));
                      }
                      setTemplateEditorTab('BUILDER');
                    }}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      padding: '6px 12px', fontSize: '0.75rem', fontWeight: 700, borderRadius: 6, border: 'none', cursor: 'pointer',
                      background: templateEditorTab === 'BUILDER' ? '#7134e2' : 'transparent',
                      color: templateEditorTab === 'BUILDER' ? '#fff' : 'var(--nt-94a3b8)'
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
                      color: templateEditorTab === 'CODE' ? '#fff' : 'var(--nt-94a3b8)'
                    }}
                  >
                    <Code style={{ width: 14, height: 14 }} />
                    <span>💻 HTML Kaynak Kodu</span>
                  </button>
                </div>

                <button onClick={() => setTemplateModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                  <X style={{ width: 20, height: 20 }} />
                </button>
              </div>
            </div>

            <form onSubmit={handleSaveTemplate} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 12, flex: 1, minHeight: 0 }}>
              <div className="ui-grid-3" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.6fr 2.2fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Şablon Kodu *</label>
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
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>Şablon Adı *</label>
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
                  <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 3 }}>E-Posta Konusu (Subject) *</label>
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
                <span style={{ fontSize: '0.68rem', fontWeight: 800, color: 'var(--ac-38bdf8)' }}>Dinamik Değişkenler:</span>
                {(templateForm.variables?.length ? templateForm.variables : ['company_name', 'contact_name', 'login_url']).map((v) => (
                  <button
                    type="button"
                    key={v}
                    onClick={() => {
                      if (templateEditorTab === 'CODE') {
                        setTemplateForm({ ...templateForm, html_content: templateForm.html_content + ` {{${v}}}` });
                      } else {
                        navigator.clipboard?.writeText(`{{${v}}}`);
                        notify(`'{{${v}}}' panoya kopyalandı! İstediğiniz blok alanına yapıştırabilirsiniz.`);
                      }
                    }}
                    style={{ fontSize: '0.62rem', fontFamily: 'monospace', padding: '2px 5px', borderRadius: 4, background: 'rgb(var(--rgb-ov) / 0.08)', color: 'var(--ac-a78bfa)', border: '1px solid rgb(var(--rgb-ov) / 0.1)', cursor: 'pointer' }}
                    title="Panoya kopyalamak veya içeriğe eklemek için tıklayın"
                  >
                    {`{{${v}}}`}
                  </button>
                ))}
              </div>

              {/* GÖRSEL BUILDER MODU (Madde 5) */}
              {templateEditorTab === 'BUILDER' ? (
                <EmailTemplateBuilder
                  blocks={templateCanvasBlocks}
                  variables={templateForm.variables?.length ? templateForm.variables : ['company_name', 'contact_name', 'login_url']}
                  onChange={(next) => {
                    setTemplateCanvasBlocks(next);
                    setTemplateBlocksInSync(true);
                    setTemplateForm((prev) => ({ ...prev, html_content: compileBlocksToHtml(next) }));
                  }}
                />
              ) : (
                /* HTML KOD EDİTÖRÜ MODU */
                <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 12, minHeight: 520, height: 'auto', maxHeight: '72vh' }}>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Code style={{ width: 13, height: 13, color: 'var(--ac-a78bfa)' }} />
                      <span>HTML Kod Editörü</span>
                    </label>
                    <textarea
                      rows="18"
                      required
                      value={templateForm.html_content}
                      onChange={(e) => { setTemplateForm({ ...templateForm, html_content: e.target.value }); setTemplateBlocksInSync(false); }}
                      placeholder="<html><body>...</body></html>"
                      className="super-admin-input"
                      style={{ flex: 1, fontFamily: 'monospace', fontSize: '0.725rem', lineHeight: 1.4, whiteSpace: 'pre', background: 'var(--sf-0b0f19)' }}
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Eye style={{ width: 13, height: 13, color: 'var(--ac-38bdf8)' }} />
                      <span>Canlı E-Posta Önizlemesi (True Render)</span>
                    </label>
                    <div style={{ flex: 1, borderRadius: 8, overflow: 'hidden', border: '1px solid rgb(var(--rgb-ov) / 0.1)', background: '#ffffff' }}>
                      <iframe
                        title="HTML Preview"
                        srcDoc={templateForm.html_content}
                        sandbox=""
                        style={{ width: '100%', height: '100%', border: 'none' }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Alt Aksiyon Butonları & Madde 4 Modal İçi Test Gönder */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: 14,
                paddingBottom: 4,
                borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                position: 'sticky',
                bottom: 0,
                background: 'var(--sf-0d1222)',
                zIndex: 20,
                marginTop: 'auto'
              }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', cursor: 'pointer' }}>
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
                    style={{ background: 'rgba(56,189,248,0.15)', color: 'var(--ac-38bdf8)', borderColor: 'rgba(56,189,248,0.3)', fontWeight: 700, padding: '7px 14px' }}
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Clock style={{ width: 20, height: 20, color: 'var(--ac-fbbf24)' }} />
                  <span>{editingSchedule ? `'${scheduleForm.name}' Zamanlama Kuralını Düzenle` : 'Yeni Bildirim Zamanlayıcısı Tanımla'}</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                  Kayıt anında veya paket bitimine 3 ay kala periyodik e-posta gönderim kuralı.
                </p>
              </div>
              <button onClick={() => setScheduleModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveSchedule} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Kural Adı *</label>
                <input
                  type="text"
                  required
                  value={scheduleForm.name}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, name: e.target.value })}
                  placeholder="Paket Bitimine 3 Ay Kala 15 Günde Bir Hatırlatıcı"
                  className="super-admin-input"
                />
              </div>

              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Tetikleme Senaryosu *</label>
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
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>İletilecek Şablon *</label>
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
                <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, padding: 10, borderRadius: 8, background: 'rgb(var(--rgb-ov) / 0.03)', border: '1px solid rgb(var(--rgb-ov) / 0.06)' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Kaç Gün Kala Başlasın?</label>
                    <input
                      type="number"
                      value={scheduleForm.target_lead_days}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, target_lead_days: Number(e.target.value) })}
                      placeholder="90 (3 Ay)"
                      className="super-admin-input"
                    />
                    <span style={{ fontSize: '0.65rem', color: 'var(--nt-94a3b8)' }}>Varsayılan: 90 gün (3 ay)</span>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>Gönderim Sıklığı (Gün)?</label>
                    <input
                      type="number"
                      value={scheduleForm.frequency_days}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, frequency_days: Number(e.target.value) })}
                      placeholder="15 (15 Günde Bir)"
                      className="super-admin-input"
                    />
                    <span style={{ fontSize: '0.65rem', color: 'var(--nt-94a3b8)' }}>Varsayılan: 15 günde bir</span>
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 12, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', cursor: 'pointer' }}>
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

      {/* ======================================================== */}
      {/* SEKTÖR TANIMLAMA MODALI (TİCARET BAKANLIĞI)              */}
      {/* ======================================================== */}
      {sectorModalOpen && (
        <div className="super-admin-modal-overlay">
          <div className="super-admin-modal-box">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 14, borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--nt-ffffff)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Layers style={{ width: 18, height: 18, color: '#10b981' }} />
                  <span>{editingSector ? `'${sectorForm.code} - ${sectorForm.name}' Sektörünü Düzenle` : 'Yeni Sektör Tanımla'}</span>
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                  T.C. Ticaret Bakanlığı resmi sektör kataloğu ana sektör tanımı.
                </p>
              </div>
              <button onClick={() => setSectorModalOpen(false)} style={{ background: 'transparent', border: 'none', color: 'var(--nt-94a3b8)', cursor: 'pointer' }}>
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            <form onSubmit={handleSaveSector} style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 10 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.725rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                    Sektör Kodu *
                  </label>
                  <input
                    type="text"
                    required
                    disabled={!!editingSector}
                    value={sectorForm.code}
                    onChange={(e) => setSectorForm({ ...sectorForm, code: e.target.value.toUpperCase() })}
                    placeholder="Örn: A, B, C..."
                    className="super-admin-input"
                    style={{ fontFamily: 'monospace', fontWeight: 800, textTransform: 'uppercase' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.725rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                    Sektör Adı *
                  </label>
                  <input
                    type="text"
                    required
                    value={sectorForm.name}
                    onChange={(e) => setSectorForm({ ...sectorForm, name: e.target.value })}
                    placeholder="Örn: BİLİŞİM, İLETİŞİM VE MEDYA"
                    className="super-admin-input"
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.725rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', marginBottom: 4 }}>
                  Sektör Açıklaması (Opsiyonel)
                </label>
                <textarea
                  rows={3}
                  value={sectorForm.description}
                  onChange={(e) => setSectorForm({ ...sectorForm, description: e.target.value })}
                  placeholder="Sektörün kapsadığı iş kolları ve genel tanım..."
                  className="super-admin-textarea"
                />
              </div>

              {/* Sektör İkonu & Resmi Seçimi (Madde 1) */}
              <div style={{ padding: '12px 14px', borderRadius: 8, background: 'rgb(var(--rgb-ov) / 0.03)', border: '1px solid rgb(var(--rgb-ov) / 0.08)', display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <label style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--nt-cbd5e1)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <ImageIcon style={{ width: 14, height: 14, color: 'var(--ac-38bdf8)' }} />
                    <span>Sektör İkonu / Görseli (Eski Usül İkon / Resim)</span>
                  </label>
                  {(sectorForm.icon || sectorForm.image_url) && (
                    <button
                      type="button"
                      onClick={() => setSectorForm({ ...sectorForm, icon: '', image_url: '' })}
                      style={{ background: 'transparent', border: 'none', color: 'var(--ac-f87171)', fontSize: '0.68rem', cursor: 'pointer', fontWeight: 700 }}
                    >
                      İkon ve Görseli Temizle ✕
                    </button>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {/* Canlı Önizleme */}
                  <div style={{ width: 50, height: 50, borderRadius: 10, background: 'rgb(var(--rgb-ov) / 0.06)', border: '2px solid rgba(16, 185, 129, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', flexShrink: 0 }}>
                    {sectorForm.image_url ? (
                      <img src={sectorForm.image_url} alt="Sektör Görseli" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                      <span style={{ fontSize: '1.75rem' }}>{sectorForm.icon || '🏢'}</span>
                    )}
                  </div>

                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <input
                        type="text"
                        value={sectorForm.icon}
                        onChange={(e) => setSectorForm({ ...sectorForm, icon: e.target.value })}
                        placeholder="İkon / Emoji (Örn: 🌲, 💻, 🌾)"
                        className="super-admin-input"
                        style={{ flex: 1, fontSize: '0.85rem' }}
                      />
                      
                      <input
                        type="file"
                        id="sector-image-file"
                        accept="image/*"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            if (file.size > 2 * 1024 * 1024) {
                              notify("Resim dosyası 2MB'den küçük olmalıdır.");
                              return;
                            }
                            const reader = new FileReader();
                            reader.onload = (ev) => {
                              setSectorForm({ ...sectorForm, image_url: ev.target.result });
                            };
                            reader.readAsDataURL(file);
                          }
                        }}
                      />
                      <label
                        htmlFor="sector-image-file"
                        className="super-admin-btn-secondary"
                        style={{ cursor: 'pointer', fontSize: '0.72rem', padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 6, margin: 0, background: 'rgba(56,189,248,0.12)', color: 'var(--ac-38bdf8)', borderColor: 'rgba(56,189,248,0.3)', whiteSpace: 'nowrap' }}
                        title="PNG, JPG veya SVG resim dosyası seçin"
                      >
                        <ImageIcon style={{ width: 13, height: 13 }} />
                        <span>{sectorForm.image_url ? 'Resmi Değiştir' : 'Resim Yükle'}</span>
                      </label>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.65rem', color: 'var(--nt-94a3b8)', marginRight: 4 }}>Hızlı Seçim:</span>
                      {['🌲', '🎭', '💻', '🌾', '👗', '🎁', '✂️', '🚗', '🛒', '🚚', '🏗️', '🏦', '🏥', '⚖️', '🎓', '⚡', '🏢', '🛡️', '⚙️', '🚀', '💎', '📈', '🌐', '📦'].map((emoji) => (
                        <button
                          key={emoji}
                          type="button"
                          onClick={() => setSectorForm({ ...sectorForm, icon: emoji })}
                          style={{
                            background: sectorForm.icon === emoji ? 'rgba(16, 185, 129, 0.3)' : 'rgb(var(--rgb-ov) / 0.05)',
                            border: sectorForm.icon === emoji ? '1px solid #10b981' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                            borderRadius: 4,
                            padding: '2px 4px',
                            fontSize: '0.9rem',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          {emoji}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input
                    type="text"
                    value={sectorForm.image_url && !sectorForm.image_url.startsWith('data:') ? sectorForm.image_url : ''}
                    onChange={(e) => setSectorForm({ ...sectorForm, image_url: e.target.value })}
                    placeholder="Veya Harici Resim Linki (https://...)"
                    className="super-admin-input"
                    style={{ fontSize: '0.725rem' }}
                  />
                  {sectorForm.image_url && (
                    <button
                      type="button"
                      onClick={() => setSectorForm({ ...sectorForm, image_url: '' })}
                      className="super-admin-btn-secondary"
                      style={{ fontSize: '0.68rem', padding: '4px 8px', color: 'var(--ac-f87171)', whiteSpace: 'nowrap' }}
                    >
                      Resmi Kaldır
                    </button>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={sectorForm.is_active}
                    onChange={(e) => setSectorForm({ ...sectorForm, is_active: e.target.checked })}
                  />
                  <span style={{ fontWeight: 700 }}>Sektör Aktif</span>
                </label>
              </div>

              {/* FOOTER BUTONLARI */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 14, borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                <button type="button" onClick={() => setSectorModalOpen(false)} className="super-admin-btn-secondary">
                  Vazgeç
                </button>
                <button type="submit" disabled={processingId === 'save-sector'} className="super-admin-btn-corporate">
                  {processingId === 'save-sector' ? <RefreshCw style={{ width: 14, height: 14 }} className="animate-spin" /> : <Save style={{ width: 14, height: 14 }} />}
                  <span>{editingSector ? 'Değişiklikleri Kaydet' : 'Sektörü Kaydet'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <TenantCreditsModal tenant={creditTenant} onClose={() => setCreditTenant(null)} />
    </div>
  );
}
