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
  // Proje maliyeti (Adım 7.5)
  getProjectCosts: (projectId) => request(`/projects/${projectId}/costs`),
  setProjectBudget: (projectId, amount, note) => request(`/projects/${projectId}/budget`, { method: 'PUT', body: JSON.stringify({ budget_try: amount, budget_note: note || null }) }),
  addCostItem: (projectId, data) => request(`/projects/${projectId}/cost-items`, { method: 'POST', body: JSON.stringify(data) }),
  updateCostItem: (projectId, itemId, data) => request(`/projects/${projectId}/cost-items/${itemId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCostItem: (projectId, itemId) => request(`/projects/${projectId}/cost-items/${itemId}`, { method: 'DELETE' }),
  uploadCostAttachment: (projectId, itemId, formData) => request(`/projects/${projectId}/cost-items/${itemId}/attachment`, { method: 'POST', body: formData }),
  downloadCostAttachment: (projectId, itemId, name) => downloadFile(`/projects/${projectId}/cost-items/${itemId}/attachment`, name),
  // Entegrasyonlar / MCP (Adım 10)
  getConnectors: () => request('/integrations/connectors'),
  getIntegrations: (tenantId) => request(`/company/${tenantId}/integrations`),
  createIntegration: (tenantId, data) => request(`/company/${tenantId}/integrations`, { method: 'POST', body: JSON.stringify(data) }),
  updateIntegration: (tenantId, id, data) => request(`/company/${tenantId}/integrations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  testIntegration: (tenantId, id) => request(`/company/${tenantId}/integrations/${id}/test`, { method: 'POST' }),
  getIntegrationTools: (tenantId, id) => request(`/company/${tenantId}/integrations/${id}/tools`),
  getIntegrationGrants: (tenantId, id) => request(`/company/${tenantId}/integrations/${id}/grants`),
  setIntegrationGrants: (tenantId, id, grants) => request(`/company/${tenantId}/integrations/${id}/grants`, { method: 'PUT', body: JSON.stringify({ grants }) }),
  getToolCalls: (tenantId, status) => request(`/company/${tenantId}/tool-calls${status ? `?status=${status}` : ''}`),
  getMyToolApprovals: () => request('/me/tool-approvals'),
  decideToolCall: (id, approve, note) => request(`/tool-calls/${id}/decision`, { method: 'POST', body: JSON.stringify({ approve, note: note || null }) }),
  // Bağlantı kataloğu ve tek tık giriş (ADIM 12.1)
  getIntegrationCatalog: () => request('/integrations/catalog'),
  adviseIntegration: (tenantId, text) => request(`/company/${tenantId}/integrations/advise`, { method: 'POST', body: JSON.stringify({ text }) }),
  startIntegrationOAuth: (tenantId, id) => request(`/company/${tenantId}/integrations/${id}/oauth/start`, { method: 'POST' }),
  disconnectIntegrationOAuth: (tenantId, id) => request(`/company/${tenantId}/integrations/${id}/oauth/disconnect`, { method: 'POST' }),
  // Ortak iş nesneleri ve eşleme stüdyosu (ADIM 12.2–12.3)
  getBusinessObjects: () => request('/integrations/objects'),
  getMappings: (tenantId, connectionId) => request(`/company/${tenantId}/mappings${connectionId ? `?connection_id=${connectionId}` : ''}`),
  getMappingTemplates: (tenantId, connector) => request(`/company/${tenantId}/mappings/templates?connector=${connector}`),
  createMapping: (tenantId, data) => request(`/company/${tenantId}/mappings`, { method: 'POST', body: JSON.stringify(data) }),
  updateMapping: (tenantId, id, data) => request(`/company/${tenantId}/mappings/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  checkMapping: (tenantId, id) => request(`/company/${tenantId}/mappings/${id}/check`, { method: 'POST' }),
  dryRunMapping: (tenantId, id, sample) => request(`/company/${tenantId}/mappings/${id}/dry-run`, { method: 'POST', body: JSON.stringify({ sample: sample || null }) }),
  approveMapping: (tenantId, id) => request(`/company/${tenantId}/mappings/${id}/approve`, { method: 'POST' }),
  archiveMapping: (tenantId, id) => request(`/company/${tenantId}/mappings/${id}/archive`, { method: 'POST' }),
  suggestMapping: (tenantId, data) => request(`/company/${tenantId}/mappings/suggest`, { method: 'POST', body: JSON.stringify(data) }),

  // Otomasyonlar (ADIM 13.2–13.5): olayla başlayan işler, RECDx uygulaması hazır kuralları, çalışma günlüğü
  getAutomations: (tenantId) => request(`/company/${tenantId}/automations`),
  createAutomation: (tenantId, data) => request(`/company/${tenantId}/automations`, { method: 'POST', body: JSON.stringify(data) }),
  updateAutomation: (tenantId, id, data) => request(`/company/${tenantId}/automations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  setAutomationStatus: (tenantId, id, status) => request(`/company/${tenantId}/automations/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  rotateAutomationSecret: (tenantId, id) => request(`/company/${tenantId}/automations/${id}/rotate-secret`, { method: 'POST' }),
  testAutomation: (tenantId, id, payload, eventType) => request(`/company/${tenantId}/automations/${id}/test`, { method: 'POST', body: JSON.stringify({ payload, event_type: eventType || null }) }),
  runAutomation: (tenantId, id) => request(`/company/${tenantId}/automations/${id}/run`, { method: 'POST' }),
  getAutomationLog: (tenantId, id) => request(`/company/${tenantId}/automations/${id}/log`),
  getCompanyAutomationLog: (tenantId) => request(`/company/${tenantId}/automation-log`),
  suggestAutomation: (tenantId, text, sample) => request(`/company/${tenantId}/automations/suggest`, { method: 'POST', body: JSON.stringify({ text, sample: sample || null }) }),
  getAutomationPresets: (tenantId, app) => request(`/company/${tenantId}/automations/presets/${app}`),
  installAutomationPresets: (tenantId, app, data) => request(`/company/${tenantId}/automations/presets/${app}`, { method: 'POST', body: JSON.stringify(data) }),
  getTargetFields: (tenantId, cid, target) => request(`/company/${tenantId}/integrations/${cid}/target-fields?${new URLSearchParams(target).toString()}`),
  // Çıktıdan kayda aktarım (ADIM 12.4)
  getTransferOptions: (projectId) => request(`/projects/${projectId}/transfer-options`),
  getProjectTransfers: (projectId) => request(`/projects/${projectId}/transfers`),
  proposeTaskTransfer: (taskId, mappingId) => request(`/tasks/${taskId}/transfers`, { method: 'POST', body: JSON.stringify({ mapping_id: mappingId }) }),
  proposeProjectTransfer: (projectId, mappingId) => request(`/projects/${projectId}/transfers`, { method: 'POST', body: JSON.stringify({ mapping_id: mappingId }) }),
  setTaskTransferRules: (taskId, ids) => request(`/tasks/${taskId}/transfer-rules`, { method: 'PUT', body: JSON.stringify({ mapping_ids: ids }) }),
  setProjectTransferOnClose: (projectId, ids) => request(`/projects/${projectId}/transfer-on-close`, { method: 'PUT', body: JSON.stringify({ mapping_ids: ids }) }),
  fixTransfer: (id, object) => request(`/transfers/${id}`, { method: 'PUT', body: JSON.stringify({ object }) }),
  decideTransfer: (id, approve, note) => request(`/transfers/${id}/decision`, { method: 'POST', body: JSON.stringify({ approve, note: note || null }) }),
  rollbackTransfer: (id) => request(`/transfers/${id}/rollback`, { method: 'POST' }),
  retryTransfer: (id) => request(`/transfers/${id}/retry`, { method: 'POST' }),
  getMyTransferApprovals: () => request('/me/transfer-approvals'),
  getCompanyTransfers: (tenantId) => request(`/company/${tenantId}/transfers`),
  getTransferPolicy: (tenantId) => request(`/company/${tenantId}/transfer-policy`),
  setTransferPolicy: (tenantId, data) => request(`/company/${tenantId}/transfer-policy`, { method: 'PUT', body: JSON.stringify(data) }),
  // RECOrion MCP sunucusu: kişisel erişim anahtarları (ADIM 12.6)
  getPersonalTokens: () => request('/me/personal-tokens'),
  createPersonalToken: (data) => request('/me/personal-tokens', { method: 'POST', body: JSON.stringify(data) }),
  revokePersonalToken: (id) => request(`/me/personal-tokens/${id}`, { method: 'DELETE' }),
  // RECDx uygulamaları (ADIM 13.1)
  getPublicRecdxApps: (planCode) => request(`/recdx-apps${planCode ? `?plan_code=${planCode}` : ''}`),
  getCompanyRecdxApps: (tenantId) => request(`/company/${tenantId}/recdx-apps`),
  setCompanyRecdxApps: (tenantId, data) => request(`/company/${tenantId}/recdx-apps`, { method: 'PUT', body: JSON.stringify(data) }),
  getAppRequests: () => request('/system/recdx-app-requests'),
  updateAppRequest: (id, data) => request(`/system/recdx-app-requests/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  retryAppRequest: (id) => request(`/system/recdx-app-requests/${id}/retry`, { method: 'POST' }),
  getCatalogAdmin: () => request('/system/integration-catalog'),
  createCatalogEntry: (data) => request('/system/integration-catalog', { method: 'POST', body: JSON.stringify(data) }),
  updateCatalogEntry: (id, data) => request(`/system/integration-catalog/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  newEdgeAgentToken: (tenantId, id) => request(`/company/${tenantId}/integrations/${id}/agent-token`, { method: 'POST' }),
  // Dashboard (Adım 9)
  getPlatformDashboard: (days = 7) => request(`/system/dashboard?days=${days}`),
  getPlatformHealth: (refresh = false) => request(`/system/health${refresh ? '?refresh=true' : ''}`),
  getCompanyDashboard: (tenantId, days = 30, departmentId = null) => request(`/company/${tenantId}/dashboard?${new URLSearchParams({ days, ...(departmentId ? { department_id: departmentId } : {}) }).toString()}`),
  // Proje kod deposu (Adım 8.5)
  getProjectRepository: (projectId) => request(`/projects/${projectId}/repository`),
  setProjectRepository: (projectId, mode) => request(`/projects/${projectId}/repository`, { method: 'PUT', body: JSON.stringify({ mode }) }),
  getRepositoryFile: (projectId, ref, path) => request(`/projects/${projectId}/repository/file?${new URLSearchParams({ ref, path }).toString()}`),
  mergeRepositoryStep: (projectId, taskId) => request(`/projects/${projectId}/repository/steps/${taskId}/merge`, { method: 'POST' }),
  getMirrorTargets: (projectId) => request(`/projects/${projectId}/repository/mirror-targets`),
  setRepositoryMirror: (projectId, connectionId, repo) => request(`/projects/${projectId}/repository/mirror`, { method: 'PUT', body: JSON.stringify({ connection_id: connectionId, repo }) }),
  clearRepositoryMirror: (projectId) => request(`/projects/${projectId}/repository/mirror`, { method: 'DELETE' }),
  downloadProjectCostReport: (projectId) => downloadFile(`/projects/${projectId}/costs/export.xlsx`, 'proje-maliyet.xlsx'),
  // LLM TL fiyat listesi (Adım 7.5.1, Süper Admin)
  getLlmPrices: () => request('/system/llm-prices'),
  addLlmPrice: (data) => request('/system/llm-prices', { method: 'POST', body: JSON.stringify(data) }),
  setEvrenCrRate: (rate) => request('/system/llm-prices/cr-rate', { method: 'PUT', body: JSON.stringify({ cr_to_try: rate }) }),
  // Her yerden onay ve bildirim tercihleri (Adım 7.3)
  getApproval: (token) => request(`/approvals/${encodeURIComponent(token)}`),
  decideApproval: (token, approve, note) => request(`/approvals/${encodeURIComponent(token)}`, { method: 'POST', body: JSON.stringify({ approve, note: note || null }) }),
  getMyApprovals: () => request('/me/approvals'),
  getNotificationPrefs: () => request('/auth/notification-prefs'),
  setNotificationPrefs: (prefs) => request('/auth/notification-prefs', { method: 'PUT', body: JSON.stringify(prefs) }),
  // İş akışı (Adım 7.1)
  getProjectWorkflow: (projectId) => request(`/projects/${projectId}/workflow`),
  submitTask: (taskId, note) => request(`/tasks/${taskId}/submit`, { method: 'POST', body: JSON.stringify({ note: note || null }) }),
  decideTask: (taskId, approve, note) => request(`/tasks/${taskId}/decision`, { method: 'POST', body: JSON.stringify({ approve, note: note || null }) }),
  getTaskArtifact: (taskId, artifactId) => request(`/tasks/${taskId}/artifacts/${artifactId}`),
  releaseTask: (taskId, action, note, assigneeId) => request(`/tasks/${taskId}/release`, { method: 'POST', body: JSON.stringify({ action, note: note || null, assignee_actor_id: assigneeId || null }) }),
  createProject: (data) => request('/projects/', { method: 'POST', body: JSON.stringify(data) }),
  getRegulationPacksAdmin: () => request('/system/regulation-packs'),
  updateRegulationPack: (id, data) => request(`/system/regulation-packs/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  publishRegulationPack: (id, data) => request(`/system/regulation-packs/${id}/publish`, { method: 'POST', body: JSON.stringify(data) }),
  getCompanyRegulationPacks: (tenantId) => request(`/company/${tenantId}/regulation-packs`),
  getCompanyRegulationPack: (tenantId, id) => request(`/company/${tenantId}/regulation-packs/${id}`),
  setCompanyRegulationPack: (tenantId, id, enabled) => request(`/company/${tenantId}/regulation-packs/${id}`, { method: 'PUT', body: JSON.stringify({ enabled }) }),
  uploadMeeting: (tenantId, formData) => request(`/company/${tenantId}/meetings`, { method: 'POST', body: formData }),
  getMeeting: (tenantId, id) => request(`/company/${tenantId}/meetings/${id}`),
  meetingToProject: (tenantId, id, data) => request(`/company/${tenantId}/meetings/${id}/project`, { method: 'POST', body: JSON.stringify(data) }),
  getModelRouter: () => request('/system/model-router'),
  startQualityRun: (models) => request('/system/model-router/runs', { method: 'POST', body: JSON.stringify({ models }) }),
  getQualityRun: (id) => request(`/system/model-router/runs/${id}`),
  setModelRoute: (taskType, modelCode, runId, note) => request('/system/model-router/routes', { method: 'POST', body: JSON.stringify({ task_type: taskType, model_code: modelCode, run_id: runId, note }) }),
  getProjectTemplates: () => request('/project-templates'),
  getProjectTemplate: (id) => request(`/project-templates/${id}`),
  useProjectTemplate: (id, data) => request(`/project-templates/${id}/use`, { method: 'POST', body: JSON.stringify(data) }),
  saveProjectAsTemplate: (projectId, data) => request(`/projects/${projectId}/save-as-template`, { method: 'POST', body: JSON.stringify(data) }),
  updateProjectTemplate: (id, data) => request(`/project-templates/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getPlatformTemplates: () => request('/system/project-templates'),
  createPlatformTemplate: (data) => request('/system/project-templates', { method: 'POST', body: JSON.stringify(data) }),
  updatePlatformTemplate: (id, data) => request(`/system/project-templates/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
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
  // Canlı akış bileti (Adım 8.2): 60 sn geçerli, tek kullanımlık
  getLiveTicket: (projectId) => request('/live/ticket', { method: 'POST', body: JSON.stringify({ project_id: projectId }) }),
  learnFromTaskChat: (taskId) => request(`/chat/learn/${taskId}`, { method: 'POST' }),

  // 2 Kademeli Kolektif Hafıza
  getMemoryItems: (tenantId, scope = null) => {
    const params = new URLSearchParams({ tenant_id: tenantId });
    if (scope) params.append('scope', scope);
    return request(`/memory/?${params.toString()}`);
  },
  searchMemory: (payload) => request('/memory/search', { method: 'POST', body: JSON.stringify(payload) }),
  promoteMemory: (memoryId) => request(`/memory/promote/${memoryId}`, { method: 'POST' }),
  rejectMemory: (memoryId, note) => request(`/memory/${memoryId}/reject`, { method: 'POST', body: JSON.stringify({ note: note || null }) }),
  // Onaylı bilgiyi geri alma (Adım 8.4): gerekçe zorunlu
  revokeMemory: (memoryId, note) => request(`/memory/${memoryId}/revoke`, { method: 'POST', body: JSON.stringify({ note }) }),
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
  // #349: RECAi adları ve yetenekleri (gerçek model adı müşteriye gelmez)
  getCompanyRecai: (tenantId) => request(`/company/${tenantId}/recai`),
  getRecaiTiers: () => request('/system/recai-tiers'),
  updateRecaiTier: (code, data) => request(`/system/recai-tiers/${code}`, { method: 'PUT', body: JSON.stringify(data) }),
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


