/**
 * RECOrion API Client
 * FastAPI Backend ile haberleşme katmanı
 */

const BASE_URL = '/api/v1';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP Error ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Hatası [${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  // Sağlık Kontrolü
  getHealth: () => request('/health'),

  // EVREN Model Kataloğu (13 Model)
  getModels: (modelType) => request(`/models/${modelType ? `?model_type=${modelType}` : ''}`),

  // Şirketler, Paketler & NACE
  getTenants: () => request('/tenants/'),
  getPlans: () => request('/tenants/plans'),
  getJobTitles: (category = null) => request(`/actors/job-titles${category ? `?category=${category}` : ''}`),
  getNaceCatalog: () => request('/tenants/nace-catalog'),
  searchNace: (query = '', limit = 30) => request(`/tenants/nace-catalog?query=${encodeURIComponent(query)}&limit=${limit}`),
  submitPurchaseRequest: (data) => request('/tenants/purchase-request', { method: 'POST', body: JSON.stringify(data) }),
  getLeads: () => request('/tenants/leads'),

  // Personeller (İnsan & AI Aktörler)
  getActors: (tenantId, actorType) => {
    const params = new URLSearchParams();
    if (tenantId) params.append('tenant_id', tenantId);
    if (actorType) params.append('actor_type', actorType);
    return request(`/actors/?${params.toString()}`);
  },

  // Projeler & İş Akışı Görevleri
  getProjects: (tenantId) => request(`/projects/${tenantId ? `?tenant_id=${tenantId}` : ''}`),
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

  // 2 Kademeli Kolektif Hafıza
  getMemoryItems: (tenantId, scope = null) => {
    const params = new URLSearchParams({ tenant_id: tenantId });
    if (scope) params.append('scope', scope);
    return request(`/memory/?${params.toString()}`);
  },
  searchMemory: (payload) => request('/memory/search', { method: 'POST', body: JSON.stringify(payload) }),
  promoteMemory: (memoryId) => request(`/memory/promote/${memoryId}`, { method: 'POST' }),

  // Kimlik Doğrulama & Profil (Auth & RBAC)
  login: (credentials) => request('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  getProfile: (actorId) => request(`/auth/profile/${actorId}`),
  updateProfile: (actorId, data) => request(`/auth/profile/${actorId}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Sistem İzinleri & Ayarları (Süper Admin)
  getPermissions: () => request('/system/permissions'),
  createPermission: (data) => request('/system/permissions', { method: 'POST', body: JSON.stringify(data) }),
  updatePermission: (permId, data) => request(`/system/permissions/${permId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePermission: (permId) => request(`/system/permissions/${permId}`, { method: 'DELETE' }),
  getSystemSettings: () => request('/system/settings'),
  setDefaultManifestoModel: (modelCode) => request('/system/settings/default-manifesto-model', { method: 'POST', body: JSON.stringify({ model_code: modelCode }) }),

  // EVREN Modelleri CRUD
  createModel: (data) => request('/models', { method: 'POST', body: JSON.stringify(data) }),
  updateModel: (modelId, data) => request(`/models/${modelId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteModel: (modelId) => request(`/models/${modelId}`, { method: 'DELETE' }),

  // Kiralama Paketleri CRUD
  createPlan: (data) => request('/tenants/plans', { method: 'POST', body: JSON.stringify(data) }),
  updatePlan: (planId, data) => request(`/tenants/plans/${planId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePlan: (planId) => request(`/tenants/plans/${planId}`, { method: 'DELETE' }),

  // NACE Kodları Kataloğu CRUD
  createNace: (data) => request('/tenants/nace-catalog', { method: 'POST', body: JSON.stringify(data) }),
  updateNace: (code, data) => request(`/tenants/nace-catalog/${code}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteNace: (code) => request(`/tenants/nace-catalog/${code}`, { method: 'DELETE' }),

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

  // Şirket Gelişmiş İşlemleri (Madde 9, 13, 14)
  adminCreateTenant: (data) => request('/tenants/admin-create', { method: 'POST', body: JSON.stringify(data) }),
  sendManualReminder: (tenantId) => request(`/tenants/${tenantId}/send-reminder`, { method: 'POST' }),
  sendManualWelcome: (tenantId) => request(`/tenants/${tenantId}/send-welcome`, { method: 'POST' }),
  generateManifesto: (data) => request('/tenants/generate-manifesto', { method: 'POST', body: JSON.stringify(data) }),
};

