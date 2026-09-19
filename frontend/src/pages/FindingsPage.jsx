import React, { useEffect, useState } from 'react';
import { AlertTriangle, Filter, Search } from 'lucide-react';
import { getRuns } from '../services/api';
import IssueCard from '../components/IssueCard';

export default function FindingsPage() {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchFindings();
  }, []);

  const fetchFindings = async () => {
    try {
      const runs = await getRuns();
      let allIssues = [];
      runs.forEach((r) => {
        if (r.issues && r.issues.length > 0) {
          r.issues.forEach((i) => {
            allIssues.push({ ...i, run_goal: r.goal, run_id: r.id });
          });
        }
      });
      setIssues(allIssues);
    } catch (err) {
      console.error("Error fetching findings:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredIssues = issues.filter((i) => {
    const cat = (i.category || i.type || '').toUpperCase();
    const sev = (i.severity || '').toUpperCase();

    const matchCategory = categoryFilter === 'ALL' || cat === categoryFilter;
    const matchSeverity = severityFilter === 'ALL' || sev === severityFilter;
    const matchSearch =
      search === '' ||
      i.title.toLowerCase().includes(search.toLowerCase()) ||
      i.description.toLowerCase().includes(search.toLowerCase()) ||
      (i.url || '').toLowerCase().includes(search.toLowerCase());

    return matchCategory && matchSeverity && matchSearch;
  });

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[var(--text)] mb-1">
            Defects &amp; Audit Findings
          </h1>
          <p className="text-xs text-[var(--text-secondary)]">
            Consolidated repository of discovered WCAG violations, UX friction points, and security issues.
          </p>
        </div>

        <div className="text-xs font-mono text-[var(--text-muted)] bg-[var(--surface)] border border-[var(--border)] px-3 py-1.5 rounded-md">
          Total Issues: <span className="font-bold text-[var(--text)]">{issues.length}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search defects by title or URL..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-[var(--surface)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
          />
        </div>

        <div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full py-1.5 px-3 text-xs bg-[var(--surface)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
          >
            <option value="ALL">All Categories</option>
            <option value="ACCESSIBILITY">Accessibility Only</option>
            <option value="FRICTION">UX Friction Only</option>
            <option value="SECURITY">Security Surface Only</option>
            <option value="BROKEN_LINK">Broken Links Only</option>
            <option value="PERFORMANCE">Performance Only</option>
          </select>
        </div>

        <div>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="w-full py-1.5 px-3 text-xs bg-[var(--surface)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md text-[var(--text)] outline-none transition-colors"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical Severity</option>
            <option value="HIGH">High Severity</option>
            <option value="MEDIUM">Medium Severity</option>
            <option value="LOW">Low Severity</option>
          </select>
        </div>
      </div>

      {/* Findings List */}
      {loading ? (
        <div className="p-16 text-center text-xs text-[var(--text-muted)] font-mono">
          Loading findings catalog...
        </div>
      ) : filteredIssues.length === 0 ? (
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-16 text-center text-xs text-[var(--text-muted)] font-mono">
          No matching findings found.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredIssues.map((issue, idx) => (
            <IssueCard key={issue.id || idx} issue={issue} />
          ))}
        </div>
      )}
    </div>
  );
}
