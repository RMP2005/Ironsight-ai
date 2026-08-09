"use client";

import type { CSSProperties } from "react";

import { formatFailureProbabilityPercent } from "@/lib/format";
import type { PredictionResponse } from "@/types/api";

type PredictiveAnalysisProps = {
  result: PredictionResponse | null;
  isAnalyzing: boolean;
  error: string | null;
  onRetry?: () => void;
};

const riskClass = {
  Low: "risk-low",
  Moderate: "risk-moderate",
  High: "risk-high",
} as const;

export function PredictiveAnalysis({
  result,
  isAnalyzing,
  error,
  onRetry,
}: PredictiveAnalysisProps) {
  if (isAnalyzing) {
    return (
      <section
        className="analysis-panel analysis-loading"
        aria-busy="true"
        aria-live="polite"
        aria-labelledby="analysis-loading-heading"
      >
        <InspectionSchematic active />
        <TelemetryTraces />
        <div className="analysis-state">
          <span className="loading-orbit" aria-hidden="true" />
          <p className="eyebrow">Analyzing machine</p>
          <h2 id="analysis-loading-heading">Processing sensor telemetry</h2>
          <p>Evaluating failure probability from the current readings.</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section
        className="analysis-panel analysis-error"
        role="alert"
        aria-labelledby="analysis-error-heading"
      >
        <InspectionSchematic />
        <div className="analysis-state">
          <p className="eyebrow">Analysis unavailable</p>
          <h2 id="analysis-error-heading">Unable to complete the machine analysis</h2>
          <p>{error}</p>
          {onRetry ? (
            <button type="button" className="retry-button" onClick={onRetry}>
              Retry analysis
            </button>
          ) : null}
        </div>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="analysis-panel analysis-idle" aria-labelledby="analysis-idle-heading">
        <InspectionSchematic />
        <TelemetryTraces muted />
        <div className="analysis-state">
          <p className="eyebrow">Ready for analysis</p>
          <h2 id="analysis-idle-heading">
            Enter the five machine sensor readings and analyze the machine.
          </h2>
          <p>Results appear here with predicted failure risk and maintenance guidance.</p>
        </div>
      </section>
    );
  }

  return <AnalysisResultView key={resultKey(result)} result={result} />;
}

function resultKey(result: PredictionResponse): string {
  return [
    result.failure_probability,
    result.risk_level,
    result.failure_alert,
    result.maintenance_recommendation,
    result.validation_warnings.join("|"),
  ].join(":");
}

function AnalysisResultView({ result }: { result: PredictionResponse }) {
  const percentage = result.failure_probability * 100;
  const displayPercent = formatFailureProbabilityPercent(result.failure_probability);
  const stateClass = riskClass[result.risk_level];
  const gaugeStyle = {
    "--risk-end": `${Math.min(100, Math.max(0, percentage)) * 3.6}deg`,
  } as CSSProperties;

  return (
    <section
      className={`analysis-panel analysis-result ${stateClass} ${result.failure_alert ? "alert-triggered" : ""}`}
      aria-live="polite"
      aria-labelledby="analysis-result-heading"
    >
      <InspectionSchematic active={result.risk_level === "High"} />
      <TelemetryTraces />
      <div className="analysis-topline">
        <div>
          <p className="eyebrow">02 / Predictive analysis</p>
          <h2 id="analysis-result-heading" className="visually-hidden">
            Predictive analysis result
          </h2>
        </div>
        <span className="panel-code">
          <span className="panel-code-dot" aria-hidden="true" />
          Live result
        </span>
      </div>
      <div className="panel-rule" aria-hidden="true" />
      <div className="risk-layout result-reveal">
        <div className="gauge-assembly">
          <div className="gauge-rings" aria-hidden="true">
            <span className="gauge-ring gauge-ring-outer" />
            <span className="gauge-ring gauge-ring-ticks" />
            <span className="gauge-ring gauge-ring-inner" />
            <span className="gauge-crosshair" />
          </div>
          <div className="risk-gauge gauge-animate" style={gaugeStyle}>
            <div className="gauge-core">
              <span>Predicted failure risk</span>
              <strong>{displayPercent}</strong>
              <em className="risk-badge">{result.risk_level} risk</em>
            </div>
          </div>
        </div>
        <div className="result-summary">
          <p
            className={`alert-status ${result.failure_alert ? "alert-active" : "alert-clear"}`}
            role="status"
          >
            <span aria-hidden="true">{result.failure_alert ? "◆" : "○"}</span>
            {result.failure_alert ? "Failure alert triggered" : "No failure alert triggered"}
          </p>
          <div className="recommendation">
            <p className="eyebrow">Maintenance recommendation</p>
            <p>{result.maintenance_recommendation}</p>
          </div>
          <p className="threshold-note">
            Decision threshold: {(result.threshold * 100).toFixed(1)}%
          </p>
        </div>
      </div>
      {result.validation_warnings.length > 0 ? (
        <div className="backend-warnings" role="status">
          <p className="eyebrow">Input outside reference range</p>
          {result.validation_warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function TelemetryTraces({ muted = false }: { muted?: boolean }) {
  return (
    <svg
      className={`telemetry-traces ${muted ? "telemetry-traces-muted" : ""}`}
      viewBox="0 0 640 420"
      aria-hidden="true"
      preserveAspectRatio="none"
    >
      <path className="trace-line trace-a" d="M20 310 C 80 290, 120 340, 180 300 S 280 250, 340 280 S 450 330, 520 270 S 600 220, 630 240" />
      <path className="trace-line trace-b" d="M10 180 C 70 160, 110 210, 170 170 S 270 120, 330 150 S 440 200, 510 140 S 590 90, 640 110" />
      <path className="trace-line trace-c" d="M0 360 C 90 350, 140 390, 220 355 S 340 310, 410 345 S 520 380, 640 330" />
    </svg>
  );
}

function InspectionSchematic({ active = false }: { active?: boolean }) {
  return (
    <div className={`inspection-schematic ${active ? "schematic-active" : ""}`} aria-hidden="true">
      <svg className="blueprint" viewBox="0 0 640 460" preserveAspectRatio="xMidYMid slice">
        <defs>
          <pattern id="schematic-hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="8" stroke="currentColor" strokeWidth="0.6" opacity="0.35" />
          </pattern>
        </defs>

        <g className="schematic-static" fill="none" stroke="currentColor" strokeWidth="1">
          <rect x="48" y="72" width="150" height="170" />
          <path d="M68 96h110M68 210h110M48 157h150" />
          <rect x="68" y="112" width="48" height="28" fill="url(#schematic-hatch)" stroke="currentColor" />
          <path d="M198 157h90l38-52h120" />
          <path d="M198 210h78l42 58h148" />
          <path d="M120 72v-28h84M120 242v36h110" strokeDasharray="4 6" />
          <path d="M36 157h12M198 157h12M430 105v-18M430 315v18" />
          <text x="56" y="64" className="schematic-label">
            BAY-A
          </text>
          <text x="250" y="88" className="schematic-label">
            AXIS X
          </text>
          <text x="520" y="58" className="schematic-label">
            INSPECT
          </text>
        </g>

        <g className="schematic-reticle" fill="none" stroke="currentColor" strokeWidth="1.1">
          <circle cx="430" cy="210" r="128" className="reticle-ring reticle-outer" />
          <circle cx="430" cy="210" r="96" className="reticle-ring reticle-mid" />
          <circle cx="430" cy="210" r="58" className="reticle-ring reticle-inner" />
          <circle cx="430" cy="210" r="14" />
          <path d="M430 70v28M430 322v28M302 210h28M530 210h28" />
          <path d="M358 138l18 18M484 138l-18 18M358 282l18-18M484 282l-18-18" />
          <path
            className="reticle-ticks"
            d="M430 82l0 10M492 110l-7 7M518 172l-10 0M492 310l-7-7M430 338l0-10M368 310l7-7M342 172l10 0M368 110l7 7"
          />
          <g className="reticle-rotator">
            <path d="M430 82 A128 128 0 0 1 542 210" strokeDasharray="18 220" />
            <circle cx="542" cy="210" r="2.5" fill="currentColor" stroke="none" />
          </g>
        </g>

        <g className="schematic-readouts" fill="currentColor" stroke="none">
          <circle className="telemetry-bead bead-a" cx="286" cy="126" r="2.2" />
          <circle className="telemetry-bead bead-b" cx="348" cy="286" r="2.2" />
          <circle className="telemetry-bead bead-c" cx="512" cy="98" r="2.2" />
        </g>
      </svg>
      <div className="schematic-scanline" />
    </div>
  );
}
