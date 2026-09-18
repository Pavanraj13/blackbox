import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import AgentPage from './pages/AgentPage';
import RunsPage from './pages/RunsPage';
import FindingsPage from './pages/FindingsPage';
import ReportPage from './pages/ReportPage';

export default function App() {
  return (
    <Router>
      <div className="flex min-h-screen bg-[#070a13] text-slate-100">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Header title="Autonomous UI/UX & Accessibility Agent" subtitle="Black-Box Agentic Testing Framework" />
          <main className="flex-1 pb-12 overflow-x-hidden">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/agent" element={<AgentPage />} />
              <Route path="/runs" element={<RunsPage />} />
              <Route path="/findings" element={<FindingsPage />} />
              <Route path="/report/:id" element={<ReportPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}
