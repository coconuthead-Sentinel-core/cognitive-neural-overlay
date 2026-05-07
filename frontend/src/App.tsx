import { useState } from "react";
import { Dashboard } from "./Dashboard";
import { Console } from "./Console";

type Tab = "console" | "dashboard";

export function App() {
  const [tab, setTab] = useState<Tab>("console");

  return (
    <div className="layout">
      <header>
        <h1>Cognitive Neural Overlay</h1>
        <span className="glyph-pipeline">📥 → 🔄 → 🧊 → 🥥 → 📤</span>
      </header>

      <nav className="tabs">
        <button
          className={tab === "console" ? "tab active" : "tab"}
          onClick={() => setTab("console")}
        >
          Console
        </button>
        <button
          className={tab === "dashboard" ? "tab active" : "tab"}
          onClick={() => setTab("dashboard")}
        >
          Audit Dashboard
        </button>
      </nav>

      {tab === "console"   && <Console />}
      {tab === "dashboard" && <Dashboard />}
    </div>
  );
}
