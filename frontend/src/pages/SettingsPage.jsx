import React, { useState, useEffect } from 'react';
import { Shield, Key, Check, Copy, RefreshCw, Cpu, Sun, Moon } from 'lucide-react';
import { getKeyInfo, getStoredApiKey, setStoredApiKey, getRuns } from '../services/api';
import { useTheme } from '../context/ThemeContext';

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  const [apiKey, setApiKey] = useState(getStoredApiKey());
  const [keyInfo, setKeyInfo] = useState({ auth_enabled: false, key_preview: '', encryption_enabled: true });
  const [testStatus, setTestStatus] = useState(null);
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadInfo();
  }, []);

  const loadInfo = async () => {
    try {
      const data = await getKeyInfo();
      setKeyInfo(data);
      if (!apiKey && data.api_key) {
        setApiKey(data.api_key);
        setStoredApiKey(data.api_key);
      }
    } catch (e) {
      console.warn('Could not fetch key info:', e);
    }
  };

  const handleSaveKey = (e) => {
    e.preventDefault();
    setStoredApiKey(apiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    verifyKey();
  };

  const verifyKey = async () => {
    setTestStatus('testing');
    try {
      await getRuns();
      setTestStatus('valid');
    } catch (err) {
      setTestStatus('invalid');
    }
  };

  const copyKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-8 py-8">
      <div className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight text-[var(--text)] mb-1">
          System Settings &amp; Security
        </h1>
        <p className="text-xs text-[var(--text-secondary)]">
          Manage backend authentication credentials, encryption preferences, and local models.
        </p>
      </div>

      <div className="space-y-6">
        {/* API Authentication */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6">
          <div className="flex items-center gap-2 mb-3">
            <Key className="w-4 h-4 text-[var(--accent)]" />
            <h2 className="text-sm font-semibold tracking-tight text-[var(--text)]">
              API Authentication Key
            </h2>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">
            All requests between the dashboard, browser extension, and FastAPI engine are authenticated with the <code className="px-1.5 py-0.5 rounded bg-[var(--surface-elevated)] border border-[var(--border)] font-mono text-[11px]">X-API-Key</code> header.
          </p>

          <form onSubmit={handleSaveKey} className="space-y-3 max-w-xl">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
                Client API Key
              </label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="bb_..."
                  className="flex-1 bg-[var(--surface-elevated)] border border-[var(--border)] focus:border-[var(--accent)] rounded-md px-3 py-2 text-xs font-mono text-[var(--text)] outline-none"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-[var(--accent)] hover:bg-blue-600 text-white rounded-md text-xs font-medium transition-colors"
                >
                  {saved ? 'Saved!' : 'Save Key'}
                </button>
                {apiKey && (
                  <button
                    type="button"
                    onClick={copyKey}
                    className="p-2 border border-[var(--border)] hover:border-[var(--border-hover)] rounded-md text-[var(--text-secondary)] hover:text-[var(--text)]"
                    title="Copy API key"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={verifyKey}
                className="inline-flex items-center gap-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text)] font-medium"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${testStatus === 'testing' ? 'animate-spin' : ''}`} />
                <span>Test Connection</span>
              </button>

              {testStatus === 'valid' && (
                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                  Authentication verified successfully.
                </span>
              )}
              {testStatus === 'invalid' && (
                <span className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                  Invalid API key or backend unreachable.
                </span>
              )}
            </div>
          </form>
        </div>

        {/* AES Encryption At Rest */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-emerald-500" />
            <h2 className="text-sm font-semibold tracking-tight text-[var(--text)]">
              AES-256-GCM Encryption at Rest
            </h2>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">
            Report file paths, session narratives, and sensitive artifacts are securely encrypted in the SQLite database before storage.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl">
            <div className="p-3 rounded-md bg-[var(--surface-elevated)] border border-[var(--border)]">
              <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                Database Encryption
              </div>
              <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                {keyInfo.encryption_enabled ? 'Active (AES-256-GCM)' : 'Disabled'}
              </div>
            </div>

            <div className="p-3 rounded-md bg-[var(--surface-elevated)] border border-[var(--border)]">
              <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                LLM Data Redaction
              </div>
              <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                Active (PII, Passwords, CCs)
              </div>
            </div>
          </div>
        </div>

        {/* Local LLM Architecture */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6">
          <div className="flex items-center gap-2 mb-3">
            <Cpu className="w-4 h-4 text-[var(--accent)]" />
            <h2 className="text-sm font-semibold tracking-tight text-[var(--text)]">
              Local LLM Multi-Model Engine
            </h2>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mb-4 leading-relaxed">
            Configured with a high-throughput dual model setup:
          </p>
          <div className="space-y-2 text-xs font-mono max-w-xl">
            <div className="flex justify-between p-2.5 rounded bg-[var(--surface-elevated)] border border-[var(--border)]">
              <span className="text-[var(--text-secondary)]">Action Planner:</span>
              <span className="font-bold text-[var(--text)]">qwen2.5:7b (~2s/step)</span>
            </div>
            <div className="flex justify-between p-2.5 rounded bg-[var(--surface-elevated)] border border-[var(--border)]">
              <span className="text-[var(--text-secondary)]">Issue Scorer &amp; Reporter:</span>
              <span className="font-bold text-[var(--text)]">qwen3.6:35b (Deep Analysis)</span>
            </div>
          </div>
        </div>

        {/* Appearance Settings */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold tracking-tight text-[var(--text)] mb-1">
                Appearance &amp; Theme
              </h2>
              <p className="text-xs text-[var(--text-secondary)]">
                Currently using <span className="font-medium capitalize text-[var(--text)]">{theme} mode</span>.
              </p>
            </div>
            <button
              onClick={toggleTheme}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-md border border-[var(--border)] hover:border-[var(--border-hover)] bg-[var(--surface-elevated)] text-xs font-medium text-[var(--text)] transition-colors"
            >
              {theme === 'dark' ? (
                <>
                  <Sun className="w-4 h-4 text-amber-400" />
                  <span>Switch to Light</span>
                </>
              ) : (
                <>
                  <Moon className="w-4 h-4 text-slate-600" />
                  <span>Switch to Dark</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
