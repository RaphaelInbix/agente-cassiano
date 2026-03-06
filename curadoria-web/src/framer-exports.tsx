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
 
import React, { useState, useEffect, useCallback, useRef } from "react"
 
// ============================================================
// TYPES
// ============================================================
interface CuratedItem {
    title: string
    source: string
    channel: string
    description: string
    author: string
    url: string
    relevance_score: number
    tags: string[]
    published_date: string
    comment_count: number
}
 
type FilterType = "all" | "newsletters" | "reddit" | "youtube"
 
// ============================================================
// CONFIGURAÇÃO - Altere para o URL da sua API
// ============================================================
const API_URL = "https://agente-cassiano.onrender.com"
 
// ============================================================
// RESPONSIVE CSS (injected via useEffect)
// ============================================================
const RESPONSIVE_CSS = `
  .curadoria-root-wrapper {
    overflow-x: hidden;
    width: 100%;
    max-width: 100vw;
  }
  .curadoria-header-wrapper {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 24px;
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 24px;
    background: #fff;
    border-bottom: 1px solid #e4e4e7;
    box-sizing: border-box;
  }
  .curadoria-content-wrapper {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px 64px;
    box-sizing: border-box;
    overflow: hidden;
  }
  .curadoria-tabs-wrapper {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin: 24px 0;
    padding: 4px;
    background: #fff;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    width: fit-content;
    max-width: 100%;
    box-sizing: border-box;
  }
  .curadoria-grid-wrapper {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(360px, 100%), 1fr));
    gap: 16px;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }
  .curadoria-card-wrapper {
    background: #fff;
    border: 1px solid #e4e4e7;
    border-radius: 16px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    border-left: 3px solid #e4e4e7;
    transition: box-shadow 200ms, transform 200ms;
    box-sizing: border-box;
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
  }
  .curadoria-card-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-width: 0;
  }
  .curadoria-card-meta-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    min-width: 0;
  }
  .curadoria-card-footer-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: auto;
    padding-top: 16px;
    border-top: 1px solid #f0f0f2;
    gap: 12px;
    min-width: 0;
  }
  .curadoria-card-author {
    font-size: 13px;
    color: #a1a1aa;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
    flex: 1;
  }
  .curadoria-card-link {
    font-size: 13px;
    font-weight: 600;
    color: #085fff;
    text-decoration: none;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .curadoria-card-title-text {
    font-size: 16px;
    font-weight: 700;
    line-height: 1.4;
    letter-spacing: -0.2px;
    word-break: break-word;
    overflow-wrap: anywhere;
    min-width: 0;
  }
  .curadoria-card-desc-text {
    font-size: 14px;
    line-height: 1.6;
    color: #71717a;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    word-break: break-word;
    overflow-wrap: anywhere;
    min-width: 0;
  }
  .curadoria-loading-wrapper {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 24px;
    margin-top: 24px;
    margin-bottom: 0;
    background: #e8f0ff;
    border: 1px solid rgba(8, 95, 255, 0.2);
    border-radius: 10px;
    box-sizing: border-box;
  }
  .curadoria-footer-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
    color: #71717a;
    background: #fafafa;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    cursor: pointer;
    font-family: inherit;
    -webkit-tap-highlight-color: transparent;
  }
  .curadoria-stats-row {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
  }
 
  /* ── TABLET (max 768px) ── */
  @media (max-width: 768px) {
    .curadoria-header-wrapper {
      flex-direction: column;
      gap: 16px;
      padding: 24px 16px;
    }
    .curadoria-content-wrapper {
      padding: 0 16px 48px;
    }
    .curadoria-grid-wrapper {
      grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr));
      gap: 12px;
    }
    .curadoria-card-wrapper {
      padding: 20px;
      border-radius: 14px;
    }
    .curadoria-loading-wrapper {
      padding: 20px;
      flex-direction: column;
      text-align: center;
    }
  }
 
  /* ── MOBILE (max 480px) ── */
  @media (max-width: 480px) {
    .curadoria-header-wrapper {
      padding: 20px 14px;
      gap: 12px;
    }
    .curadoria-content-wrapper {
      padding: 0 14px 40px;
    }
    .curadoria-tabs-wrapper {
      margin: 16px 0;
      width: 100%;
    }
    .curadoria-tabs-wrapper button {
      flex: 1;
      justify-content: center;
      padding: 8px 8px;
      font-size: 12px;
    }
    .curadoria-grid-wrapper {
      grid-template-columns: 1fr;
      gap: 12px;
    }
    .curadoria-card-wrapper {
      padding: 16px;
      gap: 12px;
      border-radius: 12px;
    }
    .curadoria-card-header-row {
      flex-wrap: wrap;
    }
    .curadoria-card-footer-row {
      padding-top: 12px;
    }
    .curadoria-card-author {
      font-size: 12px;
    }
    .curadoria-card-link {
      font-size: 12px;
    }
    .curadoria-stats-row {
      flex-direction: column;
      gap: 6px;
    }
    .curadoria-footer-btn {
      width: 100%;
      justify-content: center;
      padding: 12px 20px;
      font-size: 14px;
    }
    .curadoria-loading-wrapper {
      padding: 16px;
      gap: 12px;
    }
  }
 
  /* ── SMALL MOBILE (max 360px) ── */
  @media (max-width: 360px) {
    .curadoria-card-wrapper {
      padding: 14px;
    }
  }
`
 
// ============================================================
// HELPERS
// ============================================================
function getSourceColor(source: string): string {
    switch (source.toLowerCase()) {
        case "reddit":
            return "#ff4500"
        case "youtube":
            return "#ff0000"
        default:
            return "#085fff"
    }
}
 
function formatDate(isoDate: string): string {
    if (!isoDate) return ""
    try {
        const date = new Date(isoDate)
        if (isNaN(date.getTime())) return ""
        return date.toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            timeZone: "America/Sao_Paulo",
        })
    } catch {
        return ""
    }
}
 
// ============================================================
// CURADORIA INBIX — Componente completo para Framer
// ============================================================
export function CuradoriaInbix() {
    const [items, setItems] = useState<CuratedItem[]>([])
    const [filter, setFilter] = useState<FilterType>("all")
    const [loading, setLoading] = useState(false)
    const [lastUpdate, setLastUpdate] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [statusMsg, setStatusMsg] = useState<string | null>(null)
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
 
    // Inject responsive CSS once
    useEffect(() => {
        const id = "curadoria-responsive-css"
        if (document.getElementById(id)) return
        const style = document.createElement("style")
        style.id = id
        style.textContent = RESPONSIVE_CSS
        document.head.appendChild(style)
    }, [])
 
    const fetchData = useCallback(async (): Promise<boolean> => {
        try {
            const res = await fetch(`${API_URL}/api/curadoria`)
            if (!res.ok) throw new Error("Erro ao carregar")
            const data = await res.json()
            setItems(data.items || [])
            setLastUpdate(data.updated_at)
            // Retorna true se o backend está auto-atualizando (dados vazios)
            return !!data._auto_updating
        } catch {
            return false
        }
    }, [])
 
    const stopPolling = useCallback(() => {
        if (pollRef.current) {
            clearInterval(pollRef.current)
            pollRef.current = null
        }
    }, [])
 
    const pollStatus = useCallback(() => {
        // Limpa polling anterior para evitar intervalos duplicados
        stopPolling()
        const startTime = Date.now()
        const POLL_TIMEOUT = 180_000 // 3 min max
        pollRef.current = setInterval(async () => {
            if (Date.now() - startTime > POLL_TIMEOUT) {
                stopPolling()
                setStatusMsg(null)
                setLoading(false)
                setError("Timeout: o servidor demorou demais. Tente novamente.")
                return
            }
            try {
                const res = await fetch(`${API_URL}/api/status`)
                if (!res.ok) return
                const data = await res.json()
 
                if (data.status === "running") {
                    setStatusMsg(data.detail || "Processando...")
                } else if (data.status === "done") {
                    stopPolling()
                    setStatusMsg(null)
                    setLoading(false)
                    await fetchData()
                } else if (data.status === "error") {
                    stopPolling()
                    setStatusMsg(null)
                    setLoading(false)
                    setError(data.detail || "Erro ao atualizar")
                }
            } catch {
                /* continue polling */
            }
        }, 2000)
    }, [fetchData, stopPolling])
 
    // Na montagem, busca dados. Se vazio, ativa loading + polling automático
    useEffect(() => {
        let mounted = true
        ;(async () => {
            const autoUpdating = await fetchData()
            if (mounted && autoUpdating) {
                setLoading(true)
                setStatusMsg("Carregando conteúdo pela primeira vez...")
                pollStatus()
            }
        })()
        return () => {
            mounted = false
            stopPolling()
        }
    }, [fetchData, pollStatus, stopPolling])
 
    const handleUpdate = async () => {
        setLoading(true)
        setError(null)
        setStatusMsg("Iniciando coleta de dados...")
 
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 180_000)
 
        try {
            const res = await fetch(`${API_URL}/api/atualizar`, {
                method: "POST",
                signal: controller.signal,
            })
            clearTimeout(timeoutId)
            if (!res.ok) throw new Error("Erro")
            pollStatus()
        } catch (err) {
            clearTimeout(timeoutId)
            if (err instanceof DOMException && err.name === "AbortError") {
                setError(
                    "Timeout na conexão. O servidor pode estar iniciando (cold start). Tente novamente em 30s."
                )
            } else {
                setError("Falha na conexão com o servidor")
            }
            setLoading(false)
            setStatusMsg(null)
        }
    }
 
    const filtered = items.filter((item) => {
        if (filter === "all") return true
        if (filter === "newsletters") return item.source === "Newsletter"
        if (filter === "reddit") return item.source === "Reddit"
        if (filter === "youtube") return item.source === "YouTube"
        return true
    })
 
    const counts = {
        all: items.length,
        newsletters: items.filter((i) => i.source === "Newsletter").length,
        reddit: items.filter((i) => i.source === "Reddit").length,
        youtube: items.filter((i) => i.source === "YouTube").length,
    }
 
    const TABS: { key: FilterType; label: string }[] = [
        { key: "all", label: "Todos" },
        { key: "youtube", label: "YouTube" },
        { key: "reddit", label: "Reddit" },
        { key: "newsletters", label: "Newsletters" },
    ]
 
    const formattedDate = lastUpdate
        ? new Date(lastUpdate).toLocaleDateString("pt-BR", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
              timeZone: "America/Sao_Paulo",
          })
        : null
 
    return (
        <div style={styles.app} className="curadoria-root-wrapper">
            {/* HEADER */}
            <div style={styles.accent} />
            <div className="curadoria-header-wrapper">
                <div style={{ flex: 1 }}>
                    <div style={styles.brand}>
                        <h1 style={styles.title}>
                            Curadoria{" "}
                            <span style={{ color: "#085fff" }}>Inbix</span>
                        </h1>
                    </div>
                    <p style={styles.subtitle}>Top posts e artigos da semana</p>
                    <div className="curadoria-stats-row">
                        {items.length > 0 && (
                            <span style={styles.stat}>
                                {items.length} artigos
                            </span>
                        )}
                        {formattedDate && (
                            <span style={styles.stat}>
                                Atualizado em {formattedDate}
                            </span>
                        )}
                    </div>
                </div>
                <button
                    className="curadoria-footer-btn"
                    style={
                        loading ? { color: "#a1a1aa", opacity: 0.6 } : {}
                    }
                    onClick={handleUpdate}
                    disabled={loading}
                >
                    {loading ? "Atualizando..." : "Atualizar dados"}
                </button>
            </div>
 
            {/* MAIN CONTENT */}
            <div className="curadoria-content-wrapper">
                {/* LOADING CARD */}
                {loading && (
                    <div className="curadoria-loading-wrapper">
                        <div style={styles.loadingIcon}>
                            <svg
                                width="28"
                                height="28"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="#085fff"
                                strokeWidth="2"
                                style={{
                                    animation: "framer-spin 1s linear infinite",
                                }}
                            >
                                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                            </svg>
                            <style>{`@keyframes framer-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
                        </div>
                        <div style={styles.loadingText}>
                            <strong
                                style={{
                                    display: "block",
                                    fontSize: 15,
                                    color: "#09090b",
                                    marginBottom: 2,
                                }}
                            >
                                Buscando novas atualizações
                            </strong>
                            {statusMsg && (
                                <p
                                    style={{
                                        fontSize: 13,
                                        color: "#71717a",
                                        margin: 0,
                                    }}
                                >
                                    {statusMsg}
                                </p>
                            )}
                        </div>
                    </div>
                )}
 
                {/* TABS */}
                <div className="curadoria-tabs-wrapper">
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
                                    ...(filter === tab.key
                                        ? styles.tabCountActive
                                        : {}),
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
                            Clique em "Atualizar dados" no topo da página para buscar os
                            artigos e posts mais recentes.
                        </p>
                    </div>
                ) : (
                    <div className="curadoria-grid-wrapper">
                        {filtered.map((item, i) => {
                            const color = getSourceColor(item.source)
                            const dateStr = formatDate(item.published_date)
                            return (
                                <div
                                    key={`${item.url}-${i}`}
                                    className="curadoria-card-wrapper"
                                    style={{ borderLeftColor: color }}
                                >
                                    <div className="curadoria-card-header-row">
                                        <span
                                            style={{
                                                ...styles.cardSource,
                                                color,
                                            }}
                                        >
                                            {item.channel}
                                        </span>
                                        <div className="curadoria-card-meta-row">
                                            {dateStr && (
                                                <span style={styles.cardDate}>
                                                    {dateStr}
                                                </span>
                                            )}
                                            {item.comment_count > 0 && (
                                                <span
                                                    style={styles.cardComments}
                                                >
                                                    {item.comment_count}{" "}
                                                    comments
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <h3 className="curadoria-card-title-text">
                                        <a
                                            href={item.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            style={{
                                                color: "inherit",
                                                textDecoration: "none",
                                            }}
                                        >
                                            {item.title}
                                        </a>
                                    </h3>
                                    {item.description &&
                                        item.description !== item.title && (
                                            <p className="curadoria-card-desc-text">
                                                {item.description.length > 200
                                                    ? item.description.slice(
                                                          0,
                                                          200
                                                      ) + "..."
                                                    : item.description}
                                            </p>
                                        )}
                                    <div className="curadoria-card-footer-row">
                                        <span className="curadoria-card-author">
                                            {item.author}
                                        </span>
                                        {item.url && (
                                            <a
                                                href={item.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="curadoria-card-link"
                                            >
                                                {item.source === "YouTube"
                                                    ? "Assistir →"
                                                    : "Ler mais →"}
                                            </a>
                                        )}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
 
            {/* FOOTER */}
            <div style={styles.footer}>
                <div style={styles.footerContent}>
                    <p style={{ fontSize: 13, color: "#a1a1aa", margin: 0 }}>
                        Powered by{" "}
                        <strong style={{ color: "#71717a" }}>
                            Agente Cassiano
                        </strong>{" "}
                        — Curadoria automatizada Inbix
                    </p>
                </div>
            </div>
        </div>
    )
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
        overflowX: "hidden" as const,
    },
    accent: {
        height: 4,
        background:
            "linear-gradient(90deg, #085fff 0%, #8d49f6 50%, #085fff 100%)",
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
    },
    stat: {
        fontSize: 13,
        color: "#a1a1aa",
    },
    loadingIcon: {
        flexShrink: 0,
    },
    loadingText: {
        flex: 1,
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
        whiteSpace: "nowrap",
        WebkitTapHighlightColor: "transparent",
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
    cardSource: {
        fontSize: 12,
        fontWeight: 600,
        textTransform: "uppercase" as const,
        letterSpacing: 0.3,
    },
    cardDate: {
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        fontSize: 11,
        fontWeight: 600,
        color: "#a1a1aa",
        background: "#fafafa",
        padding: "2px 8px",
        borderRadius: 9999,
    },
    cardComments: {
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        fontSize: 11,
        fontWeight: 600,
        color: "#a1a1aa",
        background: "#fafafa",
        padding: "2px 8px",
        borderRadius: 9999,
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
    footerContent: {
        display: "flex",
        flexDirection: "column" as const,
        alignItems: "center",
        gap: 16,
    },
}
 
export default CuradoriaInbix
 