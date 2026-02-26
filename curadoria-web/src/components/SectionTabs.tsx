import React from "react";
import type { FilterType } from "../types";

interface SectionTabsProps {
  active: FilterType;
  onChange: (filter: FilterType) => void;
  counts: {
    all: number;
    newsletters: number;
    reddit: number;
  };
}

const TABS: { key: FilterType; label: string }[] = [
  { key: "all", label: "Todos" },
  { key: "newsletters", label: "Newsletters" },
  { key: "reddit", label: "Reddit" },
];

export function SectionTabs({ active, onChange, counts }: SectionTabsProps) {
  return (
    <nav className="tabs">
      {TABS.map((tab) => (
        <button
          key={tab.key}
          className={`tabs__btn ${active === tab.key ? "tabs__btn--active" : ""}`}
          onClick={() => onChange(tab.key)}
        >
          {tab.label}
          <span className="tabs__count">{counts[tab.key]}</span>
        </button>
      ))}
    </nav>
  );
}

export default SectionTabs;
