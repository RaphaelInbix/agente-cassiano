export interface CuratedItem {
  title: string;
  source: string;
  channel: string;
  description: string;
  author: string;
  url: string;
  relevance_score: number;
  tags: string[];
}

export interface CuradoriaData {
  updated_at: string | null;
  total: number;
  items: CuratedItem[];
}

export type FilterType = "all" | "newsletters" | "reddit" | "youtube";
