/**
 * FRAMER COMPONENT EXPORTS
 *
 * Para usar no Framer:
 * 1. No Framer, vá em Assets > Code > New File
 * 2. Copie o conteúdo do componente desejado
 * 3. Ajuste a API_URL para o endereço do seu servidor
 *
 * Cada componente abaixo é auto-contido (inclui estilos inline)
 * para funcionar de forma independente no Framer.
 */

import React, { useState, useEffect, useCallback, useRef } from "react";

// ============================================================
// TYPES
// ============================================================
interface CuratedItem {
  title: string;
  source: string;
  channel: string;
  description: string;
  author: string;
  url: string;
  relevance_score: number;
  tags: string[];
}

type FilterType = "all" | "newsletters" | "reddit" | "youtube";

// ============================================================
// CONFIGURAÇÃO - Altere para o URL da sua API
// ============================================================
const API_URL = "https://agente-cassiano.onrender.com";

// ============================================================
// HELPERS
// ============================================================
function getSourceColor(source: string): string {
  switch (source.toLowerCase()) {
    case "reddit":
      return "#ff4500";
    case "youtube":
      return "#ff0000";
    default:
      return "#085fff";
  }
}

// ============================================================
// CURADORIA INBIX — Componente completo para Framer
// ============================================================
export function CuradoriaInbix() {
  const [items, setItems] = useState<CuratedItem[]>([]);
  const [filter, setFilter] = useState<FilterType>("all");
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/curadoria`);
      if (!res.ok) throw new Error("Erro ao carregar");
      const data = await res.json();
      setItems(data.items || []);
      setLastUpdate(data.updated_at);
    } catch {
      /* silently fail on initial load */
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollStatus = useCallback(() => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/status`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.status === "running") {
          setStatusMsg(data.detail || "Processando...");
        } else if (data.status === "done") {
          stopPolling();
          setStatusMsg(null);
          setLoading(false);
          await fetchData();
        } else if (data.status === "error") {
          stopPolling();
          setStatusMsg(null);
          setLoading(false);
          setError(data.detail || "Erro ao atualizar");
        }
      } catch {
        /* continue polling */
      }
    }, 2000);
  }, [fetchData, stopPolling]);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const handleUpdate = async () => {
    setLoading(true);
    setError(null);
    setStatusMsg("Iniciando coleta de dados...");
    try {
      const res = await fetch(`${API_URL}/api/atualizar`, { method: "POST" });
      if (!res.ok) throw new Error("Erro");
      pollStatus();
    } catch {
      setLoading(false);
      setStatusMsg(null);
      setError("Falha na conexão com o servidor");
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

  const TABS: { key: FilterType; label: string }[] = [
    { key: "all", label: "Todos" },
    { key: "newsletters", label: "Newsletters" },
    { key: "reddit", label: "Reddit" },
    { key: "youtube", label: "YouTube" },
  ];

  const formattedDate = lastUpdate
    ? new Date(lastUpdate).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div style={styles.app}>
      {/* HEADER */}
      <div style={styles.accent} />
      <div style={styles.header}>
        <div style={{ flex: 1 }}>
          <div style={styles.brand}>
            <h1 style={styles.title}>
              Curadoria <span style={{ color: "#085fff" }}>Inbix</span>
            </h1>
          </div>
          <p style={styles.subtitle}>Top posts e artigos da semana</p>
          <div style={styles.stats}>
            {items.length > 0 && (
              <span style={styles.stat}>{items.length} artigos</span>
            )}
            {formattedDate && (
              <span style={styles.stat}>Atualizado em {formattedDate}</span>
            )}
          </div>
        </div>
        <button
          style={{
            ...styles.updateBtn,
            ...(loading ? { background: "#71717a", opacity: 0.7 } : {}),
          }}
          onClick={handleUpdate}
          disabled={loading}
        >
          {loading ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {/* MAIN CONTENT */}
      <div style={styles.content}>
        {/* LOADING CARD */}
        {loading && (
          <div style={styles.loadingCard}>
            <div style={styles.loadingIcon}>
              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#085fff"
                strokeWidth="2"
                style={{ animation: "framer-spin 1s linear infinite" }}
              >
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              <style>{`@keyframes framer-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
            </div>
            <div style={styles.loadingText}>
              <strong style={{ display: "block", fontSize: 15, color: "#09090b", marginBottom: 2 }}>
                O script Python está rodando, aguarde alguns segundos
              </strong>
              {statusMsg && (
                <p style={{ fontSize: 13, color: "#71717a", margin: 0 }}>
                  {statusMsg}
                </p>
              )}
            </div>
          </div>
        )}

        {/* TABS */}
        <div style={styles.tabs}>
          {TABS.map((tab) => (
            <button
              key={tab.key}
              style={{
                ...styles.tab,
                ...(filter === tab.key ? styles.tabActive : {}),
              }}
              onClick={() => setFilter(tab.key)}
            >
              {tab.label}
              <span
                style={{
                  ...styles.tabCount,
                  ...(filter === tab.key ? styles.tabCountActive : {}),
                }}
              >
                {counts[tab.key]}
              </span>
            </button>
          ))}
        </div>

        {/* ERROR */}
        {error && <div style={styles.error}>{error}</div>}

        {/* CARDS */}
        {filtered.length === 0 ? (
          <div style={styles.empty}>
            <h3>Nenhum conteúdo disponível</h3>
            <p style={{ color: "#a1a1aa", fontSize: 14 }}>
              Clique em "Atualizar" para buscar os artigos e posts mais
              recentes.
            </p>
          </div>
        ) : (
          <div style={styles.grid}>
            {filtered.map((item, i) => {
              const color = getSourceColor(item.source);
              return (
                <div
                  key={`${item.url}-${i}`}
                  style={{
                    ...styles.card,
                    borderLeftColor: color,
                  }}
                >
                  <div style={styles.cardHeader}>
                    <span style={{ ...styles.cardSource, color }}>
                      {item.channel}
                    </span>
                    {item.relevance_score > 0 && (
                      <span style={styles.cardScore}>
                        {Math.round(item.relevance_score)}
                      </span>
                    )}
                  </div>
                  <h3 style={styles.cardTitle}>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: "inherit", textDecoration: "none" }}
                    >
                      {item.title}
                    </a>
                  </h3>
                  {item.description && item.description !== item.title && (
                    <p style={styles.cardDesc}>
                      {item.description.length > 200
                        ? item.description.slice(0, 200) + "..."
                        : item.description}
                    </p>
                  )}
                  <div style={styles.cardFooter}>
                    <span style={{ fontSize: 13, color: "#a1a1aa" }}>
                      {item.author}
                    </span>
                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={styles.cardLink}
                      >
                        {item.source === "YouTube" ? "Assistir →" : "Ler mais →"}
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* FOOTER */}
      <div style={styles.footer}>
        <p style={{ fontSize: 13, color: "#a1a1aa" }}>
          Powered by{" "}
          <strong style={{ color: "#71717a" }}>Agente Cassiano</strong> —
          Curadoria automatizada Inbix
        </p>
      </div>
    </div>
  );
}

// ============================================================
// INLINE STYLES
// ============================================================
const styles: Record<string, React.CSSProperties> = {
  app: {
    fontFamily:
      "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    minHeight: "100vh",
    background: "#fafafa",
    color: "#09090b",
    WebkitFontSmoothing: "antialiased",
  },
  accent: {
    height: 4,
    background: "linear-gradient(90deg, #085fff 0%, #8d49f6 50%, #085fff 100%)",
  },
  header: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 24,
    maxWidth: 1200,
    margin: "0 auto",
    padding: "32px 24px",
    background: "#fff",
    borderBottom: "1px solid #e4e4e7",
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    marginBottom: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: 800,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 15,
    color: "#71717a",
    marginBottom: 16,
    maxWidth: 500,
  },
  stats: {
    display: "flex",
    gap: 24,
  },
  stat: {
    fontSize: 13,
    color: "#a1a1aa",
  },
  updateBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "12px 24px",
    fontSize: 14,
    fontWeight: 600,
    color: "#fff",
    background: "#085fff",
    borderRadius: 10,
    border: "none",
    cursor: "pointer",
    whiteSpace: "nowrap" as const,
    flexShrink: 0,
    marginTop: 4,
  },
  content: {
    maxWidth: 1200,
    margin: "0 auto",
    padding: "0 24px 64px",
  },
  loadingCard: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    padding: 24,
    marginTop: 24,
    marginBottom: 0,
    background: "#e8f0ff",
    border: "1px solid rgba(8, 95, 255, 0.2)",
    borderRadius: 10,
  },
  loadingIcon: {
    flexShrink: 0,
  },
  loadingText: {
    flex: 1,
  },
  tabs: {
    display: "flex",
    gap: 4,
    margin: "24px 0",
    padding: 4,
    background: "#fff",
    border: "1px solid #e4e4e7",
    borderRadius: 10,
    width: "fit-content",
  },
  tab: {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 20px",
    fontSize: 14,
    fontWeight: 500,
    color: "#71717a",
    borderRadius: 6,
    border: "none",
    background: "none",
    cursor: "pointer",
    fontFamily: "inherit",
  },
  tabActive: {
    color: "#085fff",
    background: "#e8f0ff",
    fontWeight: 600,
  },
  tabCount: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    minWidth: 22,
    height: 22,
    padding: "0 6px",
    fontSize: 11,
    fontWeight: 600,
    borderRadius: 9999,
    background: "#f0f0f2",
    color: "#a1a1aa",
  },
  tabCountActive: {
    background: "rgba(8,95,255,0.15)",
    color: "#085fff",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
    gap: 16,
  },
  card: {
    background: "#fff",
    border: "1px solid #e4e4e7",
    borderRadius: 16,
    padding: 24,
    display: "flex",
    flexDirection: "column" as const,
    gap: 16,
    borderLeft: "3px solid #e4e4e7",
    transition: "box-shadow 200ms, transform 200ms",
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  cardSource: {
    fontSize: 12,
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: 0.3,
  },
  cardScore: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    minWidth: 32,
    height: 24,
    padding: "0 8px",
    fontSize: 11,
    fontWeight: 700,
    color: "#a1a1aa",
    background: "#fafafa",
    borderRadius: 9999,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 700,
    lineHeight: 1.4,
    letterSpacing: -0.2,
  },
  cardDesc: {
    fontSize: 14,
    lineHeight: 1.6,
    color: "#71717a",
    overflow: "hidden",
    display: "-webkit-box",
    WebkitLineClamp: 3,
    WebkitBoxOrient: "vertical" as const,
  },
  cardFooter: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: "auto",
    paddingTop: 16,
    borderTop: "1px solid #f0f0f2",
  },
  cardLink: {
    fontSize: 13,
    fontWeight: 600,
    color: "#085fff",
    textDecoration: "none",
  },
  error: {
    padding: "16px 24px",
    marginBottom: 24,
    fontSize: 14,
    color: "#ef4444",
    background: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: 10,
  },
  empty: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    textAlign: "center" as const,
    padding: "64px 24px",
    gap: 16,
  },
  footer: {
    textAlign: "center" as const,
    padding: "32px 24px",
    borderTop: "1px solid #e4e4e7",
    background: "#fff",
  },
};

export default CuradoriaInbix;
