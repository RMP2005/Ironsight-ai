"use client";

import { useId, useState, type CSSProperties, type FormEvent } from "react";

import type { FeatureRange, ModelInfo, PredictionRequest } from "@/types/api";

type SensorDefinition = {
  field: keyof PredictionRequest;
  featureName: string;
  label: string;
  initialValue: string;
};

const sensors: SensorDefinition[] = [
  { field: "air_temperature", featureName: "Air temperature [K]", label: "Air temperature", initialValue: "298.1" },
  { field: "process_temperature", featureName: "Process temperature [K]", label: "Process temperature", initialValue: "308.6" },
  { field: "rotational_speed", featureName: "Rotational speed [rpm]", label: "Rotational speed", initialValue: "1551.0" },
  { field: "torque", featureName: "Torque [Nm]", label: "Torque", initialValue: "42.8" },
  { field: "tool_wear", featureName: "Tool wear [min]", label: "Tool wear", initialValue: "0.0" },
];

type SensorFormProps = {
  modelInfo: ModelInfo;
  isAnalyzing: boolean;
  onAnalyze: (request: PredictionRequest) => Promise<void>;
};

function SensorField({
  sensor,
  value,
  range,
  unit,
  onChange,
}: {
  sensor: SensorDefinition;
  value: string;
  range: FeatureRange | undefined;
  unit: string;
  onChange: (value: string) => void;
}) {
  const inputId = useId();
  const numericValue = Number(value);
  const hasNumericValue = value.trim() !== "" && Number.isFinite(numericValue);
  const hasRange = Boolean(range);
  const isWithinRange =
    hasNumericValue && hasRange && numericValue >= range!.min && numericValue <= range!.max;
  const isOutside = hasNumericValue && hasRange && !isWithinRange;
  const markerPosition =
    hasNumericValue && hasRange
      ? Math.min(100, Math.max(0, ((numericValue - range!.min) / (range!.max - range!.min)) * 100))
      : 50;
  const markerStyle = { "--marker-pos": `${markerPosition}%` } as CSSProperties;

  return (
    <div className={`sensor-field ${isOutside ? "sensor-outside" : ""}`}>
      <div className="sensor-field-topline">
        <label className="sensor-label" htmlFor={inputId}>
          {sensor.label}
        </label>
        <span
          className={`sensor-status-dot ${isOutside ? "dot-warn" : hasNumericValue ? "dot-ok" : "dot-idle"}`}
          aria-hidden="true"
        />
      </div>
      <div className="input-wrap">
        <input
          id={inputId}
          name={sensor.field}
          inputMode="decimal"
          autoComplete="off"
          value={value}
          aria-invalid={isOutside || undefined}
          aria-describedby={`${inputId}-range ${inputId}-state`}
          onChange={(event) => onChange(event.target.value)}
        />
        <span aria-hidden="true">{unit}</span>
      </div>
      {hasRange ? (
        <>
          <span className="range-label" id={`${inputId}-range`}>
            Reference range
          </span>
          <span className="range-value">
            {range!.min} — {range!.max} {unit}
          </span>
          <span className="range-scale" aria-hidden="true" style={markerStyle}>
            <span>Min</span>
            <i />
            <b />
            <span>Max</span>
          </span>
        </>
      ) : (
        <span className="range-label">Reference range unavailable</span>
      )}
      {hasNumericValue ? (
        <span
          className={`range-state ${isWithinRange ? "within-range" : "outside-range"}`}
          id={`${inputId}-state`}
          role={isOutside ? "status" : undefined}
        >
          {isWithinRange ? "Within reference range" : "Outside reference range"}
          {isOutside ? <small>Prediction may be less reliable.</small> : null}
        </span>
      ) : (
        <span className="range-state outside-range" id={`${inputId}-state`}>
          Enter a numeric value
        </span>
      )}
    </div>
  );
}

export function SensorForm({ modelInfo, isAnalyzing, onAnalyze }: SensorFormProps) {
  const [values, setValues] = useState<Record<keyof PredictionRequest, string>>(
    Object.fromEntries(sensors.map((sensor) => [sensor.field, sensor.initialValue])) as Record<
      keyof PredictionRequest,
      string
    >,
  );
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const request = {} as PredictionRequest;

    for (const sensor of sensors) {
      const value = Number(values[sensor.field]);
      if (!Number.isFinite(value)) {
        setFormError("Enter a numeric value for each sensor before analysis.");
        return;
      }
      request[sensor.field] = value;
    }

    setFormError(null);
    await onAnalyze(request);
  }

  return (
    <section className="instrument-panel sensor-panel" aria-labelledby="sensor-panel-heading">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">01 / Sensor telemetry</p>
          <h2 id="sensor-panel-heading">Enter sensor values</h2>
        </div>
        <span className="panel-code">
          <span className="panel-code-dot" aria-hidden="true" />
          Live input
        </span>
      </div>
      <div className="panel-rule" aria-hidden="true" />
      <p className="reference-note">
        Reference range reflects values observed in the model&apos;s training data.
      </p>
      <form onSubmit={handleSubmit} noValidate>
        <div className="sensor-grid">
          {sensors.map((sensor) => (
            <SensorField
              key={sensor.field}
              sensor={sensor}
              value={values[sensor.field]}
              range={modelInfo.feature_ranges[sensor.featureName]}
              unit={modelInfo.feature_units[sensor.featureName] ?? ""}
              onChange={(value) =>
                setValues((current) => ({ ...current, [sensor.field]: value }))
              }
            />
          ))}
        </div>
        {formError ? (
          <p className="form-error" role="alert">
            {formError}
          </p>
        ) : null}
        <button
          className="analyze-button"
          type="submit"
          disabled={isAnalyzing}
          aria-busy={isAnalyzing}
        >
          <span className="analyze-button-sweep" aria-hidden="true" />
          <span className="analyze-button-label">
            <span aria-hidden="true">◈</span>
            {isAnalyzing ? "Analyzing…" : "Analyze machine"}
          </span>
        </button>
      </form>
    </section>
  );
}
