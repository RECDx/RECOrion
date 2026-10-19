import React, { useState, useEffect } from 'react';
import {
  Building2,
  Users,
  Bot,
  Briefcase,
  Layers,
  Search,
  Plus,
  Trash2,
  Edit3,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Sparkles,
  Clock,
  Calendar,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  RefreshCw,
  Sliders,
  Shield,
  FileText,
  Check,
  ExternalLink,
  Laptop,
  Building,
  UserCheck,
  UserX,
  Cpu,
  Hash,
  Info,
  Star,
  Copy,
  Zap,
  Tag,
  Key,
  Lock,
  Eye,
  EyeOff,
  UserPlus,
  UploadCloud,
  Download,
  BookOpen,
  FileSpreadsheet,
  Globe,
  Video,
  Play,
  Link as LinkIcon
} from 'lucide-react';
import { api } from '../api';
import ThemeToggle from '../ui/ThemeToggle';
import { notify, toast } from '../ui/feedback';

export default function CompanyAdminConsole({
  currentUser,
  currentTenant,
  onSwitchToWorkspace,
  onGoToOfficialSite,
  onGoToSuperAdmin,
  onLogout
}) {
  const resolveInitialTenantId = () => {
    // COMPANY_ADMIN için currentUser.tenant_id MUTLAK önceliklidir
    if (currentUser?.role === 'COMPANY_ADMIN' && currentUser?.tenant_id) {
      return currentUser.tenant_id;
    }
    return currentTenant?.id || currentUser?.tenant_id || null;
  };

  const [activeTab, setActiveTab] = useState('DEPARTMENTS');
  const [tenantId, setTenantId] = useState(resolveInitialTenantId);
  const [tenant, setTenant] = useState(() => {
    const initId = resolveInitialTenantId();
    if (currentTenant && currentTenant.id === initId) {
      return currentTenant;
    }
    return null;
  });

  // =========================================================================
  // NORMAL İNSAN KULLANICI YÖNETİMİ & KOTA (Madde 1) STATE
  // =========================================================================
  const [users, setUsers] = useState([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [userQuota, setUserQuota] = useState({ active_users: 0, total_users: 0, max_users: 5, plan_name: '', is_limit_reached: false });
  const [userSearch, setUserSearch] = useState('');
  const [userStatusFilter, setUserStatusFilter] = useState('ALL'); // ALL | ACTIVE | DISABLED
  const [userDeptFilter, setUserDeptFilter] = useState('ALL');
  const [userViewMode, setUserViewMode] = useState('CARDS'); // CARDS | LIST
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    display_name: '',
    department_id: '',
    job_title_id: '',
    email: '',
    password: '',
    status: 'ACTIVE',
    role_id: '',
    extra_permissions: []
  });
  const [userFormError, setUserFormError] = useState('');
  const [isSavingUser, setIsSavingUser] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [isDeletingUser, setIsDeletingUser] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [systemRoles, setSystemRoles] = useState([]);
  const [isLoadingRoles, setIsLoadingRoles] = useState(false);
  const [systemPermissions, setSystemPermissions] = useState([]);
  const [isLoadingPermissions, setIsLoadingPermissions] = useState(false);
  const [permSearch, setPermSearch] = useState('');
  const [permModuleFilter, setPermModuleFilter] = useState('ALL');

  // =========================================================================
  // MADDE 1: DEPARTMANLAR STATE
  // =========================================================================
  const [departments, setDepartments] = useState([]);
  const [isLoadingDepts, setIsLoadingDepts] = useState(false);
  const [deptSearch, setDeptSearch] = useState('');
  const [deptViewMode, setDeptViewMode] = useState('CARDS'); // CARDS | LIST
  const [isDeptModalOpen, setIsDeptModalOpen] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [deptForm, setDeptForm] = useState({ name: '', description: '' });
  const [deptFormError, setDeptFormError] = useState('');
  const [isSavingDept, setIsSavingDept] = useState(false);
  const [deptToDelete, setDeptToDelete] = useState(null);
  const [isDeletingDept, setIsDeletingDept] = useState(false);

  // =========================================================================
  // MADDE 2: ŞİRKET ÜNVANLARI & RECORION AI KONTROL MOTORU STATE
  // =========================================================================
  const [jobTitles, setJobTitles] = useState([]);
  const [isLoadingTitles, setIsLoadingTitles] = useState(false);
  const [titleSearch, setTitleSearch] = useState('');
  const [titleViewMode, setTitleViewMode] = useState('CARDS'); // CARDS | LIST
  const [isTitleModalOpen, setIsTitleModalOpen] = useState(false);
  const [editingTitle, setEditingTitle] = useState(null);

  // Süper Yönetim Konsolu Şablonları & NACE Filtreleme Combobox
  const [systemTemplates, setSystemTemplates] = useState([]);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);
  const [templateFilterNaceOnly, setTemplateFilterNaceOnly] = useState(true);
  const [templateSectorFilter, setTemplateSectorFilter] = useState('COMPANY_SECTORS'); // 'COMPANY_SECTORS' | 'ALL' | specific sector name
  const [titleCreationMode, setTitleCreationMode] = useState('TEMPLATE'); // 'TEMPLATE' | 'CUSTOM'
  const [templateComboboxOpen, setTemplateComboboxOpen] = useState(false);
  const [templateSearchQuery, setTemplateSearchQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  const [titleForm, setTitleForm] = useState({
    title: '',
    code: '',
    category: 'YAZILIM',
    department_id: '',
    description: '',
    base_role_prompt: '',
    required_skills: '',
    recommended_model_code: 'glm-5.3',
    autonomy_level: 'L1',
    source_template_id: null
  });
  const [titleFormError, setTitleFormError] = useState('');
  const [isSavingTitle, setIsSavingTitle] = useState(false);
  const [isGeneratingTitlePrompt, setIsGeneratingTitlePrompt] = useState(false);
  const [titleToDelete, setTitleToDelete] = useState(null);
  const [isDeletingTitle, setIsDeletingTitle] = useState(false);
  const [expandedPromptId, setExpandedPromptId] = useState(null);

  // =========================================================================
  // MADDE 3: AI AJAN İŞE ALIM VE YAŞAM DÖNGÜSÜ STATE
  // =========================================================================
  const [aiAgents, setAiAgents] = useState([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [agentSearch, setAgentSearch] = useState('');
  const [agentStatusFilter, setAgentStatusFilter] = useState('ALL'); // ALL | ACTIVE | DISABLED
  const [agentViewMode, setAgentViewMode] = useState('CARDS'); // CARDS | LIST
  const [availableModels, setAvailableModels] = useState([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [agentQuota, setAgentQuota] = useState({ active_agents: 0, max_agents: 5, plan_name: '', is_limit_reached: false });

  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [agentForm, setAgentForm] = useState({
    display_name: '',
    model_code: 'glm-5.3',
    job_title_id: '',
    department_id: '',
    description: '',
    hired_at: new Date().toISOString().split('T')[0],
    autonomy_level: 'L1',
    system_prompt: ''
  });
  const [agentFormError, setAgentFormError] = useState('');
  const [isSavingAgent, setIsSavingAgent] = useState(false);
  const [isGeneratingAgentPrompt, setIsGeneratingAgentPrompt] = useState(false);
  const [isDeepSearchingSectorTitle, setIsDeepSearchingSectorTitle] = useState(false);
  const [deepSearchSectorTitleResult, setDeepSearchSectorTitleResult] = useState(null);
  const [isExistingAgentDeepSearchingSectorTitle, setIsExistingAgentDeepSearchingSectorTitle] = useState(false);

  // İşten Çıkarma / Pasife Çekme Modal State
  const [agentToTerminate, setAgentToTerminate] = useState(null);
  const [terminationDate, setTerminationDate] = useState(new Date().toISOString().split('T')[0]);
  const [terminationReason, setTerminationReason] = useState('');
  const [isTerminatingAgent, setIsTerminatingAgent] = useState(false);

  // Silme Onay State
  const [agentToDelete, setAgentToDelete] = useState(null);
  const [isDeletingAgent, setIsDeletingAgent] = useState(false);

  // =========================================================================
  // AI AJANLARI UZMANLIK DOKÜMANLARI & RAG HAFIZA (Madde 2) STATE
  // =========================================================================
  const [selectedAgentForDocs, setSelectedAgentForDocs] = useState(null);
  const [isDocsModalOpen, setIsDocsModalOpen] = useState(false);
  const [agentDocuments, setAgentDocuments] = useState([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const [uploadDocError, setUploadDocError] = useState('');
  const [docToDelete, setDocToDelete] = useState(null);
  const [isDeletingDoc, setIsDeletingDoc] = useState(false);
  const [previewDocId, setPreviewDocId] = useState(null);
  const [docSourceTab, setDocSourceTab] = useState('file'); // 'file' | 'web' | 'video' | 'search'
  const [webLinkUrl, setWebLinkUrl] = useState('');
  const [webLinkTitle, setWebLinkTitle] = useState('');
  const [isSubmittingWebLink, setIsSubmittingWebLink] = useState(false);
  const [videoLinkUrl, setVideoLinkUrl] = useState('');
  const [videoLinkTitle, setVideoLinkTitle] = useState('');
  const [isSubmittingVideoLink, setIsSubmittingVideoLink] = useState(false);
  const [deepSearchQuery, setDeepSearchQuery] = useState('');
  const [isSubmittingDeepSearch, setIsSubmittingDeepSearch] = useState(false);

  // =========================================================================
  // KURUMSAL MANİFESTO, SEKTÖRLER & NACE KODLARI STATE (Madde 1 & 6)
  // =========================================================================
  const [manifestoText, setManifestoText] = useState('');
  const [manifestoSectors, setManifestoSectors] = useState([]);
  const [manifestoNaceCodes, setManifestoNaceCodes] = useState([]);
  const [allSectors, setAllSectors] = useState([]);
  const [isLoadingAllSectors, setIsLoadingAllSectors] = useState(false);
  const [naceSearchQuery, setNaceSearchQuery] = useState('');
  const [naceSearchResults, setNaceSearchResults] = useState([]);
  const [isSearchingNace, setIsSearchingNace] = useState(false);
  const [customSectorInput, setCustomSectorInput] = useState('');
  const [manifestoModel, setManifestoModel] = useState('glm-5.3');
  const [manifestoInstructions, setManifestoInstructions] = useState('');
  const [isGeneratingManifesto, setIsGeneratingManifesto] = useState(false);
  const [isSavingManifesto, setIsSavingManifesto] = useState(false);

  // ESC Tuşu ile Açık Olan Detay / Düzenleme Modalını Kaydetmeden Kapatma (Madde 1)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' || e.keyCode === 27) {
        if (templateComboboxOpen) {
          setTemplateComboboxOpen(false);
        } else if (docToDelete) {
          setDocToDelete(null);
        } else if (userToDelete) {
          setUserToDelete(null);
        } else if (agentToDelete) {
          setAgentToDelete(null);
        } else if (agentToTerminate) {
          setAgentToTerminate(null);
        } else if (titleToDelete) {
          setTitleToDelete(null);
        } else if (deptToDelete) {
          setDeptToDelete(null);
        } else if (isDocsModalOpen) {
          setIsDocsModalOpen(false);
          setSelectedAgentForDocs(null);
        } else if (isUserModalOpen) {
          setIsUserModalOpen(false);
          setEditingUser(null);
        } else if (isAgentModalOpen) {
          setIsAgentModalOpen(false);
          setEditingAgent(null);
        } else if (isTitleModalOpen) {
          setIsTitleModalOpen(false);
          setEditingTitle(null);
        } else if (isDeptModalOpen) {
          setIsDeptModalOpen(false);
          setEditingDept(null);
        } else if (expandedPromptId) {
          setExpandedPromptId(null);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    templateComboboxOpen,
    userToDelete,
    agentToDelete,
    agentToTerminate,
    titleToDelete,
    deptToDelete,
    docToDelete,
    isDocsModalOpen,
    isUserModalOpen,
    isAgentModalOpen,
    isTitleModalOpen,
    isDeptModalOpen,
    expandedPromptId
  ]);

  // Bildirimler ortak toast sistemiyle gösterilir (src/ui/feedback.js)
  const showToast = (text, type = 'success') => {
    (toast[type] || toast.info)(text);
  };

  const getActiveTenantId = () => {
    if (currentUser?.role === 'COMPANY_ADMIN' && currentUser?.tenant_id) {
      return currentUser.tenant_id;
    }
    return tenantId || currentTenant?.id || tenant?.id || currentUser?.tenant_id;
  };

  // currentUser veya currentTenant değiştiğinde tenantId senkronizasyonu
  useEffect(() => {
    const expectedId = (currentUser?.role === 'COMPANY_ADMIN' && currentUser?.tenant_id)
      ? currentUser.tenant_id
      : (currentTenant?.id || currentUser?.tenant_id || null);

    if (expectedId && expectedId !== tenantId) {
      setTenantId(expectedId);
    }
  }, [currentUser, currentTenant]);

  // Şirket Bilgilerini Yükle
  useEffect(() => {
    async function fetchTenantData() {
      const targetId = getActiveTenantId();
      if (!targetId) return;

      try {
        if (!tenant || tenant.id !== targetId) {
          const details = await api.getTenantDetails(targetId);
          const tenantData = details?.tenant ? details.tenant : details;
          setTenant(tenantData);
        }
      } catch (err) {
        console.warn("Şirket detayları yüklenemedi:", err);
      }
    }
    fetchTenantData();
  }, [tenantId, currentUser]);

  // Manifesto Metni, Sektörler, NACE ve Model Senkronizasyonu (Madde 1 & 6)
  useEffect(() => {
    if (tenant) {
      if (tenant.sector_manifesto !== undefined && tenant.sector_manifesto !== null) {
        setManifestoText(tenant.sector_manifesto);
      }
      if (tenant.sectors) {
        setManifestoSectors(Array.isArray(tenant.sectors) ? [...tenant.sectors] : []);
      }
      if (tenant.nace_codes) {
        setManifestoNaceCodes(Array.isArray(tenant.nace_codes) ? [...tenant.nace_codes] : []);
      }
    }
  }, [tenant]);

  useEffect(() => {
    if (availableModels && availableModels.length > 0) {
      const exists = availableModels.some(m => m.model_code === manifestoModel);
      if (!exists) {
        setManifestoModel(availableModels[0].model_code);
      }
    }
  }, [availableModels]);

  const loadAllSectors = async () => {
    if (allSectors.length > 0) return;
    setIsLoadingAllSectors(true);
    try {
      const data = await api.getSectors(true);
      setAllSectors(data || []);
    } catch (err) {
      console.warn("Sektör tanımları alınamadı:", err);
    } finally {
      setIsLoadingAllSectors(false);
    }
  };

  // Departmanları Çek
  const loadDepartments = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsLoadingDepts(true);
    try {
      const data = await api.getDepartments(targetId);
      setDepartments(data || []);
    } catch (err) {
      console.error("Departmanlar yüklenirken hata:", err);
      showToast(err.message || "Departmanlar yüklenemedi", "error");
    } finally {
      setIsLoadingDepts(false);
    }
  };

  // Şirket Ünvanlarını Çek (Madde 2)
  const loadJobTitles = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsLoadingTitles(true);
    try {
      const data = await api.getCompanyJobTitles(targetId);
      setJobTitles(data || []);
    } catch (err) {
      console.error("Şirket ünvanları yüklenirken hata:", err);
      showToast(err.message || "Ünvanlar yüklenemedi", "error");
    } finally {
      setIsLoadingTitles(false);
    }
  };

  // Sistem Şablonlarını Çek (Combobox için)
  const loadSystemTemplates = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsLoadingTemplates(true);
    try {
      const templates = await api.getSystemJobTitleTemplates(targetId);
      setSystemTemplates(templates || []);
    } catch (err) {
      console.warn("Sistem şablonları çekilemedi:", err);
    } finally {
      setIsLoadingTemplates(false);
    }
  };

  // AI Ajanlarını Çek (Madde 3)
  const loadAIAgents = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsLoadingAgents(true);
    try {
      const data = await api.getCompanyAIAgents(targetId);
      setAiAgents(data || []);
    } catch (err) {
      console.error("AI Ajanlar yüklenirken hata:", err);
      showToast(err.message || "AI Ajanlar yüklenemedi", "error");
    } finally {
      setIsLoadingAgents(false);
    }
  };

  // AI Ajan Paket Kotasını Çek (Madde 5)
  const loadAgentQuota = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) return;
    try {
      const q = await api.getAgentQuota(targetId);
      if (q) setAgentQuota(q);
    } catch (err) {
      console.warn("Kota bilgisi alınamadı:", err);
    }
  };

  // LLM Modellerini Çek (Madde 3)
  const loadAvailableModels = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsLoadingModels(true);
    try {
      const models = await api.getAvailableLLMModels(targetId);
      setAvailableModels(models || []);
    } catch (err) {
      console.warn("LLM modelleri çekilemedi:", err);
    } finally {
      setIsLoadingModels(false);
    }
  };

  // İnsan Kullanıcıları Çek (Madde 1)
  const loadUsers = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsLoadingUsers(true);
    try {
      const data = await api.getCompanyUsers(targetId);
      setUsers(data || []);
    } catch (err) {
      console.error("Kullanıcılar yüklenirken hata:", err);
      showToast(err.message || "Kullanıcılar yüklenemedi", "error");
    } finally {
      setIsLoadingUsers(false);
    }
  };

  // İnsan Kullanıcı Paket Kotasını Çek (Madde 1)
  const loadUserQuota = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) return;
    try {
      const q = await api.getCompanyUserQuota(targetId);
      if (q) setUserQuota(q);
    } catch (err) {
      console.warn("Kullanıcı kota bilgisi alınamadı:", err);
    }
  };

  // Sistem Yetki Rollerini Çek (Süper Yöneticinin Tanımladığı)
  const loadSystemRoles = async () => {
    if (systemRoles.length > 0) return;
    setIsLoadingRoles(true);
    try {
      const roles = await api.getSystemRoles();
      setSystemRoles(roles || []);
    } catch (err) {
      console.warn("Sistem yetki rolleri alınamadı:", err);
    } finally {
      setIsLoadingRoles(false);
    }
  };

  // İzin Kataloğunu Çek
  const loadSystemPermissions = async () => {
    if (systemPermissions.length > 0) return;
    setIsLoadingPermissions(true);
    try {
      const perms = await api.getPermissions();
      setSystemPermissions(perms || []);
    } catch (err) {
      console.warn("İzin kataloğu alınamadı:", err);
    } finally {
      setIsLoadingPermissions(false);
    }
  };

  // İlk Yükleme ve Tenant Değişimi
  useEffect(() => {
    if (tenantId) {
      loadUsers();
      loadUserQuota();
      loadDepartments();
      loadJobTitles();
      loadSystemTemplates();
      loadAIAgents();
      loadAvailableModels();
      loadAgentQuota();
      loadAllSectors();
      loadSystemRoles();
      loadSystemPermissions();
    }
  }, [tenantId]);

  // Sekme Değişiminde İlgili Verileri Tazele
  useEffect(() => {
    if (activeTab === 'USERS') {
      loadUsers();
      loadUserQuota();
      loadDepartments();
      loadJobTitles();
      loadSystemRoles();
      loadSystemPermissions();
    } else if (activeTab === 'DEPARTMENTS') {
      loadDepartments();
    } else if (activeTab === 'JOB_TITLES') {
      loadJobTitles();
      if (systemTemplates.length === 0) loadSystemTemplates();
    } else if (activeTab === 'AI_AGENTS') {
      loadAIAgents();
      loadJobTitles();
      loadDepartments();
      loadAgentQuota();
      if (availableModels.length === 0) loadAvailableModels();
    } else if (activeTab === 'MANIFESTO') {
      loadAllSectors();
      if (availableModels.length === 0) loadAvailableModels();
    }
  }, [activeTab]);

  // =========================================================================
  // NORMAL İNSAN KULLANICI YÖNETİMİ HANDLERS (Madde 1)
  // =========================================================================
  const handleOpenCreateUser = () => {
    setEditingUser(null);
    const defaultRoleId = systemRoles.length > 0
      ? (systemRoles.find(r => r.name.toLowerCase().includes('standart') || r.name.toLowerCase().includes('kullanıcı'))?.id || systemRoles[0]?.id || '')
      : '';
    setUserForm({
      display_name: '',
      department_id: departments[0]?.id || '',
      job_title_id: jobTitles[0]?.id || '',
      email: '',
      password: '',
      status: 'ACTIVE',
      role_id: defaultRoleId,
      extra_permissions: []
    });
    setUserFormError('');
    setShowPassword(false);
    setIsUserModalOpen(true);
  };

  const handleOpenEditUser = (u) => {
    setEditingUser(u);
    setUserForm({
      display_name: u.display_name || '',
      department_id: u.department_id || '',
      job_title_id: u.job_title_id || '',
      email: u.email || '',
      password: '', // Boşsa değiştirilmez
      status: u.status === 'DISABLED' ? 'DISABLED' : 'ACTIVE',
      role_id: u.role_id || '',
      extra_permissions: Array.isArray(u.extra_permissions) ? [...u.extra_permissions] : []
    });
    setUserFormError('');
    setShowPassword(false);
    setIsUserModalOpen(true);
  };

  const handleGenerateStrongUserPassword = () => {
    const upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    const lower = 'abcdefghijkmnopqrstuvwxyz';
    const digits = '23456789';
    const symbols = '!@#$%&*';
    const all = upper + lower + digits + symbols;
    let pass = '';
    pass += upper.charAt(Math.floor(Math.random() * upper.length));
    pass += lower.charAt(Math.floor(Math.random() * lower.length));
    pass += digits.charAt(Math.floor(Math.random() * digits.length));
    pass += symbols.charAt(Math.floor(Math.random() * symbols.length));
    for (let i = 4; i < 14; i++) {
      pass += all.charAt(Math.floor(Math.random() * all.length));
    }
    pass = pass.split('').sort(() => 0.5 - Math.random()).join('');
    setUserForm(prev => ({ ...prev, password: pass }));
    setShowPassword(true);
    showToast('🔑 Güçlü şifre üretildi!', 'info');
  };

  const handleToggleExtraPermission = (code) => {
    setUserForm(prev => {
      const current = prev.extra_permissions || [];
      if (current.includes(code)) {
        return { ...prev, extra_permissions: current.filter(c => c !== code) };
      } else {
        return { ...prev, extra_permissions: [...current, code] };
      }
    });
  };

  const handleSaveUser = async (e) => {
    if (e) e.preventDefault();
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setUserFormError('');

    const cleanName = (userForm.display_name || '').trim();
    if (!cleanName) {
      setUserFormError('Adı Soyadı alanı zorunludur.');
      return;
    }

    const cleanEmail = (userForm.email || '').trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@')) {
      setUserFormError('Geçerli bir e-posta adresi giriniz.');
      return;
    }

    if (!editingUser) {
      if (!userForm.password || userForm.password.trim().length < 6) {
        setUserFormError('Yeni kullanıcı için en az 6 karakterli bir şifre belirleyiniz veya "Güçlü Şifre Oluştur" butonunu kullanınız.');
        return;
      }
      if (userForm.status === 'ACTIVE' && userQuota.is_limit_reached) {
        setUserFormError(`Paket kotanız (${userQuota.max_users} İnsan Kullanıcı) dolmuştur. Yeni aktif kullanıcı ekleyemezsiniz.`);
        return;
      }
    } else {
      if (userForm.password && userForm.password.trim().length < 6) {
        setUserFormError('Yeni şifre en az 6 karakter olmalıdır.');
        return;
      }
      if (editingUser.status === 'DISABLED' && userForm.status === 'ACTIVE' && userQuota.is_limit_reached) {
        setUserFormError(`Paket kotanız doludur. Pasif kullanıcıyı aktifleştiremezsiniz.`);
        return;
      }
    }

    setIsSavingUser(true);
    try {
      const payload = {
        display_name: cleanName,
        email: cleanEmail,
        department_id: userForm.department_id || null,
        job_title_id: userForm.job_title_id || null,
        status: userForm.status,
        role_id: userForm.role_id || null,
        extra_permissions: userForm.extra_permissions || []
      };

      if (userForm.password && userForm.password.trim()) {
        payload.password = userForm.password.trim();
      }

      if (editingUser) {
        await api.updateCompanyUser(targetId, editingUser.id, payload);
        showToast(`'${cleanName}' kullanıcısı başarıyla güncellendi.`);
      } else {
        await api.createCompanyUser(targetId, payload);
        showToast(`'${cleanName}' kullanıcısı başarıyla tanımlandı.`);
      }

      setIsUserModalOpen(false);
      setEditingUser(null);
      await loadUsers();
      await loadUserQuota();
    } catch (err) {
      console.error("Kullanıcı kaydetme hatası:", err);
      setUserFormError(err.message || "Kullanıcı kaydedilemedi");
    } finally {
      setIsSavingUser(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsDeletingUser(true);
    try {
      await api.deleteCompanyUser(targetId, userToDelete.id);
      showToast(`'${userToDelete.display_name}' kullanıcısı silindi.`);
      setUserToDelete(null);
      await loadUsers();
      await loadUserQuota();
    } catch (err) {
      console.error("Kullanıcı silme hatası:", err);
      showToast(err.message || "Kullanıcı silinemedi", "error");
    } finally {
      setIsDeletingUser(false);
    }
  };

  // =========================================================================
  // MADDE 1 HANDLERS (Departmanlar)
  // =========================================================================
  const handleOpenCreateDept = () => {
    setEditingDept(null);
    setDeptForm({ name: '', description: '' });
    setDeptFormError('');
    setIsDeptModalOpen(true);
  };

  const handleOpenEditDept = (dept) => {
    setEditingDept(dept);
    setDeptForm({ name: dept.name, description: dept.description || '' });
    setDeptFormError('');
    setIsDeptModalOpen(true);
  };

  const handleSaveDepartment = async (e) => {
    e.preventDefault();
    const name = deptForm.name.trim();
    if (!name) {
      setDeptFormError("Lütfen departman adını giriniz.");
      return;
    }
    if (name.length > 128) {
      setDeptFormError("Departman adı en fazla 128 karakter olabilir.");
      return;
    }

    const targetId = tenantId || tenant?.id || currentUser?.tenant_id;
    if (!targetId) {
      setDeptFormError("Şirket kimliği (Tenant ID) tespit edilemedi.");
      return;
    }

    setIsSavingDept(true);
    setDeptFormError('');
    try {
      if (editingDept) {
        const updated = await api.updateDepartment(targetId, editingDept.id, {
          name,
          description: deptForm.description.trim() || null
        });
        setDepartments(prev => prev.map(d => d.id === editingDept.id ? { ...d, ...updated } : d));
        showToast(`'${name}' departmanı başarıyla güncellendi.`);
      } else {
        const created = await api.createDepartment(targetId, {
          name,
          description: deptForm.description.trim() || null
        });
        setDepartments(prev => [...prev, created]);
        showToast(`'${name}' departmanı başarıyla oluşturuldu.`);
      }
      setIsDeptModalOpen(false);
    } catch (err) {
      setDeptFormError(err.message || "Departman kaydedilirken hata oluştu.");
    } finally {
      setIsSavingDept(false);
    }
  };

  const confirmDeleteDept = async () => {
    if (!deptToDelete) return;
    const targetId = tenantId || tenant?.id || currentUser?.tenant_id;
    setIsDeletingDept(true);
    try {
      await api.deleteDepartment(targetId, deptToDelete.id);
      setDepartments(prev => prev.filter(d => d.id !== deptToDelete.id));
      showToast(`'${deptToDelete.name}' departmanı silindi.`);
      setDeptToDelete(null);
    } catch (err) {
      showToast(err.message || "Departman silinemedi.", "error");
    } finally {
      setIsDeletingDept(false);
    }
  };

  const filteredDepartments = departments.filter(d => {
    if (!deptSearch.trim()) return true;
    const q = deptSearch.toLowerCase();
    return (
      d.name?.toLowerCase().includes(q) ||
      d.description?.toLowerCase().includes(q)
    );
  });

  const filteredUsers = users.filter(u => {
    if (userSearch.trim()) {
      const q = userSearch.toLowerCase();
      const nameMatch = (u.display_name || '').toLowerCase().includes(q);
      const emailMatch = (u.email || '').toLowerCase().includes(q);
      if (!nameMatch && !emailMatch) return false;
    }
    if (userStatusFilter === 'ACTIVE' && u.status === 'DISABLED') return false;
    if (userStatusFilter === 'DISABLED' && u.status !== 'DISABLED') return false;
    if (userDeptFilter !== 'ALL' && u.department_id !== userDeptFilter) return false;
    return true;
  });

  const copyToClipboard = (text, label) => {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
      showToast(`✓ ${label || 'Metin'} panoya kopyalandı!`);
    }
  };

  // =========================================================================
  // MADDE 2 HANDLERS (Şirket Ünvanları & RECOrion AI Kontrol Motoru)
  // =========================================================================
  const handleOpenCreateTitle = () => {
    setEditingTitle(null);
    setSelectedTemplate(null);
    setTemplateComboboxOpen(false);
    setTemplateSearchQuery('');
    setTemplateFilterNaceOnly(true);
    setTemplateSectorFilter('COMPANY_SECTORS');
    setTitleCreationMode('TEMPLATE');

    const defaultCategory = (tenant?.sectors && tenant.sectors.length > 0)
      ? String(tenant.sectors[0]).toUpperCase()
      : 'GENEL';

    const defaultDept = departments.length > 0 ? departments[0].id : '';

    setTitleForm({
      title: '',
      code: '',
      category: defaultCategory,
      department_id: defaultDept,
      description: '',
      base_role_prompt: '',
      required_skills: '',
      recommended_model_code: 'glm-5.3',
      autonomy_level: 'L1',
      source_template_id: null
    });
    setTitleFormError('');
    if (systemTemplates.length === 0) {
      loadSystemTemplates();
    }
    setIsTitleModalOpen(true);
  };

  // Combobox'tan Sistem Şablonu Seçildiğinde Otomatik Doldur (Madde 2: Rol promptu otomatik güncellenir)
  const handleSelectSystemTemplate = (tpl) => {
    setSelectedTemplate(tpl);
    setTemplateComboboxOpen(false);
    if (!tpl) return;

    setTitleForm(prev => ({
      ...prev,
      title: tpl.title,
      code: tpl.code,
      category: tpl.category,
      description: tpl.description || '',
      base_role_prompt: tpl.base_role_prompt || '', // Otomatik olarak tanımdan eklenir!
      required_skills: (tpl.required_skills || []).join(', '),
      recommended_model_code: tpl.recommended_model_code || 'glm-5.3',
      autonomy_level: tpl.autonomy_level || 'L1',
      source_template_id: tpl.id
    }));
  };

  const handleOpenEditTitle = (titleObj) => {
    setEditingTitle(titleObj);
    setSelectedTemplate(null);
    setTemplateComboboxOpen(false);
    setTitleCreationMode('CUSTOM');
    setTitleForm({
      title: titleObj.title,
      code: titleObj.code,
      category: titleObj.category,
      department_id: titleObj.department_id || '',
      description: titleObj.description || '',
      base_role_prompt: titleObj.base_role_prompt || '',
      required_skills: (titleObj.required_skills || []).join(', '),
      recommended_model_code: titleObj.recommended_model_code || 'glm-5.3',
      autonomy_level: titleObj.autonomy_level || 'L1',
      source_template_id: null
    });
    setTitleFormError('');
    setIsTitleModalOpen(true);
  };

  // Seçili EVREN AI Modeli ile Sistem Rol Promptu Yazdır (Madde 2)
  const handleGenerateTitlePrompt = async () => {
    const title = titleForm.title.trim();
    if (!title) {
      setTitleFormError("Lütfen önce ünvan adını giriniz. AI bu ünvana özel prompt üretecektir.");
      return;
    }
    const targetId = getActiveTenantId();
    if (!targetId) {
      setTitleFormError("Şirket kimliği bulunamadı.");
      return;
    }

    setIsGeneratingTitlePrompt(true);
    setTitleFormError('');
    try {
      const skillsArray = titleForm.required_skills
        ? titleForm.required_skills.split(',').map(s => s.trim()).filter(Boolean)
        : [];
      const res = await api.generateRolePrompt(targetId, {
        title,
        category: titleForm.category,
        description: titleForm.description,
        required_skills: skillsArray,
        model_code: titleForm.recommended_model_code || 'glm-5.3',
        autonomy_level: titleForm.autonomy_level || 'L1'
      });
      if (res && res.role_prompt) {
        setTitleForm(prev => ({
          ...prev,
          base_role_prompt: res.role_prompt
        }));
      }
    } catch (err) {
      console.error("AI Rol Promptu üretilemedi:", err);
      setTitleFormError("AI Rol Promptu oluşturulurken hata: " + (err.message || ''));
    } finally {
      setIsGeneratingTitlePrompt(false);
    }
  };

  const handleSaveJobTitle = async (e) => {
    e.preventDefault();
    const title = titleForm.title.trim();
    if (!title) {
      setTitleFormError("Lütfen ünvan adını giriniz.");
      return;
    }

    if (departments.length > 0 && !titleForm.department_id) {
      setTitleFormError("Lütfen ünvanın bağlı olacağı departmanı seçiniz.");
      return;
    }

    const rolePrompt = titleForm.base_role_prompt.trim();
    if (!rolePrompt) {
      setTitleFormError("Sistem Rol Promptu boş bırakılamaz. Lütfen bir şablon seçin veya kendi rol promptunuzu yazın.");
      return;
    }

    const targetId = tenantId || tenant?.id || currentUser?.tenant_id;
    if (!targetId) {
      setTitleFormError("Şirket kimliği (Tenant ID) tespit edilemedi.");
      return;
    }

    setIsSavingTitle(true);
    setTitleFormError('');

    const skillsArray = titleForm.required_skills
      ? titleForm.required_skills.split(',').map(s => s.trim()).filter(Boolean)
      : [];

    const payload = {
      title,
      code: titleForm.code.trim() || undefined,
      category: titleForm.category.trim().toUpperCase(),
      department_id: titleForm.department_id || undefined,
      description: titleForm.description.trim() || null,
      base_role_prompt: rolePrompt,
      required_skills: skillsArray,
      recommended_model_code: titleForm.recommended_model_code,
      autonomy_level: titleForm.autonomy_level,
      source_template_id: titleForm.source_template_id || undefined
    };

    try {
      if (editingTitle) {
        const updated = await api.updateCompanyJobTitle(targetId, editingTitle.id, payload);
        setJobTitles(prev => prev.map(t => t.id === editingTitle.id ? { ...t, ...updated } : t));
        showToast(`'${title}' ünvanı başarıyla güncellendi.`);
      } else {
        const created = await api.createCompanyJobTitle(targetId, payload);
        setJobTitles(prev => [created, ...prev]);

        if (created.ai_review_status === 'PROMOTED_GLOBAL') {
          showToast(`🌟 RECOrion AI: '${title}' ünvanı sistem geneli için faydalı bulundu ve ana şablona otomatik eklendi!`, 'success');
        } else {
          showToast(`'${title}' ünvanı şirketinize özel olarak başarıyla tanımlandı.`);
        }
      }
      setIsTitleModalOpen(false);
    } catch (err) {
      setTitleFormError(err.message || "Ünvan kaydedilirken bir hata oluştu.");
    } finally {
      setIsSavingTitle(false);
    }
  };

  const confirmDeleteTitle = async () => {
    if (!titleToDelete) return;
    const targetId = tenantId || tenant?.id || currentUser?.tenant_id;
    setIsDeletingTitle(true);
    try {
      await api.deleteCompanyJobTitle(targetId, titleToDelete.id);
      setJobTitles(prev => prev.filter(t => t.id !== titleToDelete.id));
      showToast(`'${titleToDelete.title}' ünvanı silindi.`);
      setTitleToDelete(null);
    } catch (err) {
      showToast(err.message || "Ünvan silinemedi.", "error");
    } finally {
      setIsDeletingTitle(false);
    }
  };

  const filteredJobTitles = jobTitles.filter(t => {
    if (!titleSearch.trim()) return true;
    const q = titleSearch.toLowerCase();
    return (
      t.title?.toLowerCase().includes(q) ||
      t.category?.toLowerCase().includes(q) ||
      t.description?.toLowerCase().includes(q) ||
      t.code?.toLowerCase().includes(q)
    );
  });

  // Combobox Filtrelenmiş Sistem Şablonları (Madde 2: Şirket Sektörlerine Göre Filtreleme)
  const companySectorsList = (tenant?.sectors || []).map(s => String(s).toUpperCase().trim());

  const filteredTemplates = systemTemplates.filter(t => {
    const tCat = (t.category || '').toUpperCase().trim();

    // Sektörel Filtreleme
    if (templateSectorFilter === 'COMPANY_SECTORS' && companySectorsList.length > 0) {
      const matchesCompanySector = companySectorsList.some(cs => cs === tCat || tCat.includes(cs) || cs.includes(tCat));
      if (!matchesCompanySector && !t.is_sector_recommended && !t.is_nace_recommended) {
        return false;
      }
    } else if (templateSectorFilter !== 'ALL' && templateSectorFilter !== 'COMPANY_SECTORS') {
      if (tCat !== templateSectorFilter.toUpperCase().trim()) {
        return false;
      }
    }

    if (templateFilterNaceOnly && !t.is_nace_recommended && !t.is_sector_recommended) {
      return false;
    }

    if (!templateSearchQuery.trim()) return true;
    const q = templateSearchQuery.toLowerCase();
    return (
      t.title?.toLowerCase().includes(q) ||
      t.category?.toLowerCase().includes(q) ||
      (t.description || '').toLowerCase().includes(q)
    );
  });

  // =========================================================================
  // MADDE 3 HANDLERS (AI Ajan İşe Alım & Yaşam Döngüsü)
  // =========================================================================
  // MADDE 3 HANDLERS (AI Ajan İşe Alım & Yaşam Döngüsü)
  // =========================================================================
  const handleOpenHireAgent = () => {
    setEditingAgent(null);
    setAgentFormError('');
    setDeepSearchSectorTitleResult(null);
    setIsDeepSearchingSectorTitle(false);

    const defaultTitle = jobTitles[0] || null;
    const defaultModel = defaultTitle?.recommended_model_code || 'glm-5.3';
    const defaultPrompt = defaultTitle?.base_role_prompt || '';
    const defaultDesc = defaultTitle?.description || '';
    const defaultDept = defaultTitle?.department_id || '';

    setAgentForm({
      display_name: '',
      model_code: defaultModel,
      job_title_id: defaultTitle?.id || '',
      department_id: defaultDept,
      description: defaultDesc,
      hired_at: new Date().toISOString().split('T')[0],
      autonomy_level: defaultTitle?.autonomy_level || 'L1',
      system_prompt: defaultPrompt,
      pending_learnings: null,
      deep_search_metadata: null
    });
    setIsAgentModalOpen(true);
  };

  const handleOpenEditAgent = (agent) => {
    setEditingAgent(agent);
    setAgentFormError('');
    setDeepSearchSectorTitleResult(null);
    setIsDeepSearchingSectorTitle(false);
    // Eğer düzenleme sırasında ajanın departmanı yoksa ünvandan tamamla
    const matchedTitle = jobTitles.find(t => t.id === agent.job_title_id);
    const deptId = agent.department_id || matchedTitle?.department_id || '';
    setAgentForm({
      display_name: agent.display_name || '',
      model_code: agent.model_code || matchedTitle?.recommended_model_code || 'glm-5.3',
      job_title_id: agent.job_title_id || '',
      department_id: deptId,
      description: agent.description || '',
      hired_at: agent.hired_at ? new Date(agent.hired_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
      autonomy_level: agent.autonomy_level || matchedTitle?.autonomy_level || 'L1',
      system_prompt: agent.system_prompt || '',
      pending_learnings: null,
      deep_search_metadata: null
    });
    setIsAgentModalOpen(true);
  };

  // Ünvan değiştiğinde otomatik departman, model, otonomi ve prompt tamamlama (Madde 3 & 4)
  const handleAgentJobTitleChange = (titleId) => {
    const selected = jobTitles.find(t => t.id === titleId);
    if (selected) {
      setAgentForm(prev => ({
        ...prev,
        job_title_id: titleId,
        department_id: selected.department_id || '', // Madde 3: Bağlı departman otomatik gelir
        model_code: selected.recommended_model_code || prev.model_code || 'glm-5.3', // Madde 4: Otomatik gelir
        autonomy_level: selected.autonomy_level || prev.autonomy_level || 'L1', // Madde 4: Otomatik gelir
        system_prompt: selected.base_role_prompt || prev.system_prompt,
        description: prev.description ? prev.description : (selected.description || '')
      }));
    } else {
      setAgentForm(prev => ({ ...prev, job_title_id: titleId, department_id: '' }));
    }
  };

  // AI Ajanına Özel Sistem Promptu Yazdır (Madde 4)
  const handleGenerateAgentPrompt = async () => {
    const agentName = agentForm.display_name.trim();
    if (!agentName) {
      setAgentFormError("Lütfen önce AI Ajan adını giriniz. Prompt bu ajanın kimliğine göre özelleştirilecektir.");
      return;
    }
    if (!agentForm.job_title_id) {
      setAgentFormError("Lütfen önce AI Ajan için bir şirket ünvanı seçiniz.");
      return;
    }
    const targetId = getActiveTenantId();
    if (!targetId) {
      setAgentFormError("Şirket kimliği bulunamadı.");
      return;
    }

    const selectedTitle = jobTitles.find(t => t.id === agentForm.job_title_id);
    const titleName = selectedTitle?.title || 'AI Ajanı';
    const category = selectedTitle?.category || 'GENEL';
    const desc = agentForm.description
      ? `${agentForm.description} (Ünvan Kapsamı: ${selectedTitle?.description || titleName})`
      : (selectedTitle?.description || titleName);

    setIsGeneratingAgentPrompt(true);
    setAgentFormError('');
    try {
      const skillsArray = selectedTitle?.required_skills || [];
      const res = await api.generateRolePrompt(targetId, {
        title: `${agentName} (${titleName})`,
        category,
        description: desc,
        required_skills: skillsArray,
        model_code: agentForm.model_code || 'glm-5.3',
        autonomy_level: agentForm.autonomy_level || 'L1'
      });
      if (res && res.role_prompt) {
        setAgentForm(prev => ({
          ...prev,
          system_prompt: res.role_prompt
        }));
      }
    } catch (err) {
      console.error("Ajan promptu üretilemedi:", err);
      setAgentFormError("Bu ajana özel AI promptu oluşturulurken hata: " + (err.message || ''));
    } finally {
      setIsGeneratingAgentPrompt(false);
    }
  };

  // Sektör & Ünvan Çift Odaklı Deep Search (Kullanıcı Talebi: Hem Şirket Sektörünü Hem de Ünvanın Ne İş Yaptığını Öğrenme)
  const handleDeepSearchSectorAndTitle = async () => {
    if (!agentForm.job_title_id) {
      setAgentFormError("Lütfen önce AI Ajan için bir şirket ünvanı seçiniz. Araştırma şirketin sektörü ve bu ünvan üzerine yapılacaktır.");
      return;
    }
    const targetId = getActiveTenantId();
    if (!targetId) {
      setAgentFormError("Şirket kimliği bulunamadı.");
      return;
    }

    setIsDeepSearchingSectorTitle(true);
    setAgentFormError('');

    try {
      const res = await api.deepSearchSectorTitle(targetId, {
        job_title_id: agentForm.job_title_id,
        agent_name: agentForm.display_name?.trim() || undefined,
        agent_id: editingAgent?.id || undefined,
        model_code: agentForm.model_code || 'glm-5.3'
      });

      if (res && res.success) {
        setDeepSearchSectorTitleResult(res);

        // Sistem promptunu otomatik zenginleştir
        if (res.enhanced_system_prompt) {
          setAgentForm(prev => ({
            ...prev,
            system_prompt: res.enhanced_system_prompt,
            pending_learnings: res.learnings || null,
            deep_search_metadata: {
              sector_name: res.sector_name,
              job_title_name: res.job_title_name,
              sector_summary: res.sector_summary,
              job_title_summary: res.job_title_summary,
              sources: res.sources || []
            }
          }));
        }

        const msg = editingAgent
          ? `🌐 '${res.job_title_name}' ünvanı ve '${res.sector_name}' sektörü internette derinlemesine araştırıldı, ${res.learnings_count || 0} kural ajanın hafızasına işlendi!`
          : `🌐 '${res.job_title_name}' ünvanı ve '${res.sector_name}' sektörü başarıyla analiz edildi! Sistem rol promptu zenginleştirildi ve ${res.learnings_count || 0} öğrenim maddesi hafıza için hazırlandı.`;
        showToast(msg, 'success');
      } else {
        throw new Error(res?.detail || "Deep Search araştırması sonuç üretemedi.");
      }
    } catch (err) {
      console.error("Sektör ve Ünvan Deep Search hatası:", err);
      setAgentFormError("Sektör ve ünvan Deep Search araştırması başarısız: " + (err.message || ''));
      showToast(err.message || "Deep search hatası oluştu.", "error");
    } finally {
      setIsDeepSearchingSectorTitle(false);
    }
  };

  const handleSaveAIAgent = async (e) => {
    e.preventDefault();
    const name = agentForm.display_name.trim();
    if (!name) {
      setAgentFormError("Lütfen AI Ajan adını giriniz.");
      return;
    }
    if (!agentForm.job_title_id) {
      setAgentFormError("Lütfen AI Ajan için bir şirket ünvanı seçiniz.");
      return;
    }
    if (!agentForm.model_code) {
      setAgentFormError("Lütfen AI Ajan için bir LLM modeli seçiniz.");
      return;
    }

    const targetId = tenantId || tenant?.id || currentUser?.tenant_id;
    if (!targetId) {
      setAgentFormError("Şirket kimliği (Tenant ID) tespit edilemedi.");
      return;
    }

    // Madde 5: Paket AI Ajanı Kotası Kontrolü (Yeni İşe Alımda)
    if (!editingAgent && agentQuota.is_limit_reached) {
      setAgentFormError(`Satın aldığınız '${agentQuota.plan_name || 'Mevcut'}' paketinin azami AI Ajan kotası (${agentQuota.max_agents} Ajan) dolmuştur. Yeni bir AI Ajanı tanımlayamazsınız. Lütfen paketinizi yükseltin veya mevcut bir ajanı pasife çekin.`);
      return;
    }

    setIsSavingAgent(true);
    setAgentFormError('');
    try {
      const payload = {
        display_name: name,
        model_code: agentForm.model_code,
        job_title_id: agentForm.job_title_id,
        department_id: agentForm.department_id || null,
        description: agentForm.description?.trim() || null,
        hired_at: agentForm.hired_at ? new Date(agentForm.hired_at).toISOString() : new Date().toISOString(),
        autonomy_level: agentForm.autonomy_level || 'L1',
        system_prompt: agentForm.system_prompt?.trim() || null,
        pending_learnings: agentForm.pending_learnings || null,
        deep_search_metadata: agentForm.deep_search_metadata || null
      };

      if (editingAgent) {
        const updated = await api.updateAIAgent(targetId, editingAgent.id, payload);
        setAiAgents(prev => prev.map(a => a.id === editingAgent.id ? { ...a, ...updated } : a));
        showToast(`'${name}' AI ajanı güncellendi.`);
      } else {
        const created = await api.hireAIAgent(targetId, payload);
        setAiAgents(prev => [created, ...prev]);
        showToast(`🎉 '${name}' AI ajanı kadroya katıldı (İşe Alındı)!`);
      }
      setIsAgentModalOpen(false);
      // Departman, ünvan ve kota sayılarını güncellemek için tazele
      loadDepartments();
      loadJobTitles();
      loadAgentQuota();
    } catch (err) {
      setAgentFormError(err.message || "AI Ajan kaydedilirken bir hata oluştu.");
    } finally {
      setIsSavingAgent(false);
    }
  };


  const handleOpenTerminateAgent = (agent) => {
    setAgentToTerminate(agent);
    setTerminationDate(new Date().toISOString().split('T')[0]);
    setTerminationReason('');
  };

  const confirmTerminateAgent = async () => {
    if (!agentToTerminate) return;
    const targetId = tenantId || tenant?.id || currentUser?.tenant_id;
    setIsTerminatingAgent(true);
    try {
      const updated = await api.terminateAIAgent(targetId, agentToTerminate.id, {
        dismissed_at: terminationDate ? new Date(terminationDate).toISOString() : new Date().toISOString(),
        reason: terminationReason || null
      });
      setAiAgents(prev => prev.map(a => a.id === agentToTerminate.id ? { ...a, ...updated } : a));
      showToast(`'${agentToTerminate.display_name}' pasife çekildi (İşten Çıkarıldı).`);
      setAgentToTerminate(null);
      loadAgentQuota();
    } catch (err) {
      showToast(err.message || "İşten çıkarma işlemi başarısız oldu.", "error");
    } finally {
      setIsTerminatingAgent(false);
    }
  };

  const handleRehireAgent = async (agent) => {
    const targetId = tenantId || tenant?.id || currentUser?.tenant_id;
    try {
      const updated = await api.rehireAIAgent(targetId, agent.id);
      setAiAgents(prev => prev.map(a => a.id === agent.id ? { ...a, ...updated } : a));
      showToast(`'${agent.display_name}' yeniden işe alındı ve aktifleştirildi.`);
      loadAgentQuota();
    } catch (err) {
      showToast(err.message || "Yeniden işe alma işlemi başarısız.", "error");
    }
  };

  const confirmDeleteAgent = async () => {
    if (!agentToDelete) return;
    const targetId = tenantId || tenant?.id || currentUser?.tenant_id;
    setIsDeletingAgent(true);
    try {
      await api.deleteAIAgent(targetId, agentToDelete.id);
      setAiAgents(prev => prev.filter(a => a.id !== agentToDelete.id));
      showToast(`'${agentToDelete.display_name}' AI ajanı silindi.`);
      setAgentToDelete(null);
      loadDepartments();
      loadJobTitles();
      loadAgentQuota();
    } catch (err) {
      showToast(err.message || "AI Ajan silinemedi.", "error");
    } finally {
      setIsDeletingAgent(false);
    }
  };

  // =========================================================================
  // AI AJANLARI UZMANLIK DOKÜMANLARI, WEB VE VİDEO KAYNAK HANDLERS (Madde 1 & 2)
  // =========================================================================
  const handleOpenAgentDocs = async (agent) => {
    setSelectedAgentForDocs(agent);
    setIsDocsModalOpen(true);
    setDocSourceTab('file');
    setWebLinkUrl('');
    setWebLinkTitle('');
    setVideoLinkUrl('');
    setVideoLinkTitle('');
    setDeepSearchQuery('');
    setUploadDocError('');
    setPreviewDocId(null);
    const targetId = getActiveTenantId();
    if (!targetId || !agent?.id) return;

    setIsLoadingDocs(true);
    try {
      const docs = await api.getAgentDocuments(targetId, agent.id);
      setAgentDocuments(docs || []);
    } catch (err) {
      console.error('Dokümanlar yüklenirken hata:', err);
      showToast(err.message || 'Dokümanlar yüklenemedi.', 'error');
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const handleAddWebLink = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!webLinkUrl.trim() || !selectedAgentForDocs) return;

    const targetId = getActiveTenantId();
    if (!targetId) return;

    setUploadDocError('');
    setIsSubmittingWebLink(true);

    try {
      const createdDoc = await api.addAgentWebLink(targetId, selectedAgentForDocs.id, {
        url: webLinkUrl.trim(),
        title: webLinkTitle.trim() || null
      });

      setAgentDocuments(prev => [createdDoc, ...prev]);
      setAiAgents(prev => prev.map(a => {
        if (a.id === selectedAgentForDocs.id) {
          return { ...a, document_count: (a.document_count || 0) + 1 };
        }
        return a;
      }));

      showToast(`'${createdDoc.original_name}' web sayfası başarıyla incelendi ve ajanın hafızasına kaydedildi!`, 'success');
      setWebLinkUrl('');
      setWebLinkTitle('');
    } catch (err) {
      console.error('Web linki ekleme hatası:', err);
      setUploadDocError(err.message || 'Web sayfası içeriği alınamadı.');
      showToast(err.message || 'Web sayfası eklenemedi.', 'error');
    } finally {
      setIsSubmittingWebLink(false);
    }
  };

  const handleAddVideoLink = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!videoLinkUrl.trim() || !selectedAgentForDocs) return;

    const targetId = getActiveTenantId();
    if (!targetId) return;

    setUploadDocError('');
    setIsSubmittingVideoLink(true);

    try {
      const createdDoc = await api.addAgentVideoLink(targetId, selectedAgentForDocs.id, {
        url: videoLinkUrl.trim(),
        title: videoLinkTitle.trim() || null
      });

      setAgentDocuments(prev => [createdDoc, ...prev]);
      setAiAgents(prev => prev.map(a => {
        if (a.id === selectedAgentForDocs.id) {
          return { ...a, document_count: (a.document_count || 0) + 1 };
        }
        return a;
      }));

      showToast(`'${createdDoc.original_name}' video içeriği ve transkripti ajanın hafızasına kaydedildi!`, 'success');
      setVideoLinkUrl('');
      setVideoLinkTitle('');
    } catch (err) {
      console.error('Video linki ekleme hatası:', err);
      setUploadDocError(err.message || 'Video bilgisi veya transkripti alınamadı.');
      showToast(err.message || 'Video eklenemedi.', 'error');
    } finally {
      setIsSubmittingVideoLink(false);
    }
  };

  const handleTriggerDeepSearch = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!deepSearchQuery.trim() || !selectedAgentForDocs) return;

    const targetId = getActiveTenantId();
    if (!targetId) return;

    setUploadDocError('');
    setIsSubmittingDeepSearch(true);

    try {
      const res = await api.triggerAgentDeepSearch(targetId, selectedAgentForDocs.id, {
        query: deepSearchQuery.trim(),
        model_code: 'glm-5.3'
      });

      const updatedDocs = await api.getAgentDocuments(targetId, selectedAgentForDocs.id);
      setAgentDocuments(updatedDocs || []);

      setAiAgents(prev => prev.map(a => {
        if (a.id === selectedAgentForDocs.id) {
          return { ...a, document_count: (a.document_count || 0) + 1 };
        }
        return a;
      }));

      showToast(`'${deepSearchQuery.trim()}' konusu derinlemesine araştırıldı ve ${res.learnings_count || 0} bilgi maddesi hafızaya kaydedildi!`, 'success');
      setDeepSearchQuery('');
    } catch (err) {
      console.error('Deep Search hatası:', err);
      setUploadDocError(err.message || 'Deep Search araştırması gerçekleştirilemedi.');
      showToast(err.message || 'Deep Search araştırması başarısız oldu.', 'error');
    } finally {
      setIsSubmittingDeepSearch(false);
    }
  };

  // Mevcut Ajan İçin Şirket Sektörü & Ünvan Deep Search Tetikleme
  const handleExistingAgentDeepSearchSectorAndTitle = async () => {
    if (!selectedAgentForDocs) return;
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsExistingAgentDeepSearchingSectorTitle(true);
    setUploadDocError('');
    try {
      const res = await api.deepSearchExistingAgentSectorTitle(
        targetId,
        selectedAgentForDocs.id,
        selectedAgentForDocs.model_code || 'glm-5.3'
      );
      const updatedDocs = await api.getAgentDocuments(targetId, selectedAgentForDocs.id);
      setAgentDocuments(updatedDocs || []);
      setAiAgents(prev => prev.map(a => {
        if (a.id === selectedAgentForDocs.id) {
          return {
            ...a,
            document_count: (a.document_count || 0) + 1,
            system_prompt: res.enhanced_system_prompt || a.system_prompt
          };
        }
        return a;
      }));
      showToast(`🌐 '${res.job_title_name}' ünvanı ve '${res.sector_name}' sektörü başarıyla araştırıldı, ${res.learnings_count || 0} bilgi maddesi hafızaya kaydedildi!`, 'success');
    } catch (err) {
      console.error('Mevcut ajan sektör deep search hatası:', err);
      setUploadDocError(err.message || 'Sektör ve ünvan araştırması gerçekleştirilemedi.');
      showToast(err.message || 'Araştırma başarısız oldu.', 'error');
    } finally {
      setIsExistingAgentDeepSearchingSectorTitle(false);
    }
  };

  const handleUploadDocument = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedAgentForDocs) return;

    const targetId = getActiveTenantId();
    if (!targetId) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    const allowed = ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt', 'csv', 'md', 'json', 'xml'];
    if (!allowed.includes(ext)) {
      setUploadDocError('Yalnızca PDF, Word (docx), Excel (xlsx), TXT, CSV, MD veya JSON formatları desteklenmektedir.');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setUploadDocError('Dosya boyutu 50MB sınırını aşamaz.');
      return;
    }

    setUploadDocError('');
    setIsUploadingDoc(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const createdDoc = await api.uploadAgentDocument(targetId, selectedAgentForDocs.id, formData);
      setAgentDocuments(prev => [createdDoc, ...prev]);

      // Ajan listesinde doküman sayısını güncelle
      setAiAgents(prev => prev.map(a => {
        if (a.id === selectedAgentForDocs.id) {
          return { ...a, document_count: (a.document_count || 0) + 1 };
        }
        return a;
      }));

      showToast(`'${file.name}' başarıyla yüklendi ve ajanın hafızasına indekslendi!`, 'success');
      e.target.value = '';
    } catch (err) {
      console.error('Doküman yükleme hatası:', err);
      setUploadDocError(err.message || 'Doküman yüklenirken hata oluştu.');
      showToast(err.message || 'Doküman yüklenemedi.', 'error');
    } finally {
      setIsUploadingDoc(false);
    }
  };

  const confirmDeleteDocument = async () => {
    if (!docToDelete || !selectedAgentForDocs) return;
    const targetId = getActiveTenantId();
    if (!targetId) return;

    setIsDeletingDoc(true);
    try {
      await api.deleteAgentDocument(targetId, selectedAgentForDocs.id, docToDelete.id);
      setAgentDocuments(prev => prev.filter(d => d.id !== docToDelete.id));

      setAiAgents(prev => prev.map(a => {
        if (a.id === selectedAgentForDocs.id) {
          return { ...a, document_count: Math.max(0, (a.document_count || 1) - 1) };
        }
        return a;
      }));

      showToast(`'${docToDelete.original_name}' dokümanı ve hafıza kaydı silindi.`);
      setDocToDelete(null);
    } catch (err) {
      console.error('Doküman silinirken hata:', err);
      showToast(err.message || 'Doküman silinemedi.', 'error');
    } finally {
      setIsDeletingDoc(false);
    }
  };

  const filteredAIAgents = aiAgents.filter(a => {
    // Durum filtresi
    if (agentStatusFilter === 'ACTIVE' && a.status === 'DISABLED') return false;
    if (agentStatusFilter === 'DISABLED' && a.status !== 'DISABLED') return false;

    // Arama filtresi
    if (!agentSearch.trim()) return true;
    const q = agentSearch.toLowerCase();
    return (
      a.display_name?.toLowerCase().includes(q) ||
      a.model_code?.toLowerCase().includes(q) ||
      a.job_title_name?.toLowerCase().includes(q) ||
      a.department_name?.toLowerCase().includes(q) ||
      a.description?.toLowerCase().includes(q)
    );
  });

  // =========================================================================
  // MADDE 1 & 6 HANDLERS: KURUMSAL MANİFESTO, SEKTÖRLER & NACE KODLARI
  // =========================================================================
  const handleSearchNace = async (query) => {
    setNaceSearchQuery(query);
    const q = (query || '').trim();
    if (q.length < 2) {
      setNaceSearchResults([]);
      return;
    }
    setIsSearchingNace(true);
    try {
      const results = await api.searchNace(q, 10);
      setNaceSearchResults(results || []);
    } catch (err) {
      console.warn("NACE arama hatası:", err);
    } finally {
      setIsSearchingNace(false);
    }
  };

  const handleAddNaceCode = (naceItem) => {
    const code = typeof naceItem === 'string' ? naceItem : (naceItem?.code || String(naceItem));
    if (!code) return;
    const exists = manifestoNaceCodes.some(c => {
      const existingCode = typeof c === 'string' ? c.split(' - ')[0].trim() : (c?.code || String(c));
      return existingCode === code;
    });
    if (!exists) {
      const itemToStore = typeof naceItem === 'object' && naceItem.title
        ? `${naceItem.code} - ${naceItem.title}`
        : code;
      setManifestoNaceCodes(prev => [...prev, itemToStore]);
    }
    setNaceSearchQuery('');
    setNaceSearchResults([]);
  };

  const handleRemoveNaceCode = (codeItem) => {
    setManifestoNaceCodes(prev => prev.filter(c => c !== codeItem));
  };

  const handleAddSector = (sector) => {
    const sectorName = typeof sector === 'string' ? sector : (sector?.name || '');
    if (!sectorName) return;
    if (!manifestoSectors.includes(sectorName)) {
      setManifestoSectors(prev => [...prev, sectorName]);
      // Sektörün varsayılan NACE kodları varsa otomatik ekle
      if (typeof sector === 'object' && sector.default_nace_codes && Array.isArray(sector.default_nace_codes)) {
        setManifestoNaceCodes(prev => {
          const currentSet = new Set(prev.map(c => typeof c === 'string' ? c.split(' - ')[0].trim() : (c?.code || String(c))));
          const toAdd = sector.default_nace_codes
            .map(c => typeof c === 'string' ? c : (c?.code ? `${c.code} - ${c.title || ''}`.trim() : String(c)))
            .filter(c => !currentSet.has(typeof c === 'string' ? c.split(' - ')[0].trim() : String(c)));
          return [...prev, ...toAdd];
        });
      }
    }
  };

  const handleAddCustomSector = () => {
    const s = customSectorInput.trim().toUpperCase();
    if (s && !manifestoSectors.includes(s)) {
      setManifestoSectors(prev => [...prev, s]);
      setCustomSectorInput('');
    }
  };

  const handleRemoveSector = (sectorToRemove) => {
    setManifestoSectors(prev => prev.filter(s => s !== sectorToRemove));
  };

  const handleResetManifestoChanges = () => {
    setManifestoText(tenant?.sector_manifesto || '');
    setManifestoSectors(tenant?.sectors ? [...tenant.sectors] : []);
    setManifestoNaceCodes(tenant?.nace_codes ? [...tenant.nace_codes] : []);
    setNaceSearchQuery('');
    setNaceSearchResults([]);
    showToast("Tüm değişiklikler kaydedilmiş orijinal değerlere sıfırlandı.");
  };

  const handleSaveManifesto = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) {
      showToast("Şirket bilgisi bulunamadı.", "error");
      return;
    }

    setIsSavingManifesto(true);
    try {
      const res = await api.updateCompanyManifesto(targetId, {
        manifesto: manifestoText,
        sectors: manifestoSectors,
        nace_codes: manifestoNaceCodes
      });
      if (res?.success) {
        showToast("Kurumsal manifesto, sektörler ve NACE kodları başarıyla kaydedildi!", "success");
        setTenant(prev => prev ? {
          ...prev,
          sector_manifesto: manifestoText,
          sectors: manifestoSectors,
          nace_codes: manifestoNaceCodes
        } : prev);
      }
    } catch (err) {
      console.error("Manifesto kaydedilirken hata:", err);
      showToast(err.message || "Manifesto kaydedilemedi.", "error");
    } finally {
      setIsSavingManifesto(false);
    }
  };

  const handleGenerateManifesto = async () => {
    const targetId = getActiveTenantId();
    if (!targetId) {
      showToast("Şirket bilgisi bulunamadı.", "error");
      return;
    }

    setIsGeneratingManifesto(true);
    try {
      const res = await api.generateCompanyManifesto(targetId, {
        model_code: manifestoModel,
        instructions: manifestoInstructions.trim() || undefined,
        current_manifesto: manifestoText.trim() || undefined,
        sectors: manifestoSectors,
        nace_codes: manifestoNaceCodes
      });
      if (res?.manifesto) {
        setManifestoText(res.manifesto);
        showToast(`Kurumsal manifesto (${res.model_code || manifestoModel}) ile hazırlandı!`, "success");
      }
    } catch (err) {
      console.error("Manifesto üretilirken hata:", err);
      showToast(err.message || "Manifesto üretilemedi.", "error");
    } finally {
      setIsGeneratingManifesto(false);
    }
  };

  const isManifestoUnchanged =
    manifestoText === (tenant?.sector_manifesto || '') &&
    JSON.stringify((manifestoSectors || []).slice().sort()) === JSON.stringify((tenant?.sectors || []).slice().sort()) &&
    JSON.stringify((manifestoNaceCodes || []).slice().sort()) === JSON.stringify((tenant?.nace_codes || []).slice().sort());

  return (
    <div className="company-admin-root" style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      backgroundColor: 'var(--sf-0a0d14)',
      color: 'var(--nt-f8fafc)',
      fontFamily: 'var(--font-sans)',
      overflow: 'hidden'
    }}>
      {/* ÜST TOPBAR */}
      <header className="company-admin-header" style={{
        height: '64px',
        padding: '0 24px',
        borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
        background: 'rgb(var(--rgb-sf-111622) / 0.85)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 50
      }}>
        {/* Sol: Logo ve Şirket Başlığı */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(113, 52, 226, 0.45)'
          }}>
            <Building2 size={20} color="#ffffff" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontWeight: '800', fontSize: '1.15rem', letterSpacing: '-0.02em', color: 'var(--nt-ffffff)' }}>
                {tenant?.name || 'Müşteri Yönetim Konsolu'}
              </span>
              <span style={{
                background: 'rgba(113, 52, 226, 0.18)',
                color: 'var(--ac-c084fc)',
                border: '1px solid rgba(113, 52, 226, 0.35)',
                fontSize: '0.675rem',
                fontWeight: '700',
                padding: '2px 8px',
                borderRadius: '6px',
                textTransform: 'uppercase'
              }}>
                ŞİRKET YÖNETİMİ
              </span>
              {tenant?.nace_codes && tenant.nace_codes.length > 0 && (
                <span style={{
                  background: 'rgba(6, 182, 212, 0.12)',
                  color: 'var(--ac-22d3ee)',
                  border: '1px solid rgba(6, 182, 212, 0.3)',
                  fontSize: '0.675rem',
                  fontWeight: '600',
                  padding: '2px 8px',
                  borderRadius: '6px'
                }}>
                  NACE: {tenant.nace_codes[0]?.code || tenant.nace_codes[0] || 'Genel'}
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--nt-94a3b8)', margin: 0 }}>
              RECOrion Otonom Yapay Zeka & Departman Yönetim Merkezi
            </p>
          </div>
        </div>

        {/* Sağ: Aksiyon Butonları & Kullanıcı */}
        <div className="company-admin-header-actions" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <ThemeToggle className="ui-hide-mobile" />
          <ThemeToggle compact className="ui-show-mobile-only" />
          {/* Çalışma Alanına Geçiş Butonu */}
          {onSwitchToWorkspace && (
            <button
              onClick={() => onSwitchToWorkspace(tenant)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '7px 14px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, rgba(20, 108, 235, 0.2) 0%, rgba(113, 52, 226, 0.2) 100%)',
                border: '1px solid rgba(20, 108, 235, 0.45)',
                color: 'var(--ac-60a5fa)',
                fontSize: '0.8rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              title="3 Bölmeli Canlı Çalışma Alanına (Work Area) Geçiş Yap"
            >
              <Laptop size={15} />
              <span>💻 Çalışma Alanı (Work Area)</span>
            </button>
          )}

          {/* Süper Admin Geri Dönüş (Eğer kullanıcı Super Admin ise) */}
          {currentUser?.role === 'SUPER_ADMIN' && onGoToSuperAdmin && (
            <button
              onClick={onGoToSuperAdmin}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 12px',
                borderRadius: '8px',
                background: 'rgba(245, 158, 11, 0.15)',
                border: '1px solid rgba(245, 158, 11, 0.4)',
                color: 'var(--ac-fbbf24)',
                fontSize: '0.775rem',
                fontWeight: '600',
                cursor: 'pointer'
              }}
              title="Platform Süper Admin Konsoluna Dön"
            >
              👑 Süper Admin Konsoluna Dön
            </button>
          )}

          {/* Resmi Site Butonu */}
          {onGoToOfficialSite && (
            <button
              onClick={onGoToOfficialSite}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 12px',
                borderRadius: '8px',
                background: 'rgb(var(--rgb-ov) / 0.05)',
                border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                color: 'var(--nt-cbd5e1)',
                fontSize: '0.775rem',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              🌐 Site
            </button>
          )}

          {/* Kullanıcı Profili */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '5px 12px',
            borderRadius: '8px',
            background: 'rgb(var(--rgb-ov) / 0.03)',
            border: '1px solid rgb(var(--rgb-ov) / 0.08)'
          }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.8rem',
              fontWeight: '700',
              color: '#ffffff'
            }}>
              {currentUser?.display_name?.charAt(0) || 'Y'}
            </div>
            <div style={{ textAlign: 'left', lineHeight: 1.2 }}>
              <div style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--nt-f8fafc)' }}>
                {currentUser?.display_name || 'Yetkili Yönetici'}
              </div>
              <div style={{ fontSize: '0.675rem', color: 'var(--nt-94a3b8)' }}>
                {currentUser?.role === 'SUPER_ADMIN' ? '👑 Platform Süper Admin' : 'Yetkili Personel'}
              </div>
            </div>
          </div>

          {/* Çıkış Butonu */}
          {onLogout && (
            <button
              onClick={onLogout}
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                color: 'var(--ac-f87171)',
                borderRadius: '8px',
                padding: '7px 11px',
                fontSize: '0.75rem',
                fontWeight: '600',
                cursor: 'pointer'
              }}
              title="Güvenli Çıkış Yap"
            >
              Çıkış
            </button>
          )}
        </div>
      </header>

      {/* ANA GÖVDE: SOL MENÜ + SAĞ İÇERİK */}
      <div className="company-admin-body" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* SOL YAN MENÜ (SIDEBAR) - tablet/telefonda üstte yatay sekme çubuğu */}
        <aside className="company-admin-sidebar" style={{
          width: '260px',
          background: 'var(--sf-0d111a)',
          borderRight: '1px solid rgb(var(--rgb-ov) / 0.08)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '16px 12px'
        }}>
          <div>
            <div style={{
              fontSize: '0.675rem',
              fontWeight: '700',
              color: 'var(--nt-64748b)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              padding: '6px 12px',
              marginBottom: '6px'
            }}>
              ORGANİZASYON YÖNETİMİ
            </div>

            <nav className="company-admin-tabs" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {/* TAB 0: KULLANICILAR (İNSAN PERSONEL - Madde 1) */}
              <button
                onClick={() => setActiveTab('USERS')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: activeTab === 'USERS' ? 'linear-gradient(135deg, rgba(113, 52, 226, 0.25) 0%, rgba(20, 108, 235, 0.25) 100%)' : 'transparent',
                  border: activeTab === 'USERS' ? '1px solid rgba(113, 52, 226, 0.5)' : '1px solid transparent',
                  color: activeTab === 'USERS' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                  fontSize: '0.85rem',
                  fontWeight: activeTab === 'USERS' ? '700' : '500',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s'
                }}
              >
                <Users size={18} color={activeTab === 'USERS' ? 'var(--ac-818cf8)' : 'var(--nt-64748b)'} />
                <span style={{ flex: 1 }}>Kullanıcı Yönetimi</span>
                <span style={{
                  fontSize: '0.7rem',
                  background: userQuota.is_limit_reached ? 'rgba(239, 68, 68, 0.2)' : 'rgb(var(--rgb-ov) / 0.08)',
                  padding: '2px 7px',
                  borderRadius: '12px',
                  color: userQuota.is_limit_reached ? 'var(--ac-f87171)' : 'var(--nt-cbd5e1)'
                }}>
                  {userQuota.active_users} / {userQuota.max_users}
                </span>
              </button>

              {/* TAB 1: DEPARTMANLAR (Madde 1) */}
              <button
                onClick={() => setActiveTab('DEPARTMENTS')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: activeTab === 'DEPARTMENTS' ? 'linear-gradient(135deg, rgba(113, 52, 226, 0.25) 0%, rgba(20, 108, 235, 0.25) 100%)' : 'transparent',
                  border: activeTab === 'DEPARTMENTS' ? '1px solid rgba(113, 52, 226, 0.5)' : '1px solid transparent',
                  color: activeTab === 'DEPARTMENTS' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                  fontSize: '0.85rem',
                  fontWeight: activeTab === 'DEPARTMENTS' ? '700' : '500',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s'
                }}
              >
                <Building2 size={18} color={activeTab === 'DEPARTMENTS' ? '#a855f7' : 'var(--nt-64748b)'} />
                <span style={{ flex: 1 }}>Departmanlar</span>
                <span style={{
                  fontSize: '0.7rem',
                  background: 'rgb(var(--rgb-ov) / 0.08)',
                  padding: '2px 7px',
                  borderRadius: '12px',
                  color: 'var(--nt-cbd5e1)'
                }}>
                  {departments.length}
                </span>
              </button>

              {/* TAB 2: ŞİRKET ÜNVANLARI (Madde 2) */}
              <button
                onClick={() => setActiveTab('JOB_TITLES')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: activeTab === 'JOB_TITLES' ? 'linear-gradient(135deg, rgba(113, 52, 226, 0.25) 0%, rgba(20, 108, 235, 0.25) 100%)' : 'transparent',
                  border: activeTab === 'JOB_TITLES' ? '1px solid rgba(113, 52, 226, 0.5)' : '1px solid transparent',
                  color: activeTab === 'JOB_TITLES' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                  fontSize: '0.85rem',
                  fontWeight: activeTab === 'JOB_TITLES' ? '700' : '500',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s'
                }}
              >
                <Briefcase size={18} color={activeTab === 'JOB_TITLES' ? 'var(--ac-38bdf8)' : 'var(--nt-64748b)'} />
                <span style={{ flex: 1 }}>Ünvan Tanımları</span>
                <span style={{
                  fontSize: '0.7rem',
                  background: 'rgb(var(--rgb-ov) / 0.08)',
                  padding: '2px 7px',
                  borderRadius: '12px',
                  color: 'var(--nt-cbd5e1)'
                }}>
                  {jobTitles.length}
                </span>
              </button>

              {/* TAB 3: AI AJAN KADROSU (Madde 3) */}
              <button
                onClick={() => setActiveTab('AI_AGENTS')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: activeTab === 'AI_AGENTS' ? 'linear-gradient(135deg, rgba(113, 52, 226, 0.25) 0%, rgba(20, 108, 235, 0.25) 100%)' : 'transparent',
                  border: activeTab === 'AI_AGENTS' ? '1px solid rgba(113, 52, 226, 0.5)' : '1px solid transparent',
                  color: activeTab === 'AI_AGENTS' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                  fontSize: '0.85rem',
                  fontWeight: activeTab === 'AI_AGENTS' ? '700' : '500',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s'
                }}
              >
                <Bot size={18} color={activeTab === 'AI_AGENTS' ? '#10b981' : 'var(--nt-64748b)'} />
                <span style={{ flex: 1 }}>AI Ajan İşe Alım</span>
                <span style={{
                  fontSize: '0.65rem',
                  background: 'rgba(16, 185, 129, 0.2)',
                  color: 'var(--ac-34d399)',
                  padding: '2px 6px',
                  borderRadius: '4px'
                }}>
                  13 Model
                </span>
              </button>

              {/* TAB 4: KURUMSAL MANİFESTO & NACE */}
              <button
                onClick={() => setActiveTab('MANIFESTO')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: activeTab === 'MANIFESTO' ? 'linear-gradient(135deg, rgba(113, 52, 226, 0.25) 0%, rgba(20, 108, 235, 0.25) 100%)' : 'transparent',
                  border: activeTab === 'MANIFESTO' ? '1px solid rgba(113, 52, 226, 0.5)' : '1px solid transparent',
                  color: activeTab === 'MANIFESTO' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                  fontSize: '0.85rem',
                  fontWeight: activeTab === 'MANIFESTO' ? '700' : '500',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s'
                }}
              >
                <FileText size={18} color={activeTab === 'MANIFESTO' ? '#f59e0b' : 'var(--nt-64748b)'} />
                <span style={{ flex: 1 }}>Sektörel Manifesto</span>
              </button>
            </nav>
          </div>

          {/* Alt Bilgi Kartı */}
          <div style={{
            background: 'rgb(var(--rgb-ov) / 0.03)',
            border: '1px solid rgb(var(--rgb-ov) / 0.06)',
            borderRadius: '10px',
            padding: '12px',
            fontSize: '0.75rem',
            color: 'var(--nt-94a3b8)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '600', color: 'var(--nt-f8fafc)', marginBottom: '4px' }}>
              <Shield size={14} color="#7134e2" />
              <span>RLS İzolasyonu Aktif</span>
            </div>
            <span>Şirketinizin departman, ünvan ve AI ajan verileri PostgreSQL Row-Level Security ile tamamen izoledir.</span>
          </div>
        </aside>

        {/* SAĞ ANA İÇERİK ALANI */}
        <main className="company-admin-content" style={{ flex: 1, overflowY: 'auto', padding: '28px 32px' }}>
          {/* ========================================================================= */}
          {/* MADDE 1: KULLANICI YÖNETİMİ (İNSAN PERSONEL) SEKMESİ */}
          {/* ========================================================================= */}
          {activeTab === 'USERS' && (
            <div>
              {/* Başlık ve Aksiyon Barı */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '20px',
                flexWrap: 'wrap',
                gap: '16px'
              }}>
                <div>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '800', letterSpacing: '-0.02em', margin: 0, color: 'var(--nt-ffffff)' }}>
                    Kullanıcı Yönetimi
                  </h2>
                  <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', margin: '4px 0 0 0' }}>
                    Şirketinizin insan personellerini tanımlayın, departman/ünvan atayın, Süper Yöneticinin rollerini ve ek izinlerini belirleyin.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    onClick={() => { loadUsers(); loadUserQuota(); }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: 'rgb(var(--rgb-ov) / 0.05)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      color: 'var(--nt-cbd5e1)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                    title="Yenile"
                  >
                    <RefreshCw size={14} className={isLoadingUsers ? 'spin' : ''} />
                    <span>Yenile</span>
                  </button>

                  <button
                    onClick={handleOpenCreateUser}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                      border: 'none',
                      color: '#ffffff',
                      padding: '9px 18px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '700',
                      cursor: 'pointer',
                      boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)',
                      transition: 'transform 0.15s'
                    }}
                  >
                    <UserPlus size={16} />
                    <span>+ Yeni Kullanıcı Tanımla</span>
                  </button>
                </div>
              </div>

              {/* PAKET KOTA GÖSTERGE KARTI */}
              <div style={{
                background: 'linear-gradient(135deg, rgb(var(--rgb-sf-141b2d) / 0.9) 0%, rgb(var(--rgb-sf-0d111a) / 0.95) 100%)',
                border: '1px solid ' + (userQuota.is_limit_reached ? 'rgba(239, 68, 68, 0.4)' : 'rgba(113, 52, 226, 0.3)'),
                borderRadius: '14px',
                padding: '18px 22px',
                marginBottom: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
                boxShadow: '0 8px 24px rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))'
              }}>
                <div style={{ flex: 1, minWidth: '280px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: '700',
                      background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                      color: '#ffffff',
                      padding: '3px 10px',
                      borderRadius: '20px',
                      letterSpacing: '0.02em'
                    }}>
                      {userQuota.plan_name || 'Kurumsal Paket'}
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--nt-f8fafc)' }}>
                      İnsan Kullanıcı Kotası
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '1.75rem', fontWeight: '900', color: userQuota.is_limit_reached ? 'var(--ac-f87171)' : 'var(--nt-ffffff)' }}>
                      {userQuota.active_users}
                    </span>
                    <span style={{ fontSize: '1rem', color: 'var(--nt-64748b)', fontWeight: '600' }}>
                      / {userQuota.max_users} Kullanıcı
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', marginLeft: '12px' }}>
                      (Kalan Kontenjan: <strong style={{ color: userQuota.is_limit_reached ? '#ef4444' : '#10b981' }}>{Math.max(0, userQuota.max_users - userQuota.active_users)}</strong>)
                    </span>
                  </div>

                  {/* İlerleme Çubuğu */}
                  <div style={{
                    width: '100%',
                    height: '8px',
                    background: 'rgb(var(--rgb-ov) / 0.08)',
                    borderRadius: '8px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${Math.min(100, Math.round(((userQuota.active_users || 0) / (userQuota.max_users || 1)) * 100))}%`,
                      background: userQuota.is_limit_reached
                        ? 'linear-gradient(90deg, #f59e0b 0%, #ef4444 100%)'
                        : 'linear-gradient(90deg, #10b981 0%, var(--ac-38bdf8) 100%)',
                      borderRadius: '8px',
                      transition: 'width 0.4s ease-out'
                    }} />
                  </div>
                </div>

                {/* Sağ Durum Rozeti */}
                <div style={{
                  padding: '12px 16px',
                  borderRadius: '10px',
                  background: userQuota.is_limit_reached ? 'rgba(239, 68, 68, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid ' + (userQuota.is_limit_reached ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'),
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  maxWidth: '380px'
                }}>
                  {userQuota.is_limit_reached ? (
                    <>
                      <AlertCircle size={24} color="var(--ac-f87171)" style={{ flexShrink: 0 }} />
                      <div style={{ fontSize: '0.78rem', color: 'var(--ac-fca5a5)', lineHeight: 1.35 }}>
                        <strong>Azami Kota Doldu:</strong> Satın aldığınız paketin kullanıcı limitine ulaştınız. Yeni kullanıcı eklemek için paketinizi yükseltin veya mevcut bir hesabı pasife alın.
                      </div>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={24} color="var(--ac-34d399)" style={{ flexShrink: 0 }} />
                      <div style={{ fontSize: '0.78rem', color: 'var(--ac-86efac)', lineHeight: 1.35 }}>
                        <strong>Kota Uygun:</strong> Satın aldığınız paket kapsamında {Math.max(0, userQuota.max_users - userQuota.active_users)} adet daha kullanıcı tanımlayabilirsiniz.
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* FİLTRE & ARAMA ÇUBUĞU */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px',
                marginBottom: '20px',
                flexWrap: 'wrap'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: '260px' }}>
                  {/* Arama Inputu */}
                  <div style={{
                    position: 'relative',
                    flex: 1,
                    maxWidth: '360px'
                  }}>
                    <Search size={15} color="var(--nt-64748b)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                      type="text"
                      placeholder="Ad soyad veya e-posta ile ara..."
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                      style={{
                        width: '100%',
                        background: 'rgb(var(--rgb-ov) / 0.04)',
                        border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                        borderRadius: '8px',
                        padding: '8px 12px 8px 34px',
                        color: 'var(--nt-ffffff)',
                        fontSize: '0.85rem',
                        outline: 'none'
                      }}
                    />
                    {userSearch && (
                      <button
                        onClick={() => setUserSearch('')}
                        style={{
                          position: 'absolute',
                          right: '10px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          background: 'none',
                          border: 'none',
                          color: 'var(--nt-64748b)',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  {/* Durum Filtresi */}
                  <div style={{ display: 'flex', background: 'rgb(var(--rgb-ov) / 0.05)', borderRadius: '8px', padding: '3px' }}>
                    <button
                      onClick={() => setUserStatusFilter('ALL')}
                      style={{
                        padding: '5px 12px',
                        borderRadius: '6px',
                        border: 'none',
                        background: userStatusFilter === 'ALL' ? '#7134e2' : 'transparent',
                        color: userStatusFilter === 'ALL' ? '#ffffff' : 'var(--nt-94a3b8)',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Tümü ({users.length})
                    </button>
                    <button
                      onClick={() => setUserStatusFilter('ACTIVE')}
                      style={{
                        padding: '5px 12px',
                        borderRadius: '6px',
                        border: 'none',
                        background: userStatusFilter === 'ACTIVE' ? '#10b981' : 'transparent',
                        color: userStatusFilter === 'ACTIVE' ? '#ffffff' : 'var(--nt-94a3b8)',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Aktif ({users.filter(u => u.status !== 'DISABLED').length})
                    </button>
                    <button
                      onClick={() => setUserStatusFilter('DISABLED')}
                      style={{
                        padding: '5px 12px',
                        borderRadius: '6px',
                        border: 'none',
                        background: userStatusFilter === 'DISABLED' ? '#ef4444' : 'transparent',
                        color: userStatusFilter === 'DISABLED' ? '#ffffff' : 'var(--nt-94a3b8)',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Pasif ({users.filter(u => u.status === 'DISABLED').length})
                    </button>
                  </div>

                  {/* Departman Filtresi */}
                  {departments.length > 0 && (
                    <select
                      value={userDeptFilter}
                      onChange={(e) => setUserDeptFilter(e.target.value)}
                      style={{
                        background: 'var(--sf-131826)',
                        border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                        borderRadius: '8px',
                        padding: '8px 12px',
                        color: 'var(--nt-cbd5e1)',
                        fontSize: '0.8rem',
                        outline: 'none',
                        cursor: 'pointer'
                      }}
                    >
                      <option value="ALL">Tüm Departmanlar</option>
                      {departments.map(d => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  )}
                </div>

                {/* Görünüm Seçici (Cards / List) */}
                <div style={{ display: 'flex', background: 'rgb(var(--rgb-ov) / 0.05)', borderRadius: '8px', padding: '3px' }}>
                  <button
                    onClick={() => setUserViewMode('CARDS')}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: 'none',
                      background: userViewMode === 'CARDS' ? 'rgb(var(--rgb-ov) / 0.15)' : 'transparent',
                      color: userViewMode === 'CARDS' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Kartlar
                  </button>
                  <button
                    onClick={() => setUserViewMode('LIST')}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: 'none',
                      background: userViewMode === 'LIST' ? 'rgb(var(--rgb-ov) / 0.15)' : 'transparent',
                      color: userViewMode === 'LIST' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Liste
                  </button>
                </div>
              </div>

              {/* YÜKLENİYOR DURUMU */}
              {isLoadingUsers && (
                <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--nt-94a3b8)' }}>
                  <RefreshCw size={28} className="spin" style={{ margin: '0 auto 12px auto', display: 'block', color: '#7134e2' }} />
                  <div>Kullanıcılar yükleniyor...</div>
                </div>
              )}

              {/* BOŞ LİSTE DURUMU */}
              {!isLoadingUsers && filteredUsers.length === 0 && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.5)',
                  border: '1px dashed rgb(var(--rgb-ov) / 0.12)',
                  borderRadius: '16px',
                  padding: '60px 20px',
                  textAlign: 'center'
                }}>
                  <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '50%',
                    background: 'rgba(113, 52, 226, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px auto'
                  }}>
                    <Users size={32} color="#a855f7" />
                  </div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--nt-ffffff)', margin: '0 0 6px 0' }}>
                    {users.length === 0 ? 'Henüz Tanımlı İnsan Personel Yok' : 'Filtreye Uygun Kullanıcı Bulunamadı'}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', maxWidth: '440px', margin: '0 auto 20px auto' }}>
                    {users.length === 0
                      ? 'Satın aldığınız paket kotası dahilinde ilk insan personelinizi tanımlayarak yetkilendirmeye başlayın.'
                      : 'Arama kriterlerinize veya departman filtresine uygun personel kaydı bulunamadı.'}
                  </p>
                  {users.length === 0 && (
                    <button
                      onClick={handleOpenCreateUser}
                      style={{
                        background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                        border: 'none',
                        color: '#ffffff',
                        padding: '10px 22px',
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        fontWeight: '700',
                        cursor: 'pointer'
                      }}
                    >
                      + İlk Kullanıcıyı Tanımla
                    </button>
                  )}
                </div>
              )}

              {/* KARTLAR GÖRÜNÜMÜ */}
              {!isLoadingUsers && filteredUsers.length > 0 && userViewMode === 'CARDS' && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 340px), 1fr))',
                  gap: '20px'
                }}>
                  {filteredUsers.map((u) => {
                    const initials = (u.display_name || 'U')
                      .split(' ')
                      .filter(Boolean)
                      .slice(0, 2)
                      .map(p => p[0].toUpperCase())
                      .join('');

                    const isPassive = u.status === 'DISABLED';

                    return (
                      <div
                        key={u.id}
                        style={{
                          background: 'rgb(var(--rgb-sf-111622) / 0.85)',
                          border: isPassive ? '1px solid rgba(239, 68, 68, 0.25)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                          borderRadius: '14px',
                          padding: '20px',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          boxShadow: '0 4px 20px rgb(var(--rgb-shade) / calc(0.2 * var(--shade-k)))',
                          transition: 'all 0.2s',
                          position: 'relative',
                          overflow: 'hidden'
                        }}
                      >
                        {/* Üst Alan: Avatar, İsim & Durum */}
                        <div>
                          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '10px', marginBottom: '14px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              <div style={{
                                width: '42px',
                                height: '42px',
                                borderRadius: '10px',
                                background: isPassive
                                  ? 'linear-gradient(135deg, var(--nt-475569) 0%, var(--nt-334155) 100%)'
                                  : 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontWeight: '800',
                                fontSize: '0.95rem',
                                color: '#ffffff',
                                boxShadow: isPassive ? 'none' : '0 4px 12px rgba(113, 52, 226, 0.35)'
                              }}>
                                {initials}
                              </div>
                              <div>
                                <h4 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--nt-ffffff)', margin: 0, lineHeight: 1.2 }}>
                                  {u.display_name}
                                </h4>
                                <div style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '6px',
                                  fontSize: '0.75rem',
                                  color: 'var(--nt-94a3b8)',
                                  marginTop: '3px'
                                }}>
                                  <span>{u.email}</span>
                                  <button
                                    onClick={() => copyToClipboard(u.email, 'E-posta')}
                                    style={{
                                      background: 'none',
                                      border: 'none',
                                      color: 'var(--nt-64748b)',
                                      cursor: 'pointer',
                                      padding: 0,
                                      display: 'flex',
                                      alignItems: 'center'
                                    }}
                                    title="E-postayı Kopyala"
                                  >
                                    <Copy size={11} />
                                  </button>
                                </div>
                              </div>
                            </div>

                            {/* Durum Rozeti */}
                            <span style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '3px 9px',
                              borderRadius: '20px',
                              fontSize: '0.7rem',
                              fontWeight: '700',
                              background: isPassive ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                              color: isPassive ? 'var(--ac-f87171)' : 'var(--ac-34d399)',
                              border: isPassive ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)'
                            }}>
                              {isPassive ? <UserX size={11} /> : <UserCheck size={11} />}
                              {isPassive ? 'Pasif' : 'Aktif'}
                            </span>
                          </div>

                          {/* Detay Bilgileri */}
                          <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px',
                            padding: '12px',
                            background: 'rgb(var(--rgb-ov) / 0.02)',
                            borderRadius: '10px',
                            border: '1px solid rgb(var(--rgb-ov) / 0.04)',
                            marginBottom: '16px'
                          }}>
                            {/* Departman */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                              <span style={{ color: 'var(--nt-64748b)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Building2 size={13} color="#a855f7" /> Departman:
                              </span>
                              <span style={{ color: u.department_name ? 'var(--nt-cbd5e1)' : 'var(--nt-64748b)', fontWeight: '500' }}>
                                {u.department_name || 'Atanmamış'}
                              </span>
                            </div>

                            {/* Ünvan */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                              <span style={{ color: 'var(--nt-64748b)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Briefcase size={13} color="var(--ac-38bdf8)" /> Ünvan:
                              </span>
                              <span style={{ color: u.job_title_name ? 'var(--nt-cbd5e1)' : 'var(--nt-64748b)', fontWeight: '500' }}>
                                {u.job_title_name || 'Atanmamış'}
                              </span>
                            </div>

                            {/* Sistem Yetki Rolü */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                              <span style={{ color: 'var(--nt-64748b)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Shield size={13} color="var(--ac-818cf8)" /> Sistem Rolü:
                              </span>
                              <span style={{
                                background: 'rgba(129, 140, 248, 0.15)',
                                color: 'var(--ac-a5b4fc)',
                                padding: '2px 8px',
                                borderRadius: '6px',
                                fontWeight: '700',
                                fontSize: '0.72rem'
                              }}>
                                {u.role_name || u.role}
                              </span>
                            </div>
                          </div>

                          {/* İzin Kataloğu Ek İzinleri */}
                          <div style={{ marginBottom: '16px' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', fontWeight: '600', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              İzin Kataloğu Ek İzinleri
                            </div>
                            {u.extra_permissions && u.extra_permissions.length > 0 ? (
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                                {u.extra_permissions.map((pCode, pIdx) => (
                                  <span
                                    key={pIdx}
                                    style={{
                                      fontSize: '0.675rem',
                                      background: 'rgba(245, 158, 11, 0.12)',
                                      border: '1px solid rgba(245, 158, 11, 0.25)',
                                      color: 'var(--ac-fbbf24)',
                                      padding: '2px 7px',
                                      borderRadius: '4px',
                                      fontFamily: 'monospace'
                                    }}
                                  >
                                    +{pCode}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span style={{ fontSize: '0.72rem', color: 'var(--nt-475569)', fontStyle: 'italic' }}>
                                Ek izin tanımlanmadı (Rol izinleri geçerli)
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Alt Butonlar */}
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'flex-end',
                          gap: '8px',
                          borderTop: '1px solid rgb(var(--rgb-ov) / 0.06)',
                          paddingTop: '14px'
                        }}>
                          <button
                            onClick={() => handleOpenEditUser(u)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px',
                              background: 'rgb(var(--rgb-ov) / 0.05)',
                              border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                              color: 'var(--nt-cbd5e1)',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: '600',
                              cursor: 'pointer',
                              transition: 'all 0.15s'
                            }}
                          >
                            <Edit3 size={13} color="var(--ac-38bdf8)" />
                            <span>Düzenle</span>
                          </button>

                          <button
                            onClick={() => setUserToDelete(u)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px',
                              background: 'rgba(239, 68, 68, 0.08)',
                              border: '1px solid rgba(239, 68, 68, 0.2)',
                              color: 'var(--ac-f87171)',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: '600',
                              cursor: 'pointer',
                              transition: 'all 0.15s'
                            }}
                          >
                            <Trash2 size={13} />
                            <span>Sil</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* LİSTE / TABLO GÖRÜNÜMÜ */}
              {!isLoadingUsers && filteredUsers.length > 0 && userViewMode === 'LIST' && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.7)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  borderRadius: '14px',
                  overflowX: 'auto'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
                    <thead>
                      <tr style={{ background: 'rgb(var(--rgb-ov) / 0.03)', borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)', color: 'var(--nt-94a3b8)' }}>
                        <th style={{ padding: '14px 18px', fontWeight: '700' }}>KULLANICI</th>
                        <th style={{ padding: '14px 18px', fontWeight: '700' }}>E-POSTA</th>
                        <th style={{ padding: '14px 18px', fontWeight: '700' }}>DEPARTMAN</th>
                        <th style={{ padding: '14px 18px', fontWeight: '700' }}>ÜNVAN</th>
                        <th style={{ padding: '14px 18px', fontWeight: '700' }}>SİSTEM ROLÜ</th>
                        <th style={{ padding: '14px 18px', fontWeight: '700' }}>EK İZİNLER</th>
                        <th style={{ padding: '14px 18px', fontWeight: '700' }}>DURUM</th>
                        <th style={{ padding: '14px 18px', fontWeight: '700', textAlign: 'right' }}>İŞLEMLER</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map((u) => {
                        const isPassive = u.status === 'DISABLED';
                        return (
                          <tr key={u.id} style={{ borderBottom: '1px solid rgb(var(--rgb-ov) / 0.04)' }}>
                            <td style={{ padding: '14px 18px', color: 'var(--nt-ffffff)', fontWeight: '600' }}>
                              {u.display_name}
                            </td>
                            <td style={{ padding: '14px 18px', color: 'var(--nt-cbd5e1)' }}>
                              {u.email}
                            </td>
                            <td style={{ padding: '14px 18px', color: u.department_name ? 'var(--nt-cbd5e1)' : 'var(--nt-64748b)' }}>
                              {u.department_name || '-'}
                            </td>
                            <td style={{ padding: '14px 18px', color: u.job_title_name ? 'var(--nt-cbd5e1)' : 'var(--nt-64748b)' }}>
                              {u.job_title_name || '-'}
                            </td>
                            <td style={{ padding: '14px 18px' }}>
                              <span style={{
                                background: 'rgba(129, 140, 248, 0.15)',
                                color: 'var(--ac-a5b4fc)',
                                padding: '3px 8px',
                                borderRadius: '6px',
                                fontWeight: '700',
                                fontSize: '0.72rem'
                              }}>
                                {u.role_name || u.role}
                              </span>
                            </td>
                            <td style={{ padding: '14px 18px' }}>
                              {u.extra_permissions && u.extra_permissions.length > 0 ? (
                                <span style={{
                                  background: 'rgba(245, 158, 11, 0.15)',
                                  color: 'var(--ac-fbbf24)',
                                  padding: '2px 7px',
                                  borderRadius: '4px',
                                  fontSize: '0.7rem',
                                  fontWeight: '600'
                                }}>
                                  +{u.extra_permissions.length} İzin
                                </span>
                              ) : (
                                <span style={{ color: 'var(--nt-475569)', fontSize: '0.72rem' }}>-</span>
                              )}
                            </td>
                            <td style={{ padding: '14px 18px' }}>
                              <span style={{
                                padding: '3px 8px',
                                borderRadius: '20px',
                                fontSize: '0.7rem',
                                fontWeight: '700',
                                background: isPassive ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                                color: isPassive ? 'var(--ac-f87171)' : 'var(--ac-34d399)'
                              }}>
                                {isPassive ? 'Pasif' : 'Aktif'}
                              </span>
                            </td>
                            <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                              <div style={{ display: 'inline-flex', gap: '6px' }}>
                                <button
                                  onClick={() => handleOpenEditUser(u)}
                                  style={{
                                    background: 'rgb(var(--rgb-ov) / 0.05)',
                                    border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                                    color: 'var(--ac-38bdf8)',
                                    padding: '5px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    cursor: 'pointer'
                                  }}
                                >
                                  Düzenle
                                </button>
                                <button
                                  onClick={() => setUserToDelete(u)}
                                  style={{
                                    background: 'rgba(239, 68, 68, 0.08)',
                                    border: '1px solid rgba(239, 68, 68, 0.2)',
                                    color: 'var(--ac-f87171)',
                                    padding: '5px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    cursor: 'pointer'
                                  }}
                                >
                                  Sil
                                </button>
                              </div>
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

          {/* ========================================================================= */}
          {/* MADDE 1: DEPARTMANLAR SEKMESİ */}
          {/* ========================================================================= */}
          {activeTab === 'DEPARTMENTS' && (
            <div>
              {/* Başlık ve Aksiyon Barı */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '24px',
                flexWrap: 'wrap',
                gap: '16px'
              }}>
                <div>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '800', letterSpacing: '-0.02em', margin: 0, color: 'var(--nt-ffffff)' }}>
                    Şirket Departmanları Tanımlama
                  </h2>
                  <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', margin: '4px 0 0 0' }}>
                    Sistemi kullanacak operasyonel, idari ve teknik departmanları tanımlayın ve yönetin.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    onClick={loadDepartments}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: 'rgb(var(--rgb-ov) / 0.05)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      color: 'var(--nt-cbd5e1)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                    title="Yenile"
                  >
                    <RefreshCw size={14} className={isLoadingDepts ? 'spin' : ''} />
                    <span>Yenile</span>
                  </button>

                  <button
                    onClick={handleOpenCreateDept}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                      border: 'none',
                      color: '#ffffff',
                      padding: '9px 18px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '700',
                      cursor: 'pointer',
                      boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)',
                      transition: 'transform 0.15s'
                    }}
                  >
                    <Plus size={16} />
                    <span>+ Yeni Departman Tanımla</span>
                  </button>
                </div>
              </div>

              {/* İstatistik & Özet Sayaçları */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))',
                gap: '16px',
                marginBottom: '24px'
              }}>
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(113, 52, 226, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Building2 size={22} color="#a855f7" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--nt-ffffff)' }}>
                      {departments.length}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Tanımlı Departman
                    </div>
                  </div>
                </div>

                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Users size={22} color="#10b981" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--nt-ffffff)' }}>
                      {departments.reduce((acc, d) => acc + (d.actor_count || 0), 0)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Atanmış Aktif Personel / Ajan
                    </div>
                  </div>
                </div>

                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(20, 108, 235, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <CheckCircle2 size={22} color="#3b82f6" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--nt-ffffff)' }}>
                      %100
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Sistem Entegrasyon Durumu
                    </div>
                  </div>
                </div>
              </div>

              {/* Arama & Görünüm Değiştirici */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '20px',
                gap: '16px',
                flexWrap: 'wrap'
              }}>
                <div style={{ position: 'relative', flex: 1, maxWidth: '380px' }}>
                  <Search size={16} color="var(--nt-64748b)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                  <input
                    type="text"
                    placeholder="Departman adı veya açıklama ile ara..."
                    value={deptSearch}
                    onChange={(e) => setDeptSearch(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgb(var(--rgb-sf-111827) / 0.7)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      borderRadius: '8px',
                      padding: '9px 12px 9px 36px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none'
                    }}
                  />
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  background: 'rgb(var(--rgb-sf-111827) / 0.6)',
                  borderRadius: '8px',
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  padding: '3px'
                }}>
                  <button
                    onClick={() => setDeptViewMode('CARDS')}
                    style={{
                      background: deptViewMode === 'CARDS' ? 'rgba(113, 52, 226, 0.35)' : 'transparent',
                      border: 'none',
                      color: deptViewMode === 'CARDS' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.775rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Kart Görünümü
                  </button>
                  <button
                    onClick={() => setDeptViewMode('LIST')}
                    style={{
                      background: deptViewMode === 'LIST' ? 'rgba(113, 52, 226, 0.35)' : 'transparent',
                      border: 'none',
                      color: deptViewMode === 'LIST' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.775rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Liste Görünümü
                  </button>
                </div>
              </div>

              {/* Yükleniyor Göstergesi */}
              {isLoadingDepts && (
                <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--nt-94a3b8)' }}>
                  <RefreshCw size={28} className="spin" style={{ margin: '0 auto 12px auto', display: 'block' }} />
                  <span>Departmanlar yükleniyor...</span>
                </div>
              )}

              {/* Boş Durum (Empty State) */}
              {!isLoadingDepts && filteredDepartments.length === 0 && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.4)',
                  border: '1px dashed rgb(var(--rgb-ov) / 0.12)',
                  borderRadius: '16px',
                  padding: '60px 20px',
                  textAlign: 'center',
                  maxWidth: '520px',
                  margin: '40px auto'
                }}>
                  <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '16px',
                    background: 'rgba(113, 52, 226, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px auto'
                  }}>
                    <Building2 size={32} color="#a855f7" />
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--nt-ffffff)', marginBottom: '8px' }}>
                    {deptSearch ? 'Eşleşen Departman Bulunamadı' : 'Henüz Tanımlı Departman Yok'}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', lineHeight: 1.5, marginBottom: '20px' }}>
                    {deptSearch
                      ? `'${deptSearch}' aramasına uygun bir departman bulunamadı.`
                      : 'Şirketinizin organizasyon şemasını oluşturmak ve personellerinizi/AI ajanlarınızı konumlandırmak için ilk departmanınızı tanımlayın.'}
                  </p>
                  {!deptSearch && (
                    <button
                      onClick={handleOpenCreateDept}
                      style={{
                        background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                        border: 'none',
                        color: '#ffffff',
                        padding: '10px 20px',
                        borderRadius: '8px',
                        fontSize: '0.875rem',
                        fontWeight: '700',
                        cursor: 'pointer',
                        boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)'
                      }}
                    >
                      + İlk Departmanı Tanımla
                    </button>
                  )}
                </div>
              )}

              {/* KART GÖRÜNÜMÜ */}
              {!isLoadingDepts && filteredDepartments.length > 0 && deptViewMode === 'CARDS' && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))',
                  gap: '20px'
                }}>
                  {filteredDepartments.map((dept, index) => {
                    const gradients = [
                      'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
                      'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                      'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
                      'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)'
                    ];
                    const cardGrad = gradients[index % gradients.length];

                    return (
                      <div
                        key={dept.id}
                        style={{
                          background: 'linear-gradient(145deg, rgb(var(--rgb-sf-141b2c) / 0.75) 0%, rgb(var(--rgb-sf-0d121e) / 0.9) 100%)',
                          border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                          borderRadius: '16px',
                          padding: '22px',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          boxShadow: '0 8px 24px rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                          transition: 'all 0.2s ease',
                          position: 'relative'
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px' }}>
                            <div style={{
                              width: '42px',
                              height: '42px',
                              borderRadius: '12px',
                              background: cardGrad,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              boxShadow: '0 4px 12px rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))'
                            }}>
                              <Building2 size={22} color="#ffffff" />
                            </div>

                            <span style={{
                              background: 'rgb(var(--rgb-ov) / 0.06)',
                              border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                              color: 'var(--nt-94a3b8)',
                              fontSize: '0.7rem',
                              fontWeight: '600',
                              padding: '3px 8px',
                              borderRadius: '12px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              <Users size={12} />
                              {dept.actor_count || 0} Aktör
                            </span>
                          </div>

                          <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--nt-ffffff)', marginBottom: '8px', lineHeight: 1.3 }}>
                            {dept.name}
                          </h3>

                          <p style={{ fontSize: '0.825rem', color: 'var(--nt-94a3b8)', lineHeight: 1.5, minHeight: '44px', marginBottom: '16px' }}>
                            {dept.description || 'Bu departman için henüz özel açıklama girilmedi.'}
                          </p>
                        </div>

                        <div style={{
                          borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                          paddingTop: '14px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between'
                        }}>
                          <div style={{ fontSize: '0.72rem', color: 'var(--nt-64748b)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                            <Calendar size={13} />
                            <span>
                              {dept.created_at ? new Date(dept.created_at).toLocaleDateString('tr-TR') : 'Bugün'}
                            </span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <button
                              onClick={() => handleOpenEditDept(dept)}
                              style={{
                                background: 'rgb(var(--rgb-ov) / 0.06)',
                                border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                                color: 'var(--nt-e2e8f0)',
                                padding: '6px 12px',
                                borderRadius: '7px',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px'
                              }}
                              title="Departmanı Düzenle"
                            >
                              <Edit3 size={13} />
                              <span>Düzenle</span>
                            </button>

                            <button
                              onClick={() => setDeptToDelete(dept)}
                              style={{
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid rgba(239, 68, 68, 0.25)',
                                color: 'var(--ac-f87171)',
                                padding: '6px 10px',
                                borderRadius: '7px',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px'
                              }}
                              title="Departmanı Sil"
                            >
                              <Trash2 size={13} />
                              <span>Sil</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* LİSTE GÖRÜNÜMÜ */}
              {!isLoadingDepts && filteredDepartments.length > 0 && deptViewMode === 'LIST' && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.7)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  borderRadius: '14px',
                  overflowX: 'auto'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '700px' }}>
                    <thead>
                      <tr style={{
                        background: 'rgb(var(--rgb-ov) / 0.03)',
                        borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
                        color: 'var(--nt-94a3b8)',
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em'
                      }}>
                        <th style={{ padding: '14px 20px' }}>Departman Adı</th>
                        <th style={{ padding: '14px 20px' }}>Açıklama</th>
                        <th style={{ padding: '14px 20px', textAlign: 'center' }}>Aktör Sayısı</th>
                        <th style={{ padding: '14px 20px' }}>Oluşturulma Tarihi</th>
                        <th style={{ padding: '14px 20px', textAlign: 'right' }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredDepartments.map((dept) => (
                        <tr key={dept.id} style={{ borderBottom: '1px solid rgb(var(--rgb-ov) / 0.05)' }}>
                          <td style={{ padding: '16px 20px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <div style={{
                                width: '32px',
                                height: '32px',
                                borderRadius: '8px',
                                background: 'rgba(113, 52, 226, 0.2)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}>
                                <Building2 size={16} color="#a855f7" />
                              </div>
                              <span style={{ fontWeight: '700', color: 'var(--nt-ffffff)', fontSize: '0.9rem' }}>
                                {dept.name}
                              </span>
                            </div>
                          </td>
                          <td style={{ padding: '16px 20px', color: 'var(--nt-94a3b8)', fontSize: '0.825rem', maxWidth: '350px' }}>
                            {dept.description || '—'}
                          </td>
                          <td style={{ padding: '16px 20px', textAlign: 'center' }}>
                            <span style={{
                              background: 'rgb(var(--rgb-ov) / 0.06)',
                              padding: '3px 9px',
                              borderRadius: '12px',
                              fontSize: '0.75rem',
                              fontWeight: '600',
                              color: 'var(--nt-cbd5e1)'
                            }}>
                              {dept.actor_count || 0}
                            </span>
                          </td>
                          <td style={{ padding: '16px 20px', color: 'var(--nt-64748b)', fontSize: '0.8rem' }}>
                            {dept.created_at ? new Date(dept.created_at).toLocaleDateString('tr-TR') : '—'}
                          </td>
                          <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                              <button
                                onClick={() => handleOpenEditDept(dept)}
                                style={{
                                  background: 'rgb(var(--rgb-ov) / 0.06)',
                                  border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                                  color: 'var(--nt-cbd5e1)',
                                  padding: '5px 10px',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  cursor: 'pointer'
                                }}
                              >
                                Düzenle
                              </button>
                              <button
                                onClick={() => setDeptToDelete(dept)}
                                style={{
                                  background: 'rgba(239, 68, 68, 0.1)',
                                  border: '1px solid rgba(239, 68, 68, 0.25)',
                                  color: 'var(--ac-f87171)',
                                  padding: '5px 10px',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  cursor: 'pointer'
                                }}
                              >
                                Sil
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ========================================================================= */}
          {/* MADDE 2: ŞİRKET ÜNVANLARI SEKMESİ (NACE & AI KONTROLLÜ) */}
          {/* ========================================================================= */}
          {activeTab === 'JOB_TITLES' && (
            <div>
              {/* Başlık ve Aksiyon Barı */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '24px',
                flexWrap: 'wrap',
                gap: '16px'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '800', letterSpacing: '-0.02em', margin: 0, color: 'var(--nt-ffffff)' }}>
                      Şirket Ünvanları ve Rol Tanımları
                    </h2>
                    <span style={{
                      background: 'linear-gradient(135deg, rgba(113, 52, 226, 0.2) 0%, rgba(20, 108, 235, 0.2) 100%)',
                      color: 'var(--ac-c084fc)',
                      border: '1px solid rgba(113, 52, 226, 0.4)',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      fontSize: '0.7rem',
                      fontWeight: '700'
                    }}>
                      MADDE 2: NACE & AI MOTORU
                    </span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', margin: '4px 0 0 0' }}>
                    Süper Yönetim Konsolu şablonlarından NACE uyumlu seçim yapın veya özel ünvan tanımlayın. RECOrion AI motoru yeni tanımları denetleyip ekosisteme kazandırır.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    onClick={loadJobTitles}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: 'rgb(var(--rgb-ov) / 0.05)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      color: 'var(--nt-cbd5e1)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                    title="Yenile"
                  >
                    <RefreshCw size={14} className={isLoadingTitles ? 'spin' : ''} />
                    <span>Yenile</span>
                  </button>

                  <button
                    onClick={handleOpenCreateTitle}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                      border: 'none',
                      color: '#ffffff',
                      padding: '9px 18px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '700',
                      cursor: 'pointer',
                      boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)',
                      transition: 'transform 0.15s'
                    }}
                  >
                    <Plus size={16} />
                    <span>+ Yeni Ünvan Tanımla</span>
                  </button>
                </div>
              </div>

              {/* İstatistik & Özet Sayaçları */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 210px), 1fr))',
                gap: '16px',
                marginBottom: '24px'
              }}>
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(56, 189, 248, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Briefcase size={22} color="var(--ac-38bdf8)" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--nt-ffffff)' }}>
                      {jobTitles.length}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Şirkete Tanımlı Ünvan
                    </div>
                  </div>
                </div>

                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(168, 85, 247, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Sparkles size={22} color="var(--ac-c084fc)" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--nt-ffffff)' }}>
                      {jobTitles.filter(t => t.ai_review_status === 'PROMOTED_GLOBAL').length}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      RECOrion AI: Ana Şablona Eklenen
                    </div>
                  </div>
                </div>

                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Users size={22} color="#10b981" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--nt-ffffff)' }}>
                      {jobTitles.reduce((acc, t) => acc + (t.actor_count || 0), 0)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Ünvanı Taşıyan Aktör Sayısı
                    </div>
                  </div>
                </div>
              </div>

              {/* Arama ve Görünüm Seçici */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '20px',
                gap: '16px',
                flexWrap: 'wrap'
              }}>
                <div style={{ position: 'relative', flex: 1, maxWidth: '380px' }}>
                  <Search size={16} color="var(--nt-64748b)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                  <input
                    type="text"
                    placeholder="Ünvan adı, kategori veya açıklama ara..."
                    value={titleSearch}
                    onChange={(e) => setTitleSearch(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgb(var(--rgb-sf-111827) / 0.7)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      borderRadius: '8px',
                      padding: '9px 12px 9px 36px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none'
                    }}
                  />
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  background: 'rgb(var(--rgb-sf-111827) / 0.6)',
                  borderRadius: '8px',
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  padding: '3px'
                }}>
                  <button
                    onClick={() => setTitleViewMode('CARDS')}
                    style={{
                      background: titleViewMode === 'CARDS' ? 'rgba(113, 52, 226, 0.35)' : 'transparent',
                      border: 'none',
                      color: titleViewMode === 'CARDS' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.775rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Kart Görünümü
                  </button>
                  <button
                    onClick={() => setTitleViewMode('LIST')}
                    style={{
                      background: titleViewMode === 'LIST' ? 'rgba(113, 52, 226, 0.35)' : 'transparent',
                      border: 'none',
                      color: titleViewMode === 'LIST' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.775rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Liste Görünümü
                  </button>
                </div>
              </div>

              {/* Yükleniyor Göstergesi */}
              {isLoadingTitles && (
                <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--nt-94a3b8)' }}>
                  <RefreshCw size={28} className="spin" style={{ margin: '0 auto 12px auto', display: 'block' }} />
                  <span>Şirket ünvanları yükleniyor...</span>
                </div>
              )}

              {/* Boş Durum */}
              {!isLoadingTitles && filteredJobTitles.length === 0 && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.4)',
                  border: '1px dashed rgb(var(--rgb-ov) / 0.12)',
                  borderRadius: '16px',
                  padding: '60px 20px',
                  textAlign: 'center',
                  maxWidth: '540px',
                  margin: '40px auto'
                }}>
                  <div style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '16px',
                    background: 'rgba(56, 189, 248, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px auto'
                  }}>
                    <Briefcase size={32} color="var(--ac-38bdf8)" />
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--nt-ffffff)', marginBottom: '8px' }}>
                    {titleSearch ? 'Eşleşen Ünvan Bulunamadı' : 'Henüz Şirketinize Tanımlı Ünvan Yok'}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', lineHeight: 1.5, marginBottom: '20px' }}>
                    {titleSearch
                      ? `'${titleSearch}' aramasına uygun bir ünvan bulunamadı.`
                      : 'Şirketinizde çalışacak yapay zeka ajanları ve personeller için Süper Admin şablonlarından NACE bazlı ünvan seçebilir veya kendi özel ünvanınızı tanımlayabilirsiniz.'}
                  </p>
                  {!titleSearch && (
                    <button
                      onClick={handleOpenCreateTitle}
                      style={{
                        background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                        border: 'none',
                        color: '#ffffff',
                        padding: '10px 22px',
                        borderRadius: '8px',
                        fontSize: '0.875rem',
                        fontWeight: '700',
                        cursor: 'pointer',
                        boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)'
                      }}
                    >
                      + İlk Ünvanı Tanımla
                    </button>
                  )}
                </div>
              )}

              {/* KART GÖRÜNÜMÜ (3D Modern Glassmorphic Ünvan Kartları) */}
              {!isLoadingTitles && filteredJobTitles.length > 0 && titleViewMode === 'CARDS' && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 360px), 1fr))',
                  gap: '20px'
                }}>
                  {filteredJobTitles.map((t) => {
                    const isPromoted = t.ai_review_status === 'PROMOTED_GLOBAL';
                    const isExpanded = expandedPromptId === t.id;

                    return (
                      <div
                        key={t.id}
                        style={{
                          background: 'linear-gradient(145deg, rgb(var(--rgb-sf-141b2c) / 0.75) 0%, rgb(var(--rgb-sf-0d121e) / 0.9) 100%)',
                          border: isPromoted ? '1px solid rgba(168, 85, 247, 0.35)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                          borderRadius: '16px',
                          padding: '22px',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          boxShadow: isPromoted
                            ? '0 8px 30px rgba(113, 52, 226, 0.25), 0 0 15px rgba(168, 85, 247, 0.15)'
                            : '0 8px 24px rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                          transition: 'all 0.2s ease',
                          position: 'relative'
                        }}
                      >
                        <div>
                          {/* Üst Kategori, Model & Rozetler */}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span style={{
                                background: 'rgba(56, 189, 248, 0.12)',
                                color: 'var(--ac-38bdf8)',
                                border: '1px solid rgba(56, 189, 248, 0.3)',
                                fontSize: '0.675rem',
                                fontWeight: '700',
                                padding: '2px 8px',
                                borderRadius: '6px',
                                textTransform: 'uppercase'
                              }}>
                                {t.category}
                              </span>

                              <span style={{
                                background: 'rgb(var(--rgb-ov) / 0.06)',
                                color: 'var(--nt-cbd5e1)',
                                fontSize: '0.675rem',
                                fontWeight: '600',
                                padding: '2px 8px',
                                borderRadius: '6px'
                              }}>
                                🤖 {t.recommended_model_code || 'glm-5.3'}
                              </span>

                              <span style={{
                                background: 'rgba(16, 185, 129, 0.12)',
                                color: 'var(--ac-34d399)',
                                fontSize: '0.675rem',
                                fontWeight: '700',
                                padding: '2px 6px',
                                borderRadius: '6px'
                              }}>
                                {t.autonomy_level || 'L1'}
                              </span>

                              {t.department_name && (
                                <span style={{
                                  background: 'rgba(99, 102, 241, 0.15)',
                                  color: 'var(--ac-a5b4fc)',
                                  border: '1px solid rgba(129, 140, 248, 0.3)',
                                  fontSize: '0.675rem',
                                  fontWeight: '700',
                                  padding: '2px 8px',
                                  borderRadius: '6px'
                                }}>
                                  🏢 {t.department_name}
                                </span>
                              )}
                            </div>

                            <span style={{
                              background: 'rgb(var(--rgb-ov) / 0.06)',
                              color: 'var(--nt-94a3b8)',
                              fontSize: '0.7rem',
                              fontWeight: '600',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              <Users size={12} />
                              {t.actor_count || 0} Aktör
                            </span>
                          </div>

                          {/* Ünvan Başlığı */}
                          <h3 style={{
                            fontSize: '1.2rem',
                            fontWeight: '800',
                            color: 'var(--nt-ffffff)',
                            marginBottom: '6px',
                            lineHeight: 1.3
                          }}>
                            {t.title}
                          </h3>

                          {/* Açıklama */}
                          <p style={{
                            fontSize: '0.825rem',
                            color: 'var(--nt-94a3b8)',
                            lineHeight: 1.5,
                            marginBottom: '12px'
                          }}>
                            {t.description || 'Bu ünvan için detaylı açıklama girilmedi.'}
                          </p>

                          {/* RECOrion AI Kontrol Değerlendirmesi Rozeti (Madde 2) */}
                          <div style={{
                            background: isPromoted ? 'rgba(168, 85, 247, 0.12)' : 'rgb(var(--rgb-ov) / 0.04)',
                            border: isPromoted ? '1px solid rgba(168, 85, 247, 0.35)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                            borderRadius: '8px',
                            padding: '8px 12px',
                            marginBottom: '14px',
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '8px'
                          }}>
                            {isPromoted ? (
                              <Sparkles size={16} color="var(--ac-c084fc)" style={{ flexShrink: 0, marginTop: '2px' }} />
                            ) : (
                              <Building size={16} color="var(--ac-60a5fa)" style={{ flexShrink: 0, marginTop: '2px' }} />
                            )}
                            <div>
                              <div style={{
                                fontSize: '0.75rem',
                                fontWeight: '700',
                                color: isPromoted ? 'var(--ac-c084fc)' : 'var(--ac-93c5fd)',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px'
                              }}>
                                <span>{isPromoted ? 'RECOrion AI: Ana Şablona Eklendi' : 'Şirkete Özel Yerel Ünvan'}</span>
                              </div>
                              <div style={{ fontSize: '0.72rem', color: 'var(--nt-cbd5e1)', lineHeight: 1.4, marginTop: '2px' }}>
                                {t.ai_review_feedback || 'RECOrion AI motoru tarafından incelendi.'}
                              </div>
                            </div>
                          </div>

                          {/* Sistem Rol Promptu Katlanabilir Alanı */}
                          <div style={{
                            background: 'var(--sf-090d16)',
                            border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                            borderRadius: '8px',
                            padding: '10px 12px',
                            marginBottom: '16px'
                          }}>
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              marginBottom: '6px'
                            }}>
                              <span style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--nt-94a3b8)', textTransform: 'uppercase' }}>
                                Sistem Rol Promptu
                              </span>
                              <button
                                onClick={() => setExpandedPromptId(isExpanded ? null : t.id)}
                                style={{
                                  background: 'transparent',
                                  border: 'none',
                                  color: 'var(--ac-38bdf8)',
                                  fontSize: '0.72rem',
                                  fontWeight: '600',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px'
                                }}
                              >
                                {isExpanded ? (
                                  <><span>Gizle</span><ChevronUp size={13} /></>
                                ) : (
                                  <><span>Tamamını Gör</span><ChevronDown size={13} /></>
                                )}
                              </button>
                            </div>

                            <p style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '0.75rem',
                              color: 'var(--nt-cbd5e1)',
                              lineHeight: 1.45,
                              margin: 0,
                              whiteSpace: 'pre-wrap',
                              maxHeight: isExpanded ? '400px' : '52px',
                              overflowY: isExpanded ? 'auto' : 'hidden',
                              transition: 'max-height 0.25s ease'
                            }}>
                              {t.base_role_prompt}
                            </p>
                          </div>

                          {/* Yetenekler */}
                          {t.required_skills && t.required_skills.length > 0 && (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginBottom: '16px' }}>
                              {t.required_skills.slice(0, 5).map((skill, sIdx) => (
                                <span key={sIdx} style={{
                                  background: 'rgb(var(--rgb-ov) / 0.05)',
                                  color: 'var(--nt-cbd5e1)',
                                  fontSize: '0.675rem',
                                  padding: '2px 7px',
                                  borderRadius: '4px'
                                }}>
                                  #{skill}
                                </span>
                              ))}
                              {t.required_skills.length > 5 && (
                                <span style={{ fontSize: '0.675rem', color: 'var(--nt-64748b)' }}>
                                  +{t.required_skills.length - 5}
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Alt Aksiyon Butonları */}
                        <div style={{
                          borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                          paddingTop: '14px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between'
                        }}>
                          <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)' }}>
                            Kod: <strong style={{ color: 'var(--nt-cbd5e1)' }}>{t.code}</strong>
                          </span>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <button
                              onClick={() => handleOpenEditTitle(t)}
                              style={{
                                background: 'rgb(var(--rgb-ov) / 0.06)',
                                border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                                color: 'var(--nt-e2e8f0)',
                                padding: '6px 12px',
                                borderRadius: '7px',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px'
                              }}
                            >
                              <Edit3 size={13} />
                              <span>Düzenle</span>
                            </button>

                            <button
                              onClick={() => setTitleToDelete(t)}
                              style={{
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid rgba(239, 68, 68, 0.25)',
                                color: 'var(--ac-f87171)',
                                padding: '6px 10px',
                                borderRadius: '7px',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px'
                              }}
                            >
                              <Trash2 size={13} />
                              <span>Sil</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* LİSTE GÖRÜNÜMÜ */}
              {!isLoadingTitles && filteredJobTitles.length > 0 && titleViewMode === 'LIST' && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.7)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  borderRadius: '14px',
                  overflowX: 'auto'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '850px' }}>
                    <thead>
                      <tr style={{
                        background: 'rgb(var(--rgb-ov) / 0.03)',
                        borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
                        color: 'var(--nt-94a3b8)',
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em'
                      }}>
                        <th style={{ padding: '14px 20px' }}>Ünvan Adı & Kod</th>
                        <th style={{ padding: '14px 20px' }}>Kategori</th>
                        <th style={{ padding: '14px 20px' }}>RECOrion AI Değerlendirmesi</th>
                        <th style={{ padding: '14px 20px' }}>Önerilen Model</th>
                        <th style={{ padding: '14px 20px', textAlign: 'center' }}>Aktör</th>
                        <th style={{ padding: '14px 20px', textAlign: 'right' }}>İşlemler</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredJobTitles.map((t) => {
                        const isPromoted = t.ai_review_status === 'PROMOTED_GLOBAL';
                        return (
                          <tr key={t.id} style={{ borderBottom: '1px solid rgb(var(--rgb-ov) / 0.05)' }}>
                            <td style={{ padding: '16px 20px' }}>
                              <div style={{ fontWeight: '700', color: 'var(--nt-ffffff)', fontSize: '0.9rem' }}>
                                {t.title}
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '3px' }}>
                                <span style={{ fontSize: '0.72rem', color: 'var(--nt-64748b)', fontFamily: 'var(--font-mono)' }}>
                                  {t.code}
                                </span>
                                {t.department_name && (
                                  <span style={{
                                    fontSize: '0.675rem',
                                    color: 'var(--ac-a5b4fc)',
                                    background: 'rgba(99, 102, 241, 0.15)',
                                    border: '1px solid rgba(129, 140, 248, 0.3)',
                                    padding: '1px 6px',
                                    borderRadius: '4px',
                                    fontWeight: 600
                                  }}>
                                    🏢 {t.department_name}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td style={{ padding: '16px 20px' }}>
                              <span style={{
                                background: 'rgba(56, 189, 248, 0.12)',
                                color: 'var(--ac-38bdf8)',
                                padding: '3px 8px',
                                borderRadius: '6px',
                                fontSize: '0.72rem',
                                fontWeight: '700'
                              }}>
                                {t.category}
                              </span>
                            </td>
                            <td style={{ padding: '16px 20px' }}>
                              <span style={{
                                background: isPromoted ? 'rgba(168, 85, 247, 0.15)' : 'rgb(var(--rgb-ov) / 0.05)',
                                color: isPromoted ? 'var(--ac-c084fc)' : 'var(--nt-94a3b8)',
                                border: isPromoted ? '1px solid rgba(168, 85, 247, 0.35)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                                padding: '3px 8px',
                                borderRadius: '6px',
                                fontSize: '0.72rem',
                                fontWeight: '600',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '5px'
                              }}>
                                {isPromoted ? <Sparkles size={12} /> : <Building size={12} />}
                                {isPromoted ? 'Ana Şablona Eklendi' : 'Şirkete Özel'}
                              </span>
                            </td>
                            <td style={{ padding: '16px 20px', color: 'var(--nt-cbd5e1)', fontSize: '0.8rem' }}>
                              🤖 {t.recommended_model_code || 'glm-5.3'}
                            </td>
                            <td style={{ padding: '16px 20px', textAlign: 'center' }}>
                              <span style={{
                                background: 'rgb(var(--rgb-ov) / 0.06)',
                                padding: '3px 9px',
                                borderRadius: '12px',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                color: 'var(--nt-cbd5e1)'
                              }}>
                                {t.actor_count || 0}
                              </span>
                            </td>
                            <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                                <button
                                  onClick={() => handleOpenEditTitle(t)}
                                  style={{
                                    background: 'rgb(var(--rgb-ov) / 0.06)',
                                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                                    color: 'var(--nt-cbd5e1)',
                                    padding: '5px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    cursor: 'pointer'
                                  }}
                                >
                                  Düzenle
                                </button>
                                <button
                                  onClick={() => setTitleToDelete(t)}
                                  style={{
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    border: '1px solid rgba(239, 68, 68, 0.25)',
                                    color: 'var(--ac-f87171)',
                                    padding: '5px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    cursor: 'pointer'
                                  }}
                                >
                                  Sil
                                </button>
                              </div>
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

          {/* ========================================================================= */}
          {/* TAB 3: AI AJAN KADROSU (Madde 3 - İşe Alım & Yaşam Döngüsü) */}
          {/* ========================================================================= */}
          {activeTab === 'AI_AGENTS' && (
            <div>
              {/* Başlık ve Aksiyon Barı */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '24px',
                flexWrap: 'wrap',
                gap: '16px'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '800', letterSpacing: '-0.02em', margin: 0, color: 'var(--nt-ffffff)' }}>
                      AI Ajanlarının İşe Alım / Tanımlama
                    </h2>
                    <span style={{
                      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(56, 189, 248, 0.2) 100%)',
                      color: 'var(--ac-34d399)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      padding: '2px 8px',
                      borderRadius: '6px',
                      fontSize: '0.7rem',
                      fontWeight: '700'
                    }}>
                      MADDE 3: DİJİTAL İŞ GÜCÜ
                    </span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', margin: '4px 0 0 0' }}>
                    Şirketiniz bünyesinde görev yapacak otonom yapay zeka personellerini işe alın, ünvan atayın ve çalışma durumlarını yönetin.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    onClick={loadAIAgents}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: 'rgb(var(--rgb-ov) / 0.05)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      color: 'var(--nt-cbd5e1)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                    title="Yenile"
                  >
                    <RefreshCw size={14} className={isLoadingAgents ? 'spin' : ''} />
                    <span>Yenile</span>
                  </button>

                  {/* Madde 5: Paket Kotası Rozeti */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    background: agentQuota.is_limit_reached ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.12)',
                    border: agentQuota.is_limit_reached ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(16, 185, 129, 0.3)',
                    padding: '7px 14px',
                    borderRadius: '8px',
                    fontSize: '0.8rem'
                  }}>
                    <span style={{ color: agentQuota.is_limit_reached ? 'var(--ac-f87171)' : 'var(--ac-34d399)', fontWeight: '700' }}>
                      {agentQuota.is_limit_reached ? '⚠️ Paket Kotası Doldu:' : '📊 Paket Kotası:'}
                    </span>
                    <span style={{ color: 'var(--nt-ffffff)', fontWeight: '800' }}>
                      {agentQuota.active_agents} / {agentQuota.max_agents} Ajan
                    </span>
                    <span style={{ color: 'var(--nt-94a3b8)', fontSize: '0.72rem' }}>
                      ({agentQuota.plan_name || 'Paket'})
                    </span>
                  </div>

                  <button
                    onClick={() => {
                      if (agentQuota.is_limit_reached) {
                        showToast(`Paketinizin azami AI Ajan kotası (${agentQuota.max_agents} Ajan) dolmuştur. Yeni ajan ekleyemezsiniz.`, "error");
                        return;
                      }
                      handleOpenHireAgent();
                    }}
                    disabled={agentQuota.is_limit_reached}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: agentQuota.is_limit_reached
                        ? 'rgb(var(--rgb-ov) / 0.08)'
                        : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: agentQuota.is_limit_reached ? '1px solid rgb(var(--rgb-ov) / 0.12)' : 'none',
                      color: agentQuota.is_limit_reached ? 'var(--nt-94a3b8)' : '#ffffff',
                      padding: '9px 18px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '700',
                      cursor: agentQuota.is_limit_reached ? 'not-allowed' : 'pointer',
                      boxShadow: agentQuota.is_limit_reached ? 'none' : '0 4px 16px rgba(16, 185, 129, 0.4)',
                      opacity: agentQuota.is_limit_reached ? 0.6 : 1,
                      transition: 'all 0.15s'
                    }}
                    title={agentQuota.is_limit_reached ? "Paketinizin azami AI Ajan hakkı dolmuştur. Lütfen paketinizi yükseltiniz." : ""}
                  >
                    <Plus size={16} />
                    <span>+ Yeni AI Ajan İşe Al</span>
                  </button>
                </div>
              </div>

              {/* İstatistik & Özet Sayaçları */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 210px), 1fr))',
                gap: '16px',
                marginBottom: '24px'
              }}>
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Bot size={22} color="#10b981" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--nt-ffffff)' }}>
                      {aiAgents.length}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Toplam AI Ajan Kadrosu
                    </div>
                  </div>
                </div>

                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(34, 197, 94, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <UserCheck size={22} color="#22c55e" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#22c55e' }}>
                      {aiAgents.filter(a => a.status !== 'DISABLED').length}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Aktif Görevde
                    </div>
                  </div>
                </div>

                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(239, 68, 68, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <UserX size={22} color="#ef4444" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--ac-f87171)' }}>
                      {aiAgents.filter(a => a.status === 'DISABLED').length}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Pasif / İşten Çıkarılan
                    </div>
                  </div>
                </div>

                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.6)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px'
                }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: 'rgba(56, 189, 248, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Briefcase size={22} color="var(--ac-38bdf8)" />
                  </div>
                  <div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800', color: 'var(--ac-38bdf8)' }}>
                      {jobTitles.length}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                      Kullanılabilir Şirket Ünvanı
                    </div>
                  </div>
                </div>
              </div>

              {/* Arama ve Filtreleme Toolbar */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '14px',
                marginBottom: '20px',
                flexWrap: 'wrap'
              }}>
                {/* Sol: Arama Kutusu ve Durum Filtreleri */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 'min(100%, 320px)' }}>
                  <div style={{
                    position: 'relative',
                    flex: 1,
                    maxWidth: '380px'
                  }}>
                    <Search size={16} color="var(--nt-64748b)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                      type="text"
                      placeholder="AI Ajan adı, model, ünvan veya departmanda ara..."
                      value={agentSearch}
                      onChange={(e) => setAgentSearch(e.target.value)}
                      style={{
                        width: '100%',
                        background: 'rgb(var(--rgb-sf-111622) / 0.8)',
                        border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                        borderRadius: '8px',
                        padding: '9px 12px 9px 36px',
                        color: 'var(--nt-ffffff)',
                        fontSize: '0.85rem',
                        outline: 'none'
                      }}
                    />
                  </div>

                  {/* Durum Filtre Butonları */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    background: 'rgb(var(--rgb-sf-111622) / 0.8)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                    borderRadius: '8px',
                    padding: '3px'
                  }}>
                    <button
                      onClick={() => setAgentStatusFilter('ALL')}
                      style={{
                        background: agentStatusFilter === 'ALL' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
                        border: 'none',
                        color: agentStatusFilter === 'ALL' ? 'var(--ac-34d399)' : 'var(--nt-94a3b8)',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Tümü ({aiAgents.length})
                    </button>
                    <button
                      onClick={() => setAgentStatusFilter('ACTIVE')}
                      style={{
                        background: agentStatusFilter === 'ACTIVE' ? 'rgba(34, 197, 94, 0.2)' : 'transparent',
                        border: 'none',
                        color: agentStatusFilter === 'ACTIVE' ? 'var(--ac-4ade80)' : 'var(--nt-94a3b8)',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Aktif ({aiAgents.filter(a => a.status !== 'DISABLED').length})
                    </button>
                    <button
                      onClick={() => setAgentStatusFilter('DISABLED')}
                      style={{
                        background: agentStatusFilter === 'DISABLED' ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
                        border: 'none',
                        color: agentStatusFilter === 'DISABLED' ? 'var(--ac-f87171)' : 'var(--nt-94a3b8)',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      Pasif / Çıkarılan ({aiAgents.filter(a => a.status === 'DISABLED').length})
                    </button>
                  </div>
                </div>

                {/* Sağ: Görünüm Seçici (Kartlar / Liste) */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  background: 'rgb(var(--rgb-sf-111622) / 0.8)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  borderRadius: '8px',
                  padding: '3px'
                }}>
                  <button
                    onClick={() => setAgentViewMode('CARDS')}
                    style={{
                      background: agentViewMode === 'CARDS' ? 'rgb(var(--rgb-ov) / 0.1)' : 'transparent',
                      border: 'none',
                      color: agentViewMode === 'CARDS' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    3D Kartlar
                  </button>
                  <button
                    onClick={() => setAgentViewMode('LIST')}
                    style={{
                      background: agentViewMode === 'LIST' ? 'rgb(var(--rgb-ov) / 0.1)' : 'transparent',
                      border: 'none',
                      color: agentViewMode === 'LIST' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Liste
                  </button>
                </div>
              </div>

              {/* Ünvan Tanımlanmamışsa Uyarı Kutusu */}
              {jobTitles.length === 0 && (
                <div style={{
                  background: 'rgba(245, 158, 11, 0.1)',
                  border: '1px solid rgba(245, 158, 11, 0.35)',
                  borderRadius: '12px',
                  padding: '18px 20px',
                  marginBottom: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <AlertCircle size={22} color="var(--ac-fbbf24)" style={{ flexShrink: 0 }} />
                    <div style={{ fontSize: '0.85rem', color: 'var(--ac-fde68a)' }}>
                      <strong>Şirketinize henüz bir ünvan tanımlanmamış:</strong> AI Ajan işe alabilmek için ajana atanacak en az bir şirket ünvanı bulunmalıdır.
                    </div>
                  </div>
                  <button
                    onClick={() => setActiveTab('JOB_TITLES')}
                    style={{
                      background: 'rgba(245, 158, 11, 0.2)',
                      border: '1px solid rgba(245, 158, 11, 0.5)',
                      color: 'var(--ac-fbbf24)',
                      padding: '7px 14px',
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      fontWeight: '700',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    Ünvan Tanımlarına Git →
                  </button>
                </div>
              )}

              {/* Boş Durum (Hiç AI Ajan Yok) */}
              {filteredAIAgents.length === 0 && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.5)',
                  border: '1px dashed rgb(var(--rgb-ov) / 0.12)',
                  borderRadius: '16px',
                  padding: '48px 24px',
                  textAlign: 'center',
                  marginTop: '16px'
                }}>
                  <div style={{
                    width: '60px',
                    height: '60px',
                    borderRadius: '16px',
                    background: 'rgba(16, 185, 129, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px auto'
                  }}>
                    <Bot size={30} color="#10b981" />
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--nt-ffffff)', marginBottom: '6px' }}>
                    {agentSearch ? 'Aramaya Uygun AI Ajan Bulunamadı' : 'Henüz İşe Alınmış AI Ajan Bulunmuyor'}
                  </h3>
                  <p style={{ fontSize: '0.825rem', color: 'var(--nt-94a3b8)', maxWidth: '440px', margin: '0 auto 20px auto' }}>
                    {agentSearch ? 'Farklı bir arama kriteri deneyin veya filtreleri sıfırlayın.' : 'Şirketiniz bünyesinde çalışacak ilk otonom yapay zeka personelini tanımlayarak operasyonel süreçleri otomatikleştirin.'}
                  </p>
                  <button
                    onClick={handleOpenHireAgent}
                    style={{
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: 'none',
                      color: '#ffffff',
                      padding: '10px 20px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '700',
                      cursor: 'pointer',
                      boxShadow: '0 4px 16px rgba(16, 185, 129, 0.4)'
                    }}
                  >
                    + İlk AI Ajanınızı İşe Alın
                  </button>
                </div>
              )}

              {/* KARTLAR GÖRÜNÜMÜ (3D Glassmorphic Cards) */}
              {agentViewMode === 'CARDS' && filteredAIAgents.length > 0 && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 330px), 1fr))',
                  gap: '20px'
                }}>
                  {filteredAIAgents.map((agent) => {
                    const isDismissed = agent.status === 'DISABLED';
                    return (
                      <div
                        key={agent.id}
                        style={{
                          background: isDismissed ? 'rgb(var(--rgb-sf-17141c) / 0.6)' : 'rgb(var(--rgb-sf-111827) / 0.7)',
                          border: isDismissed ? '1px solid rgba(239, 68, 68, 0.25)' : '1px solid rgba(16, 185, 129, 0.25)',
                          borderRadius: '16px',
                          padding: '20px',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          backdropFilter: 'blur(12px)',
                          boxShadow: '0 8px 24px rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                          transition: 'all 0.2s',
                          position: 'relative',
                          overflow: 'hidden'
                        }}
                      >
                        {/* Üst Kısım: Avatar, İsim, Durum */}
                        <div>
                          <div style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            justifyContent: 'space-between',
                            marginBottom: '14px'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              <div style={{
                                width: '46px',
                                height: '46px',
                                borderRadius: '12px',
                                background: isDismissed ? 'rgba(239, 68, 68, 0.15)' : 'linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(56, 189, 248, 0.25) 100%)',
                                border: isDismissed ? '1px solid rgba(239, 68, 68, 0.35)' : '1px solid rgba(16, 185, 129, 0.4)',
                                display: 'flex',
                                alignItems: 'center',
                                justifySelf: 'center',
                                justifyContent: 'center'
                              }}>
                                <Bot size={24} color={isDismissed ? 'var(--ac-f87171)' : 'var(--ac-34d399)'} />
                              </div>
                              <div>
                                <h4 style={{ fontSize: '1.05rem', fontWeight: '800', margin: 0, color: 'var(--nt-ffffff)' }}>
                                  {agent.display_name}
                                </h4>
                                <div style={{ fontSize: '0.72rem', color: 'var(--nt-94a3b8)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                                  ID: {agent.id.slice(0, 8)}...
                                </div>
                              </div>
                            </div>

                            {/* Durum Rozeti */}
                            <span style={{
                              background: isDismissed ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                              color: isDismissed ? 'var(--ac-f87171)' : 'var(--ac-4ade80)',
                              border: isDismissed ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(34, 197, 94, 0.3)',
                              padding: '3px 8px',
                              borderRadius: '6px',
                              fontSize: '0.675rem',
                              fontWeight: '700',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              <span style={{
                                width: '6px',
                                height: '6px',
                                borderRadius: '50%',
                                background: isDismissed ? '#ef4444' : '#22c55e'
                              }} />
                              {isDismissed ? 'PASİF (ÇIKARILDI)' : 'AKTİF GÖREVDE'}
                            </span>
                          </div>

                          {/* Rozetler: Model, Ünvan, Departman */}
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
                            <span style={{
                              background: 'rgba(113, 52, 226, 0.15)',
                              color: 'var(--ac-c084fc)',
                              border: '1px solid rgba(113, 52, 226, 0.3)',
                              padding: '3px 8px',
                              borderRadius: '6px',
                              fontSize: '0.72rem',
                              fontWeight: '700',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              🤖 {agent.model_code || 'glm-5.3'}
                            </span>

                            <span style={{
                              background: 'rgba(56, 189, 248, 0.12)',
                              color: 'var(--ac-38bdf8)',
                              border: '1px solid rgba(56, 189, 248, 0.3)',
                              padding: '3px 8px',
                              borderRadius: '6px',
                              fontSize: '0.72rem',
                              fontWeight: '600',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}>
                              <Briefcase size={11} />
                              {agent.job_title_name || 'Ünvan Atanmamış'}
                            </span>

                            {agent.department_name && (
                              <span style={{
                                background: 'rgb(var(--rgb-ov) / 0.05)',
                                color: 'var(--nt-cbd5e1)',
                                border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                                padding: '3px 8px',
                                borderRadius: '6px',
                                fontSize: '0.72rem',
                                fontWeight: '500',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px'
                              }}>
                                <Building2 size={11} />
                                {agent.department_name}
                              </span>
                            )}

                            <span style={{
                              background: 'rgba(245, 158, 11, 0.12)',
                              color: 'var(--ac-fbbf24)',
                              border: '1px solid rgba(245, 158, 11, 0.25)',
                              padding: '3px 6px',
                              borderRadius: '6px',
                              fontSize: '0.7rem',
                              fontWeight: '700'
                            }}>
                              {agent.autonomy_level || 'L1'}
                            </span>
                          </div>

                          {/* Açıklama */}
                          <p style={{
                            fontSize: '0.8rem',
                            color: 'var(--nt-94a3b8)',
                            lineHeight: 1.45,
                            margin: '0 0 16px 0',
                            minHeight: '36px'
                          }}>
                            {agent.description || 'Açıklama belirtilmemiş.'}
                          </p>

                          {/* MADDE 3 ÖZEL BÖLÜM: İŞE ALIM VE İŞTEN ÇIKMA TARİHLERİ */}
                          <div style={{
                            background: 'rgb(var(--rgb-shade) / calc(0.35 * var(--shade-k)))',
                            border: '1px solid rgb(var(--rgb-ov) / 0.06)',
                            borderRadius: '10px',
                            padding: '12px 14px',
                            marginBottom: '16px',
                            fontSize: '0.775rem'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                              <span style={{ color: 'var(--nt-94a3b8)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <Calendar size={13} color="#10b981" />
                                <span>İşe Alım Tarihi:</span>
                              </span>
                              <strong style={{ color: 'var(--nt-f8fafc)' }}>
                                {agent.hired_at ? new Date(agent.hired_at).toLocaleDateString('tr-TR') : '—'}
                              </strong>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span style={{ color: 'var(--nt-94a3b8)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <Clock size={13} color={isDismissed ? '#ef4444' : 'var(--nt-64748b)'} />
                                <span>İşten Çıkma Tarihi:</span>
                              </span>
                              {isDismissed ? (
                                <strong style={{ color: 'var(--ac-f87171)', background: 'rgba(239, 68, 68, 0.15)', padding: '1px 6px', borderRadius: '4px' }}>
                                  {agent.dismissed_at ? new Date(agent.dismissed_at).toLocaleDateString('tr-TR') : 'Pasif'}
                                </strong>
                              ) : (
                                <span style={{ color: 'var(--ac-34d399)', fontWeight: '600' }}>
                                  — (Görevde)
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Alt Kısım: Aksiyon Butonları */}
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '8px',
                          borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                          paddingTop: '14px'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <button
                              onClick={() => handleOpenEditAgent(agent)}
                              style={{
                                background: 'rgb(var(--rgb-ov) / 0.06)',
                                border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                                color: 'var(--nt-cbd5e1)',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px'
                              }}
                            >
                              <Edit3 size={12} />
                              <span>Düzenle</span>
                            </button>

                            {/* İşten Çıkar (Aktif ise) veya Tekrar İşe Al (Pasif ise) */}
                            {!isDismissed ? (
                              <button
                                onClick={() => handleOpenTerminateAgent(agent)}
                                style={{
                                  background: 'rgba(239, 68, 68, 0.12)',
                                  border: '1px solid rgba(239, 68, 68, 0.3)',
                                  color: 'var(--ac-f87171)',
                                  padding: '6px 12px',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px'
                                }}
                                title="AI Ajanını Pasife Çek / İşten Çıkar"
                              >
                                <UserX size={12} />
                                <span>İşten Çıkar</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => handleRehireAgent(agent)}
                                style={{
                                  background: 'rgba(34, 197, 94, 0.15)',
                                  border: '1px solid rgba(34, 197, 94, 0.4)',
                                  color: 'var(--ac-4ade80)',
                                  padding: '6px 12px',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px'
                                }}
                                title="Yeniden İşe Al / Aktifleştir"
                              >
                                <UserCheck size={12} />
                                <span>Tekrar İşe Al</span>
                              </button>
                            )}

                            {/* Uzmanlık Dokümanları (Madde 2) */}
                            <button
                              onClick={() => handleOpenAgentDocs(agent)}
                              style={{
                                background: 'rgba(59, 130, 246, 0.12)',
                                border: '1px solid rgba(59, 130, 246, 0.3)',
                                color: 'var(--ac-60a5fa)',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px'
                              }}
                              title="AI Ajanı Uzmanlık Dokümanları (PDF, Word, Excel) & RAG Hafızası"
                            >
                              <BookOpen size={12} />
                              <span>📚 Kaynaklar ({agent.document_count || 0})</span>
                            </button>
                          </div>

                          <button
                            onClick={() => setAgentToDelete(agent)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: 'var(--nt-64748b)',
                              cursor: 'pointer',
                              padding: '6px',
                              borderRadius: '6px'
                            }}
                            title="Tamamen Sil"
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* LİSTE GÖRÜNÜMÜ (Table View) */}
              {agentViewMode === 'LIST' && filteredAIAgents.length > 0 && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111622) / 0.7)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                  borderRadius: '16px',
                  overflow: 'hidden'
                }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ background: 'rgb(var(--rgb-ov) / 0.03)', borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                        <th style={{ padding: '14px 20px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-94a3b8)' }}>AI AJAN ADI</th>
                        <th style={{ padding: '14px 20px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-94a3b8)' }}>LLM MODELİ</th>
                        <th style={{ padding: '14px 20px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-94a3b8)' }}>ŞİRKET ÜNVANI</th>
                        <th style={{ padding: '14px 20px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-94a3b8)' }}>DEPARTMAN</th>
                        <th style={{ padding: '14px 20px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-94a3b8)' }}>İŞE ALIM TARİHİ</th>
                        <th style={{ padding: '14px 20px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-94a3b8)' }}>İŞTEN ÇIKMA TARİHİ</th>
                        <th style={{ padding: '14px 20px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-94a3b8)' }}>DURUM</th>
                        <th style={{ padding: '14px 20px', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-94a3b8)', textAlign: 'right' }}>İŞLEMLER</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredAIAgents.map((agent) => {
                        const isDismissed = agent.status === 'DISABLED';
                        return (
                          <tr key={agent.id} style={{ borderBottom: '1px solid rgb(var(--rgb-ov) / 0.05)' }}>
                            <td style={{ padding: '16px 20px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <div style={{
                                  width: '32px',
                                  height: '32px',
                                  borderRadius: '8px',
                                  background: isDismissed ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center'
                                }}>
                                  <Bot size={16} color={isDismissed ? 'var(--ac-f87171)' : 'var(--ac-34d399)'} />
                                </div>
                                <div>
                                  <span style={{ fontWeight: '700', color: 'var(--nt-ffffff)', fontSize: '0.9rem', display: 'block' }}>
                                    {agent.display_name}
                                  </span>
                                  <span style={{ fontSize: '0.72rem', color: 'var(--nt-64748b)' }}>
                                    {agent.description?.slice(0, 45) || '—'}
                                  </span>
                                </div>
                              </div>
                            </td>
                            <td style={{ padding: '16px 20px' }}>
                              <span style={{
                                background: 'rgba(113, 52, 226, 0.12)',
                                color: 'var(--ac-c084fc)',
                                padding: '3px 8px',
                                borderRadius: '6px',
                                fontSize: '0.72rem',
                                fontWeight: '700'
                              }}>
                                🤖 {agent.model_code || 'glm-5.3'}
                              </span>
                            </td>
                            <td style={{ padding: '16px 20px', color: 'var(--ac-38bdf8)', fontSize: '0.825rem', fontWeight: '600' }}>
                              {agent.job_title_name || '—'}
                            </td>
                            <td style={{ padding: '16px 20px', color: 'var(--nt-cbd5e1)', fontSize: '0.8rem' }}>
                              {agent.department_name || 'Genel'}
                            </td>
                            <td style={{ padding: '16px 20px', color: 'var(--nt-f8fafc)', fontSize: '0.8rem' }}>
                              📅 {agent.hired_at ? new Date(agent.hired_at).toLocaleDateString('tr-TR') : '—'}
                            </td>
                            <td style={{ padding: '16px 20px', fontSize: '0.8rem' }}>
                              {isDismissed ? (
                                <span style={{ color: 'var(--ac-f87171)', background: 'rgba(239, 68, 68, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                                  🚪 {agent.dismissed_at ? new Date(agent.dismissed_at).toLocaleDateString('tr-TR') : 'Pasif'}
                                </span>
                              ) : (
                                <span style={{ color: 'var(--ac-34d399)' }}>— (Aktif)</span>
                              )}
                            </td>
                            <td style={{ padding: '16px 20px' }}>
                              <span style={{
                                background: isDismissed ? 'rgba(239, 68, 68, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                                color: isDismissed ? 'var(--ac-f87171)' : 'var(--ac-4ade80)',
                                padding: '3px 8px',
                                borderRadius: '6px',
                                fontSize: '0.7rem',
                                fontWeight: '700'
                              }}>
                                {isDismissed ? 'PASİF' : 'AKTİF'}
                              </span>
                            </td>
                            <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                                <button
                                  onClick={() => handleOpenEditAgent(agent)}
                                  style={{
                                    background: 'rgb(var(--rgb-ov) / 0.06)',
                                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                                    color: 'var(--nt-cbd5e1)',
                                    padding: '5px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    cursor: 'pointer'
                                  }}
                                >
                                  Düzenle
                                </button>
                                <button
                                  onClick={() => handleOpenAgentDocs(agent)}
                                  style={{
                                    background: 'rgba(59, 130, 246, 0.12)',
                                    border: '1px solid rgba(59, 130, 246, 0.3)',
                                    color: 'var(--ac-60a5fa)',
                                    padding: '5px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '4px'
                                  }}
                                  title="Uzmanlık Dokümanları & RAG Hafızası"
                                >
                                  <BookOpen size={12} />
                                  <span>📚 Kaynaklar ({agent.document_count || 0})</span>
                                </button>
                                {!isDismissed ? (
                                  <button
                                    onClick={() => handleOpenTerminateAgent(agent)}
                                    style={{
                                      background: 'rgba(239, 68, 68, 0.1)',
                                      border: '1px solid rgba(239, 68, 68, 0.25)',
                                      color: 'var(--ac-f87171)',
                                      padding: '5px 10px',
                                      borderRadius: '6px',
                                      fontSize: '0.75rem',
                                      fontWeight: '600',
                                      cursor: 'pointer'
                                    }}
                                  >
                                    İşten Çıkar
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => handleRehireAgent(agent)}
                                    style={{
                                      background: 'rgba(34, 197, 94, 0.12)',
                                      border: '1px solid rgba(34, 197, 94, 0.3)',
                                      color: 'var(--ac-4ade80)',
                                      padding: '5px 10px',
                                      borderRadius: '6px',
                                      fontSize: '0.75rem',
                                      fontWeight: '600',
                                      cursor: 'pointer'
                                    }}
                                  >
                                    İşe Al
                                  </button>
                                )}
                                <button
                                  onClick={() => setAgentToDelete(agent)}
                                  style={{
                                    background: 'transparent',
                                    border: 'none',
                                    color: 'var(--nt-64748b)',
                                    padding: '5px',
                                    cursor: 'pointer'
                                  }}
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
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


          {/* ========================================================================= */}
          {/* TAB 4 / MADDE 6: KURUMSAL MANİFESTO SEKMESİ */}
          {/* ========================================================================= */}
          {activeTab === 'MANIFESTO' && (
            <div style={{ padding: '4px 0 30px 0', maxWidth: '1100px', margin: '0 auto' }}>
              {/* Başlık ve Aksiyon Barı */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '20px',
                flexWrap: 'wrap',
                gap: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '38px',
                    height: '38px',
                    borderRadius: '10px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 0 16px rgba(245, 158, 11, 0.25)'
                  }}>
                    <FileText size={20} color="#f59e0b" />
                  </div>
                  <div>
                    <h2 style={{ fontSize: '1.4rem', fontWeight: '800', margin: 0, color: 'var(--nt-ffffff)', letterSpacing: '-0.02em' }}>
                      Kurumsal Manifesto & Stratejik Vizyon
                    </h2>
                    <p style={{ fontSize: '0.8rem', color: 'var(--nt-94a3b8)', margin: '2px 0 0 0' }}>
                      Şirketinizin anayasasını, etik ilkelerini ve AI vizyonunu yönetin; dilediğiniz EVREN AI modeline manifestoyu düzenletin.
                    </p>
                  </div>
                </div>

                {/* Üst Aksiyon Butonları */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    onClick={handleResetManifestoChanges}
                    disabled={isSavingManifesto || isGeneratingManifesto || isManifestoUnchanged}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: 'rgb(var(--rgb-ov) / 0.05)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      color: isManifestoUnchanged ? 'var(--nt-64748b)' : 'var(--nt-cbd5e1)',
                      padding: '9px 15px',
                      borderRadius: '8px',
                      fontSize: '0.825rem',
                      fontWeight: '600',
                      cursor: isManifestoUnchanged ? 'not-allowed' : 'pointer'
                    }}
                    title="Mevcut kaydedilmiş manifestoya, sektörlere ve NACE kodlarına geri dön"
                  >
                    <RefreshCw size={14} />
                    <span>Değişiklikleri Sıfırla</span>
                  </button>

                  <button
                    onClick={handleSaveManifesto}
                    disabled={isSavingManifesto || isGeneratingManifesto}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: 'none',
                      color: '#ffffff',
                      padding: '9px 20px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '700',
                      cursor: isSavingManifesto ? 'wait' : 'pointer',
                      boxShadow: '0 4px 16px rgba(16, 185, 129, 0.35)',
                      opacity: isSavingManifesto ? 0.7 : 1
                    }}
                  >
                    <CheckCircle2 size={16} />
                    <span>{isSavingManifesto ? 'Kaydediliyor...' : '💾 Kurumsal Manifestoyu Kaydet'}</span>
                  </button>
                </div>
              </div>

              {/* ========================================================================= */}
              {/* MADDE 1: ŞİRKET SEKTÖRLERİ & NACE FAALİYET ALANLARI DÜZENLEME PANELİ */}
              {/* ========================================================================= */}
              <div style={{
                background: 'rgb(var(--rgb-sf-111622) / 0.75)',
                border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                borderRadius: '16px',
                padding: '22px',
                marginBottom: '22px',
                boxShadow: '0 8px 30px rgb(var(--rgb-shade) / calc(0.35 * var(--shade-k)))'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      width: '34px',
                      height: '34px',
                      borderRadius: '8px',
                      background: 'rgba(56, 189, 248, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Briefcase size={17} color="var(--ac-38bdf8)" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.05rem', fontWeight: '800', margin: 0, color: 'var(--nt-ffffff)' }}>
                        Şirket Sektörleri & NACE Faaliyet Alanları Düzenleme
                      </h3>
                      <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: '2px 0 0 0' }}>
                        Şirketinizin sektörlerini ve NACE kodlarını güncelleyin. Yapay zeka bu alanları kurumsal manifesto ve ajan kararlarında doğrudan referans alır.
                      </p>
                    </div>
                  </div>

                  <div style={{
                    background: 'rgba(245, 158, 11, 0.1)',
                    border: '1px solid rgba(245, 158, 11, 0.25)',
                    color: 'var(--ac-fbbf24)',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}>
                    <Sparkles size={13} />
                    <span>Tüm AI Ajanlarının Karar Referansı</span>
                  </div>
                </div>

                {/* 2 Sütunlu Grid: Sol = Sektörler, Sağ = NACE Kodları */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 420px), 1fr))',
                  gap: '20px'
                }}>
                  {/* SOL: SEKTÖRLER DÜZENLEME */}
                  <div style={{
                    background: 'rgb(var(--rgb-sf-0a0e17) / 0.6)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.06)',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <label style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--ac-c084fc)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Tag size={14} />
                        <span>Faaliyet Sektörleri</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)', fontWeight: '500' }}>
                          ({manifestoSectors.length} seçili)
                        </span>
                      </label>
                      {manifestoSectors.length > 0 && (
                        <button
                          type="button"
                          onClick={() => setManifestoSectors([])}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--ac-f87171)',
                            fontSize: '0.7rem',
                            cursor: 'pointer',
                            fontWeight: '600'
                          }}
                          title="Tüm seçili sektörleri kaldır"
                        >
                          Temizle
                        </button>
                      )}
                    </div>

                    {/* Seçili Sektör Etiketleri (Pill Badges) */}
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '6px',
                      minHeight: '44px',
                      padding: '8px',
                      borderRadius: '8px',
                      background: 'rgb(var(--rgb-shade) / calc(0.35 * var(--shade-k)))',
                      border: '1px solid rgb(var(--rgb-ov) / 0.05)',
                      alignItems: 'center'
                    }}>
                      {manifestoSectors.map((sectorName) => (
                        <span
                          key={sectorName}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            background: 'linear-gradient(135deg, rgba(113, 52, 226, 0.25) 0%, rgba(168, 85, 247, 0.15) 100%)',
                            border: '1px solid rgba(168, 85, 247, 0.4)',
                            color: '#e9d5ff',
                            padding: '3px 10px',
                            borderRadius: '20px',
                            fontSize: '0.75rem',
                            fontWeight: '600'
                          }}
                        >
                          <span>📁 {sectorName}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveSector(sectorName)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: 'var(--ac-c084fc)',
                              cursor: 'pointer',
                              padding: 0,
                              lineHeight: 1,
                              fontSize: '14px',
                              display: 'flex',
                              alignItems: 'center'
                            }}
                            title="Sektörü Kaldır"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                      {manifestoSectors.length === 0 && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--nt-64748b)' }}>
                          Henüz sektör eklenmedi. Aşağıdan seçebilir veya ekleyebilirsiniz.
                        </span>
                      )}
                    </div>

                    {/* Sistem Sektörlerinden Hızlı Seçim Açılır Menüsü */}
                    <div>
                      <select
                        onChange={(e) => {
                          const val = e.target.value;
                          if (val) {
                            const found = allSectors.find(s => s.name === val || s.code === val);
                            handleAddSector(found || val);
                            e.target.value = '';
                          }
                        }}
                        defaultValue=""
                        style={{
                          width: '100%',
                          background: 'var(--sf-0d1322)',
                          border: '1px solid rgba(113, 52, 226, 0.3)',
                          color: 'var(--nt-f8fafc)',
                          padding: '8px 12px',
                          borderRadius: '8px',
                          fontSize: '0.78rem',
                          outline: 'none',
                          marginBottom: '8px'
                        }}
                      >
                        <option value="" disabled>+ Sistem Sektör Kataloğundan Ekle...</option>
                        {allSectors.map((s) => {
                          const isAlreadyAdded = manifestoSectors.includes(s.name);
                          return (
                            <option key={s.id || s.code} value={s.name} disabled={isAlreadyAdded}>
                              {s.icon || '📁'} {s.name} {isAlreadyAdded ? '(Zaten Seçili)' : ''}
                            </option>
                          );
                        })}
                      </select>

                      {/* Özel Sektör Girişi */}
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <input
                          type="text"
                          value={customSectorInput}
                          onChange={(e) => setCustomSectorInput(e.target.value)}
                          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddCustomSector(); } }}
                          placeholder="Örn: YENİLENEBİLİR ENERJİ..."
                          style={{
                            flex: 1,
                            background: 'var(--sf-0d1322)',
                            border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                            color: 'var(--nt-f8fafc)',
                            padding: '8px 12px',
                            borderRadius: '8px',
                            fontSize: '0.78rem',
                            outline: 'none'
                          }}
                        />
                        <button
                          type="button"
                          onClick={handleAddCustomSector}
                          disabled={!customSectorInput.trim()}
                          style={{
                            background: customSectorInput.trim() ? 'rgba(113, 52, 226, 0.25)' : 'rgb(var(--rgb-ov) / 0.05)',
                            border: '1px solid rgba(113, 52, 226, 0.4)',
                            color: customSectorInput.trim() ? 'var(--ac-c084fc)' : 'var(--nt-64748b)',
                            padding: '8px 14px',
                            borderRadius: '8px',
                            fontSize: '0.78rem',
                            fontWeight: '700',
                            cursor: customSectorInput.trim() ? 'pointer' : 'default',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          + Ekle
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* SAĞ: NACE KODLARI DÜZENLEME & ARAMA */}
                  <div style={{
                    background: 'rgb(var(--rgb-sf-0a0e17) / 0.6)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.06)',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    position: 'relative'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <label style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--ac-38bdf8)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Hash size={14} />
                        <span>NACE Rev.2 Faaliyet Kodları</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)', fontWeight: '500' }}>
                          ({manifestoNaceCodes.length} kod seçili)
                        </span>
                      </label>
                      {manifestoNaceCodes.length > 0 && (
                        <button
                          type="button"
                          onClick={() => setManifestoNaceCodes([])}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--ac-f87171)',
                            fontSize: '0.7rem',
                            cursor: 'pointer',
                            fontWeight: '600'
                          }}
                          title="Tüm seçili NACE kodlarını temizle"
                        >
                          Tümünü Temizle
                        </button>
                      )}
                    </div>

                    {/* Seçili NACE Etiketleri */}
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '6px',
                      minHeight: '44px',
                      maxHeight: '120px',
                      overflowY: 'auto',
                      padding: '8px',
                      borderRadius: '8px',
                      background: 'rgb(var(--rgb-shade) / calc(0.35 * var(--shade-k)))',
                      border: '1px solid rgb(var(--rgb-ov) / 0.05)',
                      alignItems: 'center'
                    }}>
                      {manifestoNaceCodes.map((naceItem) => {
                        const displayStr = typeof naceItem === 'string'
                          ? naceItem
                          : (naceItem?.code ? `${naceItem.code} - ${naceItem.title || ''}` : String(naceItem));
                        return (
                          <span
                            key={displayStr}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              background: 'rgba(56, 189, 248, 0.15)',
                              border: '1px solid rgba(56, 189, 248, 0.35)',
                              color: 'var(--ac-38bdf8)',
                              padding: '3px 10px',
                              borderRadius: '20px',
                              fontSize: '0.75rem',
                              fontFamily: 'monospace',
                              fontWeight: '600'
                            }}
                          >
                            <span>{displayStr}</span>
                            <button
                              type="button"
                              onClick={() => handleRemoveNaceCode(naceItem)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--ac-38bdf8)',
                                cursor: 'pointer',
                                padding: 0,
                                lineHeight: 1,
                                fontSize: '14px',
                                display: 'flex',
                                alignItems: 'center'
                              }}
                              title="Kodu Kaldır"
                            >
                              ×
                            </button>
                          </span>
                        );
                      })}
                      {manifestoNaceCodes.length === 0 && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--nt-64748b)' }}>
                          Henüz NACE kodu eklenmedi. Arama kutusundan aratarak ekleyebilirsiniz.
                        </span>
                      )}
                    </div>

                    {/* NACE Arama Inputu ve Canlı Sonuç Dropdown */}
                    <div style={{ position: 'relative' }}>
                      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                        <Search size={15} color="var(--nt-64748b)" style={{ position: 'absolute', left: '12px' }} />
                        <input
                          type="text"
                          value={naceSearchQuery}
                          onChange={(e) => handleSearchNace(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              if (naceSearchQuery.trim()) {
                                handleAddNaceCode(naceSearchQuery.trim());
                              }
                            }
                          }}
                          placeholder="NACE kodu veya sektör ara (Örn: 13.20, Dokuma, Yazılım, 62.01)..."
                          style={{
                            width: '100%',
                            background: 'var(--sf-0d1322)',
                            border: '1px solid rgba(56, 189, 248, 0.3)',
                            color: 'var(--nt-f8fafc)',
                            padding: '8px 12px 8px 36px',
                            borderRadius: '8px',
                            fontSize: '0.78rem',
                            outline: 'none'
                          }}
                        />
                        {isSearchingNace && (
                          <div style={{ position: 'absolute', right: '12px' }}>
                            <RefreshCw size={13} className="spin" color="var(--ac-38bdf8)" />
                          </div>
                        )}
                      </div>

                      {/* NACE Arama Sonuçları Açılır Menüsü */}
                      {naceSearchResults.length > 0 && (
                        <div style={{
                          position: 'absolute',
                          top: '100%',
                          left: 0,
                          right: 0,
                          marginTop: '6px',
                          background: 'var(--sf-0f172a)',
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          borderRadius: '8px',
                          maxHeight: '200px',
                          overflowY: 'auto',
                          zIndex: 100,
                          boxShadow: '0 10px 25px rgb(var(--rgb-shade) / calc(0.6 * var(--shade-k)))',
                          padding: '4px'
                        }}>
                          {naceSearchResults.map((nace) => {
                            const isAlreadySelected = manifestoNaceCodes.some(c => {
                              const existingCode = typeof c === 'string' ? c.split(' - ')[0].trim() : (c?.code || String(c));
                              return existingCode === nace.code;
                            });
                            return (
                              <div
                                key={nace.code}
                                onClick={() => handleAddNaceCode(nace)}
                                style={{
                                  padding: '8px 12px',
                                  borderRadius: '6px',
                                  cursor: isAlreadySelected ? 'default' : 'pointer',
                                  background: isAlreadySelected ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  fontSize: '0.78rem',
                                  color: isAlreadySelected ? 'var(--ac-38bdf8)' : 'var(--nt-e2e8f0)',
                                  borderBottom: '1px solid rgb(var(--rgb-ov) / 0.04)'
                                }}
                                onMouseEnter={(e) => {
                                  if (!isAlreadySelected) e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)';
                                }}
                                onMouseLeave={(e) => {
                                  if (!isAlreadySelected) e.currentTarget.style.background = 'transparent';
                                }}
                              >
                                <div>
                                  <span style={{ fontWeight: '700', fontFamily: 'monospace', color: 'var(--ac-38bdf8)', marginRight: '8px' }}>
                                    {nace.code}
                                  </span>
                                  <span>{nace.title}</span>
                                  {nace.sector_group && (
                                    <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)', marginLeft: '6px' }}>
                                      ({nace.sector_group})
                                    </span>
                                  )}
                                </div>
                                <span style={{ fontSize: '0.72rem', color: isAlreadySelected ? 'var(--ac-34d399)' : 'var(--ac-38bdf8)', fontWeight: '700' }}>
                                  {isAlreadySelected ? '✓ Seçili' : '+ Ekle'}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* AI İLE MANİFESTO ÜRET / DÜZENLE KARTI (Madde 6) */}
              <div style={{
                background: 'linear-gradient(145deg, rgba(113, 52, 226, 0.12) 0%, rgba(20, 108, 235, 0.08) 100%)',
                border: '1px solid rgba(113, 52, 226, 0.35)',
                borderRadius: '14px',
                padding: '20px 22px',
                marginBottom: '20px',
                boxShadow: '0 8px 30px rgba(113, 52, 226, 0.15)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={18} color="var(--ac-c084fc)" />
                    <span style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--nt-ffffff)' }}>
                      EVREN AI ile Kurumsal Manifestoyu Düzenle veya Baştan Üret
                    </span>
                  </div>
                  <span style={{ fontSize: '0.725rem', color: 'var(--nt-94a3b8)' }}>
                    Müşteri paketinizde izin verilen modeller kullanılır
                  </span>
                </div>

                <div className="ui-grid-3" style={{
                  display: 'grid',
                  gridTemplateColumns: 'minmax(min(100%, 240px), 1fr) minmax(min(100%, 300px), 2fr) auto',
                  gap: '14px',
                  alignItems: 'flex-end'
                }}>
                  {/* Model Seçimi */}
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '6px' }}>
                      Kullanılacak EVREN AI Modeli
                    </label>
                    <select
                      value={manifestoModel}
                      onChange={(e) => setManifestoModel(e.target.value)}
                      disabled={isGeneratingManifesto}
                      style={{
                        width: '100%',
                        background: 'var(--sf-0d1322)',
                        border: '1px solid rgba(113, 52, 226, 0.4)',
                        color: 'var(--nt-f8fafc)',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        fontSize: '0.825rem',
                        fontWeight: '600',
                        outline: 'none'
                      }}
                    >
                      {availableModels && availableModels.length > 0 ? (
                        availableModels.map(m => (
                          <option key={m.model_code} value={m.model_code}>
                            🤖 {m.name} ({m.model_code})
                          </option>
                        ))
                      ) : (
                        <>
                          <option value="glm-5.3">🤖 GLM 5.3 (Ultra Hızlı Akıl Yürütme)</option>
                          <option value="gpt-5-turbo">🤖 GPT-5 Turbo (Stratejik Analiz)</option>
                          <option value="claude-3-opus">🤖 Claude 3.5 Sonnet (Kurumsal Üslup)</option>
                        </>
                      )}
                    </select>
                  </div>

                  {/* Vurgu / Düzenleme Direktifi */}
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '6px' }}>
                      Özel Vurgu veya Düzenleme Notu (Opsiyonel)
                    </label>
                    <input
                      type="text"
                      value={manifestoInstructions}
                      onChange={(e) => setManifestoInstructions(e.target.value)}
                      disabled={isGeneratingManifesto}
                      placeholder="Örn: Sürdürülebilirlik, sıfır hata ve dijital yapay zeka hızını öne çıkar..."
                      style={{
                        width: '100%',
                        background: 'var(--sf-0d1322)',
                        border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                        color: 'var(--nt-f8fafc)',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        fontSize: '0.825rem',
                        outline: 'none'
                      }}
                    />
                  </div>

                  {/* AI ile Üret Butonu */}
                  <div>
                    <button
                      onClick={handleGenerateManifesto}
                      disabled={isGeneratingManifesto}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                        border: 'none',
                        color: '#ffffff',
                        padding: '10px 20px',
                        borderRadius: '8px',
                        fontSize: '0.825rem',
                        fontWeight: '700',
                        cursor: isGeneratingManifesto ? 'wait' : 'pointer',
                        boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)',
                        whiteSpace: 'nowrap',
                        height: '42px',
                        opacity: isGeneratingManifesto ? 0.75 : 1
                      }}
                    >
                      <Sparkles size={16} className={isGeneratingManifesto ? 'spin' : ''} />
                      <span>{isGeneratingManifesto ? 'AI Hazırlıyor...' : '✨ Seçili AI ile Manifestoyu Düzenle'}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* DÜZENLENEBİLİR MANİFESTO EDİTÖRÜ */}
              <div style={{
                background: 'rgb(var(--rgb-sf-111622) / 0.75)',
                border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                borderRadius: '14px',
                padding: '20px 22px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--nt-f8fafc)' }}>
                    Kurumsal Manifesto Metni (Doğrudan Düzenlenebilir)
                  </label>
                  <span style={{ fontSize: '0.725rem', color: 'var(--nt-94a3b8)' }}>
                    {manifestoText.length} Karakter | {manifestoText.split(/\s+/).filter(Boolean).length} Kelime
                  </span>
                </div>

                <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: '0 0 12px 0' }}>
                  Bu metin doğrudan klavyenizle serbestçe düzenlenebilir veya yukarıdaki AI motoruna zenginleştirilebilir. Tüm AI personelleriniz ve departmanlarınız kararlarında bu manifestoyu kurumsal anayasa olarak referans alır.
                </p>

                <textarea
                  value={manifestoText}
                  onChange={(e) => setManifestoText(e.target.value)}
                  rows={20}
                  placeholder="Şirketinizin Kurumsal Manifestosunu buraya yazın veya yukarıdaki EVREN AI modeline hazırlatın..."
                  style={{
                    width: '100%',
                    background: 'rgb(var(--rgb-sf-0a0e17) / 0.9)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                    borderRadius: '10px',
                    padding: '16px',
                    color: 'var(--nt-f8fafc)',
                    fontSize: '0.875rem',
                    lineHeight: '1.65',
                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                    resize: 'vertical',
                    outline: 'none',
                    boxShadow: 'inset 0 2px 8px rgb(var(--rgb-shade) / calc(0.5 * var(--shade-k)))'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#7134e2'}
                  onBlur={(e) => e.target.style.borderColor = 'rgb(var(--rgb-ov) / 0.12)'}
                />

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', marginTop: '14px' }}>
                  <button
                    onClick={handleSaveManifesto}
                    disabled={isSavingManifesto || isGeneratingManifesto}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: 'none',
                      color: '#ffffff',
                      padding: '10px 24px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: '700',
                      cursor: isSavingManifesto ? 'wait' : 'pointer',
                      boxShadow: '0 4px 16px rgba(16, 185, 129, 0.35)',
                      opacity: isSavingManifesto ? 0.7 : 1
                    }}
                  >
                    <CheckCircle2 size={16} />
                    <span>{isSavingManifesto ? 'Kaydediliyor...' : '💾 Kurumsal Manifestoyu Kaydet'}</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ========================================================================= */}
      {/* MODAL: NORMAL İNSAN KULLANICI TANIMLAMA / DÜZENLEME (Madde 1) */}
      {/* ========================================================================= */}
      {isUserModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.75 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-101524)',
            border: '1px solid rgba(113, 52, 226, 0.35)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '680px',
            maxHeight: '90vh',
            boxShadow: '0 20px 50px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k))), 0 0 30px rgba(113, 52, 226, 0.25)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            {/* Modal Başlığı */}
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'linear-gradient(135deg, rgba(113, 52, 226, 0.15) 0%, rgba(20, 108, 235, 0.1) 100%)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <UserPlus size={18} color="#ffffff" />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: '800', margin: 0, color: 'var(--nt-ffffff)' }}>
                    {editingUser ? 'Kullanıcıyı Düzenle' : 'Kullanıcı Tanımlama'}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                    Madde 1: Personel Kimlik, Rol, Şifre ve İzin Kataloğu Ek İzinleri
                  </span>
                </div>
              </div>

              <button
                onClick={() => setIsUserModalOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--nt-94a3b8)',
                  fontSize: '1.25rem',
                  cursor: 'pointer',
                  padding: '4px',
                  lineHeight: 1
                }}
              >
                ✕
              </button>
            </div>

            {/* Modal Gövdesi */}
            <form onSubmit={handleSaveUser} style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              {/* Hata Bildirimi */}
              {userFormError && (
                <div style={{
                  padding: '12px 16px',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '8px',
                  color: 'var(--ac-fca5a5)',
                  fontSize: '0.8rem',
                  marginBottom: '18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <AlertCircle size={16} />
                  <span>{userFormError}</span>
                </div>
              )}

              {/* 1. Satır: Adı Soyadı & Email */}
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '6px' }}>
                    Adı Soyadı <span style={{ color: 'var(--ac-f87171)' }}>*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: Cüneyt Erdil"
                    value={userForm.display_name}
                    onChange={(e) => setUserForm(prev => ({ ...prev, display_name: e.target.value }))}
                    style={{
                      width: '100%',
                      background: 'rgb(var(--rgb-ov) / 0.05)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '6px' }}>
                    Email (Kullanıcı Adı) <span style={{ color: 'var(--ac-f87171)' }}>*</span>
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="kullanici@sirketiniz.com"
                    value={userForm.email}
                    onChange={(e) => setUserForm(prev => ({ ...prev, email: e.target.value }))}
                    style={{
                      width: '100%',
                      background: 'rgb(var(--rgb-ov) / 0.05)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none'
                    }}
                  />
                </div>
              </div>

              {/* 2. Satır: Departman & Ünvan Seçimi */}
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '6px' }}>
                    Departman
                  </label>
                  <select
                    value={userForm.department_id}
                    onChange={(e) => setUserForm(prev => ({ ...prev, department_id: e.target.value }))}
                    style={{
                      width: '100%',
                      background: 'var(--sf-131826)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="">Departman Seçiniz...</option>
                    {departments.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '6px' }}>
                    Ünvan
                  </label>
                  <select
                    value={userForm.job_title_id}
                    onChange={(e) => setUserForm(prev => ({ ...prev, job_title_id: e.target.value }))}
                    style={{
                      width: '100%',
                      background: 'var(--sf-131826)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="">Ünvan Seçiniz...</option>
                    {jobTitles.map(j => (
                      <option key={j.id} value={j.id}>{j.title}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* 3. Satır: Şifre ve Güçlü Şifre Oluşturucu */}
              <div style={{
                background: 'rgb(var(--rgb-ov) / 0.02)',
                border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                borderRadius: '10px',
                padding: '14px',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <label style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Lock size={14} color="#a855f7" />
                    <span>Giriş Şifresi</span>
                    {!editingUser && <span style={{ color: 'var(--ac-f87171)' }}>*</span>}
                  </label>

                  <button
                    type="button"
                    onClick={handleGenerateStrongUserPassword}
                    style={{
                      background: 'rgba(113, 52, 226, 0.2)',
                      border: '1px solid rgba(113, 52, 226, 0.4)',
                      color: 'var(--ac-c084fc)',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '0.725rem',
                      fontWeight: '700',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px'
                    }}
                  >
                    <Key size={12} />
                    <span>🔑 Güçlü Şifre Oluştur</span>
                  </button>
                </div>

                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder={editingUser ? 'Şifreyi değiştirmek istemiyorsanız boş bırakın' : 'En az 6 karakterli şifre'}
                    value={userForm.password}
                    onChange={(e) => setUserForm(prev => ({ ...prev, password: e.target.value }))}
                    style={{
                      width: '100%',
                      background: 'rgb(var(--rgb-ov) / 0.05)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '10px 40px 10px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      fontFamily: showPassword ? 'monospace' : 'inherit',
                      outline: 'none'
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '10px',
                      background: 'none',
                      border: 'none',
                      color: 'var(--nt-94a3b8)',
                      cursor: 'pointer',
                      padding: '4px'
                    }}
                    title={showPassword ? 'Gizle' : 'Göster'}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                {userForm.password && (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px' }}>
                    <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: '600' }}>
                      ✓ Şifre hazır
                    </span>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(userForm.password, 'Şifre')}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--ac-38bdf8)',
                        fontSize: '0.7rem',
                        cursor: 'pointer',
                        padding: 0
                      }}
                    >
                      Şifreyi Kopyala
                    </button>
                  </div>
                )}
              </div>

              {/* 4. Satır: Kullanıcı Aktif / Pasif */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '8px' }}>
                  Kullanıcı Durumu
                </label>
                <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div
                    onClick={() => setUserForm(prev => ({ ...prev, status: 'ACTIVE' }))}
                    style={{
                      padding: '12px',
                      borderRadius: '10px',
                      background: userForm.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.12)' : 'rgb(var(--rgb-ov) / 0.02)',
                      border: '1px solid ' + (userForm.status === 'ACTIVE' ? '#10b981' : 'rgb(var(--rgb-ov) / 0.08)'),
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px'
                    }}
                  >
                    <UserCheck size={18} color={userForm.status === 'ACTIVE' ? '#10b981' : 'var(--nt-64748b)'} />
                    <div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '700', color: userForm.status === 'ACTIVE' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)' }}>
                        Aktif
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)' }}>
                        Sisteme giriş yapabilir, oturum açabilir
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => setUserForm(prev => ({ ...prev, status: 'DISABLED' }))}
                    style={{
                      padding: '12px',
                      borderRadius: '10px',
                      background: userForm.status === 'DISABLED' ? 'rgba(239, 68, 68, 0.12)' : 'rgb(var(--rgb-ov) / 0.02)',
                      border: '1px solid ' + (userForm.status === 'DISABLED' ? '#ef4444' : 'rgb(var(--rgb-ov) / 0.08)'),
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px'
                    }}
                  >
                    <UserX size={18} color={userForm.status === 'DISABLED' ? '#ef4444' : 'var(--nt-64748b)'} />
                    <div>
                      <div style={{ fontSize: '0.8rem', fontWeight: '700', color: userForm.status === 'DISABLED' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)' }}>
                        Pasif
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)' }}>
                        Girişi engellenir, kota harcamaz
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 5. Satır: Sistem Yetki Rolleri (Süper Yöneticinin Tanımladığı) */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '6px' }}>
                  Sistem Yetki Rolü (Süper Yöneticinin Tanımladığı)
                </label>
                <select
                  value={userForm.role_id}
                  onChange={(e) => setUserForm(prev => ({ ...prev, role_id: e.target.value }))}
                  style={{
                    width: '100%',
                    background: 'var(--sf-131826)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                    borderRadius: '8px',
                    padding: '10px 12px',
                    color: 'var(--nt-ffffff)',
                    fontSize: '0.85rem',
                    outline: 'none',
                    cursor: 'pointer',
                    marginBottom: '8px'
                  }}
                >
                  <option value="">Standart Kullanıcı Rolü...</option>
                  {systemRoles.map(r => (
                    <option key={r.id} value={r.id}>
                      {r.name} {r.is_system ? '(Sistem Rolü)' : ''}
                    </option>
                  ))}
                </select>

                {/* Seçili Rolün Detay Kutusu */}
                {(() => {
                  const selectedRole = systemRoles.find(r => r.id === userForm.role_id);
                  if (!selectedRole) return null;
                  return (
                    <div style={{
                      padding: '10px 14px',
                      background: 'rgba(129, 140, 248, 0.08)',
                      border: '1px solid rgba(129, 140, 248, 0.2)',
                      borderRadius: '8px',
                      fontSize: '0.75rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontWeight: '700', color: 'var(--ac-a5b4fc)' }}>
                          Rol Tanımı: {selectedRole.name}
                        </span>
                        <span style={{ color: 'var(--nt-94a3b8)', fontSize: '0.7rem' }}>
                          {selectedRole.permissions?.length || 0} adet temel yetki
                        </span>
                      </div>
                      {selectedRole.description && (
                        <div style={{ color: 'var(--nt-94a3b8)', marginBottom: '6px' }}>
                          {selectedRole.description}
                        </div>
                      )}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {(selectedRole.permissions || []).slice(0, 8).map((p, idx) => (
                          <span key={idx} style={{
                            fontSize: '0.65rem',
                            background: 'rgb(var(--rgb-ov) / 0.06)',
                            padding: '1px 6px',
                            borderRadius: '3px',
                            color: 'var(--nt-cbd5e1)',
                            fontFamily: 'monospace'
                          }}>
                            {p}
                          </span>
                        ))}
                        {(selectedRole.permissions || []).length > 8 && (
                          <span style={{ fontSize: '0.65rem', color: 'var(--ac-818cf8)', padding: '1px 4px' }}>
                            +{selectedRole.permissions.length - 8} daha...
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* 6. Satır: İzin Kataloğundan Ek İzin Alanı */}
              <div style={{
                background: 'rgb(var(--rgb-ov) / 0.02)',
                border: '1px solid rgb(var(--rgb-ov) / 0.08)',
                borderRadius: '12px',
                padding: '16px',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div>
                    <label style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Tag size={14} color="#f59e0b" />
                      <span>İzin Kataloğundan Ek İzinler</span>
                    </label>
                    <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)' }}>
                      Seçilen rolün dışındaki özel yetkileri bu alandan personele doğrudan atayabilirsiniz.
                    </span>
                  </div>

                  <span style={{
                    fontSize: '0.72rem',
                    background: (userForm.extra_permissions?.length || 0) > 0 ? 'rgba(245, 158, 11, 0.2)' : 'rgb(var(--rgb-ov) / 0.05)',
                    color: (userForm.extra_permissions?.length || 0) > 0 ? 'var(--ac-fbbf24)' : 'var(--nt-64748b)',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontWeight: '700'
                  }}>
                    {userForm.extra_permissions?.length || 0} Ek İzin Seçili
                  </span>
                </div>

                {/* Modül Filtreleri ve İzin Arama */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
                  <div style={{ position: 'relative', flex: 1, minWidth: '160px' }}>
                    <Search size={13} color="var(--nt-64748b)" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                      type="text"
                      placeholder="İzin ara..."
                      value={permSearch}
                      onChange={(e) => setPermSearch(e.target.value)}
                      style={{
                        width: '100%',
                        background: 'rgb(var(--rgb-ov) / 0.04)',
                        border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                        borderRadius: '6px',
                        padding: '6px 10px 6px 28px',
                        color: 'var(--nt-ffffff)',
                        fontSize: '0.75rem',
                        outline: 'none'
                      }}
                    />
                  </div>

                  <select
                    value={permModuleFilter}
                    onChange={(e) => setPermModuleFilter(e.target.value)}
                    style={{
                      background: 'var(--sf-131826)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      borderRadius: '6px',
                      padding: '6px 10px',
                      color: 'var(--nt-cbd5e1)',
                      fontSize: '0.75rem',
                      outline: 'none'
                    }}
                  >
                    <option value="ALL">Tüm Modüller</option>
                    <option value="RBAC">RBAC (Rol & Kullanıcı)</option>
                    <option value="PLATFORM">PLATFORM (Kurum & Ayarlar)</option>
                    <option value="AGENTS">AGENTS (AI Ajanlar)</option>
                    <option value="PROJECTS">PROJECTS (Projeler & Görevler)</option>
                    <option value="CHAT">CHAT (Sohbet & İletişim)</option>
                    <option value="MEMORY">MEMORY (Kolektif Hafıza)</option>
                    <option value="BILLING">BILLING (Fatura & Paketler)</option>
                  </select>
                </div>

                {/* İzinler Kontrol Listesi */}
                <div style={{
                  maxHeight: '180px',
                  overflowY: 'auto',
                  border: '1px solid rgb(var(--rgb-ov) / 0.06)',
                  borderRadius: '8px',
                  background: 'rgb(var(--rgb-sf-0a0e17) / 0.6)',
                  padding: '6px'
                }}>
                  {systemPermissions
                    .filter(p => {
                      if (permModuleFilter !== 'ALL' && p.module !== permModuleFilter) return false;
                      if (permSearch.trim()) {
                        const q = permSearch.toLowerCase();
                        return (p.name || '').toLowerCase().includes(q) || (p.code || '').toLowerCase().includes(q);
                      }
                      return true;
                    })
                    .map(p => {
                      const isChecked = (userForm.extra_permissions || []).includes(p.code);
                      return (
                        <div
                          key={p.id || p.code}
                          onClick={() => handleToggleExtraPermission(p.code)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            padding: '6px 10px',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            background: isChecked ? 'rgba(245, 158, 11, 0.12)' : 'transparent',
                            borderBottom: '1px solid rgb(var(--rgb-ov) / 0.03)',
                            transition: 'background 0.15s'
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {}}
                            style={{ cursor: 'pointer', accentColor: '#f59e0b' }}
                          />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span style={{ fontSize: '0.78rem', fontWeight: '600', color: isChecked ? 'var(--ac-fbbf24)' : 'var(--nt-e2e8f0)' }}>
                                {p.name}
                              </span>
                              <span style={{
                                fontSize: '0.65rem',
                                color: 'var(--nt-94a3b8)',
                                background: 'rgb(var(--rgb-ov) / 0.05)',
                                padding: '1px 5px',
                                borderRadius: '3px',
                                fontFamily: 'monospace'
                              }}>
                                {p.code}
                              </span>
                            </div>
                            {p.description && (
                              <div style={{ fontSize: '0.675rem', color: 'var(--nt-64748b)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {p.description}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  {systemPermissions.length === 0 && (
                    <div style={{ padding: '20px', textAlign: 'center', color: 'var(--nt-64748b)', fontSize: '0.75rem' }}>
                      İzin kataloğu yükleniyor...
                    </div>
                  )}
                </div>
              </div>

              {/* Modal Alt Butonları */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                gap: '10px',
                borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                paddingTop: '18px',
                marginTop: '10px'
              }}>
                <button
                  type="button"
                  onClick={() => setIsUserModalOpen(false)}
                  style={{
                    background: 'rgb(var(--rgb-ov) / 0.05)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                    color: 'var(--nt-cbd5e1)',
                    padding: '9px 18px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Vazgeç
                </button>

                <button
                  type="submit"
                  disabled={isSavingUser}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                    border: 'none',
                    color: '#ffffff',
                    padding: '9px 22px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '700',
                    cursor: isSavingUser ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)',
                    opacity: isSavingUser ? 0.7 : 1
                  }}
                >
                  {isSavingUser && <RefreshCw size={14} className="spin" />}
                  <span>{isSavingUser ? 'Kaydediliyor...' : (editingUser ? 'Güncelle' : 'Kullanıcıyı Tanımla')}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: KULLANICI SİLME ONAY MODALI (Madde 1) */}
      {/* ========================================================================= */}
      {userToDelete && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.75 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-101524)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '440px',
            boxShadow: '0 20px 50px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k))), 0 0 30px rgba(239, 68, 68, 0.2)',
            overflow: 'hidden',
            padding: '24px',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                background: 'rgba(239, 68, 68, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--ac-f87171)'
              }}>
                <Trash2 size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '800', margin: 0, color: 'var(--nt-ffffff)' }}>
                  Kullanıcıyı Sil
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                  Bu işlem geri alınamaz
                </span>
              </div>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--nt-cbd5e1)', lineHeight: 1.5, marginBottom: '20px' }}>
              <strong style={{ color: 'var(--nt-ffffff)' }}>{userToDelete.display_name}</strong> ({userToDelete.email}) kullanıcısını silmek istediğinize emin misiniz? Bu kullanıcı sisteme giriş yapamayacak ve açtığı oturumlar sonlandırılacaktır.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setUserToDelete(null)}
                style={{
                  background: 'rgb(var(--rgb-ov) / 0.05)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                  color: 'var(--nt-cbd5e1)',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Vazgeç
              </button>

              <button
                type="button"
                disabled={isDeletingUser}
                onClick={handleDeleteUser}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#ef4444',
                  border: 'none',
                  color: '#ffffff',
                  padding: '8px 20px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  cursor: isDeletingUser ? 'not-allowed' : 'pointer',
                  opacity: isDeletingUser ? 0.7 : 1
                }}
              >
                {isDeletingUser && <RefreshCw size={14} className="spin" />}
                <span>{isDeletingUser ? 'Siliniyor...' : 'Evet, Sil'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: DEPARTMAN TANIMLAMA / DÜZENLEME (Madde 1) */}
      {/* ========================================================================= */}
      {isDeptModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.75 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-101524)',
            border: '1px solid rgba(113, 52, 226, 0.35)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '540px',
            boxShadow: '0 20px 50px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k))), 0 0 30px rgba(113, 52, 226, 0.25)',
            overflow: 'hidden',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'linear-gradient(135deg, rgba(113, 52, 226, 0.15) 0%, rgba(20, 108, 235, 0.1) 100%)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Building2 size={18} color="#ffffff" />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: '800', margin: 0, color: 'var(--nt-ffffff)' }}>
                    {editingDept ? 'Departmanı Düzenle' : 'Yeni Departman Tanımla'}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                    Madde 1: Departman Adı ve Açıklama Bilgileri
                  </span>
                </div>
              </div>

              <button
                onClick={() => setIsDeptModalOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--nt-94a3b8)',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <XCircle size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveDepartment} style={{ padding: '24px' }}>
              {deptFormError && (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  color: 'var(--ac-f87171)',
                  fontSize: '0.825rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '18px'
                }}>
                  <AlertCircle size={16} />
                  <span>{deptFormError}</span>
                </div>
              )}

              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                  Departman Adı <span style={{ color: '#f43f5e' }}>*</span>
                </label>
                <input
                  type="text"
                  placeholder="Örn: Yazılım ve Teknoloji Departmanı, Mali İşler..."
                  value={deptForm.name}
                  onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })}
                  autoFocus
                  style={{
                    width: '100%',
                    background: 'var(--sf-0a0d14)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                    borderRadius: '8px',
                    padding: '11px 14px',
                    color: 'var(--nt-ffffff)',
                    fontSize: '0.9rem',
                    outline: 'none'
                  }}
                />
              </div>

              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                  Departman Açıklaması
                </label>
                <textarea
                  placeholder="Departmanın organizasyonel işlevi, sorumluluk alanı ve hedeflerini açıklayınız..."
                  value={deptForm.description}
                  onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })}
                  rows={4}
                  style={{
                    width: '100%',
                    background: 'var(--sf-0a0d14)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                    borderRadius: '8px',
                    padding: '11px 14px',
                    color: 'var(--nt-ffffff)',
                    fontSize: '0.85rem',
                    outline: 'none',
                    lineHeight: 1.5,
                    resize: 'vertical'
                  }}
                />
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                gap: '12px',
                borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                paddingTop: '18px'
              }}>
                <button
                  type="button"
                  onClick={() => setIsDeptModalOpen(false)}
                  style={{
                    background: 'rgb(var(--rgb-ov) / 0.06)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                    color: 'var(--nt-cbd5e1)',
                    padding: '9px 18px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  İptal
                </button>

                <button
                  type="submit"
                  disabled={isSavingDept}
                  style={{
                    background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                    border: 'none',
                    color: '#ffffff',
                    padding: '9px 24px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '700',
                    cursor: isSavingDept ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    opacity: isSavingDept ? 0.7 : 1
                  }}
                >
                  {isSavingDept ? (
                    <>
                      <RefreshCw size={15} className="spin" />
                      <span>Kaydediliyor...</span>
                    </>
                  ) : (
                    <>
                      <Check size={16} />
                      <span>{editingDept ? 'Değişiklikleri Kaydet' : 'Departmanı Tanımla'}</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: ÜNVAN TANIMLAMA / DÜZENLEME (Madde 2 - NACE Combobox & AI Kontrol) */}
      {/* ========================================================================= */}
      {isTitleModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-101524)',
            border: '1px solid rgba(113, 52, 226, 0.45)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '680px',
            maxHeight: '90vh',
            boxShadow: '0 20px 60px rgb(var(--rgb-shade) / calc(0.9 * var(--shade-k))), 0 0 35px rgba(113, 52, 226, 0.3)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            {/* Modal Başlığı */}
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'linear-gradient(135deg, rgba(113, 52, 226, 0.2) 0%, rgba(20, 108, 235, 0.15) 100%)',
              flexShrink: 0
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '9px',
                  background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Briefcase size={18} color="#ffffff" />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: '800', margin: 0, color: 'var(--nt-ffffff)' }}>
                    {editingTitle ? 'Ünvanı Düzenle' : 'Şirket Ünvanı Tanımla'}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                    Madde 2: NACE Sektörel Şablon Seçimi & Otomatik Rol Promptu
                  </span>
                </div>
              </div>

              <button
                onClick={() => setIsTitleModalOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--nt-94a3b8)',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <XCircle size={20} />
              </button>
            </div>

            {/* Modal Form Gövdesi (Scroll edilebilir) */}
            <form onSubmit={handleSaveJobTitle} style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              {titleFormError && (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  color: 'var(--ac-f87171)',
                  fontSize: '0.825rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '18px'
                }}>
                  <AlertCircle size={16} />
                  <span>{titleFormError}</span>
                </div>
              )}

              {/* RECOrion AI Kontrol Bilgilendirme Bannerı */}
              <div style={{
                background: 'linear-gradient(135deg, rgba(113, 52, 226, 0.12) 0%, rgba(20, 108, 235, 0.08) 100%)',
                border: '1px solid rgba(113, 52, 226, 0.3)',
                borderRadius: '10px',
                padding: '12px 14px',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px'
              }}>
                <Sparkles size={18} color="var(--ac-c084fc)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div style={{ fontSize: '0.78rem', color: 'var(--nt-cbd5e1)', lineHeight: 1.45 }}>
                  <strong style={{ color: 'var(--nt-ffffff)' }}>RECOrion AI Otonom Denetim Motoru:</strong> Tanımlayacağınız ünvan ve Sistem Rol Promptu, kaydettiğiniz anda RECOrion AI modeli tarafından incelenecek; sistem geneli ve sektör için faydalı görülenler otomatik olarak Ana Sistem Şablonuna eklenecektir.
                </div>
              </div>

              {/* ========================================================================= */}
              {/* 1. BAĞLI DEPARTMAN SEÇİMİ (Madde 2)                                      */}
              {/* ========================================================================= */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '700', color: 'var(--ac-38bdf8)', marginBottom: '6px' }}>
                  🏢 Bağlı Departman {departments.length > 0 && <span style={{ color: '#f43f5e' }}>*</span>}
                </label>
                {departments.length > 0 ? (
                  <select
                    required
                    value={titleForm.department_id || ''}
                    onChange={(e) => setTitleForm({ ...titleForm, department_id: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--sf-0a0d14)',
                      border: '1px solid rgba(56, 189, 248, 0.35)',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.875rem',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="">-- Şirket Departmanı Seçiniz --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        📁 {d.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div style={{
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: 'var(--ac-fca5a5)',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <AlertCircle size={15} />
                    <span>Henüz tanımlı bir departmanınız yok. Lütfen önce Departmanlar sekmesinden bir departman oluşturunuz.</span>
                  </div>
                )}
              </div>

              {/* ========================================================================= */}
              {/* 2. ÜNVAN SEÇİM / TANIMLAMA MODU (Madde 2)                                 */}
              {/* ========================================================================= */}
              {!editingTitle && (
                <div style={{ marginBottom: '18px' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', marginBottom: '8px' }}>
                    Ünvan Kaynağı ve Tanımlama Yöntemi:
                  </label>
                  <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <button
                      type="button"
                      onClick={() => {
                        setTitleCreationMode('TEMPLATE');
                        setTemplateSectorFilter('COMPANY_SECTORS');
                      }}
                      style={{
                        padding: '10px 14px',
                        borderRadius: '8px',
                        border: titleCreationMode === 'TEMPLATE' ? '1px solid var(--ac-38bdf8)' : '1px solid rgb(var(--rgb-ov) / 0.1)',
                        background: titleCreationMode === 'TEMPLATE' ? 'rgba(56, 189, 248, 0.18)' : 'rgb(var(--rgb-ov) / 0.03)',
                        color: titleCreationMode === 'TEMPLATE' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                        cursor: 'pointer',
                        fontSize: '0.825rem',
                        fontWeight: '700',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Tag size={15} color={titleCreationMode === 'TEMPLATE' ? 'var(--ac-38bdf8)' : 'var(--nt-94a3b8)'} />
                      <span>Sistem Tanımlamalarından Seçin</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setTitleCreationMode('CUSTOM');
                        setSelectedTemplate(null);
                      }}
                      style={{
                        padding: '10px 14px',
                        borderRadius: '8px',
                        border: titleCreationMode === 'CUSTOM' ? '1px solid var(--ac-c084fc)' : '1px solid rgb(var(--rgb-ov) / 0.1)',
                        background: titleCreationMode === 'CUSTOM' ? 'rgba(192, 132, 252, 0.18)' : 'rgb(var(--rgb-ov) / 0.03)',
                        color: titleCreationMode === 'CUSTOM' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                        cursor: 'pointer',
                        fontSize: '0.825rem',
                        fontWeight: '700',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Briefcase size={15} color={titleCreationMode === 'CUSTOM' ? 'var(--ac-c084fc)' : 'var(--nt-94a3b8)'} />
                      <span>Sektör Seçerek Kendi Ünvanını Yaz</span>
                    </button>
                  </div>
                </div>
              )}

              {/* ========================================================================= */}
              {/* MOD A: SÜPER YÖNETİCİ SEKTÖREL ÜNVANLARI (COMBOBOX)                        */}
              {/* ========================================================================= */}
              {!editingTitle && titleCreationMode === 'TEMPLATE' && (
                <div style={{
                  background: 'rgb(var(--rgb-sf-111827) / 0.8)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  borderRadius: '12px',
                  padding: '16px',
                  marginBottom: '22px'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '10px',
                    flexWrap: 'wrap',
                    gap: '8px'
                  }}>
                    <label style={{ fontSize: '0.825rem', fontWeight: '700', color: 'var(--ac-38bdf8)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Tag size={15} />
                      <span>Sektörel Şablon Ünvanları (Seçilince Rol Promptu Otomatik Yüklenir)</span>
                    </label>

                    {/* Şirket Sektörleri Filtre Butonları (Madde 2) */}
                    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                      {companySectorsList.length > 0 && (
                        <button
                          type="button"
                          onClick={() => {
                            setTemplateSectorFilter('COMPANY_SECTORS');
                            setTemplateFilterNaceOnly(true);
                          }}
                          style={{
                            background: templateSectorFilter === 'COMPANY_SECTORS' ? 'rgba(56, 189, 248, 0.25)' : 'rgb(var(--rgb-ov) / 0.05)',
                            border: templateSectorFilter === 'COMPANY_SECTORS' ? '1px solid var(--ac-38bdf8)' : '1px solid rgb(var(--rgb-ov) / 0.1)',
                            color: templateSectorFilter === 'COMPANY_SECTORS' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '0.7rem',
                            fontWeight: '700',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                        >
                          <Star size={11} color={templateSectorFilter === 'COMPANY_SECTORS' ? 'var(--ac-38bdf8)' : 'var(--nt-94a3b8)'} />
                          <span>🏢 Şirket Sektörlerim ({companySectorsList.join(', ')})</span>
                        </button>
                      )}

                      {companySectorsList.map((secName) => (
                        <button
                          key={secName}
                          type="button"
                          onClick={() => {
                            setTemplateSectorFilter(secName);
                            setTemplateFilterNaceOnly(false);
                          }}
                          style={{
                            background: templateSectorFilter === secName ? 'rgba(99, 102, 241, 0.35)' : 'rgb(var(--rgb-ov) / 0.04)',
                            border: templateSectorFilter === secName ? '1px solid var(--ac-818cf8)' : '1px solid rgb(var(--rgb-ov) / 0.08)',
                            color: templateSectorFilter === secName ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            fontSize: '0.7rem',
                            fontWeight: '600',
                            cursor: 'pointer'
                          }}
                        >
                          {secName}
                        </button>
                      ))}

                      <button
                        type="button"
                        onClick={() => {
                          setTemplateSectorFilter('ALL');
                          setTemplateFilterNaceOnly(false);
                        }}
                        style={{
                          background: templateSectorFilter === 'ALL' ? 'rgba(56, 189, 248, 0.25)' : 'rgb(var(--rgb-ov) / 0.05)',
                          border: templateSectorFilter === 'ALL' ? '1px solid var(--ac-38bdf8)' : '1px solid rgb(var(--rgb-ov) / 0.1)',
                          color: templateSectorFilter === 'ALL' ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '0.7rem',
                          fontWeight: '600',
                          cursor: 'pointer'
                        }}
                      >
                        Tüm Sektörler ({systemTemplates.length})
                      </button>
                    </div>
                  </div>

                  {/* Combobox Seçici Alanı */}
                  <div style={{ position: 'relative' }}>
                    <div
                      onClick={() => setTemplateComboboxOpen(!templateComboboxOpen)}
                      style={{
                        width: '100%',
                        background: 'var(--sf-0a0d14)',
                        border: '1px solid rgb(var(--rgb-ov) / 0.15)',
                        borderRadius: '8px',
                        padding: '10px 14px',
                        color: selectedTemplate ? 'var(--nt-ffffff)' : 'var(--nt-94a3b8)',
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                        {selectedTemplate ? (
                          <>
                            <span style={{ fontWeight: '700', color: 'var(--ac-38bdf8)' }}>{selectedTemplate.title}</span>
                            <span style={{ fontSize: '0.7rem', background: 'rgb(var(--rgb-ov) / 0.08)', padding: '2px 6px', borderRadius: '4px', color: 'var(--nt-94a3b8)' }}>
                              {selectedTemplate.category}
                            </span>
                            {selectedTemplate.is_sector_recommended && (
                              <span style={{ fontSize: '0.675rem', background: 'rgba(99, 102, 241, 0.3)', color: 'var(--ac-a5b4fc)', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                                📁 Şirket Sektörü
                              </span>
                            )}
                          </>
                        ) : (
                          <span>Şablon seçmek için tıklayın (Seçilince Rol Promptu otomatik yüklenecektir)...</span>
                        )}
                      </div>
                      <ChevronDown size={16} color="var(--nt-64748b)" />
                    </div>

                    {/* Combobox Açılır Liste */}
                    {templateComboboxOpen && (
                      <div style={{
                        position: 'absolute',
                        top: '105%',
                        left: 0,
                        right: 0,
                        background: 'var(--sf-0f1422)',
                        border: '1px solid rgba(56, 189, 248, 0.4)',
                        borderRadius: '8px',
                        boxShadow: '0 12px 30px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
                        zIndex: 20,
                        maxHeight: '260px',
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden'
                      }}>
                        {/* Arama Inputu */}
                        <div style={{ padding: '8px 10px', borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)' }}>
                          <input
                            type="text"
                            placeholder="Şablon ünvanlarda ara..."
                            value={templateSearchQuery}
                            onChange={(e) => setTemplateSearchQuery(e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            autoFocus
                            style={{
                              width: '100%',
                              background: 'var(--sf-070a10)',
                              border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                              borderRadius: '6px',
                              padding: '6px 10px',
                              color: 'var(--nt-ffffff)',
                              fontSize: '0.8rem',
                              outline: 'none'
                            }}
                          />
                        </div>

                        {/* Şablon Öğeleri */}
                        <div style={{ overflowY: 'auto', flex: 1 }}>
                          {filteredTemplates.map(tpl => (
                            <div
                              key={tpl.id}
                              onClick={() => handleSelectSystemTemplate(tpl)}
                              style={{
                                padding: '10px 14px',
                                borderBottom: '1px solid rgb(var(--rgb-ov) / 0.05)',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                transition: 'background 0.15s'
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.12)'}
                              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                            >
                              <div>
                                <div style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--nt-ffffff)' }}>
                                  {tpl.title}
                                </div>
                                <div style={{ fontSize: '0.72rem', color: 'var(--nt-94a3b8)' }}>
                                  {tpl.description ? tpl.description.slice(0, 60) + '...' : tpl.category}
                                </div>
                              </div>

                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                {tpl.is_sector_recommended && (
                                  <span style={{
                                    fontSize: '0.65rem',
                                    background: 'rgba(99, 102, 241, 0.3)',
                                    color: 'var(--ac-c7d2fe)',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    fontWeight: '700'
                                  }}>
                                    📁 Sektörünüz
                                  </span>
                                )}
                                <span style={{
                                  fontSize: '0.65rem',
                                  background: 'rgb(var(--rgb-ov) / 0.08)',
                                  color: 'var(--nt-cbd5e1)',
                                  padding: '2px 6px',
                                  borderRadius: '4px'
                                }}>
                                  {tpl.category}
                                </span>
                              </div>
                            </div>
                          ))}

                          {filteredTemplates.length === 0 && (
                            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--nt-94a3b8)', fontSize: '0.8rem' }}>
                              Eşleşen sistem şablonu bulunamadı. Filtreyi 'Tüm Sektörler' olarak değiştirebilirsiniz.
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--nt-64748b)', marginTop: '6px', display: 'block' }}>
                    * Şablon seçtiğinizde ünvan adı, sektörü ve <strong>Sistem Rol Promptu</strong> otomatik olarak aşağıdaki forma aktarılır.
                  </span>
                </div>
              )}

              {/* ========================================================================= */}
              {/* 3. ÜNVAN ADI & SEKTÖREL KATEGORİ (Madde 2: Sektör seçerek kendi ünvanını yazar) */}
              {/* ========================================================================= */}
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                    Ünvan Adı <span style={{ color: '#f43f5e' }}>*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Örn: Kıdemli Fullstack Mimarı, Kumaş Kalite Kontrol Mimarı..."
                    value={titleForm.title}
                    onChange={(e) => setTitleForm({ ...titleForm, title: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--sf-0a0d14)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.875rem',
                      outline: 'none'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                    Sektör / Kategori
                  </label>
                  <select
                    value={titleForm.category}
                    onChange={(e) => setTitleForm({ ...titleForm, category: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--sf-0a0d14)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    {/* Şirketin Tanımlı Sektörleri (Öncelikli) */}
                    {companySectorsList.length > 0 && (
                      <optgroup label="🏢 Şirketinizin Sektörleri">
                        {companySectorsList.map((sec) => (
                          <option key={sec} value={sec}>
                            ⭐ {sec}
                          </option>
                        ))}
                      </optgroup>
                    )}
                    <optgroup label="Diğer Sektörler & Kategoriler">
                      <option value="TEKSTIL">TEKSTIL</option>
                      <option value="YAZILIM">YAZILIM</option>
                      <option value="ANALIZ">ANALİZ</option>
                      <option value="FINANS">FİNANS</option>
                      <option value="HUKUK">HUKUK</option>
                      <option value="TASARIM">TASARIM</option>
                      <option value="OPERASYON">OPERASYON</option>
                      <option value="URETIM">ÜRETİM / İMALAT</option>
                      <option value="GENEL">GENEL</option>
                    </optgroup>
                  </select>
                </div>
              </div>

              {/* Ünvan Açıklaması */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                  Ünvan Açıklaması / Görev Tanımı
                </label>
                <input
                  type="text"
                  placeholder="Bu unvanın şirket içerisindeki temel sorumluluğu..."
                  value={titleForm.description}
                  onChange={(e) => setTitleForm({ ...titleForm, description: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--sf-0a0d14)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                    borderRadius: '8px',
                    padding: '9px 14px',
                    color: 'var(--nt-ffffff)',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
              </div>

              {/* Model Seçimi (Müşteri Paketindeki Modeller) & Otonomi Seviyesi (Madde 2) */}
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <label style={{ fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)' }}>
                      Önerilen EVREN AI Modeli
                    </label>
                    <span style={{ fontSize: '0.7rem', color: 'var(--ac-38bdf8)', background: 'rgba(56, 189, 248, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                      Paket Kapsamında
                    </span>
                  </div>
                  <select
                    value={titleForm.recommended_model_code}
                    onChange={(e) => setTitleForm({ ...titleForm, recommended_model_code: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--sf-0a0d14)',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      borderRadius: '8px',
                      padding: '9px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.825rem',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    {availableModels && availableModels.length > 0 ? (
                      availableModels.map((m) => (
                        <option key={m.id || m.model_code} value={m.model_code}>
                          {m.display_name} ({m.model_code})
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="glm-5.3">glm-5.3 (Sistem Mimarı & İleri Muhakeme)</option>
                        <option value="deepseek-v4.1-flash">deepseek-v4.1-flash (Kıdemli Kodlama & Test)</option>
                        <option value="mimo-v2.6-pro">mimo-v2.6-pro (Stratejik Planlama & Analiz)</option>
                        <option value="deepseek-v4-flash">deepseek-v4-flash (Hızlı Kod & QA)</option>
                        <option value="qwen3.8-flash-next">qwen3.8-flash-next (Operasyonel Asistan)</option>
                        <option value="gemma-4-31b">gemma-4-31b (Dokümantasyon & PR)</option>
                        <option value="qwen3-vl-30b">qwen3-vl-30b (Vision & Tasarım)</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                    Otonomi Seviyesi
                  </label>
                  <select
                    value={titleForm.autonomy_level}
                    onChange={(e) => setTitleForm({ ...titleForm, autonomy_level: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--sf-0a0d14)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '9px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.825rem',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="L1">L1 - Standart (Her adımda onay)</option>
                    <option value="L2">L2 - Yarı Otonom (Kritik adımlarda onay)</option>
                    <option value="L3">L3 - Tam Otonom (Yalnızca nihai onay)</option>
                  </select>
                </div>
              </div>

              {/* SİSTEM ROL PROMPTU (AI İle Yazdırılabilir veya Kullanıcı Kendisi Yazabilir - Madde 2) */}
              <div style={{ marginBottom: '18px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                  <label style={{ fontSize: '0.825rem', fontWeight: '700', color: 'var(--ac-c084fc)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={14} />
                    <span>Sistem Rol Promptu (Persona & Talimatlar) <span style={{ color: '#f43f5e' }}>*</span></span>
                  </label>

                  {/* AI ile Rol Promptu Yazdır Butonu (Madde 2) */}
                  <button
                    type="button"
                    onClick={handleGenerateTitlePrompt}
                    disabled={isGeneratingTitlePrompt}
                    style={{
                      background: isGeneratingTitlePrompt
                        ? 'rgba(168, 85, 247, 0.2)'
                        : 'linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(56, 189, 248, 0.3))',
                      border: '1px solid rgba(168, 85, 247, 0.5)',
                      color: 'var(--nt-f8fafc)',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: '700',
                      cursor: isGeneratingTitlePrompt ? 'wait' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      boxShadow: '0 2px 8px rgba(168, 85, 247, 0.2)',
                      transition: 'all 0.15s ease'
                    }}
                    title="Seçili EVREN AI Modeli ile bu ünvana özel Sistem Rol Promptu oluştur"
                  >
                    <Sparkles size={13} color={isGeneratingTitlePrompt ? 'var(--nt-e2e8f0)' : 'var(--ac-d8b4fe)'} />
                    <span>
                      {isGeneratingTitlePrompt
                        ? 'AI Promptu Yazıyor...'
                        : `✨ Seçili Model (${titleForm.recommended_model_code || 'AI'}) ile Prompt Yazdır`}
                    </span>
                  </button>
                </div>

                <textarea
                  placeholder="Ajanın veya personelin kimliğini, görev tanımını, kalite kapılarını ve çıktı standartlarını tanımlayan Sistem Rol Promptunu buraya yazınız veya yukarıdaki AI butonuyla otomatik yazdırınız..."
                  value={titleForm.base_role_prompt}
                  onChange={(e) => setTitleForm({ ...titleForm, base_role_prompt: e.target.value })}
                  rows={8}
                  style={{
                    width: '100%',
                    background: 'var(--sf-070a10)',
                    border: '1px solid rgba(168, 85, 247, 0.35)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                    color: 'var(--nt-f8fafc)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    lineHeight: 1.5,
                    outline: 'none',
                    resize: 'vertical'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--nt-94a3b8)', marginTop: '4px', display: 'block' }}>
                  * İster seçili AI modeliyle otomatik yazdırın, ister şablondan yükleyin, isterseniz kendiniz dilediğiniz gibi düzenleyin.
                </span>
              </div>

              {/* Gerekli Yetenekler */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                  Gerekli Yetenekler (Virgülle ayırınız)
                </label>
                <input
                  type="text"
                  placeholder="Örn: Python, React, PostgreSQL, Güvenlik Testi..."
                  value={titleForm.required_skills}
                  onChange={(e) => setTitleForm({ ...titleForm, required_skills: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--sf-0a0d14)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                    borderRadius: '8px',
                    padding: '9px 14px',
                    color: 'var(--nt-ffffff)',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
              </div>

              {/* Butonlar */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                gap: '12px',
                borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                paddingTop: '18px'
              }}>
                <button
                  type="button"
                  onClick={() => setIsTitleModalOpen(false)}
                  style={{
                    background: 'rgb(var(--rgb-ov) / 0.06)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                    color: 'var(--nt-cbd5e1)',
                    padding: '9px 18px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  İptal
                </button>

                <button
                  type="submit"
                  disabled={isSavingTitle}
                  style={{
                    background: 'linear-gradient(135deg, #7134e2 0%, #146ceb 100%)',
                    border: 'none',
                    color: '#ffffff',
                    padding: '9px 24px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '700',
                    cursor: isSavingTitle ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 16px rgba(113, 52, 226, 0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    opacity: isSavingTitle ? 0.7 : 1
                  }}
                >
                  {isSavingTitle ? (
                    <>
                      <RefreshCw size={15} className="spin" />
                      <span>RECOrion AI İnceliyor & Kaydediyor...</span>
                    </>
                  ) : (
                    <>
                      <Check size={16} />
                      <span>{editingTitle ? 'Değişiklikleri Kaydet' : 'Ünvanı Tanımla & AI Kontrolünden Geçir'}</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SİLME ONAY MODALI (Departman) */}
      {/* ========================================================================= */}
      {deptToDelete && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1100,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-131826)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '440px',
            padding: '24px',
            textAlign: 'center',
            boxShadow: '0 20px 50px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))'
          }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto'
            }}>
              <Trash2 size={26} color="#ef4444" />
            </div>

            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--nt-ffffff)', marginBottom: '8px' }}>
              Departmanı Silmek İstiyor musunuz?
            </h3>

            <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', lineHeight: 1.5, marginBottom: '22px' }}>
              <strong style={{ color: 'var(--nt-f8fafc)' }}>'{deptToDelete.name}'</strong> departmanı silinecektir.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
              <button
                onClick={() => setDeptToDelete(null)}
                style={{
                  background: 'rgb(var(--rgb-ov) / 0.08)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                  color: 'var(--nt-cbd5e1)',
                  padding: '9px 18px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Vazgeç
              </button>

              <button
                onClick={confirmDeleteDept}
                disabled={isDeletingDept}
                style={{
                  background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  border: 'none',
                  color: '#ffffff',
                  padding: '9px 22px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  cursor: isDeletingDept ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {isDeletingDept ? 'Siliniyor...' : 'Evet, Sil'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SİLME ONAY MODALI (Ünvan) */}
      {/* ========================================================================= */}
      {titleToDelete && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1100,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-131826)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '440px',
            padding: '24px',
            textAlign: 'center',
            boxShadow: '0 20px 50px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))'
          }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto'
            }}>
              <Trash2 size={26} color="#ef4444" />
            </div>

            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--nt-ffffff)', marginBottom: '8px' }}>
              Ünvanı Silmek İstiyor musunuz?
            </h3>

            <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', lineHeight: 1.5, marginBottom: '22px' }}>
              <strong style={{ color: 'var(--nt-f8fafc)' }}>'{titleToDelete.title}'</strong> ünvanı silinecektir. Bu ünvana atanmış AI personelleri veya çalışanların ünvan bağı boşa çıkacaktır.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
              <button
                onClick={() => setTitleToDelete(null)}
                style={{
                  background: 'rgb(var(--rgb-ov) / 0.08)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                  color: 'var(--nt-cbd5e1)',
                  padding: '9px 18px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Vazgeç
              </button>

              <button
                onClick={confirmDeleteTitle}
                disabled={isDeletingTitle}
                style={{
                  background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  border: 'none',
                  color: '#ffffff',
                  padding: '9px 22px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  cursor: isDeletingTitle ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {isDeletingTitle ? 'Siliniyor...' : 'Evet, Sil'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: AI AJAN İŞE ALIM / TANIMLAMA (Madde 3) */}
      {/* ========================================================================= */}
      {isAgentModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-101524)',
            border: '1px solid rgba(16, 185, 129, 0.45)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '680px',
            maxHeight: '90vh',
            boxShadow: '0 20px 60px rgb(var(--rgb-shade) / calc(0.9 * var(--shade-k))), 0 0 35px rgba(16, 185, 129, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            animation: 'fadeIn 0.2s ease-out'
          }}>
            {/* Modal Başlığı */}
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(20, 108, 235, 0.15) 100%)',
              flexShrink: 0
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '9px',
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Bot size={20} color="#ffffff" />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: '800', margin: 0, color: 'var(--nt-ffffff)' }}>
                    {editingAgent ? 'AI Ajan Bilgilerini Düzenle' : 'Yeni AI Ajan İşe Alım / Tanımlama'}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                    Madde 3: Ajan Adı, LLM Modeli, Şirket Ünvanı ve İşe Alım Tarihi
                  </span>
                </div>
              </div>

              <button
                onClick={() => setIsAgentModalOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--nt-94a3b8)',
                  cursor: 'pointer',
                  padding: '4px'
                }}
              >
                <XCircle size={20} />
              </button>
            </div>

            {/* Form Gövdesi */}
            <form onSubmit={handleSaveAIAgent} style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              {/* Madde 5: Paket Kotası Aşım Uyarısı */}
              {!editingAgent && agentQuota.is_limit_reached && (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.18)',
                  border: '1px solid rgba(239, 68, 68, 0.45)',
                  borderRadius: '8px',
                  padding: '12px 14px',
                  color: 'var(--ac-fca5a5)',
                  fontSize: '0.825rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  marginBottom: '18px'
                }}>
                  <AlertCircle size={18} color="#ef4444" style={{ flexShrink: 0 }} />
                  <div>
                    <strong style={{ color: 'var(--nt-ffffff)' }}>Paket AI Ajan Kotanız Dolmuştur:</strong> Satın aldığınız '{agentQuota.plan_name || 'Mevcut'}' paketinin azami sınırı {agentQuota.max_agents} ajandır ({agentQuota.active_agents} aktif ajanınız bulunuyor). Yeni ajan eklemek için paketinizi yükseltin veya mevcut bir ajanı pasife çekin.
                  </div>
                </div>
              )}

              {agentFormError && (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  color: 'var(--ac-f87171)',
                  fontSize: '0.825rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '18px'
                }}>
                  <AlertCircle size={16} />
                  <span>{agentFormError}</span>
                </div>
              )}

              {/* 1. AI Ajan Adı */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                  AI Ajan Adı <span style={{ color: '#f43f5e' }}>*</span>
                </label>
                <input
                  type="text"
                  placeholder="Örn: Orion-Dev1, Veri Mimarı Ajanı, Finans Analisti Zehra..."
                  value={agentForm.display_name}
                  onChange={(e) => setAgentForm({ ...agentForm, display_name: e.target.value })}
                  autoFocus
                  style={{
                    width: '100%',
                    background: 'var(--sf-0a0d14)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    color: 'var(--nt-ffffff)',
                    fontSize: '0.9rem',
                    outline: 'none'
                  }}
                />
              </div>

              {/* 2. Şirket Ünvanı ve Departman Seçimi */}
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--ac-38bdf8)', marginBottom: '6px' }}>
                    Şirket Ünvanı (Madde 2'den Seçim) <span style={{ color: '#f43f5e' }}>*</span>
                  </label>
                  <select
                    value={agentForm.job_title_id}
                    onChange={(e) => handleAgentJobTitleChange(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--sf-0a0d14)',
                      border: '1px solid rgba(56, 189, 248, 0.4)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none'
                    }}
                  >
                    <option value="">-- Ünvan Seçiniz --</option>
                    {jobTitles.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.title} ({t.category})
                      </option>
                    ))}
                  </select>
                  <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', marginTop: '4px', display: 'block' }}>
                    * Ünvan seçildiğinde önerilen LLM modeli ve Sistem Promptu otomatik aktarılır.
                  </span>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <label style={{ fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-94a3b8)' }}>
                      Bağlı Departman
                    </label>
                    <span style={{ fontSize: '0.675rem', color: 'var(--ac-38bdf8)', background: 'rgba(56, 189, 248, 0.1)', padding: '2px 6px', borderRadius: '4px', fontWeight: '700' }}>
                      🔒 Ünvandan Otomatik Gelir
                    </span>
                  </div>
                  <select
                    value={agentForm.department_id || ''}
                    disabled={true}
                    style={{
                      width: '100%',
                      background: 'rgb(var(--rgb-sf-0a0d14) / 0.75)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: agentForm.department_id ? 'var(--ac-38bdf8)' : 'var(--nt-64748b)',
                      fontSize: '0.85rem',
                      outline: 'none',
                      cursor: 'not-allowed',
                      fontWeight: agentForm.department_id ? '700' : 'normal'
                    }}
                  >
                    <option value="">-- Ünvana Atanmış Departman Yok --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        🏢 {d.name}
                      </option>
                    ))}
                  </select>
                  <span style={{ fontSize: '0.7rem', color: 'var(--nt-64748b)', marginTop: '4px', display: 'block' }}>
                    * Ünvan doğrudan bir departmana bağlı olduğu için değiştirilemez.
                  </span>
                </div>
              </div>

              {/* 3. LLM Modeli ve Otonomi Seviyesi (Madde 4: Ünvandan otomatik gelir, değiştirilebilir) */}
              <div className="ui-grid-2" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px', marginBottom: '16px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <label style={{ fontSize: '0.825rem', fontWeight: '600', color: 'var(--ac-c084fc)' }}>
                      AI Ajan LLM Modeli <span style={{ color: '#f43f5e' }}>*</span>
                    </label>
                    <span style={{ fontSize: '0.7rem', color: 'var(--ac-38bdf8)', background: 'rgba(56, 189, 248, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                      Değiştirilebilir
                    </span>
                  </div>
                  <select
                    value={agentForm.model_code}
                    onChange={(e) => setAgentForm({ ...agentForm, model_code: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--sf-0a0d14)',
                      border: '1px solid rgba(168, 85, 247, 0.4)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    {availableModels && availableModels.length > 0 ? (
                      availableModels.map((m) => (
                        <option key={m.id || m.model_code} value={m.model_code}>
                          {m.display_name} ({m.model_code})
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="glm-5.3">GLM 5.3 (Sistem Mimarı & İleri Muhakeme)</option>
                        <option value="deepseek-v4.1-flash">DeepSeek V4.1 Flash (Kıdemli Kodlama & Test)</option>
                        <option value="mimo-v2.6-pro">MIMO V2.6 Pro (İş Analisti & Muhakeme)</option>
                        <option value="deepseek-v4-flash">DeepSeek V4 Flash (Hızlı Kod & QA)</option>
                        <option value="qwen3.8-flash-next">Qwen3.8 Flash Next (Operasyonel Asistan)</option>
                        <option value="gemma-4-31b">Gemma 4 31B (Dokümantasyon & PR)</option>
                        <option value="qwen3-vl-30b">Qwen3 VL 30B (Vision & Tasarım)</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <label style={{ fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)' }}>
                      Otonomi Seviyesi
                    </label>
                    <span style={{ fontSize: '0.7rem', color: 'var(--nt-94a3b8)' }}>
                      Değiştirilebilir
                    </span>
                  </div>
                  <select
                    value={agentForm.autonomy_level}
                    onChange={(e) => setAgentForm({ ...agentForm, autonomy_level: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--sf-0a0d14)',
                      border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                      borderRadius: '8px',
                      padding: '10px 12px',
                      color: 'var(--nt-ffffff)',
                      fontSize: '0.85rem',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="L1">L1 - Standart (Onaylı)</option>
                    <option value="L2">L2 - Yarı Otonom</option>
                    <option value="L3">L3 - Tam Otonom</option>
                  </select>
                </div>
              </div>

              {/* 4. İşe Alım Tarihi (Tanımlama Tarihi) */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: '#10b981', marginBottom: '6px' }}>
                  📅 AI Ajan İşe Alım Tarihi (Tanımlama Tarihi) <span style={{ color: '#f43f5e' }}>*</span>
                </label>
                <input
                  type="date"
                  value={agentForm.hired_at}
                  onChange={(e) => setAgentForm({ ...agentForm, hired_at: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--sf-0a0d14)',
                    border: '1px solid rgba(16, 185, 129, 0.35)',
                    borderRadius: '8px',
                    padding: '9px 14px',
                    color: 'var(--nt-ffffff)',
                    fontSize: '0.875rem',
                    outline: 'none'
                  }}
                />
              </div>

              {/* 5. AI Ajan Açıklaması */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                  AI Ajan Açıklaması / Özel Görev Notu
                </label>
                <textarea
                  placeholder="Bu AI ajanın şirket operasyonundaki özel rolünü ve görev kapsamını belirtiniz..."
                  value={agentForm.description}
                  onChange={(e) => setAgentForm({ ...agentForm, description: e.target.value })}
                  rows={2}
                  style={{
                    width: '100%',
                    background: 'var(--sf-0a0d14)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                    borderRadius: '8px',
                    padding: '9px 14px',
                    color: 'var(--nt-ffffff)',
                    fontSize: '0.85rem',
                    outline: 'none',
                    lineHeight: 1.45,
                    resize: 'vertical'
                  }}
                />
              </div>

              {/* 6. Sistem Rol Promptu & Sektör + Ünvan Deep Search Motoru */}
              <div style={{ marginBottom: '18px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                  <label style={{ fontSize: '0.825rem', fontWeight: '700', color: 'var(--ac-c084fc)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={14} />
                    <span>Sistem Rol Promptu (Persona & Talimatlar) <span style={{ color: '#f43f5e' }}>*</span></span>
                  </label>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    {/* Sektör & Ünvan Çift Odaklı Deep Search Eğitimi Butonu */}
                    <button
                      type="button"
                      onClick={handleDeepSearchSectorAndTitle}
                      disabled={isDeepSearchingSectorTitle || isGeneratingAgentPrompt}
                      style={{
                        background: isDeepSearchingSectorTitle
                          ? 'rgba(59, 130, 246, 0.25)'
                          : 'linear-gradient(135deg, rgba(59, 130, 246, 0.35) 0%, rgba(147, 51, 234, 0.35) 100%)',
                        border: '1px solid rgba(59, 130, 246, 0.6)',
                        color: 'var(--nt-ffffff)',
                        padding: '6px 14px',
                        borderRadius: '7px',
                        fontSize: '0.75rem',
                        fontWeight: '700',
                        cursor: (isDeepSearchingSectorTitle || isGeneratingAgentPrompt) ? 'wait' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        boxShadow: '0 2px 10px rgba(59, 130, 246, 0.25)',
                        transition: 'all 0.15s ease'
                      }}
                      title="Şirketin sektörü ve bu sektörde bu ünvanın tam olarak ne iş yaptığı üzerine internette derinlemesine araştırma yap, ajanı eğit ve zengin sistem promptu oluştur"
                    >
                      {isDeepSearchingSectorTitle ? (
                        <RefreshCw size={13} color="var(--ac-93c5fd)" style={{ animation: 'spin 1s linear infinite' }} />
                      ) : (
                        <Globe size={13} color="var(--ac-60a5fa)" />
                      )}
                      <span>
                        {isDeepSearchingSectorTitle
                          ? 'Sektör & Ünvan Deep Search Yapılıyor...'
                          : '🌐 Sektör & Ünvan Deep Search ile Eğit ve Prompt Yaz'}
                      </span>
                    </button>

                    {/* AI ile Hızlı Prompt Yazdır Butonu */}
                    <button
                      type="button"
                      onClick={handleGenerateAgentPrompt}
                      disabled={isGeneratingAgentPrompt || isDeepSearchingSectorTitle}
                      style={{
                        background: isGeneratingAgentPrompt
                          ? 'rgba(168, 85, 247, 0.2)'
                          : 'rgb(var(--rgb-ov) / 0.05)',
                        border: '1px solid rgba(168, 85, 247, 0.4)',
                        color: 'var(--ac-d8b4fe)',
                        padding: '6px 12px',
                        borderRadius: '7px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        cursor: (isGeneratingAgentPrompt || isDeepSearchingSectorTitle) ? 'wait' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        transition: 'all 0.15s ease'
                      }}
                      title="Seçili model ile hızlı prompt taslağı üretir"
                    >
                      <Sparkles size={12} color="var(--ac-c084fc)" />
                      <span>
                        {isGeneratingAgentPrompt ? 'Yazıyor...' : '✨ Hızlı Prompt'}
                      </span>
                    </button>
                  </div>
                </div>

                {/* Deep Search Çalışırken Canlı Durum Kartı */}
                {isDeepSearchingSectorTitle && (
                  <div style={{
                    marginBottom: '12px',
                    background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.25) 0%, rgba(88, 28, 135, 0.25) 100%)',
                    border: '1px solid rgba(59, 130, 246, 0.4)',
                    borderRadius: '10px',
                    padding: '12px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <RefreshCw size={18} color="var(--ac-60a5fa)" style={{ animation: 'spin 1.2s linear infinite' }} />
                      <div>
                        <div style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--ac-93c5fd)' }}>
                          Şirket Sektörü & Ünvan Dinamikleri İnternette Derinlemesine Taranıyor...
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--nt-cbd5e1)' }}>
                          1) Şirketin sektörel mevzuat ve pazar dinamikleri araştırılıyor • 2) Sektörde bu ünvanın tam olarak ne iş yaptığı, görev ve süreçleri taranıyor • 3) AI personeli için uzmanlık kuralları ve sistem rol yönergesi sentezleniyor.
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Deep Search Başarıyla Tamamlandığında Rapor Kartı */}
                {deepSearchSectorTitleResult && !isDeepSearchingSectorTitle && (
                  <div style={{
                    marginBottom: '14px',
                    background: 'rgb(var(--rgb-sf-0f172a) / 0.85)',
                    border: '1px solid rgba(59, 130, 246, 0.45)',
                    borderRadius: '12px',
                    padding: '14px 16px',
                    boxShadow: '0 4px 16px rgb(var(--rgb-shade) / calc(0.3 * var(--shade-k)))'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)', paddingBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <CheckCircle2 size={16} color="var(--ac-4ade80)" />
                        <span style={{ fontSize: '0.825rem', fontWeight: '700', color: 'var(--nt-f8fafc)' }}>
                          Sektör & Ünvan Deep Search Analiz Raporu
                        </span>
                      </div>
                      <span style={{ fontSize: '0.7rem', color: 'var(--ac-93c5fd)', background: 'rgba(59, 130, 246, 0.15)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                        {deepSearchSectorTitleResult.learnings_count || 0} Bilgi Maddesi Hazır
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))', gap: '10px', marginBottom: '10px' }}>
                      {/* Sektör Analiz Özeti */}
                      <div style={{ background: 'rgba(59, 130, 246, 0.06)', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: '8px', padding: '10px 12px' }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--ac-60a5fa)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Building size={12} />
                          <span>ŞİRKET SEKTÖRÜ: {deepSearchSectorTitleResult.sector_name}</span>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', margin: 0, lineHeight: 1.45 }}>
                          {deepSearchSectorTitleResult.sector_summary || 'Sektör dinamikleri analiz edildi.'}
                        </p>
                      </div>

                      {/* Ünvan Görev ve Süreç Özeti */}
                      <div style={{ background: 'rgba(168, 85, 247, 0.06)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: '8px', padding: '10px 12px' }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--ac-c084fc)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Briefcase size={12} />
                          <span>SEKTÖREL ÜNVAN: {deepSearchSectorTitleResult.job_title_name}</span>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', margin: 0, lineHeight: 1.45 }}>
                          {deepSearchSectorTitleResult.job_title_summary || 'Ünvanın görev ve süreçleri analiz edildi.'}
                        </p>
                      </div>
                    </div>

                    {/* Çıkarılan Öğrenim Maddeleri & Kaynaklar */}
                    {deepSearchSectorTitleResult.learnings && deepSearchSectorTitleResult.learnings.length > 0 && (
                      <div style={{ marginBottom: '10px' }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: '600', color: 'var(--nt-94a3b8)', marginBottom: '6px' }}>
                          Tespit Edilen Temel Yetkinlik & Kural Maddeleri:
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {deepSearchSectorTitleResult.learnings.slice(0, 4).map((l, idx) => (
                            <span key={idx} style={{
                              fontSize: '0.68rem',
                              background: 'rgb(var(--rgb-ov) / 0.05)',
                              border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                              color: 'var(--nt-e2e8f0)',
                              padding: '3px 8px',
                              borderRadius: '4px',
                              maxWidth: '100%',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }} title={l.content || l.summary}>
                              • {l.title || l.summary || `Kural ${idx + 1}`}
                            </span>
                          ))}
                          {deepSearchSectorTitleResult.learnings.length > 4 && (
                            <span style={{ fontSize: '0.68rem', color: 'var(--nt-94a3b8)', padding: '3px 6px' }}>
                              +{deepSearchSectorTitleResult.learnings.length - 4} madde daha
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Bilgilendirme Notu */}
                    <div style={{
                      fontSize: '0.72rem',
                      color: 'var(--ac-4ade80)',
                      background: 'rgba(34, 197, 94, 0.1)',
                      border: '1px solid rgba(34, 197, 94, 0.25)',
                      padding: '6px 10px',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}>
                      <Info size={13} color="var(--ac-4ade80)" />
                      <span>
                        Bu AI Ajanı kaydedildiğinde tüm bu kurallar ajanın kolektif hafızasına (Qdrant & MemoryItem) ve uzmanlık dokümanlarına otomatik kaydedilecektir.
                      </span>
                    </div>
                  </div>
                )}

                <textarea
                  placeholder="Ajanın sistem talimatı... Seçilen ünvandan otomatik devralınır veya yukarıdaki 'Sektör & Ünvan Deep Search' butonu ile internette araştırılarak zenginleştirilebilir."
                  value={agentForm.system_prompt}
                  onChange={(e) => setAgentForm({ ...agentForm, system_prompt: e.target.value })}
                  rows={6}
                  style={{
                    width: '100%',
                    background: 'var(--sf-070a10)',
                    border: '1px solid rgba(168, 85, 247, 0.35)',
                    borderRadius: '8px',
                    padding: '12px 14px',
                    color: 'var(--nt-f8fafc)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    lineHeight: 1.5,
                    outline: 'none',
                    resize: 'vertical'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--nt-94a3b8)', marginTop: '4px', display: 'block' }}>
                  * Ünvandan otomatik yüklenir. 'Sektör & Ünvan Deep Search' butonu ile şirketin sektörü ve ünvanın ne iş yaptığı internette araştırılarak bu yönerge otomatik güncellenebilir.
                </span>
              </div>

              {/* Butonlar */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                gap: '12px',
                borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
                paddingTop: '18px'
              }}>
                <button
                  type="button"
                  onClick={() => setIsAgentModalOpen(false)}
                  style={{
                    background: 'rgb(var(--rgb-ov) / 0.06)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                    color: 'var(--nt-cbd5e1)',
                    padding: '9px 18px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  İptal
                </button>

                <button
                  type="submit"
                  disabled={isSavingAgent || (!editingAgent && agentQuota.is_limit_reached)}
                  style={{
                    background: (!editingAgent && agentQuota.is_limit_reached)
                      ? 'rgb(var(--rgb-ov) / 0.08)'
                      : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    border: (!editingAgent && agentQuota.is_limit_reached) ? '1px solid rgb(var(--rgb-ov) / 0.12)' : 'none',
                    color: (!editingAgent && agentQuota.is_limit_reached) ? 'var(--nt-94a3b8)' : '#ffffff',
                    padding: '9px 24px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: '700',
                    cursor: (isSavingAgent || (!editingAgent && agentQuota.is_limit_reached)) ? 'not-allowed' : 'pointer',
                    boxShadow: (!editingAgent && agentQuota.is_limit_reached) ? 'none' : '0 4px 16px rgba(16, 185, 129, 0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    opacity: (isSavingAgent || (!editingAgent && agentQuota.is_limit_reached)) ? 0.6 : 1
                  }}
                >
                  {isSavingAgent ? (
                    <>
                      <RefreshCw size={15} className="spin" />
                      <span>Kaydediliyor...</span>
                    </>
                  ) : (
                    <>
                      <Check size={16} />
                      <span>{editingAgent ? 'Değişiklikleri Kaydet' : 'İşe Alımı Tamamla & Kadroya Ekle'}</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: AI AJAN İŞTEN ÇIKARMA / PASİFE ÇEKME (Madde 3) */}
      {/* ========================================================================= */}
      {agentToTerminate && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1100,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-131826)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '480px',
            padding: '26px',
            boxShadow: '0 20px 50px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))'
          }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto'
            }}>
              <UserX size={26} color="#ef4444" />
            </div>

            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--nt-ffffff)', marginBottom: '6px', textAlign: 'center' }}>
              AI Ajanını İşten Çıkar / Pasife Al
            </h3>

            <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', lineHeight: 1.5, marginBottom: '20px', textAlign: 'center' }}>
              <strong style={{ color: 'var(--nt-f8fafc)' }}>'{agentToTerminate.display_name}'</strong> adlı AI ajanının şirket içindeki aktif görevi sonlandırılacaktır.
            </p>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                🚪 İşten Çıkma / Pasife Çekilme Tarihi <span style={{ color: '#f43f5e' }}>*</span>
              </label>
              <input
                type="date"
                value={terminationDate}
                onChange={(e) => setTerminationDate(e.target.value)}
                style={{
                  width: '100%',
                  background: 'var(--sf-0a0d14)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  borderRadius: '8px',
                  padding: '9px 14px',
                  color: 'var(--nt-ffffff)',
                  fontSize: '0.875rem',
                  outline: 'none'
                }}
              />
            </div>

            <div style={{ marginBottom: '22px' }}>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: '600', color: 'var(--nt-e2e8f0)', marginBottom: '6px' }}>
                İşten Çıkarma / Pasife Çekme Nedeni
              </label>
              <textarea
                placeholder="Örn: Proje tamamlandı, yeni model mimarisine geçildi, operasyonel ihtiyaç sona erdi..."
                value={terminationReason}
                onChange={(e) => setTerminationReason(e.target.value)}
                rows={2}
                style={{
                  width: '100%',
                  background: 'var(--sf-0a0d14)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                  borderRadius: '8px',
                  padding: '9px 12px',
                  color: 'var(--nt-ffffff)',
                  fontSize: '0.825rem',
                  outline: 'none',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
              <button
                type="button"
                onClick={() => setAgentToTerminate(null)}
                style={{
                  background: 'rgb(var(--rgb-ov) / 0.08)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                  color: 'var(--nt-cbd5e1)',
                  padding: '9px 18px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Vazgeç
              </button>

              <button
                type="button"
                onClick={confirmTerminateAgent}
                disabled={isTerminatingAgent}
                style={{
                  background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  border: 'none',
                  color: '#ffffff',
                  padding: '9px 22px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  cursor: isTerminatingAgent ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {isTerminatingAgent ? 'İşleniyor...' : 'Evet, İşten Çıkar ve Pasife Al'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SİLME ONAY MODALI (AI Ajan) */}
      {/* ========================================================================= */}
      {agentToDelete && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1100,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-131826)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '440px',
            padding: '24px',
            textAlign: 'center',
            boxShadow: '0 20px 50px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))'
          }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto'
            }}>
              <Trash2 size={26} color="#ef4444" />
            </div>

            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--nt-ffffff)', marginBottom: '8px' }}>
              AI Ajanını Silmek İstiyor musunuz?
            </h3>

            <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', lineHeight: 1.5, marginBottom: '22px' }}>
              <strong style={{ color: 'var(--nt-f8fafc)' }}>'{agentToDelete.display_name}'</strong> AI ajanı sistemden kalıcı olarak silinecektir.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
              <button
                onClick={() => setAgentToDelete(null)}
                style={{
                  background: 'rgb(var(--rgb-ov) / 0.08)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                  color: 'var(--nt-cbd5e1)',
                  padding: '9px 18px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Vazgeç
              </button>

              <button
                onClick={confirmDeleteAgent}
                disabled={isDeletingAgent}
                style={{
                  background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  border: 'none',
                  color: '#ffffff',
                  padding: '9px 22px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  cursor: isDeletingAgent ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {isDeletingAgent ? 'Siliniyor...' : 'Evet, Sil'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: AI AJANI UZMANLIK DOKÜMANLARI & RAG HAFIZA YÖNETİMİ (Madde 2)       */}
      {/* ========================================================================= */}
      {isDocsModalOpen && selectedAgentForDocs && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1100,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-111827)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '20px',
            width: '100%',
            maxWidth: '820px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 25px 60px rgb(var(--rgb-shade) / calc(0.9 * var(--shade-k)))',
            overflow: 'hidden'
          }}>
            {/* Modal Başlık */}
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid rgb(var(--rgb-ov) / 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgb(var(--rgb-ov) / 0.02)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(139, 92, 246, 0.25) 100%)',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <BookOpen size={22} color="var(--ac-60a5fa)" />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--nt-ffffff)', margin: 0 }}>
                      {selectedAgentForDocs.display_name} — Uzmanlık Dokümanları
                    </h3>
                    <span style={{
                      background: 'rgba(59, 130, 246, 0.15)',
                      color: 'var(--ac-93c5fd)',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      fontSize: '0.72rem',
                      fontWeight: '700',
                      padding: '2px 8px',
                      borderRadius: '6px'
                    }}>
                      RAG / Kolektif Hafıza
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--nt-94a3b8)', margin: '4px 0 0 0' }}>
                    {selectedAgentForDocs.job_title_name ? `${selectedAgentForDocs.job_title_name} • ` : ''}
                    {selectedAgentForDocs.model_display_name || selectedAgentForDocs.model_code || 'AI Modeli'}
                  </p>
                </div>
              </div>

              <button
                onClick={() => { setIsDocsModalOpen(false); setSelectedAgentForDocs(null); }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--nt-94a3b8)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '6px'
                }}
              >
                <XCircle size={22} />
              </button>
            </div>

            {/* Modal Gövde (Scrollable) */}
            <div style={{
              padding: '24px',
              overflowY: 'auto',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              gap: '20px'
            }}>
              {/* Bilgilendirme Banner */}
              <div style={{
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                border: '1px solid rgba(59, 130, 246, 0.25)',
                borderRadius: '12px',
                padding: '14px 18px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px'
              }}>
                <Sparkles size={20} color="var(--ac-60a5fa)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div style={{ fontSize: '0.825rem', color: 'var(--nt-cbd5e1)', lineHeight: 1.5 }}>
                  <strong style={{ color: 'var(--nt-ffffff)' }}>Akıllı Vektör & Hibrit Hafıza Entegrasyonu:</strong> Yüklediğiniz dokümanların içeriği arka planda otomatik olarak analiz edilir, metinleri ayrıştırılır ve Qdrant kolektif vektör hafızasına (Qwen3-Embedding) kaydedilir. AI ajanı şirket süreçlerinde kararlar alırken bu dokümanlardaki verileri referans alır.
                </div>
              </div>

              {/* Kaynak Ekleme Sekmeleri (Dosya, Web Sayfası, YouTube Video) */}
              <div style={{
                display: 'flex',
                gap: '8px',
                background: 'rgb(var(--rgb-ov) / 0.03)',
                padding: '4px',
                borderRadius: '12px',
                border: '1px solid rgb(var(--rgb-ov) / 0.08)'
              }}>
                <button
                  type="button"
                  onClick={() => { setDocSourceTab('file'); setUploadDocError(''); }}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '0.825rem',
                    fontWeight: '700',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    background: docSourceTab === 'file' ? 'linear-gradient(135deg, #2563eb, #3b82f6)' : 'transparent',
                    color: docSourceTab === 'file' ? '#ffffff' : 'var(--nt-94a3b8)'
                  }}
                >
                  <FileText size={16} />
                  <span>Dosya Yükle</span>
                </button>

                <button
                  type="button"
                  onClick={() => { setDocSourceTab('web'); setUploadDocError(''); }}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '0.825rem',
                    fontWeight: '700',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    background: docSourceTab === 'web' ? 'linear-gradient(135deg, #0284c7, var(--ac-38bdf8))' : 'transparent',
                    color: docSourceTab === 'web' ? '#ffffff' : 'var(--nt-94a3b8)'
                  }}
                >
                  <Globe size={16} />
                  <span>Web Sayfası Ekle</span>
                </button>

                <button
                  type="button"
                  onClick={() => { setDocSourceTab('video'); setUploadDocError(''); }}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '0.825rem',
                    fontWeight: '700',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    background: docSourceTab === 'video' ? 'linear-gradient(135deg, #dc2626, #ef4444)' : 'transparent',
                    color: docSourceTab === 'video' ? '#ffffff' : 'var(--nt-94a3b8)'
                  }}
                >
                  <Video size={16} />
                  <span>YouTube / Video</span>
                </button>

                <button
                  type="button"
                  onClick={() => { setDocSourceTab('search'); setUploadDocError(''); }}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '0.825rem',
                    fontWeight: '700',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    background: docSourceTab === 'search' ? 'linear-gradient(135deg, #7c3aed, #a855f7)' : 'transparent',
                    color: docSourceTab === 'search' ? '#ffffff' : 'var(--nt-94a3b8)'
                  }}
                >
                  <Search size={16} />
                  <span>Deep Search</span>
                </button>
              </div>

              {/* Sekme 1: Dosya / Doküman Yükleme */}
              {docSourceTab === 'file' && (
                <div style={{
                  border: '2px dashed rgba(59, 130, 246, 0.35)',
                  borderRadius: '14px',
                  padding: '24px 20px',
                  textAlign: 'center',
                  background: 'rgba(59, 130, 246, 0.03)',
                  transition: 'all 0.2s',
                  position: 'relative'
                }}>
                  <input
                    type="file"
                    id="agentDocFileInput"
                    accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.csv,.md,.json"
                    onChange={handleUploadDocument}
                    disabled={isUploadingDoc}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      opacity: 0,
                      cursor: isUploadingDoc ? 'not-allowed' : 'pointer',
                      width: '100%',
                      height: '100%'
                    }}
                  />

                  <div style={{ pointerEvents: 'none' }}>
                    <div style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      background: 'rgba(59, 130, 246, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 10px auto'
                    }}>
                      {isUploadingDoc ? (
                        <RefreshCw size={22} color="var(--ac-60a5fa)" style={{ animation: 'spin 1s linear infinite' }} />
                      ) : (
                        <UploadCloud size={22} color="var(--ac-60a5fa)" />
                      )}
                    </div>

                    {isUploadingDoc ? (
                      <div>
                        <h4 style={{ fontSize: '0.925rem', fontWeight: '700', color: 'var(--ac-60a5fa)', margin: '0 0 4px 0' }}>
                          Doküman Yükleniyor ve Ayrıştırılıyor...
                        </h4>
                        <p style={{ fontSize: '0.78rem', color: 'var(--nt-94a3b8)', margin: 0 }}>
                          Metinler çıkarılıyor ve ajanın hafıza vektör motoruna indeksleniyor. Lütfen bekleyiniz.
                        </p>
                      </div>
                    ) : (
                      <div>
                        <h4 style={{ fontSize: '0.925rem', fontWeight: '700', color: 'var(--nt-ffffff)', margin: '0 0 4px 0' }}>
                          Doküman Yüklemek İçin Tıklayın veya Dosyayı Sürükleyin
                        </h4>
                        <p style={{ fontSize: '0.76rem', color: 'var(--nt-94a3b8)', margin: '0 0 10px 0' }}>
                          Desteklenen formatlar: PDF, Word (.docx), Excel (.xlsx), TXT, CSV, Markdown (Azami 50MB)
                        </p>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          <span style={{ fontSize: '0.68rem', fontWeight: '700', padding: '2px 7px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--ac-f87171)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>PDF</span>
                          <span style={{ fontSize: '0.68rem', fontWeight: '700', padding: '2px 7px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.15)', color: 'var(--ac-60a5fa)', border: '1px solid rgba(59, 130, 246, 0.3)' }}>WORD</span>
                          <span style={{ fontSize: '0.68rem', fontWeight: '700', padding: '2px 7px', borderRadius: '4px', background: 'rgba(34, 197, 94, 0.15)', color: 'var(--ac-4ade80)', border: '1px solid rgba(34, 197, 94, 0.3)' }}>EXCEL</span>
                          <span style={{ fontSize: '0.68rem', fontWeight: '700', padding: '2px 7px', borderRadius: '4px', background: 'rgba(168, 85, 247, 0.15)', color: 'var(--ac-c084fc)', border: '1px solid rgba(168, 85, 247, 0.3)' }}>TXT / CSV</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Sekme 2: Web Sayfası Ekleme */}
              {docSourceTab === 'web' && (
                <form onSubmit={handleAddWebLink} style={{
                  background: 'rgba(2, 132, 199, 0.05)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  borderRadius: '14px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: 'rgba(56, 189, 248, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <Globe size={20} color="var(--ac-38bdf8)" />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.925rem', fontWeight: '700', color: 'var(--nt-ffffff)', margin: 0 }}>
                        Araştırma İçin Web Sayfası Tanımla
                      </h4>
                      <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: '2px 0 0 0' }}>
                        AI Ajanı sayfayı ziyaret ederek metinleri tarar ve kolektif hafızasına indeksler.
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div>
                      <label style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--nt-cbd5e1)', display: 'block', marginBottom: '4px' }}>
                        Web Sayfası URL'si *
                      </label>
                      <input
                        type="url"
                        required
                        value={webLinkUrl}
                        onChange={(e) => setWebLinkUrl(e.target.value)}
                        placeholder="https://docs.orneksirket.com veya araştırma makalesi..."
                        disabled={isSubmittingWebLink}
                        style={{
                          width: '100%',
                          background: 'rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          borderRadius: '8px',
                          padding: '10px 12px',
                          color: 'var(--nt-ffffff)',
                          fontSize: '0.825rem',
                          outline: 'none'
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--nt-cbd5e1)', display: 'block', marginBottom: '4px' }}>
                        Konu / Kaynak Başlığı (Opsiyonel)
                      </label>
                      <input
                        type="text"
                        value={webLinkTitle}
                        onChange={(e) => setWebLinkTitle(e.target.value)}
                        placeholder="Örn: 2026 Sektörel Pazar Analizi veya Şirket Kılavuzu"
                        disabled={isSubmittingWebLink}
                        style={{
                          width: '100%',
                          background: 'rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                          border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                          borderRadius: '8px',
                          padding: '8px 12px',
                          color: 'var(--nt-ffffff)',
                          fontSize: '0.825rem',
                          outline: 'none'
                        }}
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmittingWebLink || !webLinkUrl.trim()}
                    style={{
                      alignSelf: 'flex-end',
                      background: isSubmittingWebLink ? 'rgba(56, 189, 248, 0.3)' : 'linear-gradient(135deg, #0284c7 0%, var(--ac-38bdf8) 100%)',
                      border: 'none',
                      color: 'var(--nt-ffffff)',
                      padding: '10px 18px',
                      borderRadius: '8px',
                      fontSize: '0.825rem',
                      fontWeight: '700',
                      cursor: isSubmittingWebLink ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      boxShadow: '0 4px 14px rgba(2, 132, 199, 0.3)'
                    }}
                  >
                    {isSubmittingWebLink ? (
                      <>
                        <RefreshCw size={15} color="#ffffff" style={{ animation: 'spin 1s linear infinite' }} />
                        <span>Sayfa Taranıyor ve Hafızaya Alınıyor...</span>
                      </>
                    ) : (
                      <>
                        <Globe size={15} />
                        <span>Web Sayfasını İncele ve Hafızaya Kaydet</span>
                      </>
                    )}
                  </button>
                </form>
              )}

              {/* Sekme 3: YouTube / Online Video Ekleme */}
              {docSourceTab === 'video' && (
                <form onSubmit={handleAddVideoLink} style={{
                  background: 'rgba(220, 38, 38, 0.05)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  borderRadius: '14px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: 'rgba(239, 68, 68, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <Video size={20} color="#ef4444" />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.925rem', fontWeight: '700', color: 'var(--nt-ffffff)', margin: 0 }}>
                        İzleyerek & Dinleyerek Öğrenme: YouTube Video Bağlantısı
                      </h4>
                      <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: '2px 0 0 0' }}>
                        AI Ajanı videonun başlığını, kanalını ve altyazı/konuşma transkriptini çıkarıp hafızasına indeksler.
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div>
                      <label style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--nt-cbd5e1)', display: 'block', marginBottom: '4px' }}>
                        YouTube Video URL'si *
                      </label>
                      <input
                        type="url"
                        required
                        value={videoLinkUrl}
                        onChange={(e) => setVideoLinkUrl(e.target.value)}
                        placeholder="https://www.youtube.com/watch?v=... veya https://youtu.be/..."
                        disabled={isSubmittingVideoLink}
                        style={{
                          width: '100%',
                          background: 'rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          borderRadius: '8px',
                          padding: '10px 12px',
                          color: 'var(--nt-ffffff)',
                          fontSize: '0.825rem',
                          outline: 'none'
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--nt-cbd5e1)', display: 'block', marginBottom: '4px' }}>
                        Video Başlığı / Konu Notu (Opsiyonel)
                      </label>
                      <input
                        type="text"
                        value={videoLinkTitle}
                        onChange={(e) => setVideoLinkTitle(e.target.value)}
                        placeholder="Örn: 2026 Kurumsal Satış ve Müşteri İlişkileri Eğitimi"
                        disabled={isSubmittingVideoLink}
                        style={{
                          width: '100%',
                          background: 'rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                          border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                          borderRadius: '8px',
                          padding: '8px 12px',
                          color: 'var(--nt-ffffff)',
                          fontSize: '0.825rem',
                          outline: 'none'
                        }}
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmittingVideoLink || !videoLinkUrl.trim()}
                    style={{
                      alignSelf: 'flex-end',
                      background: isSubmittingVideoLink ? 'rgba(239, 68, 68, 0.3)' : 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)',
                      border: 'none',
                      color: 'var(--nt-ffffff)',
                      padding: '10px 18px',
                      borderRadius: '8px',
                      fontSize: '0.825rem',
                      fontWeight: '700',
                      cursor: isSubmittingVideoLink ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      boxShadow: '0 4px 14px rgba(220, 38, 38, 0.3)'
                    }}
                  >
                    {isSubmittingVideoLink ? (
                      <>
                        <RefreshCw size={15} color="#ffffff" style={{ animation: 'spin 1s linear infinite' }} />
                        <span>Transkript Çekiliyor ve İndeksleniyor...</span>
                      </>
                    ) : (
                      <>
                        <Play size={15} />
                        <span>Videoyu ve Transkripti Hafızaya Kaydet</span>
                      </>
                    )}
                  </button>
                </form>
              )}

              {/* Sekme 4: Deep Search ile Araştır & Öğren */}
              {docSourceTab === 'search' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {/* Hızlı Buton: Şirket Sektörü & Bu Ünvan Üzerine Deep Search */}
                  <div style={{
                    background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.2) 0%, rgba(88, 28, 135, 0.2) 100%)',
                    border: '1px solid rgba(59, 130, 246, 0.35)',
                    borderRadius: '14px',
                    padding: '16px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '10px',
                        background: 'rgba(59, 130, 246, 0.2)',
                        border: '1px solid rgba(59, 130, 246, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        <Globe size={22} color="var(--ac-60a5fa)" />
                      </div>
                      <div>
                        <h4 style={{ fontSize: '0.925rem', fontWeight: '800', color: 'var(--nt-ffffff)', margin: 0 }}>
                          Şirket Sektörü & Ünvan Uzmanlık Araştırması
                        </h4>
                        <p style={{ fontSize: '0.75rem', color: 'var(--nt-cbd5e1)', margin: '3px 0 0 0' }}>
                          Ajanın bağlı olduğu şirket sektörünü ve atanmış olduğu <strong>{selectedAgentForDocs?.job_title_name || 'ünvan'}</strong> görev kapsamını internette derinlemesine araştırıp hafızaya kaydeder.
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={handleExistingAgentDeepSearchSectorAndTitle}
                      disabled={isExistingAgentDeepSearchingSectorTitle}
                      style={{
                        background: isExistingAgentDeepSearchingSectorTitle ? 'rgba(59, 130, 246, 0.3)' : 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                        border: 'none',
                        color: 'var(--nt-ffffff)',
                        padding: '10px 18px',
                        borderRadius: '8px',
                        fontSize: '0.8rem',
                        fontWeight: '700',
                        cursor: isExistingAgentDeepSearchingSectorTitle ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        boxShadow: '0 4px 14px rgba(37, 99, 235, 0.35)'
                      }}
                    >
                      {isExistingAgentDeepSearchingSectorTitle ? (
                        <>
                          <RefreshCw size={14} color="#ffffff" style={{ animation: 'spin 1s linear infinite' }} />
                          <span>Sektör & Ünvan Araştırılıyor...</span>
                        </>
                      ) : (
                        <>
                          <Globe size={14} />
                          <span>Sektör & Ünvan Deep Search Başlat</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Özel Konu Deep Search Formu */}
                  <form onSubmit={handleTriggerDeepSearch} style={{
                    background: 'rgba(124, 58, 237, 0.05)',
                    border: '1px solid rgba(168, 85, 247, 0.25)',
                    borderRadius: '14px',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '10px',
                        background: 'rgba(168, 85, 247, 0.15)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        <Search size={20} color="var(--ac-c084fc)" />
                      </div>
                      <div>
                        <h4 style={{ fontSize: '0.925rem', fontWeight: '700', color: 'var(--nt-ffffff)', margin: 0 }}>
                          Özel Konulu Deep Search & Öğrenme Motoru
                        </h4>
                        <p style={{ fontSize: '0.75rem', color: 'var(--nt-94a3b8)', margin: '2px 0 0 0' }}>
                          AI Ajanı belirlediğiniz spesifik konuda webde derin araştırma yapar, sayfaları sentezler ve elde ettiği uzmanlık bilgilerini hafızasına indeksler.
                        </p>
                      </div>
                    </div>

                    <div>
                      <label style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--nt-cbd5e1)', display: 'block', marginBottom: '4px' }}>
                        Araştırma Konusu / Pazar Sorusu *
                      </label>
                      <input
                        type="text"
                        required
                        value={deepSearchQuery}
                        onChange={(e) => setDeepSearchQuery(e.target.value)}
                        placeholder="Örn: 2026 Türkiye e-İrsaliye ve Vergi Mevzuatı Değişiklikleri veya B2B Müşteri Kazanım Yöntemleri..."
                        disabled={isSubmittingDeepSearch}
                        style={{
                          width: '100%',
                          background: 'rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                          border: '1px solid rgba(168, 85, 247, 0.3)',
                          borderRadius: '8px',
                          padding: '10px 12px',
                          color: 'var(--nt-ffffff)',
                          fontSize: '0.825rem',
                          outline: 'none'
                        }}
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isSubmittingDeepSearch || !deepSearchQuery.trim()}
                      style={{
                        alignSelf: 'flex-end',
                        background: isSubmittingDeepSearch ? 'rgba(168, 85, 247, 0.3)' : 'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)',
                        border: 'none',
                        color: 'var(--nt-ffffff)',
                        padding: '10px 18px',
                        borderRadius: '8px',
                        fontSize: '0.825rem',
                        fontWeight: '700',
                        cursor: isSubmittingDeepSearch ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        boxShadow: '0 4px 14px rgba(124, 58, 237, 0.3)'
                      }}
                    >
                      {isSubmittingDeepSearch ? (
                        <>
                          <RefreshCw size={15} color="#ffffff" style={{ animation: 'spin 1s linear infinite' }} />
                          <span>Web Taranıyor, Sayfalar İnceleniyor ve Hafıza Sentezleniyor...</span>
                        </>
                      ) : (
                        <>
                          <Search size={15} />
                          <span>İnternette Araştır, Sentezle ve Hafızaya Kaydet</span>
                        </>
                      )}
                    </button>
                  </form>
                </div>
              )}

              {/* Hata Mesajı */}
              {uploadDocError && (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  borderRadius: '10px',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <AlertCircle size={18} color="#ef4444" style={{ flexShrink: 0 }} />
                  <span style={{ fontSize: '0.8rem', color: 'var(--ac-fca5a5)' }}>{uploadDocError}</span>
                </div>
              )}

              {/* Yüklü Dokümanlar ve Kaynaklar Listesi */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--nt-ffffff)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>📚 Ajanın Öğrenme & Hafıza Kütüphanesi</span>
                    <span style={{
                      background: 'rgb(var(--rgb-ov) / 0.08)',
                      color: 'var(--nt-cbd5e1)',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      fontSize: '0.75rem'
                    }}>
                      {agentDocuments.length} Kaynak
                    </span>
                  </h4>
                </div>

                {isLoadingDocs ? (
                  <div style={{ padding: '30px', textAlign: 'center', color: 'var(--nt-94a3b8)', fontSize: '0.85rem' }}>
                    <RefreshCw size={20} color="var(--ac-60a5fa)" style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
                    <div>Kaynaklar yükleniyor...</div>
                  </div>
                ) : agentDocuments.length === 0 ? (
                  <div style={{
                    padding: '36px 20px',
                    textAlign: 'center',
                    background: 'rgb(var(--rgb-ov) / 0.02)',
                    border: '1px solid rgb(var(--rgb-ov) / 0.05)',
                    borderRadius: '14px'
                  }}>
                    <BookOpen size={32} color="var(--nt-64748b)" style={{ margin: '0 auto 10px auto' }} />
                    <h5 style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--nt-cbd5e1)', margin: '0 0 4px 0' }}>
                      Henüz Kaynak veya Doküman Eklenmedi
                    </h5>
                    <p style={{ fontSize: '0.78rem', color: 'var(--nt-64748b)', margin: 0, maxWidth: '420px', marginInline: 'auto' }}>
                      Bu AI ajanı için şirket süreç kılavuzları, araştırma web sayfaları veya eğitim videoları ekleyerek uzmanlık seviyesini artırabilirsiniz.
                    </p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {agentDocuments.map(doc => {
                      const ext = (doc.file_type || '').toLowerCase();
                      const isWeb = ext === 'web';
                      const isYoutube = ext === 'youtube';
                      const isDeepSearch = ext === 'deep_search';
                      const isPdf = ext === 'pdf';
                      const isExcel = ext === 'xlsx' || ext === 'xls';
                      const isWord = ext === 'docx' || ext === 'doc';
                      const isPreviewOpen = previewDocId === doc.id;

                      const sizeStr = isWeb
                        ? 'Web Sayfası İçeriği'
                        : isYoutube
                        ? 'Video Transkripti'
                        : isDeepSearch
                        ? 'Araştırma & Sentez Raporu'
                        : doc.file_size > 1024 * 1024
                        ? `${(doc.file_size / (1024 * 1024)).toFixed(2)} MB`
                        : `${(doc.file_size / 1024).toFixed(1)} KB`;

                      return (
                        <div
                          key={doc.id}
                          style={{
                            background: 'rgb(var(--rgb-ov) / 0.03)',
                            border: '1px solid rgb(var(--rgb-ov) / 0.07)',
                            borderRadius: '12px',
                            padding: '14px 16px',
                            transition: 'background 0.2s'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
                              <div style={{
                                width: '38px',
                                height: '38px',
                                borderRadius: '10px',
                                background: isDeepSearch
                                  ? 'rgba(168, 85, 247, 0.15)'
                                  : isWeb
                                  ? 'rgba(56, 189, 248, 0.15)'
                                  : isYoutube
                                  ? 'rgba(239, 68, 68, 0.15)'
                                  : isPdf
                                  ? 'rgba(239, 68, 68, 0.15)'
                                  : isExcel
                                  ? 'rgba(34, 197, 94, 0.15)'
                                  : isWord
                                  ? 'rgba(59, 130, 246, 0.15)'
                                  : 'rgba(168, 85, 247, 0.15)',
                                border: `1px solid ${
                                  isDeepSearch
                                    ? 'rgba(168, 85, 247, 0.35)'
                                    : isWeb
                                    ? 'rgba(56, 189, 248, 0.3)'
                                    : isYoutube
                                    ? 'rgba(239, 68, 68, 0.3)'
                                    : isPdf
                                    ? 'rgba(239, 68, 68, 0.3)'
                                    : isExcel
                                    ? 'rgba(34, 197, 94, 0.3)'
                                    : isWord
                                    ? 'rgba(59, 130, 246, 0.3)'
                                    : 'rgba(168, 85, 247, 0.3)'
                                }`,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexShrink: 0
                              }}>
                                {isDeepSearch ? (
                                  <Search size={20} color="var(--ac-c084fc)" />
                                ) : isWeb ? (
                                  <Globe size={20} color="var(--ac-38bdf8)" />
                                ) : isYoutube ? (
                                  <Video size={20} color="#ef4444" />
                                ) : isExcel ? (
                                  <FileSpreadsheet size={20} color="var(--ac-4ade80)" />
                                ) : (
                                  <FileText size={20} color={isPdf ? 'var(--ac-f87171)' : isWord ? 'var(--ac-60a5fa)' : 'var(--ac-c084fc)'} />
                                )}
                              </div>

                              <div style={{ minWidth: 0, flex: 1 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <span style={{
                                    fontSize: '0.85rem',
                                    fontWeight: '700',
                                    color: 'var(--nt-ffffff)',
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis'
                                  }} title={doc.original_name}>
                                    {doc.original_name}
                                  </span>
                                  <span style={{
                                    fontSize: '0.65rem',
                                    fontWeight: '800',
                                    textTransform: 'uppercase',
                                    padding: '1px 5px',
                                    borderRadius: '4px',
                                    background: isDeepSearch
                                      ? 'rgba(168, 85, 247, 0.2)'
                                      : isWeb
                                      ? 'rgba(56, 189, 248, 0.2)'
                                      : isYoutube
                                      ? 'rgba(239, 68, 68, 0.2)'
                                      : isPdf
                                      ? 'rgba(239, 68, 68, 0.2)'
                                      : isExcel
                                      ? 'rgba(34, 197, 94, 0.2)'
                                      : isWord
                                      ? 'rgba(59, 130, 246, 0.2)'
                                      : 'rgba(168, 85, 247, 0.2)',
                                    color: isDeepSearch
                                      ? 'var(--ac-d8b4fe)'
                                      : isWeb
                                      ? 'var(--ac-7dd3fc)'
                                      : isYoutube
                                      ? 'var(--ac-fca5a5)'
                                      : isPdf
                                      ? 'var(--ac-fca5a5)'
                                      : isExcel
                                      ? 'var(--ac-86efac)'
                                      : isWord
                                      ? 'var(--ac-93c5fd)'
                                      : 'var(--ac-d8b4fe)'
                                  }}>
                                    {isDeepSearch ? '🔍 DEEP SEARCH' : isWeb ? 'WEB SAYFASI' : isYoutube ? 'YOUTUBE VİDEO' : doc.file_type}
                                  </span>
                                </div>

                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px', fontSize: '0.75rem', color: 'var(--nt-94a3b8)' }}>
                                  <span>{sizeStr}</span>
                                  <span>•</span>
                                  <span>{doc.created_at ? new Date(doc.created_at).toLocaleDateString('tr-TR') : '—'}</span>
                                  <span>•</span>
                                  <span style={{ color: 'var(--ac-34d399)', display: 'inline-flex', alignItems: 'center', gap: '3px', fontWeight: '600' }}>
                                    <CheckCircle2 size={11} />
                                    {doc.status === 'INDEXED' ? 'Hafızada & İndeksli' : 'Eklendi'}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                              {/* Önizle Butonu */}
                              <button
                                onClick={() => setPreviewDocId(isPreviewOpen ? null : doc.id)}
                                style={{
                                  background: isPreviewOpen ? 'rgba(59, 130, 246, 0.25)' : 'rgb(var(--rgb-ov) / 0.05)',
                                  border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                                  color: isPreviewOpen ? 'var(--ac-93c5fd)' : 'var(--nt-cbd5e1)',
                                  padding: '6px 10px',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px'
                                }}
                                title="Metin Özeti ve Ayrıştırılan İçerik Önizlemesi"
                              >
                                <Eye size={13} />
                                <span>{isPreviewOpen ? 'Kapat' : 'Önizle'}</span>
                              </button>

                              {/* Web / Video Bağlantısını Aç, Deep Search Raporunu İndir veya Dosyayı İndir */}
                              {isWeb || isYoutube ? (
                                <a
                                  href={doc.storage_path || '#'}
                                  target="_blank"
                                  rel="noreferrer"
                                  style={{
                                    background: isWeb ? 'rgba(56, 189, 248, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                                    border: `1px solid ${isWeb ? 'rgba(56, 189, 248, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                                    color: isWeb ? 'var(--ac-38bdf8)' : 'var(--ac-f87171)',
                                    padding: '6px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '4px',
                                    textDecoration: 'none'
                                  }}
                                  title={isWeb ? 'Web Sayfasını Yeni Sekmede Aç' : 'YouTube Videosunu Yeni Sekmede Aç'}
                                >
                                  <ExternalLink size={13} />
                                  <span>{isWeb ? 'Sayfayı Aç' : 'Videoyu Aç'}</span>
                                </a>
                              ) : isDeepSearch ? (
                                <a
                                  href={api.getAgentDocumentDownloadUrl(getActiveTenantId(), selectedAgentForDocs.id, doc.id)}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    api.downloadAgentDocument(getActiveTenantId(), selectedAgentForDocs.id, doc.id, doc.original_name)
                                      .catch((err) => notify(`Doküman indirilemedi: ${err.message}`));
                                  }}
                                  target="_blank"
                                  rel="noreferrer"
                                  download
                                  style={{
                                    background: 'rgba(168, 85, 247, 0.12)',
                                    border: '1px solid rgba(168, 85, 247, 0.3)',
                                    color: 'var(--ac-c084fc)',
                                    padding: '6px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '4px',
                                    textDecoration: 'none'
                                  }}
                                  title="Deep Search Araştırma Raporunu İndir"
                                >
                                  <Download size={13} />
                                  <span>Raporu İndir</span>
                                </a>
                              ) : (
                                <a
                                  href={api.getAgentDocumentDownloadUrl(getActiveTenantId(), selectedAgentForDocs.id, doc.id)}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    api.downloadAgentDocument(getActiveTenantId(), selectedAgentForDocs.id, doc.id, doc.original_name)
                                      .catch((err) => notify(`Doküman indirilemedi: ${err.message}`));
                                  }}
                                  target="_blank"
                                  rel="noreferrer"
                                  download
                                  style={{
                                    background: 'rgb(var(--rgb-ov) / 0.05)',
                                    border: '1px solid rgb(var(--rgb-ov) / 0.1)',
                                    color: 'var(--nt-cbd5e1)',
                                    padding: '6px 10px',
                                    borderRadius: '6px',
                                    fontSize: '0.75rem',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '4px',
                                    textDecoration: 'none'
                                  }}
                                  title="Orijinal Dokümanı İndir"
                                >
                                  <Download size={13} />
                                  <span>İndir</span>
                                </a>
                              )}

                              {/* Sil Butonu */}
                              <button
                                onClick={() => setDocToDelete(doc)}
                                style={{
                                  background: 'rgba(239, 68, 68, 0.1)',
                                  border: '1px solid rgba(239, 68, 68, 0.25)',
                                  color: 'var(--ac-f87171)',
                                  padding: '6px 8px',
                                  borderRadius: '6px',
                                  fontSize: '0.75rem',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px'
                                }}
                                title="Dokümanı ve Hafıza Kaydını Sil"
                              >
                                <Trash2 size={13} />
                              </button>
                            </div>
                          </div>

                          {/* Ayrıştırılan Metin / Özet Genişletme Bölümü */}
                          {isPreviewOpen && (
                            <div style={{
                              marginTop: '12px',
                              padding: '12px 14px',
                              background: 'rgb(var(--rgb-shade) / calc(0.4 * var(--shade-k)))',
                              border: '1px solid rgba(59, 130, 246, 0.25)',
                              borderRadius: '8px',
                              fontSize: '0.775rem'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                                <span style={{ color: 'var(--ac-60a5fa)', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <Sparkles size={12} />
                                  Ayrıştırılan Metin ve Hafıza Önizlemesi:
                                </span>
                                <span style={{ color: 'var(--nt-64748b)', fontSize: '0.7rem' }}>
                                  Qdrant RAG İndeksi
                                </span>
                              </div>
                              <p style={{
                                color: 'var(--nt-e2e8f0)',
                                margin: 0,
                                lineHeight: 1.5,
                                whiteSpace: 'pre-wrap',
                                maxHeight: '180px',
                                overflowY: 'auto'
                              }}>
                                {doc.extracted_text_preview || doc.summary || 'Bu dokümandan metin içeriği çıkarılamadı veya dosya boş.'}
                              </p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Alt Kısım */}
            <div style={{
              padding: '14px 24px',
              borderTop: '1px solid rgb(var(--rgb-ov) / 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              background: 'rgb(var(--rgb-ov) / 0.02)'
            }}>
              <button
                onClick={() => { setIsDocsModalOpen(false); setSelectedAgentForDocs(null); }}
                style={{
                  background: 'rgb(var(--rgb-ov) / 0.08)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.15)',
                  color: 'var(--nt-ffffff)',
                  padding: '8px 20px',
                  borderRadius: '8px',
                  fontSize: '0.825rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SİLME ONAY MODALI (AI Ajan Dokümanı)                                      */}
      {/* ========================================================================= */}
      {docToDelete && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1200,
          padding: '20px'
        }}>
          <div style={{
            background: 'var(--sf-131826)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '440px',
            padding: '24px',
            textAlign: 'center',
            boxShadow: '0 20px 50px rgb(var(--rgb-shade) / calc(0.8 * var(--shade-k)))'
          }}>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto'
            }}>
              <Trash2 size={26} color="#ef4444" />
            </div>

            <h3 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--nt-ffffff)', marginBottom: '8px' }}>
              Dokümanı Silmek İstiyor musunuz?
            </h3>

            <p style={{ fontSize: '0.85rem', color: 'var(--nt-94a3b8)', lineHeight: 1.5, marginBottom: '22px' }}>
              <strong style={{ color: 'var(--nt-f8fafc)' }}>'{docToDelete.original_name}'</strong> dokümanı ve bu dokümandan oluşturulan ajanın kolektif hafıza (vektör RAG) kayıtları kalıcı olarak silinecektir.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
              <button
                onClick={() => setDocToDelete(null)}
                style={{
                  background: 'rgb(var(--rgb-ov) / 0.08)',
                  border: '1px solid rgb(var(--rgb-ov) / 0.12)',
                  color: 'var(--nt-cbd5e1)',
                  padding: '9px 18px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Vazgeç
              </button>

              <button
                onClick={confirmDeleteDocument}
                disabled={isDeletingDoc}
                style={{
                  background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                  border: 'none',
                  color: '#ffffff',
                  padding: '9px 22px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  cursor: isDeletingDoc ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {isDeletingDoc ? 'Siliniyor...' : 'Evet, Sil'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

