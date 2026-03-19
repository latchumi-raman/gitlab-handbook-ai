

const TOPICS = [
  { label: "CREDIT values",    query: "What are GitLab's CREDIT values and what does each one mean?" },
  { label: "Product direction", query: "What is GitLab's current product direction and strategy?" },
  { label: "Hiring process",   query: "How does GitLab's hiring and interview process work?" },
  { label: "Engineering",      query: "What is GitLab's engineering culture and development practices?" },
  { label: "Remote work",      query: "How does GitLab handle all-remote work and async communication?" },
  { label: "OKRs & goals",     query: "How does GitLab run OKRs and set company goals?" },
  { label: "Compensation",     query: "How does GitLab handle compensation and its pay transparency policy?" },
  { label: "Career growth",    query: "What does the career development framework look like at GitLab?" },
];

interface QuickTopicsProps {
  onSelect: (query: string) => void;
}

export function QuickTopics({ onSelect }: QuickTopicsProps) {
  return (
    <div>
      <p className="px-3 text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1.5">
        Quick topics
      </p>
      {TOPICS.map((t) => (
        <button
          key={t.label}
          onClick={() => onSelect(t.query)}
          className="sidebar-item w-full text-left"
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}