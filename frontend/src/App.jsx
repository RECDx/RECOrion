import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LeftPane from './components/LeftPane';
import MiddlePane from './components/MiddlePane';
import RightPane from './components/RightPane';
import CreateTaskModal from './components/CreateTaskModal';
import OfficialLanding from './components/OfficialLanding';
import SuperAdminConsole from './components/SuperAdminConsole';
import CompanyAdminConsole from './components/CompanyAdminConsole';
import ResetPassword from './components/ResetPassword';
import ProjectHub from './components/projects/ProjectHub';
import ProjectPlanner from './components/projects/ProjectPlanner';
import { api, session } from './api';
import { notify } from './ui/feedback';

// Kayıtlı kullanıcı yalnızca geçerli bir oturum token'ı varsa kullanılır
function loadSavedUser() {
  try {
    if (!session.getToken()) return null;
    const u = localStorage.getItem('recorion_user');
    return u ? JSON.parse(u) : null;
  } catch {
    return null;
  }
}

export default function App() {
  const [currentUser, setCurrentUser] = useState(loadSavedUser);

  const [currentView, setCurrentView] = useState(() => {
    const hash = typeof window !== 'undefined' ? window.location.hash : '';
    const savedUser = loadSavedUser();
    const savedView = typeof window !== 'undefined' ? localStorage.getItem('recorion_current_view') : null;

    if (hash.startsWith('#/super-admin') && savedUser?.role === 'SUPER_ADMIN') {
      return 'SUPER_ADMIN_CONSOLE';
    }
    if (hash === '#/company-admin' && savedUser) {
      return 'COMPANY_ADMIN_CONSOLE';
    }
    if (hash.startsWith('#/workspace') && savedUser) {
      return 'WORKSPACE';
    }
    if (savedUser?.role === 'SUPER_ADMIN') {
      return 'SUPER_ADMIN_CONSOLE';
    }
    if (savedUser?.role === 'COMPANY_ADMIN') {
      return 'COMPANY_ADMIN_CONSOLE';
    }
    if (hash === '#/landing') {
      return 'LANDING';
    }
    if (savedView === 'COMPANY_ADMIN_CONSOLE' && savedUser) {
      return 'COMPANY_ADMIN_CONSOLE';
    }
    if (savedView === 'SUPER_ADMIN_CONSOLE' && savedUser?.role === 'SUPER_ADMIN') {
      return 'SUPER_ADMIN_CONSOLE';
    }
    if (savedView === 'WORKSPACE' && savedUser) {
      return 'WORKSPACE';
    }
    return 'LANDING';
  });

  const [health, setHealth] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [actors, setActors] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('glm-5.3');
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [messages, setMessages] = useState([]);
  const [memoryItems, setMemoryItems] = useState([]);
  const [chatFilter, setChatFilter] = useState('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  // KVKK modu: RECDx yöneticisi başka bir şirketin Work Space'ini içerik olmadan görüntüler
  const [kvkkRestricted, setKvkkRestricted] = useState(false);
  // Tablet/telefonda aynı anda tek bölme gösterilir
  const [activePane, setActivePane] = useState('middle');
  // Work Space modu: HUB (proje listesi), PLANNER (proje planlama), WORK (görev sohbeti)
  const [workspaceMode, setWorkspaceMode] = useState(() => (typeof window !== 'undefined' && /^#\/workspace\?project=/.test(window.location.hash) ? 'PLANNER' : 'HUB'));
  // E-posta/Telegram bildirimindeki #/workspace?project=<id> bağlantısı doğrudan projeyi açar
  const [plannerProjectId, setPlannerProjectId] = useState(() => {
    const m = typeof window !== 'undefined' ? window.location.hash.match(/^#\/workspace\?project=([0-9a-f-]{36})/i) : null;
    return m ? m[1] : null;
  });

  // URL Hash ve Görünüm Eşitlemesi
  useEffect(() => {
    try {
      if (window.location.hash.startsWith('#/reset-password')) return; // şifre belirleme sayfası adresini koru
      localStorage.setItem('recorion_current_view', currentView);
      if (currentView === 'SUPER_ADMIN_CONSOLE') {
        if (!window.location.hash.startsWith('#/super-admin')) {
          window.history.replaceState(null, '', '#/super-admin/dashboard');
        }
      } else if (currentView === 'COMPANY_ADMIN_CONSOLE') {
        if (window.location.hash !== '#/company-admin') {
          window.history.replaceState(null, '', '#/company-admin');
        }
      } else if (currentView === 'WORKSPACE') {
        if (!window.location.hash.startsWith('#/workspace')) {
          window.history.replaceState(null, '', '#/workspace');
        }
      } else {
        if (window.location.hash !== '#/landing') {
          window.history.replaceState(null, '', '#/landing');
        }
      }
    } catch (e) {
      console.warn("Routing sync error:", e);
    }
  }, [currentView]);

  // Tarayıcı İleri/Geri Butonları Dinleme
  useEffect(() => {
    const handleLocationChange = () => {
      const hash = window.location.hash;
      if (hash.startsWith('#/reset-password')) return;
      const u = currentUser || loadSavedUser();

      if (hash.startsWith('#/super-admin')) {
        if (u?.role === 'SUPER_ADMIN') {
          setCurrentView('SUPER_ADMIN_CONSOLE');
        } else {
          setCurrentView('LANDING');
        }
      } else if (hash === '#/company-admin') {
        if (u) {
          setCurrentView('COMPANY_ADMIN_CONSOLE');
        } else {
          setCurrentView('LANDING');
        }
      } else if (hash.startsWith('#/workspace')) {
        if (u) {
          setCurrentView('WORKSPACE');
        } else {
          setCurrentView('LANDING');
        }
      } else {
        // Geri tuşuyla #/landing veya boş hash'e gelindiyse ve kullanıcı SUPER_ADMIN ise konsolda tut
        if (u?.role === 'SUPER_ADMIN') {
          setCurrentView('SUPER_ADMIN_CONSOLE');
          window.history.replaceState(null, '', '#/super-admin/dashboard');
        } else if (u?.role === 'COMPANY_ADMIN') {
          setCurrentView('COMPANY_ADMIN_CONSOLE');
          window.history.replaceState(null, '', '#/company-admin');
        } else {
          setCurrentView('LANDING');
        }
      }
    };

    window.addEventListener('popstate', handleLocationChange);
    window.addEventListener('hashchange', handleLocationChange);
    return () => {
      window.removeEventListener('popstate', handleLocationChange);
      window.removeEventListener('hashchange', handleLocationChange);
    };
  }, [currentUser]);

  // 1. Initial Load: sağlık durumu; oturum varsa kullanıcının kendi şirketi
  useEffect(() => {
    async function initPlatform() {
      try {
        setHealth(await api.getHealth());
      } catch (err) {
        console.error("Sağlık kontrolü hatası:", err);
      }

      const savedUser = loadSavedUser();
      if (!savedUser?.tenant_id) return;
      try {
        const mData = await api.getModels();
        setModels(mData);
        if (mData.length > 0) setSelectedModel(mData[0].model_code);
        await loadTenantWorkspace(savedUser.tenant_id);
      } catch (err) {
        console.error("Platform başlatma hatası:", err);
      }
    }
    initPlatform();
  }, []);

  // Oturum süresi dolarsa veya token geçersizse otomatik çıkış
  useEffect(() => {
    const onUnauthorized = () => {
      handleLogout();
      notify('Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın.');
    };
    window.addEventListener('recorion:unauthorized', onUnauthorized);
    return () => window.removeEventListener('recorion:unauthorized', onUnauthorized);
  }, []);

  // 2. Load Tasks when Active Project Changes
  useEffect(() => {
    if (!activeProject) return;
    async function loadTasks() {
      try {
        const tList = await api.getTasks(activeProject.id);
        setTasks(tList);
        if (tList.length > 0) {
          setSelectedTask(tList[0]);
        }
      } catch (err) {
        console.error("Görev yükleme hatası:", err);
      }
    }
    loadTasks();
  }, [activeProject]);

  // 3. Load Chat History when Selected Task or Chat Filter Changes
  useEffect(() => {
    if (!selectedTask) return;
    async function loadChat() {
      try {
        let msgList = [];
        if (chatFilter === 'ALL') {
          // Task-specific history
          msgList = await api.getChatHistory(selectedTask.id, null, true);
        } else if (chatFilter === 'MY') {
          // Yalnızca giriş yapmış kullanıcının mesajları
          msgList = await api.getChatHistory(selectedTask.id, currentUser?.actor_id || null, true);
        } else if (chatFilter === 'A2A') {
          // Project-wide Agent-to-Agent negotiations
          msgList = await api.getProjectChatHistory(selectedTask.project_id, null, 'AGENT_TO_AGENT');
        }
        setMessages(msgList);
      } catch (err) {
        console.error("Sohbet geçmişi çekme hatası:", err);
      }
    }
    loadChat();
  }, [selectedTask, chatFilter, actors]);

  // 4. Send Message (Gemini Web Persistent Flow)
  const handleSendMessage = async ({ content, isPrivate, overrideModel }) => {
    if (!selectedTask || !content.trim()) return;

    setIsLoading(true);

    try {
      const response = await api.sendMessage({
        task_id: selectedTask.id,
        content: content,
        override_model_code: overrideModel || selectedModel,
        is_private: isPrivate,
        message_type: 'CHAT'
      });

      // Append messages
      setMessages((prev) => [
        ...prev,
        response.user_message,
        {
          ...response.assistant_message,
          citations: response.citations
        }
      ]);

      // Refresh memory items if citations or updates occurred
      if (tenant?.id) {
        const updatedMem = await api.getMemoryItems(tenant.id);
        setMemoryItems(updatedMem);
      }
    } catch (err) {
      notify(`Mesaj gönderilemedi: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 5. Create New Task
  const handleCreateTask = async (taskData) => {
    if (!activeProject) return;
    try {
      const newTask = await api.createTask(activeProject.id, taskData);
      setTasks((prev) => [newTask, ...prev]);
      setSelectedTask(newTask);
    } catch (err) {
      notify(`Görev oluşturulamadı: ${err.message}`);
    }
  };

  // 6. Promote Memory to Corporate Memory (NS_GLOBAL)
  const handlePromoteMemory = async (memoryId) => {
    try {
      await api.promoteMemory(memoryId);
      if (tenant?.id) {
        const updatedMem = await api.getMemoryItems(tenant.id);
        setMemoryItems(updatedMem);
      }
      notify("Bilgi başarıyla Şirket Kurum Hafızasına (NS_GLOBAL) terfi ettirildi!");
    } catch (err) {
      notify(`Hafıza terfi hatası: ${err.message}`);
    }
  };

  // Şirketin Work Space verilerini (personel, proje, hafıza) yükler
  async function loadTenantWorkspace(tenantId) {
    setKvkkRestricted(false);
    const details = await api.getTenantDetails(tenantId);
    const userTenant = details?.tenant || details;
    if (!userTenant) return;
    setTenant(userTenant);
    setActors(await api.getActors(userTenant.id));
    const prjData = await api.getProjects(userTenant.id);
    setProjects(prjData);
    if (prjData.length > 0) {
      setActiveProject(prjData[0]);
    } else {
      setActiveProject(null);
      setTasks([]);
      setSelectedTask(null);
    }
    setMemoryItems(await api.getMemoryItems(userTenant.id));
  }

  const handleLogout = () => {
    session.clear();
    setCurrentUser(null);
    setTenant(null);
    setActors([]);
    setProjects([]);
    setActiveProject(null);
    setTasks([]);
    setSelectedTask(null);
    setMemoryItems([]);
    setCurrentView('LANDING');
    window.location.hash = '#/landing';
  };

  const handleEnterPlatform = async (loggedInUser) => {
    const user = loggedInUser || currentUser;
    if (!user) return;
    setCurrentUser(user);

    // Giriş yapan kullanıcının şirketini derhal yükle ve senkronize et
    if (user.tenant_id) {
      try {
        const mData = await api.getModels();
        setModels(mData);
        if (mData.length > 0) setSelectedModel(mData[0].model_code);
        await loadTenantWorkspace(user.tenant_id);
      } catch (e) {
        console.warn("Giriş yapan kullanıcının şirketi senkronize edilemedi:", e);
      }
    }

    if (user.role === 'SUPER_ADMIN') {
      setCurrentView('SUPER_ADMIN_CONSOLE');
      window.location.hash = '#/super-admin/dashboard';
    } else if (user.role === 'COMPANY_ADMIN') {
      setCurrentView('COMPANY_ADMIN_CONSOLE');
      window.location.hash = '#/company-admin';
    } else {
      setCurrentView('WORKSPACE');
      window.location.hash = '#/workspace';
    }
  };

  const handleSwitchTenant = async (selectedTenant) => {
    if (!selectedTenant) return;
    // KVKK: RECDx yöneticileri başka şirketin Work Space'ine geçebilir ama içeriğini (proje, sohbet, hafıza) göremez
    if (currentUser?.tenant_id && selectedTenant.id !== currentUser.tenant_id) {
      setTenant(selectedTenant);
      setActors([]);
      setProjects([]);
      setActiveProject(null);
      setTasks([]);
      setSelectedTask(null);
      setMessages([]);
      setMemoryItems([]);
      setKvkkRestricted(true);
      setCurrentView('WORKSPACE');
      return;
    }
    try {
      await loadTenantWorkspace(selectedTenant.id);
    } catch (err) {
      console.error("Şirket verileri yüklenirken hata:", err);
    }
    setCurrentView('WORKSPACE');
  };

  // E-postadaki şifre belirleme bağlantısı (#/reset-password?token=...) oturumdan bağımsız açılır
  if (typeof window !== 'undefined' && window.location.hash.startsWith('#/reset-password')) {
    return (
      <ResetPassword
        onDone={() => {
          window.location.hash = '#/landing';
          setCurrentView('LANDING');
        }}
      />
    );
  }

  if (currentView === 'LANDING') {
    return (
      <OfficialLanding 
        currentUser={currentUser}
        onEnterWorkspace={handleEnterPlatform} 
        onLogout={handleLogout}
      />
    );
  }

  if (currentView === 'SUPER_ADMIN_CONSOLE') {
    return (
      <SuperAdminConsole 
        currentUser={currentUser}
        onUpdateCurrentUser={(updated) => {
          setCurrentUser(updated);
          localStorage.setItem('recorion_user', JSON.stringify(updated));
        }}
        onLogout={handleLogout}
        onGoToOfficialSite={() => setCurrentView('LANDING')}
        onSwitchToWorkspace={handleSwitchTenant}
        onSwitchToCompanyAdmin={(selectedT) => {
          if (selectedT) setTenant(selectedT);
          setCurrentView('COMPANY_ADMIN_CONSOLE');
          window.location.hash = '#/company-admin';
        }}
      />
    );
  }

  if (currentView === 'COMPANY_ADMIN_CONSOLE') {
    return (
      <CompanyAdminConsole
        currentUser={currentUser}
        currentTenant={tenant}
        onSwitchToWorkspace={(selectedT) => {
          if (selectedT) handleSwitchTenant(selectedT);
          else setCurrentView('WORKSPACE');
        }}
        onGoToOfficialSite={() => setCurrentView('LANDING')}
        onGoToSuperAdmin={() => {
          setCurrentView('SUPER_ADMIN_CONSOLE');
          window.location.hash = '#/super-admin/dashboard';
        }}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <div className="work-area-layout">
      {kvkkRestricted && (
        <div
          role="status"
          style={{
            background: 'linear-gradient(90deg, rgba(234, 179, 8, 0.18), rgba(234, 179, 8, 0.08))',
            borderBottom: '1px solid rgba(234, 179, 8, 0.45)',
            color: 'var(--ac-fde68a)',
            padding: '10px 20px',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <span style={{ fontSize: '1.1rem' }}>🔒</span>
          <span>
            <strong>KVKK Koruma Modu:</strong> {tenant?.name} şirketinin Work Space alanını görüntülüyorsunuz.
            Kişisel verilerin korunması gereği bu şirketin projeleri, görevleri, sohbetleri ve kurum hafızası
            RECDx yöneticilerine gösterilmez.
          </span>
        </div>
      )}
      {/* Top Navigation */}
      <Navbar 
        health={health}
        tenant={tenant}
        models={models}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        onGoToOfficialSite={() => setCurrentView('LANDING')}
        onGoToAdminConsole={() => {
          setCurrentView('SUPER_ADMIN_CONSOLE');
          window.location.hash = '#/super-admin/dashboard';
        }}
        onGoToCompanyAdmin={() => {
          setCurrentView('COMPANY_ADMIN_CONSOLE');
          window.location.hash = '#/company-admin';
        }}
        onLogout={handleLogout}
        currentUser={currentUser}
      />

      <nav className="ws-mode" aria-label="Work Space">
        {[['HUB', 'Projeler'], ['WORK', 'Çalışma Alanı']].map(([key, label]) => (
          <button key={key} type="button" className={(workspaceMode === key || (key === 'HUB' && workspaceMode === 'PLANNER')) ? 'active' : ''}
            onClick={() => setWorkspaceMode(key)} disabled={kvkkRestricted && key === 'HUB'}>
            {label}{key === 'WORK' && activeProject ? ` · ${activeProject.name}` : ''}
          </button>
        ))}
      </nav>

      {workspaceMode === 'HUB' && !kvkkRestricted && tenant && (
        <ProjectHub
          tenant={tenant}
          currentUser={currentUser}
          actors={actors}
          onOpen={(p) => { setPlannerProjectId(p.id); setWorkspaceMode('PLANNER'); }}
        />
      )}
      {workspaceMode === 'PLANNER' && !kvkkRestricted && tenant && plannerProjectId && (
        <ProjectPlanner
          key={plannerProjectId}
          projectId={plannerProjectId}
          tenant={tenant}
          currentUser={currentUser}
          onBack={() => { setWorkspaceMode('HUB'); window.history.replaceState(null, '', '#/workspace'); }}
          onOpenWork={(p) => { setActiveProject(p); setWorkspaceMode('WORK'); }}
        />
      )}

      {(workspaceMode === 'WORK' || kvkkRestricted) && (<>
      {/* Tri-Pane Work Area */}
      <nav className="pane-switcher" aria-label="Çalışma alanı bölmeleri">
        {[['left', 'Proje & Görevler'], ['middle', 'Sohbet'], ['right', 'Çıktı & Hafıza']].map(([key, label]) => (
          <button key={key} type="button" className={activePane === key ? 'active' : ''} onClick={() => setActivePane(key)}>
            {label}
          </button>
        ))}
      </nav>
      <div className="tri-pane-container" data-active-pane={activePane}>
        {/* Left Pane: Project, Workflow & Team */}
        <LeftPane 
          project={activeProject}
          tasks={tasks}
          selectedTask={selectedTask}
          onSelectTask={setSelectedTask}
          actors={actors}
          chatFilter={chatFilter}
          onSetChatFilter={setChatFilter}
          onCreateTaskModal={() => setIsModalOpen(true)}
        />

        {/* Middle Pane: Persistent Chat & Live Thought Stream */}
        <MiddlePane 
          selectedTask={selectedTask}
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          actors={actors}
          models={models}
          selectedModel={selectedModel}
          onSelectModel={setSelectedModel}
        />

        {/* Right Pane: Quality Gate & 2-Tier Collective Memory */}
        <RightPane 
          selectedTask={selectedTask}
          memoryItems={memoryItems}
          onPromoteMemory={handlePromoteMemory}
          onApproveQualityGate={() => notify("Kalite Kapısı onaylandı. Görev sonraki AI personeline devredildi.")}
          onRejectQualityGate={() => notify("Revizyon talep edildi. Ajan geribildirime göre çıktıyı güncelleyecek.")}
        />
      </div>

      </>)}

      {/* Task Creation Modal */}
      <CreateTaskModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleCreateTask}
        actors={actors}
      />
    </div>
  );
}
