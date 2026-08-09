"use client";

import { useCallback, useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { PredictiveAnalysis } from "@/components/PredictiveAnalysis";
import { SensorForm } from "@/components/SensorForm";
import { getErrorMessage, getModelInfo, predictMachine } from "@/lib/api";
import type { ModelInfo, PredictionRequest, PredictionResponse } from "@/types/api";

export default function Home() {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(true);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [lastRequest, setLastRequest] = useState<PredictionRequest | null>(null);

  const applyModelInfo = useCallback((info: ModelInfo) => {
    setModelInfo(info);
    setConnectionError(
      info.is_loaded
        ? null
        : "The analysis service is reachable, but the model is not loaded.",
    );
  }, []);

  const failConnection = useCallback((error: unknown) => {
    setModelInfo(null);
    setConnectionError(
      getErrorMessage(
        error,
        "Unable to connect to the IronSight analysis service. Confirm the FastAPI backend is running on the configured URL.",
      ),
    );
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function connect() {
      try {
        const info = await getModelInfo();
        if (cancelled) {
          return;
        }
        applyModelInfo(info);
      } catch (error) {
        if (cancelled) {
          return;
        }
        failConnection(error);
      } finally {
        if (!cancelled) {
          setIsLoadingMetadata(false);
        }
      }
    }

    void connect();

    return () => {
      cancelled = true;
    };
  }, [applyModelInfo, failConnection]);

  async function loadModelInfo() {
    setIsLoadingMetadata(true);
    setConnectionError(null);
    try {
      applyModelInfo(await getModelInfo());
    } catch (error) {
      failConnection(error);
    } finally {
      setIsLoadingMetadata(false);
    }
  }

  async function handleAnalyze(request: PredictionRequest) {
    setLastRequest(request);
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      setResult(await predictMachine(request));
    } catch (error) {
      setAnalysisError(
        getErrorMessage(
          error,
          "Unable to complete the machine analysis. Please verify that the analysis service is running and try again.",
        ),
      );
    } finally {
      setIsAnalyzing(false);
    }
  }

  function handleRetryAnalysis() {
    if (lastRequest) {
      void handleAnalyze(lastRequest);
    }
  }

  const backendAvailable = modelInfo?.is_loaded === true;

  return (
    <main className="app-shell">
      <div className="atmosphere" aria-hidden="true">
        <div className="grid-overlay" />
        <div className="grid-overlay grid-overlay-fine" />
        <div className="telemetry-scan" />
        <div className="telemetry-rail telemetry-rail-left" />
        <div className="telemetry-rail telemetry-rail-right" />
      </div>
      <AppHeader isOnline={backendAvailable} />
      {!backendAvailable ? (
        <section className="offline-panel" aria-live="polite" aria-busy={isLoadingMetadata}>
          <p className="eyebrow">
            {isLoadingMetadata ? "Connecting to analysis service" : "System offline"}
          </p>
          <h1>
            {isLoadingMetadata
              ? "Loading IronSight AI"
              : "Unable to connect to the IronSight analysis service"}
          </h1>
          {!isLoadingMetadata ? (
            <p>
              {connectionError ?? "Start the FastAPI backend to enable machine analysis."}
            </p>
          ) : (
            <p>Checking model availability…</p>
          )}
          {!isLoadingMetadata ? (
            <button type="button" className="retry-button" onClick={() => void loadModelInfo()}>
              Retry connection
            </button>
          ) : null}
        </section>
      ) : (
        <div className="workbench">
          <SensorForm modelInfo={modelInfo} isAnalyzing={isAnalyzing} onAnalyze={handleAnalyze} />
          <PredictiveAnalysis
            result={result}
            isAnalyzing={isAnalyzing}
            error={analysisError}
            onRetry={lastRequest ? handleRetryAnalysis : undefined}
          />
        </div>
      )}
      <footer>
        IronSight AI is a predictive-maintenance decision-support prototype. Predictions should be
        reviewed by qualified engineering personnel.
      </footer>
    </main>
  );
}
