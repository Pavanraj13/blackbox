import React, { useState } from 'react';
import { Puzzle, Chrome, Copy, Check, ExternalLink, Shield } from 'lucide-react';
import { getStoredApiKey } from '../services/api';

export default function ExtensionGuidePage() {
  const [copiedPath, setCopiedPath] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const apiKey = getStoredApiKey();
  const extensionPath = 'c:\\Users\\SRIRAM\\Documents\\GitHub\\blackbox\\blackbox\\extension';

  const copyPath = () => {
    navigator.clipboard.writeText(extensionPath);
    setCopiedPath(true);
    setTimeout(() => setCopiedPath(false), 2000);
  };

  const copyKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-8 py-8">
      <div className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight text-[var(--text)] mb-1">
          Chrome Browser Extension Guide
        </h1>
        <p className="text-xs text-[var(--text-secondary)]">
          Install the Blackbox toolbar extension to test any web application with a single click directly from your active browser tab.
        </p>
      </div>

      <div className="space-y-6">
        {/* Quick Credentials Panel */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-xs font-semibold text-[var(--text)] mb-1">
              Extension Directory Path
            </div>
            <code className="text-xs font-mono text-[var(--accent)] bg-[var(--surface-elevated)] px-2 py-1 rounded border border-[var(--border)]">
              {extensionPath}
            </code>
          </div>
          <button
            onClick={copyPath}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[var(--border)] hover:border-[var(--border-hover)] bg-[var(--surface-elevated)] text-xs font-medium text-[var(--text)] transition-colors self-start sm:self-auto"
          >
            {copiedPath ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedPath ? 'Path Copied' : 'Copy Folder Path'}</span>
          </button>
        </div>

        {/* Steps */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-6 space-y-6">
          <div className="flex gap-4 items-start">
            <div className="w-6 h-6 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] font-semibold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
              1
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[var(--text)] mb-1">
                Open Extension Manager in Chrome, Edge, or Brave
              </h3>
              <p className="text-xs text-[var(--text-secondary)] mb-2">
                Type the URL into your browser address bar:
              </p>
              <code className="inline-block px-2.5 py-1 rounded bg-[var(--surface-elevated)] border border-[var(--border)] text-xs font-mono text-[var(--text)]">
                chrome://extensions
              </code>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="w-6 h-6 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] font-semibold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
              2
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[var(--text)] mb-1">
                Enable Developer Mode
              </h3>
              <p className="text-xs text-[var(--text-secondary)]">
                Toggle the <strong>Developer mode</strong> switch in the top-right corner of the Extensions page.
              </p>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="w-6 h-6 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] font-semibold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
              3
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[var(--text)] mb-1">
                Load Unpacked Extension
              </h3>
              <p className="text-xs text-[var(--text-secondary)] mb-2">
                Click the <strong>Load unpacked</strong> button and select the project extension directory:
              </p>
              <div className="p-3 bg-[var(--surface-elevated)] border border-[var(--border)] rounded text-xs font-mono text-[var(--text)]">
                {extensionPath}
              </div>
            </div>
          </div>

          <div className="flex gap-4 items-start">
            <div className="w-6 h-6 rounded-full bg-[var(--accent-soft)] text-[var(--accent)] font-semibold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
              4
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[var(--text)] mb-1">
                Authenticate &amp; Start Testing
              </h3>
              <p className="text-xs text-[var(--text-secondary)] mb-3">
                Click the Blackbox extension icon in your browser toolbar. If prompted for your API key, click <strong>Config</strong> in the popup and paste your key.
              </p>
              {apiKey && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--text-muted)] font-medium">Your API Key:</span>
                  <code className="text-xs font-mono text-[var(--text)] bg-[var(--surface-elevated)] px-2 py-0.5 rounded border border-[var(--border)]">
                    {apiKey.slice(0, 10)}...{apiKey.slice(-4)}
                  </code>
                  <button
                    onClick={copyKey}
                    className="inline-flex items-center gap-1 text-xs text-[var(--accent)] hover:underline font-medium"
                  >
                    {copiedKey ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedKey ? 'Copied' : 'Copy Key'}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
