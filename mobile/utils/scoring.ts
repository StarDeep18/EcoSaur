export const calculateClientScore = (scorecard: {
  nova_group: number;
  sugar_load: string;
  sodium_load: string;
  additive_density: string;
  protein_quality: string;
  fiber_quality: string;
}) => {
  if (!scorecard) return 70;
  let s = 100;
  s -= (scorecard.nova_group * 12);
  if (scorecard.sugar_load === "High") s -= 15;
  if (scorecard.sugar_load === "Moderate") s -= 5;
  if (scorecard.sodium_load === "High") s -= 10;
  if (scorecard.additive_density === "High") s -= 10;
  if (scorecard.additive_density === "Medium") s -= 5;
  if (scorecard.protein_quality === "High Source") s += 8;
  if (scorecard.fiber_quality === "High Source") s += 8;
  return Math.max(20, Math.min(100, s));
};

export const scoreToGradeLetter = (score: number) => {
  if (score >= 90) return 'S';
  if (score >= 80) return 'A';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  if (score >= 40) return 'D';
  return 'F';
};

export const getMetricColor = (metricName: string, value: string | number, isHealthyMetric = false) => {
  if (metricName === "NOVA") {
    const val = Number(value);
    if (val === 1) return "#10b981"; // green
    if (val === 2) return "#a3e635"; // light green
    if (val === 3) return "#fb923c"; // orange
    return "#ef4444"; // red
  }
  
  if (isHealthyMetric) {
    return value === "High Source" ? "#10b981" : "#64748b";
  }
  
  if (value === "High") return "#ef4444";
  if (value === "Medium" || value === "Moderate") return "#facc15";
  return "#10b981"; // Low
};
