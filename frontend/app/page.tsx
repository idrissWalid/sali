"use client";

import { useState, useEffect, useRef } from "react";
import { Panel, Group, Separator } from "react-resizable-panels";
import Sidebar from "./components/Sidebar";
import SourcesPanel from "./components/SourcesPanel";
import ChatPanel from "./components/ChatPanel";
import StudioPanel from "./components/StudioPanel";
import SettingsModal from "./components/SettingsModal";
import ShareModal from "./components/ShareModal";
import AvatarMenu from "./components/AvatarMenu";
import Modal from "./components/Modal";

interface Source {
  name: string;
  type: "tabular" | "document";
  meta: string;
}

interface SessionItem {
  id: string;
  title: string;
  type: string;
  filename?: string;
  created_at: string;
}

export default function Home() {
  const [sources, setSources] = useState<Source[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [initialMessage, setInitialMessage] = useState<{ role: "assistant"; text: string; isSummary?: boolean } | null>(null);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [leftTab, setLeftTab] = useState<"sources" | "history">("sources");
  
  const [models, setModels] = useState<string[]>(["gemma2:latest"]);
  const [selectedModel, setSelectedModel] = useState<string>("gemma2:latest");

  // Modal & Dropdown visibility states
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isShareOpen, setIsShareOpen] = useState(false);
  const [isAvatarOpen, setIsAvatarOpen] = useState(false);
  const [isNewSessionConfirmOpen, setIsNewSessionConfirmOpen] = useState(false);

  // Anchor ref for positioning avatar dropdown
  const avatarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  // Charger la liste des sessions au montage
  useEffect(() => {
    const savedModel = localStorage.getItem("selected_model");
    if (savedModel) {
      setSelectedModel(savedModel);
    }
    fetchSessions();
    fetchModels();
    const savedSessionId = localStorage.getItem("active_session_id");
    if (savedSessionId) {
      handleSelectSession(savedSessionId);
    }
  }, []);

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem("active_session_id", sessionId);
    } else {
      localStorage.removeItem("active_session_id");
    }
  }, [sessionId]);

  const fetchSessions = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/api/sessions`);
      const data = await res.json();
      setSessions(data || []);
    } catch (err) {
      console.error("Erreur lors du chargement des sessions:", err);
    }
  };

  const fetchModels = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/api/llm-models`);
      const data = await res.json();
      if (data.models && data.models.length > 0) {
        setModels(data.models);
        const savedModel = localStorage.getItem("selected_model");
        if (savedModel && data.models.includes(savedModel)) {
          setSelectedModel(savedModel);
        } else {
          setSelectedModel(data.models[0]);
        }
      }
    } catch (err) {
      console.error("Erreur lors du chargement des modèles LLM:", err);
    }
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedModel(val);
    localStorage.setItem("selected_model", val);
  };

  const handleSelectSession = async (id: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/api/sessions/${id}`);
      if (!res.ok) throw new Error("Erreur serveur");
      const data = await res.json();
      
      setSessionId(data.id);
      
      // Mettre à jour les sources avec le fichier de la session
      if (data.filename) {
        setSources([
          {
            name: data.filename,
            type: data.type === "tabular" ? "tabular" : "document",
            meta: data.type === "tabular" ? "Données tabulaires" : "Document PDF/Word",
          }
        ]);
        setLeftTab("sources");
      } else {
        setSources([]);
      }
      
      // Pas de message initial lors de la reprise d'une session
      setInitialMessage(null);
    } catch (err) {
      console.error("Erreur lors du chargement des détails de la session:", err);
      if (id === localStorage.getItem("active_session_id")) {
        localStorage.removeItem("active_session_id");
      }
    }
  };

  const handleDeleteSession = async (id: string) => {
    if (!confirm("Voulez-vous vraiment supprimer cette discussion ?")) return;
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      await fetch(`${apiUrl}/api/sessions/${id}`, { method: "DELETE" });
      
      // Recharger la liste
      fetchSessions();
      
      // Si la session en cours a été supprimée, on réinitialise
      if (sessionId === id) {
        handleNewSession();
      }
    } catch (err) {
      console.error("Erreur lors de la suppression de la session:", err);
    }
  };

  const handleUpload = (data: any) => {
    setSessionId(data.session_id);
    const newSource: Source = {
      name: data.filename || data.profile?.filename || "Source",
      type: data.type === "tabular_analyzed" ? "tabular" : "document",
      meta: data.type === "tabular_analyzed" ? "Données tabulaires" : "Document PDF/Word",
    };
    setSources(s => [...s, newSource]);
    setLeftTab("sources");
    const text = data.type === "tabular_analyzed" ? data.interpretation : data.summary;
    setInitialMessage({ role: "assistant", text, isSummary: data.type === "tabular_analyzed" });
    
    // Rafraîchir l'historique des sessions
    fetchSessions();
  };

  const handleRemove = (index: number) => {
    setSources(s => s.filter((_, i) => i !== index));
  };

  const handleNewSession = () => {
    setSources([]);
    setSessionId(null);
    setInitialMessage(null);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "var(--bg-app)", color: "var(--text-main)", transition: "all 0.3s ease", overflow: "hidden" }}>

      {/* TOPBAR */}
      <div style={{ height: "64px", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", background: "var(--bg-panel)", borderBottom: "1px solid var(--border-color)", flexShrink: 0, position: "relative" }}>

        {/* Gauche : logo + nom */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "10px", overflow: "hidden", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <img
              src="/logo.png"
              alt="Logo"
              width={36}
              height={36}
              style={{ objectFit: "contain" }}
            />
          </div>
          <span style={{ fontFamily: "'Google Sans',sans-serif", fontSize: "18px", fontWeight: 500, color: "var(--text-main)" }}>
            No-Code Data Intelligence
          </span>
        </div>

        {/* Droite : boutons */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          
          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            style={{ width: "36px", height: "36px", borderRadius: "50%", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-main)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {[
              {
                label: "＋ Nouvelle session",
                action: () => {
                  if (sources.length > 0) {
                    setIsNewSessionConfirmOpen(true);
                  } else {
                    handleNewSession();
                  }
                }
              },
              { label: "↗ Partager", action: () => setIsShareOpen(true) },
              { label: "⚙ Paramètres", action: () => setIsSettingsOpen(true) },
            ].map((btn, i) => (
              <button key={i} onClick={btn.action}
                style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 18px", borderRadius: "24px", border: "1px solid var(--border-color)", color: "var(--text-main)", fontSize: "14px", fontFamily: "'Google Sans',sans-serif", background: "transparent", cursor: "pointer", transition: "background .15s" }}
                onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "var(--bubble-ai)"}
                onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
              >
                {btn.label}
              </button>
            ))}
            <div
              ref={avatarRef}
              onClick={() => setIsAvatarOpen(!isAvatarOpen)}
              style={{ width: "36px", height: "36px", borderRadius: "50%", background: "linear-gradient(135deg,#8ab4f8,#c58af9)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px", fontWeight: 500, color: "#fff", cursor: "pointer" }}
            >
              W
            </div>
          </div>

          {/* Avatar Menu Dropdown Overlay */}
          <AvatarMenu isOpen={isAvatarOpen} onClose={() => setIsAvatarOpen(false)} anchorRef={avatarRef} />
        </div>

      </div>

      {/* MAIN */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden", padding: "0 8px" }}>
        <Group orientation="horizontal">
          <Panel defaultSize={22} minSize={15} style={{ height: "100%" }}>
            <div style={{
              height: "98%",
              marginTop: "10px",
              display: "flex",
              flexDirection: "column",
              background: "var(--bg-panel)",
              borderRadius: "12px",
              border: "1px solid var(--border-color)",
              overflow: "hidden",
            }}>
              {/* Tab Switcher */}
              <div style={{
                display: "flex",
                borderBottom: "1px solid var(--border-muted)",
                background: "var(--bg-panel)",
                padding: "2px 4px 0",
              }}>
                <button
                  onClick={() => setLeftTab("sources")}
                  style={{
                    flex: 1,
                    padding: "12px 6px",
                    background: "none",
                    border: "none",
                    borderBottom: `2.5px solid ${leftTab === "sources" ? "var(--accent-color)" : "transparent"}`,
                    color: leftTab === "sources" ? "var(--text-main)" : "var(--text-muted)",
                    fontSize: "13px",
                    fontWeight: 600,
                    cursor: "pointer",
                    transition: "all 0.15s",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                  }}
                >
                  📁 Sources ({sources.length})
                </button>
                <button
                  onClick={() => setLeftTab("history")}
                  style={{
                    flex: 1,
                    padding: "12px 6px",
                    background: "none",
                    border: "none",
                    borderBottom: `2.5px solid ${leftTab === "history" ? "var(--accent-color)" : "transparent"}`,
                    color: leftTab === "history" ? "var(--text-main)" : "var(--text-muted)",
                    fontSize: "13px",
                    fontWeight: 600,
                    cursor: "pointer",
                    transition: "all 0.15s",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px",
                  }}
                >
                  💬 Historique
                </button>
              </div>

              {/* Tab Content */}
              <div style={{ flex: 1, overflow: "hidden" }}>
                {leftTab === "sources" ? (
                  <SourcesPanel sources={sources} onUpload={handleUpload} onRemove={handleRemove} hideHeader={true} selectedModel={selectedModel} />
                ) : (
                  <Sidebar
                    sessions={sessions}
                    currentSessionId={sessionId}
                    onSelectSession={handleSelectSession}
                    onDeleteSession={handleDeleteSession}
                    onNewSession={handleNewSession}
                    hideHeader={true}
                  />
                )}
              </div>
            </div>
          </Panel>
          <Separator style={{ width: "8px", background: "transparent", cursor: "col-resize", transition: "background 0.2s" }} />
          <Panel defaultSize={55} minSize={30} style={{ height: "100%" }}>
            <ChatPanel sessionId={sessionId} sourceCount={sources.length} initialMessage={initialMessage} selectedModel={selectedModel} />
          </Panel>
          <Separator style={{ width: "8px", background: "transparent", cursor: "col-resize", transition: "background 0.2s" }} />
          <Panel defaultSize={23} minSize={15} style={{ height: "100%" }}>
            <StudioPanel sessionId={sessionId} />
          </Panel>
        </Group>
      </div>

      {/* FOOTER */}
      <div style={{ height: "28px", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontSize: "11px", color: "var(--text-dim)" }}>
        No-Code Data Intelligence peut se tromper. Veuillez donc vérifier ses réponses.
      </div>

      {/* Global Modals */}
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        models={models}
        selectedModel={selectedModel}
        onModelChange={(m) => {
          setSelectedModel(m);
          localStorage.setItem("selected_model", m);
        }}
      />
      <ShareModal isOpen={isShareOpen} onClose={() => setIsShareOpen(false)} sourcesCount={sources.length} />

      {/* Confirmation Modal for Reset Session */}
      <Modal isOpen={isNewSessionConfirmOpen} onClose={() => setIsNewSessionConfirmOpen(false)} title="Confirmation">
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ fontSize: "14px", color: "var(--text-main)" }}>
            Êtes-vous sûr de vouloir commencer une nouvelle session ? Toutes vos sources et discussions en cours seront définitivement effacées de l'écran.
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "8px" }}>
            <button
              onClick={() => setIsNewSessionConfirmOpen(false)}
              style={{
                padding: "8px 18px",
                borderRadius: "18px",
                border: "1.5px solid var(--border-color)",
                color: "var(--text-muted)",
                fontSize: "13px",
                fontWeight: 500,
                background: "transparent",
                cursor: "pointer",
              }}
            >
              Annuler
            </button>
            <button
              onClick={() => {
                handleNewSession();
                setIsNewSessionConfirmOpen(false);
              }}
              style={{
                padding: "8px 24px",
                borderRadius: "18px",
                border: "none",
                color: "var(--bg-app)",
                background: "#ea4335",
                fontSize: "13px",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Confirmer
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}