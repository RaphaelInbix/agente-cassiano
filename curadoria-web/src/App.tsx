import React, { useState, useEffect, useCallback, useRef } from "react";
import { Header } from "./components/Header";
import { SectionTabs } from "./components/SectionTabs";
import { ContentCard } from "./components/ContentCard";
import type { CuratedItem, FilterType } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "";

function App() {
  const [items, setItems] = useState<CuratedItem[]>([]);
  const [filter, setFilter] = useState<FilterType>("all");
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [initialLoad, setInitialLoad] = useState(true);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/api/curadoria`);
      if (!res.ok) throw new Error("Erro ao carregar dados");
      const data = await res.json();
      setItems(data.items);
      setLastUpdate(data.updated_at);
      setError(null);
      return !!data._auto_updating;
    } catch (err) {
      console.error("Erro ao buscar dados:", err);
      return false;
    } finally {
      setInitialLoad(false);
    }
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollStatus = useCallback(() => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/status`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.status === "running") {
          setStatusMsg(data.message || "Processando...");
        } else if (data.status === "done") {
          stopPolling();
          setStatusMsg(null);
          setLoading(false);
          await fetchData();
        } else if (data.status === "error") {
          stopPolling();
          setStatusMsg(null);
          setLoading(false);
          setError(data.message || "Erro ao atualizar");
        }
      } catch {
        // ignore polling errors
      }
    }, 2000);
  }, [fetchData, stopPolling]);

  // Na montagem, busca dados. Se vazio, ativa loading + polling automático
  useEffect(() => {
    let mounted = true;
    (async () => {
      const autoUpdating = await fetchData();
      if (mounted && autoUpdating) {
        setLoading(true);
        setStatusMsg("Carregando conteúdo pela primeira vez...");
        pollStatus();
      }
    })();
    return () => { mounted = false; stopPolling(); };
  }, [fetchData, pollStatus, stopPolling]);

  const handleUpdate = async () => {
    setLoading(true);
    setError(null);
    setStatusMsg("Iniciando coleta de dados...");

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120_000);

    try {
      const res = await fetch(`${API_BASE}/api/atualizar`, {
        method: "POST",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error("Erro ao atualizar");
      pollStatus();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof DOMException && err.name === "AbortError") {
        setError("Timeout na conexão. O servidor pode estar iniciando (cold start). Tente novamente em 30s.");
      } else {
        setError("Falha na conexão com o servidor. Verifique se a API está rodando.");
      }
      setLoading(false);
      setStatusMsg(null);
    }
  };

  const filtered = items.filter((item) => {
    if (filter === "all") return true;
    if (filter === "newsletters") return item.source === "Newsletter";
    if (filter === "reddit") return item.source === "Reddit";
    if (filter === "youtube") return item.source === "YouTube";
    return true;
  });

  const counts = {
    all: items.length,
    newsletters: items.filter((i) => i.source === "Newsletter").length,
    reddit: items.filter((i) => i.source === "Reddit").length,
    youtube: items.filter((i) => i.source === "YouTube").length,
  };

  return (
    <div className="app">
      <Header
        lastUpdate={lastUpdate}
        totalItems={items.length}
      />

      <main className="main">
        {loading && (
          <div className="loading-card">
            <div className="loading-card__icon">
              <svg className="spinner" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
            </div>
            <div className="loading-card__text">
              <strong>O script Python está rodando, aguarde alguns segundos</strong>
              {statusMsg && <p>{statusMsg}</p>}
            </div>
          </div>
        )}

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
            <p>Clique em "Atualizar dados" no rodapé para buscar os artigos e posts mais recentes.</p>
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
        <div className="footer__content">
          <p>
            Powered by <strong>Agente Cassiano</strong> &mdash; Curadoria automatizada Inbix
          </p>
          <button
            className={`footer__update-btn ${loading ? "footer__update-btn--loading" : ""}`}
            onClick={handleUpdate}
            disabled={loading}
          >
            {loading ? (
              <>
                <svg className="spinner" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                Atualizando...
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 4 23 10 17 10" />
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                </svg>
                Atualizar dados
              </>
            )}
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;
