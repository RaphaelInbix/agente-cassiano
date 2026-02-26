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

import React, { useState, useEffect, useCallback } from "react";

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

// ============================================================
// CONFIGURAÇÃO - Altere para o URL da sua API
// ============================================================
const API_URL = "https://agente-cassiano.onrender.com"; // Alterar para URL de produção

// ============================================================
// CURADORIA INBIX — Componente completo para Framer
// ============================================================
export function CuradoriaInbix() {
  const [items, setItems] = useState<CuratedItem[]>([]);
  const [filter, setFilter] = useState<"all" | "newsletters" | "reddit">("all");
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [statusMsg, setStatusMsg] = useState<string>("");

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

  const pollStatus = useCallback(async () => {
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/status`);
        const data = await res.json();
        setStatusMsg(data.detail || "");
        if (data.status === "done") {
          clearInterval(poll);
          setLoading(false);
          setStatusMsg("");
          await fetchData();
        } else if (data.status === "error") {
          clearInterval(poll);
          setLoading(false);
          setStatusMsg("");
          setError(data.detail || "Erro ao atualizar");
        }
      } catch {
        /* continue polling */
      }
    }, 3000);
    return poll;
  }, [fetchData]);

  const handleUpdate = async () => {
    setLoading(true);
    setError(null);
    setStatusMsg("Iniciando...");
    try {
      const res = await fetch(`${API_URL}/api/atualizar`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        pollStatus();
      } else {
        setLoading(false);
        setError("Erro ao iniciar atualização");
      }
    } catch {
      setLoading(false);
      setError("Falha na conexão com o servidor");
    }
  };

  const filtered = items.filter((item) => {
    if (filter === "newsletters") return item.source !== "Reddit";
    if (filter === "reddit") return item.source === "Reddit";
    return true;
  });

  const counts = {
    all: items.length,
    newsletters: items.filter((i) => i.source !== "Reddit").length,
    reddit: items.filter((i) => i.source === "Reddit").length,
  };

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
      {/* HEADER ATUALIZADO */}
      <div style={styles.accent} />
      <div style={styles.header}>
        <div style={{ flex: 1 }}>
          <div style={styles.brand}>
            <h1 style={styles.title}>
              Curadoria <span style={{ color: "#085fff" }}>Inbix</span>
            </h1>
          </div>
          <p style={styles.subtitle}>Top post e artigos da semana.</p>
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

      {/* TABS */}
      <div style={styles.content}>
        <div style={styles.tabs}>
          {(["all", "newsletters", "reddit"] as const).map((key) => (
            <button
              key={key}
              style={{
                ...styles.tab,
                ...(filter === key ? styles.tabActive : {}),
              }}
              onClick={() => setFilter(key)}
            >
              {key === "all"
                ? "Todos"
                : key === "newsletters"
                  ? "Newsletters"
                  : "Reddit"}
              <span
                style={{
                  ...styles.tabCount,
                  ...(filter === key ? styles.tabCountActive : {}),
                }}
              >
                {counts[key]}
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
            {filtered.map((item, i) => (
              <div
                key={`${item.url}-${i}`}
                style={{
                  ...styles.card,
                  borderLeftColor:
                    item.source === "Reddit" ? "#ff4500" : "#085fff",
                }}
              >
                <div style={styles.cardHeader}>
                  <span
                    style={{
                      ...styles.cardSource,
                      color: item.source === "Reddit" ? "#ff4500" : "#085fff",
                    }}
                  >
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
                      Ler mais →
                    </a>
                  )}
                </div>
              </div>
            ))}
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
