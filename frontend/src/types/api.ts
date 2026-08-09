export type FeatureRange = {
  min: number;
  max: number;
  unit: string;
};

export type ModelInfo = {
  is_loaded: boolean;
  target_name: string;
  threshold: number;
  feature_names: string[];
  feature_units: Record<string, string>;
  feature_ranges: Record<string, FeatureRange>;
};

export type PredictionRequest = {
  air_temperature: number;
  process_temperature: number;
  rotational_speed: number;
  torque: number;
  tool_wear: number;
};

export type PredictionResponse = {
  failure_probability: number;
  threshold: number;
  failure_alert: boolean;
  risk_level: "Low" | "Moderate" | "High";
  maintenance_recommendation: string;
  validation_warnings: string[];
};
