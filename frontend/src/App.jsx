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
import ApprovePage from './components/approvals/ApprovePage';
import ApprovalsInbox from './components/approvals/ApprovalsInbox';
import { api, session } from './api';
import { mergeMessages, useProjectLive } from './live';
import CompanyDashboard from './components/dashboard/CompanyDashboard';
import { confirmDialog, notify, promptDialog, toast } from './ui/feedback';

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
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [messages, setMessages] = useState([]);
  const [memoryItems, setMemoryItems] = useState([]);
  const [chatFilter, setChatFilter] = useState('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  // Canlı akış (Adım 8.2): AI'ın o an ne yaptığı (görev kimliği + metin)
  const [liveThought, setLiveThought] = useState(null);
  // KVKK modu: RECDx yöneticisi başka bir şirketin Work Space'ini içerik olmadan görüntüler
  const [kvkkRestricted, setKvkkRestricted] = useState(false);
  // Tablet/telefonda aynı anda tek bölme gösterilir
  const [activePane, setActivePane] = useState('middle');
  // Bekleyen kararlar (Onaylarım sayacı)
  const [approvalCount, setApprovalCount] = useState(0);
  // Work Space modu: HUB (proje listesi), PLANNER (proje planlama), WORK (görev sohbeti), INBOX (Onaylarım)
  // #/workspace?project=<id>&view=work bağlantısı doğrudan Çalışma Alanını açar (Adım 8.3)
  const [workspaceMode, setWorkspaceMode] = useState(() => {
    if (typeof window === 'undefined' || !/^#\/workspace\?project=/.test(window.location.hash)) return 'HUB';
    return /[?&]view=work(&|$)/.test(window.location.hash) ? 'WORK' : 'PLANNER';
  });
  // Çalışma Alanı: adımların akış durumu/yetkileri/son çıktısı ve proje ekibi (Adım 8.3)
  const [flowTasks, setFlowTasks] = useState({});
  const [projectInfo, setProjectInfo] = useState({ members: [], can_manage: false });
  // E-posta/Telegram bildirimindeki #/workspace?project=<id> bağlantısı doğrudan projeyi açar
  const [plannerProjectId, setPlannerProjectId] = useState(() => {
    const m = typeof window !== 'undefined' ? window.location.hash.match(/^#\/workspace\?project=([0-9a-f-]{36})/i) : null;
    return m ? m[1] : null;
  });

  // URL Hash ve Görünüm Eşitlemesi
  useEffect(() => {
    try {
      if (window.location.hash.startsWith('#/reset-password') || window.location.hash.startsWith('#/approve')) return; // bağımsız sayfa adresini koru
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
      if (hash.startsWith('#/reset-password') || hash.startsWith('#/approve')) return;
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
        await loadTenantWorkspace(savedUser.tenant_id);
      } catch (err) {
        console.error("Platform başlatma hatası:", err);
      }
    }
    initPlatform();
  }, []);

  // Onaylarım sayacı: Work Space açıkken periyodik yenilenir
  useEffect(() => {
    if (currentView !== 'WORKSPACE' || kvkkRestricted || !currentUser) return undefined;
    // İş adımı onayları + AI personelin onay bekleyen araç (yazma) işlemleri (Adım 10)
    const load = () => Promise.all([api.getMyApprovals(), api.getMyToolApprovals().catch(() => [])])
      .then(([r, t]) => setApprovalCount(r.length + t.length)).catch(() => {});
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [currentView, kvkkRestricted, currentUser]);

  // Oturum süresi dolarsa veya token geçersizse otomatik çıkış
  useEffect(() => {
    const onUnauthorized = () => {
      handleLogout();
      notify('Oturumunuzun süresi doldu. Lütfen tekrar giriş yapın.');
    };
    window.addEventListener('recorion:unauthorized', onUnauthorized);
    return () => window.removeEventListener('recorion:unauthorized', onUnauthorized);
  }, []);

  // 2. Load Tasks when Active Project Changes: görevler + akış durumu (yetki, son çıktı) birlikte yenilenir
  const reloadWork = React.useCallback(async (projectId, keepSelection = true) => {
    const [tList, flow] = await Promise.all([api.getTasks(projectId), api.getProjectWorkflow(projectId).catch(() => null)]);
    setTasks(tList);
    setFlowTasks(Object.fromEntries((flow?.tasks || []).map((t) => [t.id, t])));
    setSelectedTask((cur) => (keepSelection && tList.find((x) => x.id === cur?.id)) || tList[0] || null);
  }, []);
  useEffect(() => {
    if (!activeProject) return;
    setFlowTasks({});
    reloadWork(activeProject.id, false).catch((err) => console.error("Görev yükleme hatası:", err));
    api.getProject(activeProject.id).then((d) => setProjectInfo({ members: d.members || [], can_manage: !!d.can_manage }))
      .catch(() => setProjectInfo({ members: [], can_manage: false }));
  }, [activeProject, reloadWork]);
  // Çalışma Alanındayken adres çubuğu paylaşılabilir doğrudan bağlantıyı gösterir
  useEffect(() => {
    if (workspaceMode === 'WORK' && activeProject && currentView === 'WORKSPACE') {
      window.history.replaceState(null, '', `#/workspace?project=${activeProject.id}&view=work`);
    }
  }, [workspaceMode, activeProject, currentView]);

  // Canlı akış (Adım 8.2): yeni mesajlar, iş akışı olayları ve AI düşünce adımları sayfa yenilemeden gelir
  const liveRefresh = React.useRef(null);
  const liveStatus = useProjectLive(workspaceMode === 'WORK' && !kvkkRestricted ? activeProject?.id : null, (e) => {
    if (e.type === 'thought') {
      setLiveThought({ taskId: e.task_id, text: e.text, at: Date.now() });
      return;
    }
    if (e.type === 'message') {
      const m = e.message;
      if (m.role === 'assistant') setLiveThought((t) => (t && t.taskId === m.task_id ? null : t));
      const shown = selectedTask && m.task_id === selectedTask.id
        && (chatFilter === 'ALL' || (chatFilter === 'MY' && m.sender_actor_id === currentUser?.actor_id));
      if (shown) setMessages((prev) => mergeMessages(prev, [m]));
      return;
    }
    if (e.type === 'task_event') {
      // Adım ilerledi/durdu: eski "yazıyor" göstergesi kalmaz (sonraki iş varsa yeni düşünce adımı gelir)
      if (e.kind !== 'TASK_STARTED') setLiveThought((t) => (t && t.taskId === e.task_id ? null : t));
      // Aynı anda gelen olaylar tek yenilemede toplanır
      clearTimeout(liveRefresh.current);
      liveRefresh.current = setTimeout(() => {
        if (activeProject) reloadWork(activeProject.id).catch(() => { /* bir sonraki olayda yeniden denenir */ });
      }, 600);
    }
  });

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
  const handleSendMessage = async ({ content, isPrivate, attachments = [] }) => {
    if (!selectedTask || !content.trim()) return false;

    setIsLoading(true);

    try {
      const response = await api.sendMessage({
        task_id: selectedTask.id,
        content: content,
        is_private: isPrivate,
        message_type: 'CHAT',
        attachments: attachments.map((a) => a.id),
      });

      // Mesajlar canlı akıştan da gelebilir: kimliğe göre birleştirilir (kaynak kartları yanıta eklenir)
      setMessages((prev) => mergeMessages(prev, [response.user_message, { ...response.assistant_message, citations: response.citations }]));

      // Refresh memory items if citations or updates occurred
      if (tenant?.id) {
        const updatedMem = await api.getMemoryItems(tenant.id);
        setMemoryItems(updatedMem);
      }
      return true;
    } catch (err) {
      notify(`Mesaj gönderilemedi: ${err.message}`);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // İş akışı komutları (Adım 7.1): sinyal akışa gider, durum birkaç saniye içinde güncellenir
  const runTaskAction = async (fn, message) => {
    try {
      await fn();
      toast.success(message);
      setTimeout(() => { if (activeProject) reloadWork(activeProject.id).catch(() => {}); }, 1500);
    } catch (err) {
      toast.error(err.message);
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
  // Hafıza kararları (Adım 8.4): Kurum Hafızasına onay/taşıma, ret (gerekçe isteğe bağlı), geri alma (gerekçe zorunlu)
  const canPromote = !!currentUser?.permissions?.some((p) => p === 'memory:promote' || p === '*');
  // Pano (ADIM 9.3): şirket yöneticisi veya departman panosu yetkisi olan kendi departmanını görür
  const canDashboard = !!currentUser?.permissions?.some((p) => p === 'department:dashboard' || p === 'tenant:manage');
  const handleMemoryAction = async (kind, item) => {
    try {
      if (kind === 'promote') {
        const ok = await confirmDialog({ title: 'Kurum hafızasına ekle', message: `Bu bilgi şirketin tüm AI personelinin bilgisine eklenecek:\n\n"${item.content.slice(0, 300)}"` });
        if (!ok) return;
        await api.promoteMemory(item.id);
        toast.success('Bilgi Kurum Hafızasına eklendi; tüm AI personel kullanır.');
      } else if (kind === 'reject') {
        const note = await promptDialog({ title: 'Bilgiyi reddet', message: 'Gerekçe (isteğe bağlı):' });
        if (note === null) return;
        await api.rejectMemory(item.id, note);
        toast.success('Bilgi reddedildi; öğrenilmeyecek.');
      } else if (kind === 'revoke') {
        const note = await promptDialog({ title: 'Bilgiyi geri al', message: 'Geri alma gerekçesi (zorunlu; AI personel bu bilgiyi artık kullanmaz):' });
        if (note === null) return;
        if (!note.trim()) { toast.warning('Geri alma gerekçesini yazın.'); return; }
        await api.revokeMemory(item.id, note.trim());
        toast.success('Bilgi geri alındı; AI personel artık kullanmayacak.');
      }
      if (tenant?.id) setMemoryItems(await api.getMemoryItems(tenant.id));
    } catch (err) {
      toast.error(err.message);
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
    // Doğrudan bağlantıdaki proje (yoksa ilk proje)
    const wanted = window.location.hash.match(/^#\/workspace\?project=([0-9a-f-]{36})/i)?.[1];
    const target = (wanted && prjData.find((p) => p.id === wanted)) || prjData[0];
    if (wanted && /[?&]view=work(&|$)/.test(window.location.hash) && !prjData.some((p) => p.id === wanted)) {
      notify('Bağlantıdaki projeyi göremiyorsunuz (ekibinde değilsiniz veya proje kaldırıldı).');
    }
    if (target) {
      setActiveProject(target);
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

  // E-posta/Telegram'daki onay bağlantısı (#/approve?token=...) oturumdan bağımsız açılır (Adım 7.3)
  if (typeof window !== 'undefined' && window.location.hash.startsWith('#/approve')) {
    return <ApprovePage onDone={() => { window.location.hash = currentUser ? '#/workspace' : '#/landing'; window.location.reload(); }} />;
  }

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
        {[['HUB', 'Projeler'], ['INBOX', approvalCount ? `Onaylarım (${approvalCount})` : 'Onaylarım'], ['WORK', 'Çalışma Alanı'],
          ...(canDashboard ? [['PANO', 'Pano']] : [])].map(([key, label]) => (
          <button key={key} type="button" className={(workspaceMode === key || (key === 'HUB' && workspaceMode === 'PLANNER')) ? 'active' : ''}
            onClick={() => setWorkspaceMode(key)} disabled={kvkkRestricted && key !== 'WORK'}>
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
      {workspaceMode === 'PANO' && !kvkkRestricted && tenant && canDashboard && (
        <div className="pj-page"><CompanyDashboard tenantId={tenant.id} title="Pano" /></div>
      )}
      {workspaceMode === 'INBOX' && !kvkkRestricted && (
        <ApprovalsInbox
          onCount={setApprovalCount}
          onOpenProject={(id) => { setPlannerProjectId(id); setWorkspaceMode('PLANNER'); }}
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
          projects={projects}
          onSelectProject={(p) => { if (p.id !== activeProject?.id) { setMessages([]); setActiveProject(p); } }}
          members={projectInfo.members}
          canManage={projectInfo.can_manage}
          flowTasks={flowTasks}
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
          project={activeProject}
          currentUser={currentUser}
          flowTask={selectedTask ? flowTasks[selectedTask.id] : null}
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          liveThought={liveThought && selectedTask && liveThought.taskId === selectedTask.id ? liveThought.text : null}
          liveStatus={liveStatus}
          actors={actors}
        />

        {/* Right Pane: Quality Gate & 2-Tier Collective Memory */}
        <RightPane 
          selectedTask={selectedTask}
          flowTask={selectedTask ? flowTasks[selectedTask.id] : null}
          memoryItems={memoryItems}
          actors={actors}
          canPromote={canPromote}
          onMemoryAction={handleMemoryAction}
          onApproveQualityGate={(t) => runTaskAction(() => api.decideTask(t.id, true), 'Onaylandı; iş akışı sonraki adıma geçiyor.')}
          onRejectQualityGate={async (t) => {
            const note = await promptDialog({ message: 'Revizyon gerekçesi (personel buna göre düzeltecek):' });
            if (note && note.trim()) runTaskAction(() => api.decideTask(t.id, false, note.trim()), 'Revizyon istendi.');
          }}
          onSubmitTask={async (t) => {
            const note = await promptDialog({ message: 'Teslim notu (isteğe bağlı):' });
            if (note !== null) runTaskAction(() => api.submitTask(t.id, note), 'Teslim edildi; onaya gönderiliyor.');
          }}
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
