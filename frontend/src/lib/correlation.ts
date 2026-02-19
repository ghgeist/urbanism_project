/**
 * Correlation calculation utilities for component analysis.
 */

/**
 * Calculate Pearson correlation coefficient between two arrays.
 * Handles null values by filtering them out before calculation.
 *
 * @param x First variable array (may contain nulls)
 * @param y Second variable array (may contain nulls)
 * @returns Correlation coefficient (-1 to 1), or 0 if insufficient data
 */
export function calculateCorrelation(x: (number | null)[], y: (number | null)[]): number {
  const pairs = x
    .map((xi, i) => ({ x: xi, y: y[i] }))
    .filter((p) => p.x != null && p.y != null) as { x: number; y: number }[];

  if (pairs.length < 2) return 0;

  const n = pairs.length;
  const sumX = pairs.reduce((sum, p) => sum + p.x, 0);
  const sumY = pairs.reduce((sum, p) => sum + p.y, 0);
  const sumXY = pairs.reduce((sum, p) => sum + p.x * p.y, 0);
  const sumX2 = pairs.reduce((sum, p) => sum + p.x * p.x, 0);
  const sumY2 = pairs.reduce((sum, p) => sum + p.y * p.y, 0);

  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

  return denominator === 0 ? 0 : numerator / denominator;
}
