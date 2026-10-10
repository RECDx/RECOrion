import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LeftPane from './components/LeftPane';
import MiddlePane from './components/MiddlePane';
import RightPane from './components/RightPane';
import CreateTaskModal from './components/CreateTaskModal';
import OfficialLanding from './components/OfficialLanding';
import SuperAdminConsole from './components/SuperAdminConsole';
import { api } from './api';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const u = localStorage.getItem('recorion_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  });

  const [currentView, setCurrentView] = useState(() => {
    const hash = typeof window !== 'undefined' ? window.location.hash : '';
    const savedUser = (() => {
      try {
        const u = localStorage.getItem('recorion_user');
        return u ? JSON.parse(u) : null;
      } catch {
        return null;
      }
    })();
    const savedView = typeof window !== 'undefined' ? localStorage.getItem('recorion_current_view') : null;

    if (hash.startsWith('#/super-admin') && savedUser?.role === 'SUPER_ADMIN') {
      return 'SUPER_ADMIN_CONSOLE';
    }
    if (hash === '#/workspace' && savedUser) {
      return 'WORKSPACE';
    }
    if (savedUser?.role === 'SUPER_ADMIN') {
      return 'SUPER_ADMIN_CONSOLE';
    }
    if (hash === '#/landing') {
      return 'LANDING';
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

  // URL Hash ve Görünüm Eşitlemesi
  useEffect(() => {
    try {
      localStorage.setItem('recorion_current_view', currentView);
      if (currentView === 'SUPER_ADMIN_CONSOLE') {
        if (!window.location.hash.startsWith('#/super-admin')) {
          window.history.replaceState(null, '', '#/super-admin/dashboard');
        }
      } else if (currentView === 'WORKSPACE') {
        if (window.location.hash !== '#/workspace') {
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
      const u = currentUser || (() => {
        try {
          const raw = localStorage.getItem('recorion_user');
          return raw ? JSON.parse(raw) : null;
        } catch { return null; }
      })();

      if (hash.startsWith('#/super-admin')) {
        if (u?.role === 'SUPER_ADMIN') {
          setCurrentView('SUPER_ADMIN_CONSOLE');
        } else {
          setCurrentView('LANDING');
        }
      } else if (hash === '#/workspace') {
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

  // 1. Initial Load: Cluster Health, Models, Tenant, Actors
  useEffect(() => {
    async function initPlatform() {
      try {
        const hData = await api.getHealth();
        setHealth(hData);

        const mData = await api.getModels();
        setModels(mData);
        if (mData.length > 0) setSelectedModel(mData[0].model_code);

        const tData = await api.getTenants();
        if (tData.length > 0) {
          const defaultTenant = tData[0];
          setTenant(defaultTenant);

          const actData = await api.getActors(defaultTenant.id);
          setActors(actData);

          const prjData = await api.getProjects(defaultTenant.id);
          setProjects(prjData);
          if (prjData.length > 0) {
            setActiveProject(prjData[0]);
          }

          const memData = await api.getMemoryItems(defaultTenant.id);
          setMemoryItems(memData);
        }
      } catch (err) {
        console.error("Platform başlatma hatası:", err);
      }
    }
    initPlatform();
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
          // Filter to user messages
          const humanAdmin = actors.find(a => a.actor_type === 'HUMAN');
          msgList = await api.getChatHistory(selectedTask.id, humanAdmin?.id || null, true);
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
    const humanAdmin = actors.find(a => a.actor_type === 'HUMAN');

    try {
      const response = await api.sendMessage({
        task_id: selectedTask.id,
        content: content,
        sender_actor_id: humanAdmin?.id || null,
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
      alert(`Mesaj gönderilemedi: ${err.message}`);
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
      alert(`Görev oluşturulamadı: ${err.message}`);
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
      alert("Bilgi başarıyla Şirket Kurum Hafızasına (NS_GLOBAL) terfi ettirildi!");
    } catch (err) {
      alert(`Hafıza terfi hatası: ${err.message}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('recorion_user');
    localStorage.removeItem('recorion_current_view');
    setCurrentUser(null);
    setCurrentView('LANDING');
    window.location.hash = '#/landing';
  };

  const handleEnterPlatform = (loggedInUser) => {
    const user = loggedInUser || currentUser;
    if (!user) return;
    setCurrentUser(user);
    if (user.role === 'SUPER_ADMIN') {
      setCurrentView('SUPER_ADMIN_CONSOLE');
      window.location.hash = '#/super-admin/dashboard';
    } else {
      setCurrentView('WORKSPACE');
      window.location.hash = '#/workspace';
    }
  };

  const handleSwitchTenant = async (selectedTenant) => {
    if (!selectedTenant) return;
    setTenant(selectedTenant);
    try {
      const actData = await api.getActors(selectedTenant.id);
      setActors(actData);
      const prjData = await api.getProjects(selectedTenant.id);
      setProjects(prjData);
      if (prjData.length > 0) {
        setActiveProject(prjData[0]);
      } else {
        setActiveProject(null);
        setTasks([]);
        setSelectedTask(null);
      }
      const memData = await api.getMemoryItems(selectedTenant.id);
      setMemoryItems(memData);
    } catch (err) {
      console.error("Şirket verileri yüklenirken hata:", err);
    }
    setCurrentView('WORKSPACE');
  };

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
      />
    );
  }

  return (
    <div className="work-area-layout">
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
        onLogout={handleLogout}
        currentUser={currentUser}
      />

      {/* Tri-Pane Work Area */}
      <div className="tri-pane-container">
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
          onApproveQualityGate={() => alert("Kalite Kapısı onaylandı. Görev sonraki AI personeline devredildi.")}
          onRejectQualityGate={() => alert("Revizyon talep edildi. Ajan geribildirime göre çıktıyı güncelleyecek.")}
        />
      </div>

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
