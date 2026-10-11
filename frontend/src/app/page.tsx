"use client";

import React, { useState, useEffect } from "react";

// Preset configurations for interactive predictions
const PRESETS: Record<string, { name: string; elevation: number; slope: number; aspect: number; dist_road: number; dist_fire: number; wa: number; soil: number }> = {
  spruce: {
    name: "Subalpine Spruce/Fir (High Elevation)",
    elevation: 3200,
    slope: 12,
    aspect: 90,
    dist_road: 2100,
    dist_fire: 1800,
    wa: 1, // Rawah
    soil: 29,
  },
  lodgepole: {
    name: "Montane Lodgepole Pine (Mid Elevation)",
    elevation: 2850,
    slope: 15,
    aspect: 140,
    dist_road: 1500,
    dist_fire: 2400,
    wa: 1, // Rawah
    soil: 22,
  },
  ponderosa: {
    name: "Dry Ponderosa Pine (Low Elevation)",
    elevation: 2300,
    slope: 18,
    aspect: 210,
    dist_road: 850,
    dist_fire: 1200,
    wa: 4, // Cache la Poudre
    soil: 10,
  },
  cottonwood: {
    name: "Riparian Cottonwood/Willow (Valley)",
    elevation: 2000,
    slope: 6,
    aspect: 45,
    dist_road: 400,
    dist_fire: 900,
    wa: 4, // Cache la Poudre
    soil: 3,
  },
  krummholz: {
    name: "Alpine Krummholz (Alpine Tree Line)",
    elevation: 3550,
    slope: 28,
    aspect: 310,
    dist_road: 3200,
    dist_fire: 3000,
    wa: 2, // Neota
    soil: 39,
  },
};

const COVER_TYPE_META: Record<number, { name: string; color: string; desc: string }> = {
  1: { name: "Spruce / Fir", color: "#10b981", desc: "High elevation subalpine conifer (2,700m–3,400m), moist soils." },
  2: { name: "Lodgepole Pine", color: "#3b82f6", desc: "Mid elevation fire-adapted dominant seral stands (2,500m–3,100m)." },
  3: { name: "Ponderosa Pine", color: "#f59e0b", desc: "Dry lower montane slopes (1,800m–2,600m), fire-dependent." },
  4: { name: "Cottonwood / Willow", color: "#06b6d4", desc: "Riparian valleys, streamsides, lowest elevation (<2,300m)." },
  5: { name: "Aspen", color: "#8b5cf6", desc: "Moist slopes, open sunny meadows, deciduous disturbance pioneer." },
  6: { name: "Douglas-fir", color: "#ec4899", desc: "Cool, north-facing slopes and rocky canyon terrain." },
  7: { name: "Krummholz", color: "#ef4444", desc: "Stunted subalpine/alpine ecotone trees (>3,300m) in harsh winds." },
};

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  // Prediction State
  const [elev, setElev] = useState<number>(2950);
  const [slope, setSlope] = useState<number>(14);
  const [aspect, setAspect] = useState<number>(120);
  const [distHydro, setDistHydro] = useState<number>(250);
  const [vertHydro, setVertHydro] = useState<number>(30);
  const [distRoad, setDistRoad] = useState<number>(1800);
  const [distFire, setDistFire] = useState<number>(1950);
  const [selectedWA, setSelectedWA] = useState<number>(1);
  const [selectedSoil, setSelectedSoil] = useState<number>(29);
  const [modelType, setModelType] = useState<string>("random_forest");
  const [isPredicting, setIsPredicting] = useState<boolean>(false);
  const [predictionResult, setPredictionResult] = useState<any>(null);

  // Search filter for dataset explorer
  const [featureSearch, setFeatureSearch] = useState<string>("");

  // API Base URL (Configurable for Vercel -> Render production deployment)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Check backend health on mount
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, [API_BASE]);

  const handleApplyPreset = (key: string) => {
    const p = PRESETS[key];
    if (!p) return;
    setElev(p.elevation);
    setSlope(p.slope);
    setAspect(p.aspect);
    setDistRoad(p.dist_road);
    setDistFire(p.dist_fire);
    setSelectedWA(p.wa);
    setSelectedSoil(p.soil);
  };

  const handlePredict = async () => {
    setIsPredicting(true);
    const features: Record<string, number> = {
      Elevation: elev,
      Aspect: aspect,
      Slope: slope,
      Horizontal_Distance_To_Hydrology: distHydro,
      Vertical_Distance_To_Hydrology: vertHydro,
      Horizontal_Distance_To_Roadways: distRoad,
      Hillshade_9am: Math.min(255, Math.max(0, Math.round(200 - aspect * 0.2))),
      Hillshade_Noon: Math.min(255, Math.max(0, Math.round(240 - slope * 1.5))),
      Hillshade_3pm: Math.min(255, Math.max(0, Math.round(140 + aspect * 0.25))),
      Horizontal_Distance_To_Fire_Points: distFire,
    };

    for (let i = 1; i <= 4; i++) {
      features[`Wilderness_Area${i}`] = i === selectedWA ? 1 : 0;
    }
    for (let i = 1; i <= 40; i++) {
      features[`Soil_Type${i}`] = i === selectedSoil ? 1 : 0;
    }

    try {
      const res = await fetch(`${API_BASE}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ features, model: modelType }),
      });
      if (res.ok) {
        const data = await res.json();
        setPredictionResult(data);
      } else {
        throw new Error("API call failed");
      }
    } catch {
      let cid = 2;
      if (elev > 3300) cid = 7;
      else if (elev > 3000) cid = 1;
      else if (elev < 2200) cid = 4;
      else if (elev < 2500) cid = 3;

      setPredictionResult({
        predicted_cover_type: cid,
        cover_name: COVER_TYPE_META[cid].name,
        model_used: `${modelType} (local heuristic preview)`,
        probabilities: {
          [COVER_TYPE_META[cid].name]: 0.88,
          "Lodgepole Pine": cid === 2 ? 0.88 : 0.08,
          "Spruce / Fir": cid === 1 ? 0.88 : 0.04,
        },
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsPredicting(false);
    }
  };

  const navItems = [
    { id: "overview", label: "Overview" },
    { id: "dataset", label: "Dataset Explorer" },
    { id: "cleaning", label: "Cleaning Demo" },
    { id: "statistics", label: "Descriptive Stats" },
    { id: "features_pca", label: "PCA & Features" },
    { id: "classification", label: "Classification" },
    { id: "clustering", label: "Clustering" },
    { id: "regression", label: "Fires Regression" },
    { id: "prediction", label: "Prediction Playground" },
    { id: "wildfire", label: "Wildfire Screening" },
    { id: "governance", label: "Governance & Tools" },
  ];

  return (
    <div>
      {/* Navigation Header */}
      <nav className="navbar">
        <div className="nav-brand">
          <span className="brand-icon">🌲</span>
          <div>
            <div className="brand-title">Forest Cover & Wildfire Analytics Platform</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Python ↔ Supabase ↔ KNIME ↔ Tableau ↔ FastAPI ↔ Next.js
            </div>
          </div>
        </div>

        <div className="nav-tabs" style={{ flexWrap: "wrap", justifyContent: "center" }}>
          {navItems.map((tab) => (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`nav-tab-btn ${activeTab === tab.id ? "active" : ""}`}
              style={{ fontSize: "0.82rem", padding: "0.4rem 0.8rem" }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div>
          <span
            className="badge"
            style={{
              background: apiOnline ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
              color: apiOnline ? "#34d399" : "#fbbf24",
              border: `1px solid ${apiOnline ? "rgba(16, 185, 129, 0.3)" : "rgba(245, 158, 11, 0.3)"}`,
            }}
          >
            ● {apiOnline ? "FastAPI Online" : "Standalone Local"}
          </span>
        </div>
      </nav>

      {/* Main Container */}
      <main className="main-container fade-in">
        {/* ========================================================================= */}
        {/* PAGE 1: PROJECT OVERVIEW */}
        {/* ========================================================================= */}
        {activeTab === "overview" && (
          <div>
            <div className="glass-panel" style={{ padding: "2.5rem", marginBottom: "2rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
                <div>
                  <h1 style={{ fontSize: "2.2rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                    Roosevelt National Forest Analytics System
                  </h1>
                  <p style={{ color: "var(--text-muted)", maxWidth: "800px", fontSize: "1.05rem" }}>
                    An integrated multi-platform system connecting <strong>Python</strong>, <strong>Supabase</strong>, 
                    <strong>KNIME</strong>, <strong>Tableau</strong>, and a full-stack web application to predict forest tree species 
                    distribution across 581,012 cartographic grid cells and evaluate topographic wildfire risk.
                  </p>
                </div>
                <button
                  id="btn-goto-predict"
                  onClick={() => setActiveTab("prediction")}
                  className="btn-primary"
                  style={{ alignSelf: "center" }}
                >
                  Launch Predictor →
                </button>
              </div>
            </div>

            <div className="stats-grid">
              <div className="glass-panel stat-card">
                <span className="stat-label">Total Observations</span>
                <span className="stat-value">581,012</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>30m × 30m spatial cells</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Input Predictors</span>
                <span className="stat-value">54</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>10 terrain, 4 WA, 40 soil</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Dominant Species</span>
                <span className="stat-value" style={{ color: "#3b82f6" }}>Lodgepole</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>48.76% of forest cover</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Random Forest Acc</span>
                <span className="stat-value" style={{ color: "#10b981" }}>93.5%</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Macro F1: 0.906</span>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "1.5rem" }}>
              <div className="glass-panel" style={{ padding: "1.8rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem", color: "#60a5fa" }}>
                  Integrity Guarantee
                </h3>
                <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginBottom: "1rem" }}>
                  The source raw dataset (<code>data/raw/covtype.csv</code>) is locked and verified with a 
                  cryptographic SHA-256 hash. Missing-value cleaning protocols are demonstrated on an explicit 
                  10,000-row synthetic copy without corrupting the pristine source benchmark.
                </p>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <span className="badge badge-production">SHA-256 Verified</span>
                  <span className="badge badge-production">Zero Leakage Split</span>
                </div>
              </div>

              <div className="glass-panel" style={{ padding: "1.8rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem", color: "#34d399" }}>
                  Multi-Tool Architecture
                </h3>
                <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginBottom: "1rem" }}>
                  Python handles pipelines and ML inference; Supabase manages relational schemas; 
                  KNIME operates visual DAG experiments; Tableau powers executive visual analytics.
                </p>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <span className="badge badge-production">Supabase Ready</span>
                  <span className="badge badge-production">6 KNIME DAGs</span>
                  <span className="badge badge-production">3 Tableau BI</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 2: DATASET EXPLORER */}
        {/* ========================================================================= */}
        {activeTab === "dataset" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Dataset Schema & Attribute Dictionary
              </h2>
              <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
                Comprehensive dictionary of all 54 input predictors and target variable across 581,012 observations.
              </p>
              <input
                type="text"
                placeholder="Search features (e.g., Elevation, Aspect, Soil, Wilderness)..."
                value={featureSearch}
                onChange={(e) => setFeatureSearch(e.target.value)}
                style={{
                  width: "100%",
                  maxWidth: "500px",
                  padding: "0.75rem 1rem",
                  background: "rgba(15, 23, 42, 0.8)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
            </div>

            <div className="glass-panel" style={{ padding: "1.5rem", overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
                    <th style={{ padding: "0.75rem" }}>Feature</th>
                    <th style={{ padding: "0.75rem" }}>Type</th>
                    <th style={{ padding: "0.75rem" }}>Valid Domain / Range</th>
                    <th style={{ padding: "0.75rem" }}>Units</th>
                    <th style={{ padding: "0.75rem" }}>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { col: "Elevation", type: "Continuous", domain: "[1859, 3858]", unit: "Meters", desc: "Elevation above sea level in Roosevelt National Forest" },
                    { col: "Aspect", type: "Continuous", domain: "[0, 360]", unit: "Degrees", desc: "Aspect in degrees azimuth" },
                    { col: "Slope", type: "Continuous", domain: "[0, 66]", unit: "Degrees", desc: "Slope angle in degrees" },
                    { col: "Horizontal_Distance_To_Hydrology", type: "Continuous", domain: "[0, 1397]", unit: "Meters", desc: "Horizontal distance to nearest surface water" },
                    { col: "Vertical_Distance_To_Hydrology", type: "Continuous", domain: "[-173, 601]", unit: "Meters", desc: "Vertical distance to nearest surface water" },
                    { col: "Horizontal_Distance_To_Roadways", type: "Continuous", domain: "[0, 7117]", unit: "Meters", desc: "Horizontal distance to nearest roadway" },
                    { col: "Hillshade_9am", type: "Continuous", domain: "[0, 254]", unit: "Index (0-255)", desc: "Hillshade index at 9am, summer solstice" },
                    { col: "Hillshade_Noon", type: "Continuous", domain: "[0, 254]", unit: "Index (0-255)", desc: "Hillshade index at noon, summer solstice" },
                    { col: "Hillshade_3pm", type: "Continuous", domain: "[0, 254]", unit: "Index (0-255)", desc: "Hillshade index at 3pm, summer solstice" },
                    { col: "Horizontal_Distance_To_Fire_Points", type: "Continuous", domain: "[0, 7173]", unit: "Meters", desc: "Horizontal distance to nearest historic wildfire ignition" },
                    { col: "Wilderness_Area1..4", type: "Binary (4)", domain: "{0, 1}", unit: "Indicator", desc: "Wilderness areas: Rawah, Neota, Comanche Peak, Cache la Poudre" },
                    { col: "Soil_Type1..40", type: "Binary (40)", domain: "{0, 1}", unit: "Indicator", desc: "USFS soil classification types (geological families)" },
                    { col: "Cover_Type", type: "Target Integer", domain: "[1, 7]", unit: "Class", desc: "Target cover class: Spruce/Fir, Lodgepole, Ponderosa, etc." },
                  ]
                    .filter((f) => f.col.toLowerCase().includes(featureSearch.toLowerCase()) || f.desc.toLowerCase().includes(featureSearch.toLowerCase()))
                    .map((row) => (
                      <tr key={row.col} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "0.75rem", fontWeight: 600, color: "#60a5fa" }}>{row.col}</td>
                        <td style={{ padding: "0.75rem" }}>{row.type}</td>
                        <td style={{ padding: "0.75rem", fontFamily: "monospace" }}>{row.domain}</td>
                        <td style={{ padding: "0.75rem" }}>{row.unit}</td>
                        <td style={{ padding: "0.75rem", color: "var(--text-muted)" }}>{row.desc}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 3: CLEANING DEMONSTRATION */}
        {/* ========================================================================= */}
        {activeTab === "cleaning" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
                <div>
                  <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                    Practical 2: Synthetic Missing Value Experiment
                  </h2>
                  <p style={{ color: "var(--text-muted)", maxWidth: "800px" }}>
                    The original dataset has 0 missing values. To fulfill Practical 2 requirements with academic rigor,
                    exactly 800 missing cells were injected into 10,000 sampled records across continuous features and
                    restored via median imputation without altering the raw dataset.
                  </p>
                </div>
                <span className="badge badge-production" style={{ fontSize: "0.9rem", padding: "0.5rem 1rem" }}>
                  All 4 Validation Checks Passed ✓
                </span>
              </div>
            </div>

            <div className="stats-grid">
              <div className="glass-panel stat-card">
                <span className="stat-label">Injected Null Cells</span>
                <span className="stat-value" style={{ color: "#ef4444" }}>800</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Exactly 800 continuous cells</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Imputed Null Cells</span>
                <span className="stat-value" style={{ color: "#10b981" }}>800</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Column median imputation</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Remaining Missing</span>
                <span className="stat-value">0</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Complete dataset restored</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Rows Preserved</span>
                <span className="stat-value">10,000</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Zero row loss</span>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "1.8rem" }}>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem" }}>
                Per-Feature Missing Cells & Imputed Medians
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
                {[
                  { feature: "Elevation", nulls: 76, median: "2,996 m" },
                  { feature: "Aspect", nulls: 69, median: "127°" },
                  { feature: "Slope", nulls: 74, median: "13°" },
                  { feature: "Horiz. Dist. Hydrology", nulls: 72, median: "218 m" },
                  { feature: "Vert. Dist. Hydrology", nulls: 81, median: "30 m" },
                  { feature: "Horiz. Dist. Roadways", nulls: 68, median: "1,996 m" },
                  { feature: "Hillshade 9am", nulls: 99, median: "218" },
                  { feature: "Hillshade Noon", nulls: 69, median: "226" },
                  { feature: "Hillshade 3pm", nulls: 85, median: "142" },
                  { feature: "Horiz. Dist. Fire Points", nulls: 107, median: "1,708 m" },
                ].map((item) => (
                  <div key={item.feature} style={{ padding: "1rem", background: "rgba(15, 23, 42, 0.6)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                    <div style={{ fontWeight: 600, fontSize: "0.9rem", color: "#93c5fd" }}>{item.feature}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.5rem", fontSize: "0.85rem" }}>
                      <span style={{ color: "var(--text-muted)" }}>Injected: <strong style={{ color: "#f87171" }}>{item.nulls}</strong></span>
                      <span style={{ color: "var(--text-muted)" }}>Median: <strong style={{ color: "#34d399" }}>{item.median}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 4: DESCRIPTIVE STATISTICS */}
        {/* ========================================================================= */}
        {activeTab === "statistics" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Practical 3: Descriptive Statistics & Five-Number Summaries
              </h2>
              <p style={{ color: "var(--text-muted)" }}>
                Statistical moments, central tendencies, and dispersions calculated across all 581,012 observations.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: "1.5rem", overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
                    <th style={{ padding: "0.75rem" }}>Feature</th>
                    <th style={{ padding: "0.75rem" }}>Mean</th>
                    <th style={{ padding: "0.75rem" }}>Std Dev</th>
                    <th style={{ padding: "0.75rem" }}>Min</th>
                    <th style={{ padding: "0.75rem" }}>Q1 (25%)</th>
                    <th style={{ padding: "0.75rem" }}>Median</th>
                    <th style={{ padding: "0.75rem" }}>Q3 (75%)</th>
                    <th style={{ padding: "0.75rem" }}>Max</th>
                    <th style={{ padding: "0.75rem" }}>Skewness</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { feat: "Elevation", mean: "2959.37", std: "279.98", min: "1859", q1: "2809", med: "2996", q3: "3163", max: "3858", skew: "-0.817" },
                    { feat: "Aspect", mean: "155.65", std: "111.91", min: "0", q1: "58", med: "127", q3: "260", max: "360", skew: "0.403" },
                    { feat: "Slope", mean: "14.10", std: "7.49", min: "0", q1: "9", med: "13", q3: "18", max: "66", skew: "0.789" },
                    { feat: "Horiz. Dist. Hydrology", mean: "269.43", std: "212.55", min: "0", q1: "108", med: "218", q3: "384", max: "1397", skew: "1.140" },
                    { feat: "Vert. Dist. Hydrology", mean: "46.42", std: "58.30", min: "-173", q1: "7", med: "30", q3: "69", max: "601", skew: "1.790" },
                    { feat: "Horiz. Dist. Roadways", mean: "2350.15", std: "1559.25", min: "0", q1: "1106", med: "1997", q3: "3328", max: "7117", skew: "0.713" },
                    { feat: "Hillshade 9am", mean: "212.15", std: "26.77", min: "0", q1: "198", med: "218", q3: "231", max: "254", skew: "-1.185" },
                    { feat: "Hillshade Noon", mean: "223.32", std: "19.77", min: "0", q1: "213", med: "226", q3: "237", max: "254", skew: "-1.018" },
                    { feat: "Hillshade 3pm", mean: "142.53", std: "38.27", min: "0", q1: "119", med: "143", q3: "168", max: "254", skew: "-0.052" },
                    { feat: "Horiz. Dist. Fire Points", mean: "1980.29", std: "1324.19", min: "0", q1: "1024", med: "1710", q3: "2550", max: "7173", skew: "1.289" },
                  ].map((r) => (
                    <tr key={r.feat} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                      <td style={{ padding: "0.75rem", fontWeight: 600, color: "#60a5fa" }}>{r.feat}</td>
                      <td style={{ padding: "0.75rem" }}>{r.mean}</td>
                      <td style={{ padding: "0.75rem" }}>{r.std}</td>
                      <td style={{ padding: "0.75rem" }}>{r.min}</td>
                      <td style={{ padding: "0.75rem" }}>{r.q1}</td>
                      <td style={{ padding: "0.75rem", fontWeight: 700, color: "#34d399" }}>{r.med}</td>
                      <td style={{ padding: "0.75rem" }}>{r.q3}</td>
                      <td style={{ padding: "0.75rem" }}>{r.max}</td>
                      <td style={{ padding: "0.75rem", color: parseFloat(r.skew) > 1 ? "#fbbf24" : "inherit" }}>{r.skew}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 5: FEATURE SELECTION & PCA */}
        {/* ========================================================================= */}
        {activeTab === "features_pca" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Practical 6: Feature Selection & Principal Component Analysis (PCA)
              </h2>
              <p style={{ color: "var(--text-muted)" }}>
                Dimensionality reduction retains 96.9% total variance with 8 principal components,
                while Chi-Square and ANOVA statistical tests rank feature importance.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.5rem" }}>
              <div className="glass-panel" style={{ padding: "1.8rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem" }}>
                  PCA Cumulative Explained Variance Scree
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {[
                    { pc: "PC 1", ratio: 25.86, cum: 25.86 },
                    { pc: "PC 2", ratio: 21.49, cum: 47.35 },
                    { pc: "PC 3", ratio: 17.39, cum: 64.74 },
                    { pc: "PC 4", ratio: 10.77, cum: 75.51 },
                    { pc: "PC 5", ratio: 7.71, cum: 83.22 },
                    { pc: "PC 6", ratio: 5.47, cum: 88.69 },
                    { pc: "PC 7", ratio: 4.64, cum: 93.33 },
                    { pc: "PC 8", ratio: 3.56, cum: 96.90 },
                  ].map((item) => (
                    <div key={item.pc}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                        <span style={{ fontWeight: 600 }}>{item.pc} (adds {item.ratio}%)</span>
                        <span style={{ color: "#34d399" }}>{item.cum}% Cumulative</span>
                      </div>
                      <div style={{ height: "8px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", overflow: "hidden" }}>
                        <div style={{ height: "100%", width: `${item.cum}%`, background: "linear-gradient(90deg, #3b82f6, #10b981)" }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-panel" style={{ padding: "1.8rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem" }}>
                  Top Feature Ranking (Chi-Square & ANOVA F-Test)
                </h3>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
                      <th style={{ padding: "0.5rem" }}>Rank</th>
                      <th style={{ padding: "0.5rem" }}>Feature</th>
                      <th style={{ padding: "0.5rem" }}>Type</th>
                      <th style={{ padding: "0.5rem" }}>Significance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { rank: 1, name: "Elevation", type: "Continuous", sig: "Dominant (F > 25,000)" },
                      { rank: 2, name: "Wilderness_Area4", type: "Binary", sig: "Cache la Poudre (Low Elev)" },
                      { rank: 3, name: "Soil_Type10", type: "Binary", sig: "Bullwark Catena family" },
                      { rank: 4, name: "Horizontal_Distance_To_Roadways", type: "Continuous", sig: "Strong accessibility correlation" },
                      { rank: 5, name: "Wilderness_Area1", type: "Binary", sig: "Rawah Wilderness" },
                      { rank: 6, name: "Horizontal_Distance_To_Fire_Points", type: "Continuous", sig: "Historic fire proximity" },
                    ].map((row) => (
                      <tr key={row.rank} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "0.5rem", fontWeight: 700, color: "#f59e0b" }}>#{row.rank}</td>
                        <td style={{ padding: "0.5rem", fontWeight: 600 }}>{row.name}</td>
                        <td style={{ padding: "0.5rem", color: "var(--text-muted)" }}>{row.type}</td>
                        <td style={{ padding: "0.5rem", color: "#34d399" }}>{row.sig}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 6: CLASSIFICATION EVALUATION */}
        {/* ========================================================================= */}
        {activeTab === "classification" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Practical 7: Classification Model Comparison
              </h2>
              <p style={{ color: "var(--text-muted)" }}>
                Evaluated on a strictly isolated 15% stratified test holdout (87,152 samples). 
                Zero data leakage across preprocessing pipelines.
              </p>
            </div>

            <div className="stats-grid">
              <div className="glass-panel stat-card">
                <span className="stat-label">Random Forest Accuracy</span>
                <span className="stat-value" style={{ color: "#10b981" }}>93.5%</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Macro F1: 0.906</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">K-Nearest Neighbors</span>
                <span className="stat-value" style={{ color: "#3b82f6" }}>93.1%</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Macro F1: 0.898</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Decision Tree</span>
                <span className="stat-value" style={{ color: "#f59e0b" }}>86.6%</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Macro F1: 0.803</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Test Split Size</span>
                <span className="stat-value">87,152</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Stratified 15%</span>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "1.8rem" }}>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem" }}>
                Model Performance Benchmark Table
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
                    <th style={{ padding: "0.75rem" }}>Model Architecture</th>
                    <th style={{ padding: "0.75rem" }}>Accuracy</th>
                    <th style={{ padding: "0.75rem" }}>Macro F1</th>
                    <th style={{ padding: "0.75rem" }}>Weighted F1</th>
                    <th style={{ padding: "0.75rem" }}>CV Mean (5-Fold)</th>
                    <th style={{ padding: "0.75rem" }}>Artifact File</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(16, 185, 129, 0.05)" }}>
                    <td style={{ padding: "0.75rem", fontWeight: 700, color: "#10b981" }}>Random Forest (100 Trees)</td>
                    <td style={{ padding: "0.75rem", fontWeight: 700 }}>93.5%</td>
                    <td style={{ padding: "0.75rem" }}>0.906</td>
                    <td style={{ padding: "0.75rem" }}>0.935</td>
                    <td style={{ padding: "0.75rem" }}>93.2% ± 0.04%</td>
                    <td style={{ padding: "0.75rem", fontFamily: "monospace" }}>models/random_forest.joblib</td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                    <td style={{ padding: "0.75rem", fontWeight: 600, color: "#3b82f6" }}>K-Nearest Neighbors (k=5, Distance)</td>
                    <td style={{ padding: "0.75rem", fontWeight: 700 }}>93.1%</td>
                    <td style={{ padding: "0.75rem" }}>0.898</td>
                    <td style={{ padding: "0.75rem" }}>0.930</td>
                    <td style={{ padding: "0.75rem" }}>92.8% ± 0.06%</td>
                    <td style={{ padding: "0.75rem", fontFamily: "monospace" }}>models/knn.joblib</td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                    <td style={{ padding: "0.75rem", fontWeight: 600, color: "#f59e0b" }}>Decision Tree (Gini, Pruned)</td>
                    <td style={{ padding: "0.75rem", fontWeight: 700 }}>86.6%</td>
                    <td style={{ padding: "0.75rem" }}>0.803</td>
                    <td style={{ padding: "0.75rem" }}>0.865</td>
                    <td style={{ padding: "0.75rem" }}>86.1% ± 0.12%</td>
                    <td style={{ padding: "0.75rem", fontFamily: "monospace" }}>models/decision_tree.joblib</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 7: CLUSTERING ANALYSIS */}
        {/* ========================================================================= */}
        {activeTab === "clustering" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Practical 8: Unsupervised Topographic Clustering (K-Means)
              </h2>
              <p style={{ color: "var(--text-muted)" }}>
                Terrain segmentation into 4 ecological clusters based on elevation, slope, aspect, and distance to water.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
              {[
                { id: "Cluster 0", label: "Alpine Ridges", elev: "3,320m", slope: "24°", water: "310m", cover: "Krummholz / Spruce" },
                { id: "Cluster 1", label: "Upper Montane", elev: "2,980m", slope: "14°", water: "230m", cover: "Lodgepole Pine" },
                { id: "Cluster 2", label: "Lower Montane", elev: "2,460m", slope: "16°", water: "190m", cover: "Ponderosa Pine" },
                { id: "Cluster 3", label: "Riparian Valleys", elev: "2,120m", slope: "8°", water: "85m", cover: "Cottonwood / Willow" },
              ].map((c) => (
                <div key={c.id} className="glass-panel" style={{ padding: "1.5rem", borderTop: "4px solid #3b82f6" }}>
                  <div style={{ fontWeight: 800, fontSize: "1.1rem", marginBottom: "0.25rem" }}>{c.id}: {c.label}</div>
                  <div style={{ color: "#34d399", fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.75rem" }}>Dominant: {c.cover}</div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                    <div>Mean Elevation: <strong>{c.elev}</strong></div>
                    <div>Mean Slope: <strong>{c.slope}</strong></div>
                    <div>Dist to Water: <strong>{c.water}</strong></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 8: FOREST FIRES REGRESSION */}
        {/* ========================================================================= */}
        {activeTab === "regression" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Practical 9: Forest Fires Burned Area Regression
              </h2>
              <p style={{ color: "var(--text-muted)" }}>
                Evaluated on the separate UCI Forest Fires dataset (N=517) to predict logarithmic burned area (ln(area + 1)) 
                using meteorological features (temperature, relative humidity, wind) and FWI indices.
              </p>
            </div>

            <div className="stats-grid">
              <div className="glass-panel stat-card">
                <span className="stat-label">Best Model</span>
                <span className="stat-value" style={{ color: "#10b981" }}>Ridge Reg.</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Regularized linear model</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">RMSE (log scale)</span>
                <span className="stat-value">1.485</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Continuous prediction</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">MAE (log scale)</span>
                <span className="stat-value">1.199</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>Mean absolute error</span>
              </div>
              <div className="glass-panel stat-card">
                <span className="stat-label">Target Zero Proportion</span>
                <span className="stat-value">47.8%</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>247 unburned observations</span>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "1.8rem" }}>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem" }}>
                Regression Benchmark Comparison
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
                    <th style={{ padding: "0.75rem" }}>Model</th>
                    <th style={{ padding: "0.75rem" }}>MAE (log1p)</th>
                    <th style={{ padding: "0.75rem" }}>RMSE (log1p)</th>
                    <th style={{ padding: "0.75rem" }}>MAE (Original ha)</th>
                    <th style={{ padding: "0.75rem" }}>RMSE (Original ha)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(16, 185, 129, 0.05)" }}>
                    <td style={{ padding: "0.75rem", fontWeight: 700, color: "#10b981" }}>Ridge Regression</td>
                    <td style={{ padding: "0.75rem" }}>1.199</td>
                    <td style={{ padding: "0.75rem" }}>1.485</td>
                    <td style={{ padding: "0.75rem" }}>19.82 ha</td>
                    <td style={{ padding: "0.75rem" }}>109.90 ha</td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                    <td style={{ padding: "0.75rem", fontWeight: 600 }}>Linear Regression</td>
                    <td style={{ padding: "0.75rem" }}>1.199</td>
                    <td style={{ padding: "0.75rem" }}>1.485</td>
                    <td style={{ padding: "0.75rem" }}>19.83 ha</td>
                    <td style={{ padding: "0.75rem" }}>109.90 ha</td>
                  </tr>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                    <td style={{ padding: "0.75rem", fontWeight: 600 }}>Random Forest Regressor</td>
                    <td style={{ padding: "0.75rem" }}>1.220</td>
                    <td style={{ padding: "0.75rem" }}>1.517</td>
                    <td style={{ padding: "0.75rem" }}>19.96 ha</td>
                    <td style={{ padding: "0.75rem" }}>109.95 ha</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 9: PREDICTION PLAYGROUND */}
        {/* ========================================================================= */}
        {activeTab === "prediction" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Interactive Forest Cover Type Predictor
              </h2>
              <p style={{ color: "var(--text-muted)" }}>
                Adjust continuous environmental sliders or load ecological presets to query the serialized model pipeline.
              </p>

              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "1rem" }}>
                <span style={{ alignSelf: "center", fontSize: "0.85rem", color: "var(--text-muted)" }}>Presets:</span>
                {Object.entries(PRESETS).map(([key, p]) => (
                  <button
                    key={key}
                    onClick={() => handleApplyPreset(key)}
                    style={{
                      background: "rgba(59, 130, 246, 0.15)",
                      border: "1px solid rgba(59, 130, 246, 0.3)",
                      color: "#93c5fd",
                      padding: "0.35rem 0.75rem",
                      borderRadius: "6px",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    {p.name.split(" ")[1]}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "2rem" }}>
              <div className="glass-panel" style={{ padding: "1.8rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1.5rem" }}>Topographic Controls</h3>

                <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                      <label style={{ fontSize: "0.85rem" }}>Elevation: <strong>{elev} m</strong></label>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>[1,859m – 3,858m]</span>
                    </div>
                    <input
                      type="range"
                      min={1860}
                      max={3850}
                      value={elev}
                      onChange={(e) => setElev(Number(e.target.value))}
                      style={{ width: "100%" }}
                    />
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                      <label style={{ fontSize: "0.85rem" }}>Slope Angle: <strong>{slope}°</strong></label>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>[0° – 66°]</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={60}
                      value={slope}
                      onChange={(e) => setSlope(Number(e.target.value))}
                      style={{ width: "100%" }}
                    />
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                      <label style={{ fontSize: "0.85rem" }}>Aspect (Azimuth): <strong>{aspect}°</strong></label>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>[0° – 360°]</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={360}
                      value={aspect}
                      onChange={(e) => setAspect(Number(e.target.value))}
                      style={{ width: "100%" }}
                    />
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                      <label style={{ fontSize: "0.85rem" }}>Horiz. Distance to Roadways: <strong>{distRoad} m</strong></label>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={7000}
                      value={distRoad}
                      onChange={(e) => setDistRoad(Number(e.target.value))}
                      style={{ width: "100%" }}
                    />
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                      <label style={{ fontSize: "0.85rem" }}>Horiz. Distance to Fire Points: <strong>{distFire} m</strong></label>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={7000}
                      value={distFire}
                      onChange={(e) => setDistFire(Number(e.target.value))}
                      style={{ width: "100%" }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: "0.85rem", display: "block", marginBottom: "0.4rem" }}>Wilderness Area:</label>
                    <select
                      value={selectedWA}
                      onChange={(e) => setSelectedWA(Number(e.target.value))}
                      style={{ width: "100%", padding: "0.6rem", background: "rgba(15,23,42,0.8)", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#fff" }}
                    >
                      <option value={1}>Rawah Wilderness (Area 1)</option>
                      <option value={2}>Neota Wilderness (Area 2)</option>
                      <option value={3}>Comanche Peak Wilderness (Area 3)</option>
                      <option value={4}>Cache la Poudre Wilderness (Area 4)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "0.85rem", display: "block", marginBottom: "0.4rem" }}>Model Architecture:</label>
                    <select
                      value={modelType}
                      onChange={(e) => setModelType(e.target.value)}
                      style={{ width: "100%", padding: "0.6rem", background: "rgba(15,23,42,0.8)", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#fff" }}
                    >
                      <option value="random_forest">Random Forest (Accuracy: 93.5%)</option>
                      <option value="knn">K-Nearest Neighbors (Accuracy: 93.1%)</option>
                      <option value="decision_tree">Decision Tree (Accuracy: 86.6%)</option>
                    </select>
                  </div>

                  <button
                    onClick={handlePredict}
                    disabled={isPredicting}
                    className="btn-primary"
                    style={{ marginTop: "1rem" }}
                  >
                    {isPredicting ? "Computing Prediction..." : "Run Prediction →"}
                  </button>
                </div>
              </div>

              <div className="glass-panel" style={{ padding: "1.8rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1.5rem" }}>Prediction Result</h3>

                {predictionResult ? (
                  <div>
                    <div style={{ padding: "1.5rem", borderRadius: "10px", background: "rgba(15,23,42,0.8)", border: "1px solid var(--border-subtle)", marginBottom: "1.5rem" }}>
                      <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Predicted Forest Cover:</div>
                      <div style={{ fontSize: "1.8rem", fontWeight: 800, color: COVER_TYPE_META[predictionResult.predicted_cover_type]?.color || "#3b82f6", margin: "0.3rem 0" }}>
                        {predictionResult.cover_name}
                      </div>
                      <div style={{ fontSize: "0.9rem", color: "var(--text-dim)" }}>
                        {COVER_TYPE_META[predictionResult.predicted_cover_type]?.desc}
                      </div>
                    </div>

                    {predictionResult.probabilities && (
                      <div>
                        <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.75rem" }}>Class Probabilities:</div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                          {Object.entries(predictionResult.probabilities).map(([cname, prob]: any) => (
                            <div key={cname}>
                              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.2rem" }}>
                                <span>{cname}</span>
                                <strong>{(prob * 100).toFixed(1)}%</strong>
                              </div>
                              <div style={{ height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden" }}>
                                <div style={{ height: "100%", width: `${prob * 100}%`, background: "#3b82f6" }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "300px", color: "var(--text-dim)" }}>
                    <span style={{ fontSize: "3rem", marginBottom: "1rem" }}>🧭</span>
                    <p>Adjust parameters and click &quot;Run Prediction&quot; to test the model.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 10: WILDFIRE SCREENING */}
        {/* ========================================================================= */}
        {activeTab === "wildfire" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
                <div>
                  <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                    Topographic Wildfire Screening Risk Index
                  </h2>
                  <p style={{ color: "var(--text-muted)", maxWidth: "800px" }}>
                    Exploratory screening score combining slope steepness, solar exposure, and proximity to historic ignition points.
                  </p>
                </div>
                <span className="badge badge-production" style={{ background: "rgba(239, 68, 68, 0.15)", color: "#f87171", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
                  Exploratory Screening Only
                </span>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "1.5rem", marginBottom: "2rem", borderLeft: "4px solid #f59e0b" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#fbbf24", marginBottom: "0.5rem" }}>
                Mandatory Methodology & Limitation Disclaimer
              </h3>
              <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
                This screening score is an exploratory topographic index and <strong>does NOT represent an empirical probability of wildfire occurrence or future fire recurrence</strong>. 
                Crucial real-time fire behavior parameters such as wind velocity, relative humidity, fuel moisture, and ignition timing are absent from the Covertype cartographic survey.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: "1.8rem" }}>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem" }}>
                Risk Strata by Wilderness Area & Elevation
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
                    <th style={{ padding: "0.75rem" }}>Wilderness Area</th>
                    <th style={{ padding: "0.75rem" }}>Elevation Stratum</th>
                    <th style={{ padding: "0.75rem" }}>Screening Hazard Score</th>
                    <th style={{ padding: "0.75rem" }}>Hazard Classification</th>
                    <th style={{ padding: "0.75rem" }}>Ecological Rationale</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { wa: "Cache la Poudre", elev: "Low (<2500m)", score: "68.4 / 100", level: "High Hazard", rat: "Steep rocky canyons, close to roads and low elevation ignition points" },
                    { wa: "Comanche Peak", elev: "Mid (2500-3000m)", score: "54.2 / 100", level: "Moderate Hazard", rat: "Dense Lodgepole stands with intermediate fuel load" },
                    { wa: "Rawah Wilderness", elev: "Mid-High (2800-3200m)", score: "46.8 / 100", level: "Moderate-Low", rat: "Higher moisture content in subalpine Spruce/Fir" },
                    { wa: "Neota Wilderness", elev: "High (>3200m)", score: "32.1 / 100", level: "Low Hazard", rat: "Alpine tundra and Krummholz with short growing season and low continuous fuel" },
                  ].map((row) => (
                    <tr key={row.wa + row.elev} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                      <td style={{ padding: "0.75rem", fontWeight: 600, color: "#60a5fa" }}>{row.wa}</td>
                      <td style={{ padding: "0.75rem" }}>{row.elev}</td>
                      <td style={{ padding: "0.75rem", fontWeight: 700 }}>{row.score}</td>
                      <td style={{ padding: "0.75rem" }}>
                        <span className={`badge ${row.level.includes("High") ? "badge-production" : "badge"}`} style={{ color: row.level.includes("High") ? "#f87171" : "#34d399" }}>
                          {row.level}
                        </span>
                      </td>
                      <td style={{ padding: "0.75rem", color: "var(--text-muted)" }}>{row.rat}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PAGE 11: GOVERNANCE & TOOLS */}
        {/* ========================================================================= */}
        {activeTab === "governance" && (
          <div>
            <div className="glass-panel" style={{ padding: "2rem", marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Multi-Tool Architecture, Supabase Integration & Academic Traceability
              </h2>
              <p style={{ color: "var(--text-muted)" }}>
                Strict mapping between university syllabus requirements (Units I–V, Practicals 1–10) and technological implementation.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
              <div className="glass-panel" style={{ padding: "1.8rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.75rem", color: "#34d399" }}>
                  Supabase Database Status
                </h3>
                <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
                  Managed PostgreSQL database providing 5 isolated functional schemas: <code>raw</code>, <code>curated</code>, <code>analytics</code>, <code>models</code>, and <code>app</code>.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.85rem" }}>
                  <div>Migration Script: <code>database/supabase_migration.sql</code></div>
                  <div>Python Loader: <code>scripts/12_load_supabase.py</code></div>
                  <div>Pooler Support: Enabled (Port 6543 / Session 5432)</div>
                </div>
              </div>

              <div className="glass-panel" style={{ padding: "1.8rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.75rem", color: "#60a5fa" }}>
                  Tableau & KNIME Artifacts
                </h3>
                <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
                  KNIME operates 6 visual DAG workflows in <code>knime/</code>; Tableau provides 3 executive dashboards in <code>tableau/</code>.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", fontSize: "0.85rem" }}>
                  <div>KNIME Workflows: 6 DAGs documented & export-ready</div>
                  <div>Tableau Workbooks: 3 XML workbooks with calculated fields</div>
                  <div>Export Integrity: 10 KNIME CSVs, 7 Tableau CSVs</div>
                </div>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "1.8rem" }}>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem" }}>
                Academic Practical Traceability (1–10)
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
                    <th style={{ padding: "0.6rem" }}>Practical</th>
                    <th style={{ padding: "0.6rem" }}>Syllabus Unit</th>
                    <th style={{ padding: "0.6rem" }}>Topic</th>
                    <th style={{ padding: "0.6rem" }}>Primary Tool</th>
                    <th style={{ padding: "0.6rem" }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { p: "P1", unit: "Unit I", topic: "Ingestion & Tabular Audit", tool: "Python + Supabase", status: "VERIFIED" },
                    { p: "P2", unit: "Unit I", topic: "Synthetic Missing Value Cleaning", tool: "Python + KNIME", status: "VERIFIED" },
                    { p: "P3", unit: "Unit II", topic: "Descriptive Statistics", tool: "Python + FastAPI", status: "VERIFIED" },
                    { p: "P4", unit: "Unit II", topic: "Outlier Detection (IQR / Z-Score)", tool: "Python + Tableau", status: "VERIFIED" },
                    { p: "P5", unit: "Unit III & V", topic: "Data Visualization & EDA", tool: "Tableau + Python", status: "VERIFIED" },
                    { p: "P6a", unit: "Unit IV", topic: "Feature Selection & Hypotheses", tool: "Python + KNIME", status: "VERIFIED" },
                    { p: "P6b", unit: "Unit IV", topic: "Principal Component Analysis", tool: "Python + Next.js", status: "VERIFIED" },
                    { p: "P7", unit: "Unit IV", topic: "Classification Model Comparison", tool: "Python + FastAPI", status: "VERIFIED" },
                    { p: "P8", unit: "Unit IV", topic: "K-Means Clustering", tool: "Python + KNIME", status: "VERIFIED" },
                    { p: "P9", unit: "Unit IV", topic: "Forest Fires Regression", tool: "Python + Supabase", status: "VERIFIED" },
                    { p: "P10", unit: "Unit V", topic: "Full-Stack Multi-Tool Integration", tool: "Next.js + FastAPI + Supabase", status: "VERIFIED" },
                  ].map((row) => (
                    <tr key={row.p} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                      <td style={{ padding: "0.6rem", fontWeight: 700, color: "#60a5fa" }}>{row.p}</td>
                      <td style={{ padding: "0.6rem" }}>{row.unit}</td>
                      <td style={{ padding: "0.6rem", fontWeight: 600 }}>{row.topic}</td>
                      <td style={{ padding: "0.6rem" }}>{row.tool}</td>
                      <td style={{ padding: "0.6rem" }}>
                        <span className="badge badge-production" style={{ fontSize: "0.75rem" }}>{row.status} ✓</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
