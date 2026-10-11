"use client";

import React, { useState, useMemo } from "react";
import { BookOpen, Search, Sparkles, Lightbulb, HelpCircle, X, ChevronRight, Layers, ArrowRight } from "lucide-react";
import { GLOSSARY_TERMS, GlossaryTerm } from "./glossary_data";

interface GlossarySectionProps {
  isModal?: boolean;
  onClose?: () => void;
  onNavigateTab?: (tabId: string) => void;
}

export default function GlossarySection({ isModal = false, onClose, onNavigateTab }: GlossarySectionProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  const categories = ["All", "Data & Pipeline", "Statistics", "Machine Learning", "Wildfire & Forestry", "Governance & Tools"];

  const filteredTerms = useMemo(() => {
    return GLOSSARY_TERMS.filter((item) => {
      const matchesCategory = selectedCategory === "All" || item.category === selectedCategory;
      const q = searchTerm.toLowerCase();
      const matchesSearch =
        item.term.toLowerCase().includes(q) ||
        item.simpleDef.toLowerCase().includes(q) ||
        item.analogy.toLowerCase().includes(q) ||
        item.whyItMatters.toLowerCase().includes(q);
      return matchesCategory && matchesSearch;
    });
  }, [searchTerm, selectedCategory]);

  return (
    <div className={isModal ? "glossary-modal-inner" : "fade-in"}>
      {/* Header Banner */}
      <div
        className="glass-panel"
        style={{
          padding: isModal ? "1.5rem" : "2rem",
          marginBottom: "1.5rem",
          background: "linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 253, 244, 0.9) 100%)",
          border: "1px solid rgba(16, 185, 129, 0.25)",
          position: "relative",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "0.45rem", background: "rgba(16, 185, 129, 0.12)", border: "1px solid rgba(16, 185, 129, 0.25)", borderRadius: "999px", padding: "0.25rem 0.75rem", fontSize: "0.78rem", fontWeight: 700, color: "#047857", marginBottom: "0.75rem" }}>
              <Lightbulb size={14} style={{ color: "#059669" }} />
              <span>Demystifying Technical Terms For Everyday People</span>
            </div>
            <h2 style={{ fontSize: isModal ? "1.5rem" : "1.85rem", fontWeight: 800, color: "var(--text-heading)", margin: "0 0 0.5rem 0" }}>
              Plain English & Intuition Dictionary
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", margin: 0, maxWidth: "750px", lineHeight: 1.55 }}>
              Forest science and AI are full of heavy jargon like <em>DAG</em>, <em>PCA</em>, <em>Macro F1</em>, <em>Aspect</em>, and <em>Imputation</em>.
              Here is what every single term means in simple everyday words, backed by clear real-world analogies.
            </p>
          </div>

          {isModal && onClose && (
            <button
              onClick={onClose}
              className="sidebar-close-btn"
              style={{ display: "flex", background: "#f1f5f9", borderRadius: "8px", padding: "0.4rem" }}
              aria-label="Close glossary"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Search & Category Filter Controls */}
        <div style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ position: "relative", maxWidth: "600px" }}>
            <Search size={18} style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)", color: "var(--text-dim)" }} />
            <input
              type="text"
              placeholder="Search any term (e.g., PCA, Random Forest, Aspect, Skewness, DAG, Crown Fire)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: "100%",
                padding: "0.75rem 1rem 0.75rem 2.6rem",
                borderRadius: "10px",
                border: "1px solid var(--border-medium)",
                background: "#ffffff",
                fontSize: "0.92rem",
                boxShadow: "0 2px 8px rgba(0,0,0,0.03)",
                outline: "none",
              }}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm("")}
                style={{ position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--text-dim)" }}
              >
                <X size={16} />
              </button>
            )}
          </div>

          {/* Category Filter Pills */}
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {categories.map((cat) => {
              const isSelected = selectedCategory === cat;
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    padding: "0.45rem 0.95rem",
                    borderRadius: "999px",
                    border: isSelected ? "1px solid #059669" : "1px solid var(--border-subtle)",
                    background: isSelected ? "var(--accent-mint-light)" : "#ffffff",
                    color: isSelected ? "#064e3b" : "var(--text-muted)",
                    fontWeight: isSelected ? 700 : 500,
                    fontSize: "0.82rem",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                >
                  {cat}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Results Count Banner */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", padding: "0 0.5rem" }}>
        <span style={{ fontSize: "0.88rem", color: "var(--text-muted)" }}>
          Showing <strong>{filteredTerms.length}</strong> of {GLOSSARY_TERMS.length} technical concepts
        </span>
        {searchTerm && (
          <button
            onClick={() => setSearchTerm("")}
            style={{ background: "none", border: "none", color: "#059669", fontSize: "0.82rem", cursor: "pointer", fontWeight: 600 }}
          >
            Clear Search Filter
          </button>
        )}
      </div>

      {/* Glossary Cards Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.25rem" }}>
        {filteredTerms.map((item) => (
          <div
            key={item.id}
            className="glass-panel"
            style={{
              padding: "1.5rem",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              background: "#ffffff",
              border: "1px solid var(--border-subtle)",
              borderRadius: "14px",
              boxShadow: "0 3px 12px rgba(0,0,0,0.03)",
            }}
          >
            <div>
              {/* Card Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.75rem", marginBottom: "0.75rem" }}>
                <div>
                  <span
                    style={{
                      display: "inline-block",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      color: "#059669",
                      background: "rgba(16, 185, 129, 0.1)",
                      padding: "0.2rem 0.55rem",
                      borderRadius: "6px",
                      marginBottom: "0.35rem",
                    }}
                  >
                    {item.category} • {item.tag}
                  </span>
                  <h3 style={{ fontSize: "1.18rem", fontWeight: 800, color: "var(--text-heading)", margin: 0, lineHeight: 1.3 }}>
                    {item.term}
                  </h3>
                </div>
              </div>

              {/* In Plain English */}
              <div style={{ marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-dim)", marginBottom: "0.25rem" }}>
                  In Everyday Words:
                </div>
                <p style={{ fontSize: "0.92rem", color: "var(--text-main)", lineHeight: 1.5, margin: 0, fontWeight: 500 }}>
                  {item.simpleDef}
                </p>
              </div>

              {/* Intuition & Metaphor Box */}
              <div
                style={{
                  background: "linear-gradient(135deg, rgba(254, 243, 199, 0.45) 0%, rgba(254, 249, 195, 0.35) 100%)",
                  border: "1px solid rgba(245, 158, 11, 0.28)",
                  borderRadius: "10px",
                  padding: "0.85rem 1rem",
                  marginBottom: "1rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", color: "#b45309", fontWeight: 700, fontSize: "0.8rem", marginBottom: "0.3rem" }}>
                  <Lightbulb size={14} />
                  <span>Real-World Intuition / Analogy:</span>
                </div>
                <p style={{ fontSize: "0.86rem", color: "#78350f", lineHeight: 1.5, margin: 0 }}>
                  {item.analogy}
                </p>
              </div>

              {/* Why It Matters */}
              <div style={{ marginBottom: "0.85rem" }}>
                <div style={{ fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.04em", color: "#047857", marginBottom: "0.25rem" }}>
                  Why It Matters for Forest & Wildfire Safety:
                </div>
                <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.45, margin: 0 }}>
                  {item.whyItMatters}
                </p>
              </div>
            </div>

            {/* Where Used Footer */}
            <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "0.75rem", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.76rem" }}>
              <span style={{ color: "var(--text-dim)" }}>
                Where it is used: <strong style={{ color: "var(--text-heading)" }}>{item.whereUsed}</strong>
              </span>
            </div>
          </div>
        ))}
      </div>

      {filteredTerms.length === 0 && (
        <div style={{ textAlign: "center", padding: "3rem 1rem", background: "#ffffff", borderRadius: "14px", border: "1px solid var(--border-subtle)" }}>
          <HelpCircle size={36} style={{ color: "var(--text-dim)", marginBottom: "0.5rem" }} />
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-heading)", marginBottom: "0.3rem" }}>
            No matching terms found for &quot;{searchTerm}&quot;
          </h3>
          <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
            Try searching for words like &quot;PCA&quot;, &quot;Slope&quot;, &quot;Aspect&quot;, &quot;Forest&quot;, &quot;F1&quot;, or &quot;Imputation&quot;.
          </p>
          <button
            onClick={() => {
              setSearchTerm("");
              setSelectedCategory("All");
            }}
            className="btn-secondary"
            style={{ fontSize: "0.85rem", padding: "0.5rem 1rem" }}
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
}
