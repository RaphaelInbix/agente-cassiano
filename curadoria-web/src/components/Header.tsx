import React from "react";

interface HeaderProps {
  onUpdate: () => void;
  loading: boolean;
  lastUpdate: string | null;
  totalItems: number;
}

export function Header({ onUpdate, loading, lastUpdate, totalItems }: HeaderProps) {
  const formattedDate = lastUpdate
    ? new Date(lastUpdate).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "America/Sao_Paulo",
      })
    : null;

  return (
    <header className="header">
      <div className="header__accent" />
      <div className="header__content">
        <div className="header__text">
          <div className="header__brand">
            <h1 className="header__title">
              Curadoria <span className="header__title--accent">Inbix</span>
            </h1>
          </div>
          <p className="header__subtitle">
            Top posts e artigos da semana
          </p>
          <div className="header__stats">
            {totalItems > 0 && (
              <span className="header__stat">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
                {totalItems} artigos
              </span>
            )}
            {formattedDate && (
              <span className="header__stat">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                Atualizado em {formattedDate}
              </span>
            )}
          </div>
        </div>
        <button
          className={`header__update-btn ${loading ? "header__update-btn--loading" : ""}`}
          onClick={onUpdate}
          disabled={loading}
        >
          {loading ? (
            <>
              <svg className="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Atualizando...
            </>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              Atualizar
            </>
          )}
        </button>
      </div>
    </header>
  );
}

export default Header;
