import React, { useState, useEffect, useCallback } from "react";
import { Header } from "./components/Header";
import { SectionTabs } from "./components/SectionTabs";
import { ContentCard } from "./components/ContentCard";
import type { CuratedItem, CuradoriaData, FilterType } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "";

function App() {
  const [items, setItems] = useState<CuratedItem[]>([]);
  const [filter, setFilter] = useState<FilterType>("all");
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [initialLoad, setInitialLoad] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/curadoria`);
      if (!res.ok) throw new Error("Erro ao carregar dados");
      const data: CuradoriaData = await res.json();
      setItems(data.items);
      setLastUpdate(data.updated_at);
      setError(null);
    } catch (err) {
      console.error("Erro ao buscar dados:", err);
    } finally {
      setInitialLoad(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUpdate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/atualizar`, { method: "POST" });
      if (!res.ok) throw new Error("Erro ao atualizar");
      const data = await res.json();
      if (data.success) {
        setItems(data.items);
        setLastUpdate(data.updated_at);
      } else {
        setError(data.error || "Erro desconhecido ao atualizar");
      }
    } catch (err) {
      setError("Falha na conexão com o servidor. Verifique se a API está rodando.");
    } finally {
      setLoading(false);
    }
  };

  const filtered = items.filter((item) => {
    if (filter === "all") return true;
    if (filter === "newsletters") return item.source !== "Reddit";
    if (filter === "reddit") return item.source === "Reddit";
    return true;
  });

  const counts = {
    all: items.length,
    newsletters: items.filter((i) => i.source !== "Reddit").length,
    reddit: items.filter((i) => i.source === "Reddit").length,
  };

  return (
    <div className="app">
      <Header
        onUpdate={handleUpdate}
        loading={loading}
        lastUpdate={lastUpdate}
        totalItems={items.length}
      />

      <main className="main">
        <SectionTabs active={filter} onChange={setFilter} counts={counts} />

        {error && (
          <div className="error-banner">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            {error}
          </div>
        )}

        {initialLoad ? (
          <div className="empty-state">
            <div className="skeleton-grid">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="skeleton-card" />
              ))}
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#d1d1d6" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <h3>Nenhum conteúdo disponível</h3>
            <p>Clique em "Atualizar" para buscar os artigos e posts mais recentes.</p>
          </div>
        ) : (
          <div className="content-grid">
            {filtered.map((item, index) => (
              <ContentCard key={`${item.url}-${index}`} item={item} />
            ))}
          </div>
        )}
      </main>

      <footer className="footer">
        <p>
          Powered by <strong>Agente Cassiano</strong> &mdash; Curadoria automatizada Inbix
        </p>
      </footer>
    </div>
  );
}

export default App;
