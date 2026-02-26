import React from "react";
import type { CuratedItem } from "../types";

interface ContentCardProps {
  item: CuratedItem;
}

function getSourceColor(source: string): string {
  switch (source.toLowerCase()) {
    case "reddit":
      return "#ff4500";
    default:
      return "#085fff";
  }
}

function getSourceIcon(source: string) {
  if (source.toLowerCase() === "reddit") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm6.066 13.26c.041.307.062.618.062.934 0 3.19-3.695 5.776-8.25 5.776S1.628 17.384 1.628 14.194c0-.316.021-.627.062-.934a1.835 1.835 0 0 1-.736-1.478c0-1.016.823-1.839 1.839-1.839.494 0 .942.196 1.272.514 1.256-.889 2.984-1.46 4.906-1.521l.984-4.593.019-.005 3.22.687c.165-.387.553-.66.999-.66a1.108 1.108 0 0 1 0 2.216 1.108 1.108 0 0 1-1.06-.788l-2.86-.61-.87 4.065c1.876.078 3.555.65 4.784 1.524a1.836 1.836 0 0 1 3.108 1.328c0 .59-.28 1.117-.736 1.478zM8.5 13.5a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5zm7 0a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5zm-3.5 4.5c1.528 0 2.866-.572 3.535-1.42a.375.375 0 0 0-.574-.484C14.49 16.66 13.32 17.1 12 17.1s-2.49-.44-2.961-1.004a.375.375 0 0 0-.574.484c.669.848 2.007 1.42 3.535 1.42z" />
      </svg>
    );
  }
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22,6 12,13 2,6" />
    </svg>
  );
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + "...";
}

export function ContentCard({ item }: ContentCardProps) {
  const sourceColor = getSourceColor(item.source);

  return (
    <article className="card" style={{ "--source-color": sourceColor } as React.CSSProperties}>
      <div className="card__header">
        <div className="card__source" style={{ color: sourceColor }}>
          {getSourceIcon(item.source)}
          <span>{item.channel}</span>
        </div>
        {item.relevance_score > 0 && (
          <span className="card__score" title="Score de relevância">
            {Math.round(item.relevance_score)}
          </span>
        )}
      </div>

      <h3 className="card__title">
        <a href={item.url} target="_blank" rel="noopener noreferrer">
          {item.title}
        </a>
      </h3>

      {item.description && item.description !== item.title && (
        <p className="card__description">
          {truncateText(item.description, 200)}
        </p>
      )}

      <div className="card__footer">
        <span className="card__author">{item.author}</span>
        {item.url && (
          <a
            className="card__link"
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Ler mais
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </a>
        )}
      </div>
    </article>
  );
}

export default ContentCard;
