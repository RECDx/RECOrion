/**
 * RECOrion API Client
 * FastAPI Backend ile haberleşme katmanı
 */

const BASE_URL = '/api/v1';
const TOKEN_KEY = 'recorion_token';

/**
 * Oturum token'ı. "Beni Hatırla" seçiliyse localStorage, değilse sessionStorage
 * (tarayıcı kapanınca silinir) kullanılır.
 */
export const session = {
  getToken: () => {
    try {
      return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  setToken: (token, rememberMe) => {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(TOKEN_KEY);
      (rememberMe ? localStorage : sessionStorage).setItem(TOKEN_KEY, token);
    } catch (e) {
      console.warn('Oturum bilgisi kaydedilemedi:', e);
    }
  },
  clear: () => {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem('recorion_user');
      localStorage.removeItem('recorion_current_view');
    } catch {
      /* depolama erişilemiyor */
    }
  },
};

function authHeaders(extra = {}) {
  const headers = { ...extra };
  const token = session.getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

// Oturum süresi dolduğunda veya token geçersiz olduğunda uygulama bu olayı dinleyip çıkış yapar
function handleUnauthorized() {
  if (session.getToken()) {
    session.clear();
    window.dispatchEvent(new Event('recorion:unauthorized'));
  }
}

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = authHeaders(options.headers);
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      if (res.status === 401 && endpoint !== '/auth/login') handleUnauthorized();
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP Error ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Hatası [${endpoint}]:`, err);
    throw err;
  }
}

/** Yetkili dosya indirme: token'lı istekle indirip tarayıcıya kaydettirir. */
async function downloadFile(endpoint, fallbackName) {
  const res = await fetch(`${BASE_URL}${endpoint}`, { headers: authHeaders() });
  if (!res.ok) {
    if (res.status === 401) handleUnauthorized();
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP Error ${res.status}`);
  }
  const disposition = res.headers.get('content-disposition') || '';
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
  const fileName = match ? decodeURIComponent(match[1]) : (fallbackName || 'dokuman');
  const blobUrl = URL.createObjectURL(await res.blob());
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
}

export const api = {
  // Sağlık Kontrolü
  getHealth: () => request('/health'),

  // EVREN Model Kataloğu (13 Model)
  getModels: (modelType) => request(`/models/${modelType ? `?model_type=${modelType}` : ''}`),

  // Şirketler, Paketler & NACE
  getTenants: () => request('/tenants/'),
  getOdooProducts: (search = '') => request(`/tenants/odoo/products${search ? `?search=${encodeURIComponent(search)}` : ''}`),
  getPlans: (activeOnly = false) => request(`/tenants/plans${activeOnly ? '?active_only=true' : ''}`),
  getJobTitles: (category = null) => request(`/actors/job-titles${category ? `?category=${category}` : ''}`),
  getNaceCatalog: () => request('/tenants/nace-catalog'),
  searchNace: (query = '', limit = 30) => request(`/tenants/nace-catalog?query=${encodeURIComponent(query)}&limit=${limit}`),
  submitPurchaseRequest: (data) => request('/tenants/purchase-request', { method: 'POST', body: JSON.stringify(data) }),
  sendPurchaseEmailCode: (email) => request('/tenants/purchase-request/send-code', { method: 'POST', body: JSON.stringify({ email }) }),
  getPublicStats: () => request('/public/stats'),
  getLeads: () => request('/tenants/leads'),

  // Personeller (İnsan & AI Aktörler)
  getActors: (tenantId, actorType) => {
    const params = new URLSearchParams();
    if (tenantId) params.append('tenant_id', tenantId);
    if (actorType) params.append('actor_type', actorType);
    return request(`/actors/?${params.toString()}`);
  },

  // Projeler & İş Akışı Görevleri
  getProjects: (tenantId, scope = 'mine') => request(`/projects/?${new URLSearchParams({ ...(tenantId ? { tenant_id: tenantId } : {}), scope }).toString()}`),
  // Proje/Case (Adım 6)
  getProject: (projectId) => request(`/projects/${projectId}`),
  updateProject: (projectId, data) => request(`/projects/${projectId}`, { method: 'PUT', body: JSON.stringify(data) }),
  changeProjectStatus: (projectId, action, summary) => request(`/projects/${projectId}/status`, { method: 'POST', body: JSON.stringify({ action, summary }) }),
  addProjectMember: (projectId, actorId, role) => request(`/projects/${projectId}/members`, { method: 'POST', body: JSON.stringify({ actor_id: actorId, role }) }),
  removeProjectMember: (projectId, actorId) => request(`/projects/${projectId}/members/${actorId}`, { method: 'DELETE' }),
  suggestProjectPlan: (projectId, feedback, useChat = false) => request(`/projects/${projectId}/plan/suggest`, { method: 'POST', body: JSON.stringify({ feedback: feedback || null, use_chat: useChat }) }),
  saveProjectPlan: (projectId, plan) => request(`/projects/${projectId}/plan`, { method: 'PUT', body: JSON.stringify(plan) }),
  approveProjectPlan: (projectId) => request(`/projects/${projectId}/plan/approve`, { method: 'POST' }),
  getProjectPlanChat: (projectId) => request(`/projects/${projectId}/plan/chat`),
  sendProjectPlanChat: (projectId, content) => request(`/projects/${projectId}/plan/chat`, { method: 'POST', body: JSON.stringify({ content }) }),
  simulateProject: (projectId, startDate) => request(`/projects/${projectId}/simulate`, { method: 'POST', body: JSON.stringify({ start_date: startDate || null }) }),
  // Telegram bildirimleri (Adım 6.5)
  getTelegramStatus: () => request('/auth/telegram'),
  linkTelegram: () => request('/auth/telegram/link', { method: 'POST' }),
  unlinkTelegram: () => request('/auth/telegram/link', { method: 'DELETE' }),
  // İş akışı (Adım 7.1)
  getProjectWorkflow: (projectId) => request(`/projects/${projectId}/workflow`),
  submitTask: (taskId, note) => request(`/tasks/${taskId}/submit`, { method: 'POST', body: JSON.stringify({ note: note || null }) }),
  decideTask: (taskId, approve, note) => request(`/tasks/${taskId}/decision`, { method: 'POST', body: JSON.stringify({ approve, note: note || null }) }),
  releaseTask: (taskId, action, note, assigneeId) => request(`/tasks/${taskId}/release`, { method: 'POST', body: JSON.stringify({ action, note: note || null, assignee_actor_id: assigneeId || null }) }),
  createProject: (data) => request('/projects/', { method: 'POST', body: JSON.stringify(data) }),
  getTasks: (projectId) => request(`/projects/${projectId}/tasks`),
  createTask: (projectId, data) => request(`/projects/${projectId}/tasks`, { method: 'POST', body: JSON.stringify(data) }),

  // Kalıcı Sohbet ve Canlı Düşünce Akışı (Gemini Web Tarzı)
  getChatHistory: (taskId, actorId = null, includePrivate = false) => {
    const params = new URLSearchParams();
    if (actorId) params.append('actor_id', actorId);
    if (includePrivate) params.append('include_private', 'true');
    return request(`/chat/history/${taskId}?${params.toString()}`);
  },
  getProjectChatHistory: (projectId, actorId = null, messageType = null) => {
    const params = new URLSearchParams();
    if (actorId) params.append('actor_id', actorId);
    if (messageType) params.append('message_type', messageType);
    return request(`/chat/project/${projectId}?${params.toString()}`);
  },
  sendMessage: (payload) => request('/chat/send', { method: 'POST', body: JSON.stringify(payload) }),
  learnFromTaskChat: (taskId) => request(`/chat/learn/${taskId}`, { method: 'POST' }),

  // 2 Kademeli Kolektif Hafıza
  getMemoryItems: (tenantId, scope = null) => {
    const params = new URLSearchParams({ tenant_id: tenantId });
    if (scope) params.append('scope', scope);
    return request(`/memory/?${params.toString()}`);
  },
  searchMemory: (payload) => request('/memory/search', { method: 'POST', body: JSON.stringify(payload) }),
  promoteMemory: (memoryId) => request(`/memory/promote/${memoryId}`, { method: 'POST' }),
  rejectMemory: (memoryId) => request(`/memory/${memoryId}/reject`, { method: 'POST' }),
  getMemoryCandidates: (tenantId) => request(`/memory/?tenant_id=${tenantId}&status=CANDIDATE`),
  // Bilgi katmanları (Adım 5.5)
  getAgentKnowledge: (tenantId, agentId) => request(`/company/${tenantId}/ai-agents/${agentId}/knowledge`),
  searchAgentKnowledge: (tenantId, agentId, query, projectId) => request(`/company/${tenantId}/ai-agents/${agentId}/knowledge/search`, { method: 'POST', body: JSON.stringify({ query, project_id: projectId || null }) }),
  getProjectDocuments: (projectId) => request(`/projects/${projectId}/documents`),
  uploadProjectDocument: (projectId, formData) => request(`/projects/${projectId}/documents`, { method: 'POST', body: formData }),
  promoteProjectKnowledge: (projectId, documentIds) => request(`/projects/${projectId}/knowledge/promote`, { method: 'POST', body: JSON.stringify({ document_ids: documentIds }) }),

  // Kimlik Doğrulama & Profil (Auth & RBAC)
  login: (credentials) => request('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  getProfile: (actorId) => request(`/auth/profile/${actorId}`),
  getMe: () => request('/auth/me'),
  requestPasswordReset: (email) => request('/auth/password-reset/request', { method: 'POST', body: JSON.stringify({ email }) }),
  confirmPasswordReset: (token, newPassword) => request('/auth/password-reset/confirm', { method: 'POST', body: JSON.stringify({ token, new_password: newPassword }) }),
  getCompanyEntitlements: (tenantId) => request(`/company/${tenantId}/entitlements`),
  updateProfile: (actorId, data) => request(`/auth/profile/${actorId}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Sistem İzinleri & Ayarları (Süper Admin)
  getPermissions: () => request('/system/permissions'),
  createPermission: (data) => request('/system/permissions', { method: 'POST', body: JSON.stringify(data) }),
  updatePermission: (permId, data) => request(`/system/permissions/${permId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePermission: (permId) => request(`/system/permissions/${permId}`, { method: 'DELETE' }),
  getSystemSettings: () => request('/system/settings'),
  setDefaultManifestoModel: (modelCode) => request('/system/settings/default-manifesto-model', { method: 'POST', body: JSON.stringify({ model_code: modelCode }) }),

  // Sistem Yetki Rolleri (RBAC - Madde 1)
  getSystemRoles: () => request('/system/roles'),
  createSystemRole: (data) => request('/system/roles', { method: 'POST', body: JSON.stringify(data) }),
  updateSystemRole: (roleId, data) => request(`/system/roles/${roleId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSystemRole: (roleId) => request(`/system/roles/${roleId}`, { method: 'DELETE' }),

  // EVREN Modelleri CRUD
  createModel: (data) => request('/models', { method: 'POST', body: JSON.stringify(data) }),
  updateModel: (modelId, data) => request(`/models/${modelId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteModel: (modelId) => request(`/models/${modelId}`, { method: 'DELETE' }),

  // Kiralama Paketleri CRUD
  createPlan: (data) => request('/tenants/plans', { method: 'POST', body: JSON.stringify(data) }),
  updatePlan: (planId, data) => request(`/tenants/plans/${planId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePlan: (planId) => request(`/tenants/plans/${planId}`, { method: 'DELETE' }),

  // Türkiye Ticaret Bakanlığı Sektör Tanımları (Madde 1)
  getSectors: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.search) qs.append('search', params.search);
    if (params.active_only !== undefined) qs.append('active_only', params.active_only);
    const query = qs.toString();
    return request(`/sectors/${query ? `?${query}` : ''}`);
  },
  getSector: (code) => request(`/sectors/${encodeURIComponent(code)}`),
  createSector: (data) => request('/sectors/', { method: 'POST', body: JSON.stringify(data) }),
  updateSector: (code, data) => request(`/sectors/${encodeURIComponent(code)}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSector: (code) => request(`/sectors/${encodeURIComponent(code)}`, { method: 'DELETE' }),

  // Türkiye Ticaret Bakanlığı Meslek Tanımları (Madde 1)
  getProfessions: (params = {}) => {
    const p = (params && typeof params === 'object') ? params : {};
    const qs = new URLSearchParams();
    if (p.sector_code) qs.append('sector_code', p.sector_code);
    if (p.search) qs.append('q', p.search);
    if (p.q) qs.append('q', p.q);
    if (p.is_active !== undefined) qs.append('is_active', p.is_active);
    if (p.active_only !== undefined) qs.append('is_active', p.active_only);
    qs.append('limit', p.limit || 500);
    if (p.offset) qs.append('offset', p.offset);
    const query = qs.toString();
    return request(`/professions/${query ? `?${query}` : ''}`);
  },
  getProfession: (code) => request(`/professions/${encodeURIComponent(code)}`),
  createProfession: (data) => request('/professions/', { method: 'POST', body: JSON.stringify(data) }),
  updateProfession: (code, data) => request(`/professions/${encodeURIComponent(code)}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProfession: (code) => request(`/professions/${encodeURIComponent(code)}`, { method: 'DELETE' }),

  // Şirketler & Detay Yönetimi
  getTenantDetails: (tenantId) => request(`/tenants/${tenantId}/details`),
  updateTenant: (tenantId, data) => request(`/tenants/${tenantId}`, { method: 'PUT', body: JSON.stringify(data) }),
  toggleTenantStatus: (tenantId) => request(`/tenants/${tenantId}/toggle-status`, { method: 'POST' }),
  updateTenantAdmin: (tenantId, data) => request(`/tenants/${tenantId}/admin-user`, { method: 'PUT', body: JSON.stringify(data) }),
  generateTenantAdminPassword: (tenantId) => request(`/tenants/${tenantId}/generate-password`, { method: 'POST' }),
  approveRegisteredTenant: (tenantId) => request(`/tenants/${tenantId}/approve`, { method: 'POST' }),

  // Sektörel Ünvanlar & Prompt Üretimi
  createAdminJobTitle: (data) => request('/actors/job-titles/admin', { method: 'POST', body: JSON.stringify(data) }),
  updateJobTitle: (titleId, data) => request(`/actors/job-titles/${titleId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteJobTitle: (titleId) => request(`/actors/job-titles/${titleId}`, { method: 'DELETE' }),
  regenerateJobTitlePrompt: (titleId) => request(`/actors/job-titles/${titleId}/regenerate-prompt`, { method: 'POST' }),

  // Leads & Roller
  approveLead: (leadId) => request(`/tenants/leads/${leadId}/approve`, { method: 'POST' }),
  rejectLead: (leadId, reason) => request(`/tenants/leads/${leadId}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),
  retryLeadOdooSync: (leadId) => request(`/tenants/leads/${leadId}/odoo-sync`, { method: 'POST' }),
  getRoles: (tenantId) => request(`/tenants/${tenantId}/roles`),
  createRole: (tenantId, data) => request(`/tenants/${tenantId}/roles`, { method: 'POST', body: JSON.stringify(data) }),
  createCustomJobTitle: (data) => request('/actors/job-titles', { method: 'POST', body: JSON.stringify(data) }),

  // E-Posta Şablonları (Madde 1)
  getEmailTemplates: () => request('/system/email-templates'),
  createEmailTemplate: (data) => request('/system/email-templates', { method: 'POST', body: JSON.stringify(data) }),
  updateEmailTemplate: (id, data) => request(`/system/email-templates/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteEmailTemplate: (id) => request(`/system/email-templates/${id}`, { method: 'DELETE' }),
  testSendEmailTemplate: (id, data) => request(`/system/email-templates/${id}/test-send`, { method: 'POST', body: JSON.stringify(data) }),

  // Zamanlayıcılar / Schedules (Madde 2)
  getSchedules: () => request('/system/schedules'),
  createSchedule: (data) => request('/system/schedules', { method: 'POST', body: JSON.stringify(data) }),
  updateSchedule: (id, data) => request(`/system/schedules/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSchedule: (id) => request(`/system/schedules/${id}`, { method: 'DELETE' }),
  triggerSchedule: (id) => request(`/system/schedules/${id}/trigger`, { method: 'POST' }),

  // Şirket Gelişmiş İşlemleri (Madde 9, 13, 14, Silme)
  adminCreateTenant: (data) => request('/tenants/admin-create', { method: 'POST', body: JSON.stringify(data) }),
  deleteTenant: (tenantId) => request(`/tenants/${tenantId}`, { method: 'DELETE' }),
  sendManualReminder: (tenantId) => request(`/tenants/${tenantId}/send-reminder`, { method: 'POST' }),
  sendManualWelcome: (tenantId) => request(`/tenants/${tenantId}/send-welcome`, { method: 'POST' }),
  generateManifesto: (data) => request('/tenants/generate-manifesto', { method: 'POST', body: JSON.stringify(data) }),

  // Müşteri Şirket Yönetimi (Company Admin) - Departmanlar (Madde 1)
  getDepartments: (tenantId) => request(`/company/${tenantId}/departments`),
  createDepartment: (tenantId, data) => request(`/company/${tenantId}/departments`, { method: 'POST', body: JSON.stringify(data) }),
  updateDepartment: (tenantId, departmentId, data) => request(`/company/${tenantId}/departments/${departmentId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDepartment: (tenantId, departmentId) => request(`/company/${tenantId}/departments/${departmentId}`, { method: 'DELETE' }),

  // Müşteri Şirket Yönetimi (Company Admin) - Ünvanlar & AI Kontrolü (Madde 2)
  getCompanyJobTitles: (tenantId) => request(`/company/${tenantId}/job-titles`),
  getSystemJobTitleTemplates: (tenantId, params = {}) => {
    const query = new URLSearchParams();
    if (params.category) query.append('category', params.category);
    if (params.search) query.append('search', params.search);
    const qs = query.toString();
    return request(`/company/${tenantId}/job-titles/system-templates${qs ? `?${qs}` : ''}`);
  },
  createCompanyJobTitle: (tenantId, data) => request(`/company/${tenantId}/job-titles`, { method: 'POST', body: JSON.stringify(data) }),
  updateCompanyJobTitle: (tenantId, titleId, data) => request(`/company/${tenantId}/job-titles/${titleId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCompanyJobTitle: (tenantId, titleId) => request(`/company/${tenantId}/job-titles/${titleId}`, { method: 'DELETE' }),
  generateRolePrompt: (tenantId, data) => request(`/company/${tenantId}/generate-role-prompt`, { method: 'POST', body: JSON.stringify(data) }),

  // Müşteri Şirket Yönetimi (Company Admin) - AI Ajan İşe Alım & Yaşam Döngüsü (Madde 3)
  getAvailableLLMModels: (tenantId) => request(`/company/${tenantId}/llm-models`),
  getCompanyAIAgents: (tenantId, params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    const qs = query.toString();
    return request(`/company/${tenantId}/ai-agents${qs ? `?${qs}` : ''}`);
  },
  hireAIAgent: (tenantId, data) => request(`/company/${tenantId}/ai-agents`, { method: 'POST', body: JSON.stringify(data) }),
  updateAIAgent: (tenantId, agentId, data) => request(`/company/${tenantId}/ai-agents/${agentId}`, { method: 'PUT', body: JSON.stringify(data) }),
  terminateAIAgent: (tenantId, agentId, data = {}) => request(`/company/${tenantId}/ai-agents/${agentId}/terminate`, { method: 'POST', body: JSON.stringify(data) }),
  rehireAIAgent: (tenantId, agentId) => request(`/company/${tenantId}/ai-agents/${agentId}/rehire`, { method: 'POST' }),
  deleteAIAgent: (tenantId, agentId) => request(`/company/${tenantId}/ai-agents/${agentId}`, { method: 'DELETE' }),
  getAgentQuota: (tenantId) => request(`/company/${tenantId}/agent-quota`),

  // AI Ajan Uzmanlık Dokümanları, Web, Video & Deep Search Kaynak Yönetimi
  getAgentDocuments: (tenantId, agentId) => request(`/company/${tenantId}/ai-agents/${agentId}/documents`),
  uploadAgentDocument: (tenantId, agentId, formData) => request(`/company/${tenantId}/ai-agents/${agentId}/documents`, { method: 'POST', body: formData }),
  addAgentWebLink: (tenantId, agentId, data) => request(`/company/${tenantId}/ai-agents/${agentId}/web-links`, { method: 'POST', body: JSON.stringify(data) }),
  addAgentVideoLink: (tenantId, agentId, data) => request(`/company/${tenantId}/ai-agents/${agentId}/video-links`, { method: 'POST', body: JSON.stringify(data) }),
  triggerAgentDeepSearch: (tenantId, agentId, data) => request(`/company/${tenantId}/ai-agents/${agentId}/deep-search`, { method: 'POST', body: JSON.stringify(data) }),
  deepSearchSectorTitle: (tenantId, data) => request(`/company/${tenantId}/ai-agents/deep-search-sector-title`, { method: 'POST', body: JSON.stringify(data) }),
  deepSearchExistingAgentSectorTitle: (tenantId, agentId, modelCode) => request(`/company/${tenantId}/ai-agents/${agentId}/deep-search-sector-title${modelCode ? `?model_code=${encodeURIComponent(modelCode)}` : ''}`, { method: 'POST' }),
  deleteAgentDocument: (tenantId, agentId, documentId) => request(`/company/${tenantId}/ai-agents/${agentId}/documents/${documentId}`, { method: 'DELETE' }),
  getAgentDocumentDownloadUrl: (tenantId, agentId, documentId) => `${BASE_URL}/company/${tenantId}/ai-agents/${agentId}/documents/${documentId}/download`,
  downloadAgentDocument: (tenantId, agentId, documentId, fallbackName) =>
    downloadFile(`/company/${tenantId}/ai-agents/${agentId}/documents/${documentId}/download`, fallbackName),

  // Müşteri Şirket Yönetimi - Kurumsal Manifesto (Madde 6)
  updateCompanyManifesto: (tenantId, data) => request(`/company/${tenantId}/manifesto`, { method: 'PUT', body: JSON.stringify(data) }),
  generateCompanyManifesto: (tenantId, data) => request(`/company/${tenantId}/generate-manifesto`, { method: 'POST', body: JSON.stringify(data) }),

  // Müşteri Şirket Yönetimi (Company Admin) - Normal İnsan Kullanıcı Yönetimi (Madde 1)
  getCompanyUsers: (tenantId, params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.search) query.append('search', params.search);
    const qs = query.toString();
    return request(`/company/${tenantId}/users${qs ? `?${qs}` : ''}`);
  },
  getCompanyUserQuota: (tenantId) => request(`/company/${tenantId}/user-quota`),
  createCompanyUser: (tenantId, data) => request(`/company/${tenantId}/users`, { method: 'POST', body: JSON.stringify(data) }),
  updateCompanyUser: (tenantId, userId, data) => request(`/company/${tenantId}/users/${userId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCompanyUser: (tenantId, userId) => request(`/company/${tenantId}/users/${userId}`, { method: 'DELETE' }),

  // Platform departman ve unvan kataloğu (Adım 5)
  getCatalogSummary: () => request('/catalog/summary'),
  getCatalogDepartments: (params = {}) => request(`/catalog/departments?${new URLSearchParams(params).toString()}`),
  getCatalogTitles: (params = {}) => request(`/catalog/titles?${new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null)).toString()}`),
  getCatalogTitle: (id) => request(`/catalog/titles/${id}`),
  createCatalogDepartment: (data) => request('/catalog/departments', { method: 'POST', body: JSON.stringify(data) }),
  updateCatalogDepartment: (id, data) => request(`/catalog/departments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCatalogDepartment: (id) => request(`/catalog/departments/${id}`, { method: 'DELETE' }),
  createCatalogTitle: (data) => request('/catalog/titles', { method: 'POST', body: JSON.stringify(data) }),
  updateCatalogTitle: (id, data) => request(`/catalog/titles/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCatalogTitle: (id) => request(`/catalog/titles/${id}`, { method: 'DELETE' }),
  getCompanyCatalogRecommended: (tenantId) => request(`/company/${tenantId}/catalog/recommended`),
  getHireOptions: (tenantId) => request(`/company/${tenantId}/hire/options`),
  getHireTitles: (tenantId, params) => request(`/company/${tenantId}/hire/titles?${new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString()}`),
  getHirePreview: (tenantId, titleId, departmentName) => request(`/company/${tenantId}/hire/preview?title_id=${titleId}&department_name=${encodeURIComponent(departmentName || '')}`),
  importCatalogDepartments: (tenantId, ids) => request(`/company/${tenantId}/departments/from-catalog`, { method: 'POST', body: JSON.stringify({ catalog_department_ids: ids }) }),

  // Öğrenme dokümanları (Adım 5.4): AI personel, şirket unvanı ve platform katalog unvanı
  getDocument: (id) => request(`/documents/${id}`),
  approveDocument: (id, card = {}) => request(`/documents/${id}/approve`, { method: 'POST', body: JSON.stringify(card) }),
  rejectDocument: (id, reason) => request(`/documents/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),
  testDocument: (id) => request(`/documents/${id}/test`, { method: 'POST' }),
  reprocessDocument: (id) => request(`/documents/${id}/reprocess`, { method: 'POST' }),
  uploadDocumentVersion: (id, formData) => request(`/documents/${id}/versions`, { method: 'POST', body: formData }),
  deleteDocument: (id) => request(`/documents/${id}`, { method: 'DELETE' }),
  downloadDocument: (id, fallbackName) => downloadFile(`/documents/${id}/download`, fallbackName),
  getCompanyTitleDocuments: (tenantId, titleId) => request(`/company/${tenantId}/job-titles/${titleId}/documents`),
  uploadCompanyTitleDocument: (tenantId, titleId, formData) => request(`/company/${tenantId}/job-titles/${titleId}/documents`, { method: 'POST', body: formData }),
  getPlatformTitleDocuments: (titleId) => request(`/catalog/titles/${titleId}/documents`),
  uploadPlatformTitleDocument: (titleId, formData) => request(`/catalog/titles/${titleId}/documents`, { method: 'POST', body: formData }),

  // Kredi ve yapay zeka kullanımı (Adım 4)
  getCompanyCredits: (tenantId) => request(`/company/${tenantId}/credits`),
  topupCredits: (tenantId, data) => request(`/tenants/${tenantId}/credits/topup`, { method: 'POST', body: JSON.stringify(data) }),
  getPlatformLLMUsage: () => request('/system/llm/usage'),
  syncEvrenModels: () => request('/models/sync-evren', { method: 'POST' }),
  getModelSettings: () => request('/system/settings/models'),
  updateModelSettings: (settings) => request('/system/settings/models', { method: 'PUT', body: JSON.stringify({ settings }) }),

  // Beyin AI (şirketin organizatör yapay zekası)
  getBrainSettings: (tenantId) => request(`/company/${tenantId}/brain/settings`),
  updateBrainSettings: (tenantId, brainModelCode) => request(`/company/${tenantId}/brain/settings`, { method: 'PUT', body: JSON.stringify({ brain_model_code: brainModelCode || null }) }),
  getBrainHistory: (tenantId) => request(`/company/${tenantId}/brain/history`),
  sendBrainMessage: (tenantId, content) => request(`/company/${tenantId}/brain/chat`, { method: 'POST', body: JSON.stringify({ content }) }),

  // Süper Yönetici asistanı
  getAssistantHistory: () => request('/system/assistant/history'),
  sendAssistantMessage: (content) => request('/system/assistant/chat', { method: 'POST', body: JSON.stringify({ content }) }),
};


