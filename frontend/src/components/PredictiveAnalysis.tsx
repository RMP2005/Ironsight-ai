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
        <Blueprint />
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
        <Blueprint />
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
        <Blueprint />
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

  const percentage = result.failure_probability * 100;
  const displayPercent = formatFailureProbabilityPercent(result.failure_probability);
  const stateClass = riskClass[result.risk_level];
  const gaugeStyle = {
    "--risk-progress": `${Math.min(100, Math.max(0, percentage)) * 3.6}deg`,
  } as CSSProperties;

  return (
    <section
      className={`analysis-panel analysis-result ${stateClass} ${result.failure_alert ? "alert-triggered" : ""}`}
      aria-live="polite"
      aria-labelledby="analysis-result-heading"
    >
      <Blueprint />
      <div className="analysis-topline">
        <div>
          <p className="eyebrow">02 / Predictive analysis</p>
          <h2 id="analysis-result-heading" className="visually-hidden">
            Predictive analysis result
          </h2>
        </div>
        <span className="panel-code">Live result</span>
      </div>
      <div className="risk-layout">
        <div className="risk-gauge" style={gaugeStyle}>
          <div className="gauge-core">
            <span>Predicted failure risk</span>
            <strong>{displayPercent}</strong>
            <em className="risk-badge">{result.risk_level} risk</em>
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

function Blueprint() {
  return (
    <svg className="blueprint" viewBox="0 0 600 420" aria-hidden="true">
      <g fill="none" stroke="currentColor">
        <circle cx="390" cy="210" r="112" />
        <circle cx="390" cy="210" r="62" />
        <circle cx="390" cy="210" r="17" />
        <path d="M74 301h198l45-63h156M75 120h122l42 56h202M132 80v276M510 92v236M269 128v165" />
        <path d="M39 210h510M390 50v319M285 302l54-36 45 58M230 177l56-35" strokeDasharray="5 8" />
        <rect x="65" y="142" width="115" height="136" rx="8" />
        <path d="M84 162h75M84 258h75" />
      </g>
    </svg>
  );
}
