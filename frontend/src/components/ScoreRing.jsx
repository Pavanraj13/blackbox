import React from 'react';

export default function ScoreRing({ score = 100, size = 120, strokeWidth = 8, label = 'Health Score' }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  const getColor = () => {
    if (clampedScore >= 80) return '#10b981'; // emerald
    if (clampedScore >= 50) return '#f59e0b'; // amber
    return '#ef4444'; // rose
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="w-full h-full transform -rotate-90" viewBox={`0 0 ${size} ${size}`}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="currentColor"
            className="text-zinc-200 dark:text-zinc-800"
            strokeWidth={strokeWidth}
          />
          {/* Animated score circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={getColor()}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold tracking-tight text-[var(--text)] font-mono">
            {clampedScore.toFixed(0)}
          </span>
          <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-medium">
            / 100
          </span>
        </div>
      </div>
      {label && (
        <span className="mt-2 text-xs font-medium uppercase tracking-wider text-[var(--text-secondary)]">
          {label}
        </span>
      )}
    </div>
  );
}
