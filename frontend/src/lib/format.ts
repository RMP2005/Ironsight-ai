/** Display-only formatting for failure probability (fraction 0–1). Does not mutate the raw value. */
export function formatFailureProbabilityPercent(probability: number): string {
  const percentage = probability * 100;

  if (!Number.isFinite(percentage)) {
    return "—";
  }

  if (percentage < 1) {
    return `${percentage.toFixed(2)}%`;
  }

  if (percentage < 99.95) {
    return `${percentage.toFixed(1)}%`;
  }

  if (percentage < 100) {
    return `${percentage.toFixed(2)}%`;
  }

  return `${percentage.toFixed(1)}%`;
}
