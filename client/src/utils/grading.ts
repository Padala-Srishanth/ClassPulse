/**
 * calculateAcademicGrade — Dynamically maps test score percentages to standard letter grades.
 */
export function calculateAcademicGrade(testScorePercentage: number | null | undefined): {
  grade: string;
  color: string;
  bgColor: string;
  label: string;
} {
  if (testScorePercentage === null || testScorePercentage === undefined || isNaN(testScorePercentage)) {
    return { grade: 'N/A', color: '#64748b', bgColor: '#f1f5f9', label: 'No exams' };
  }
  if (testScorePercentage >= 90) {
    return { grade: 'A+', color: '#15803d', bgColor: '#dcfce7', label: `${testScorePercentage.toFixed(1)}%` };
  }
  if (testScorePercentage >= 80) {
    return { grade: 'A', color: '#16a34a', bgColor: '#f0fdf4', label: `${testScorePercentage.toFixed(1)}%` };
  }
  if (testScorePercentage >= 70) {
    return { grade: 'B', color: '#2563eb', bgColor: '#eff6ff', label: `${testScorePercentage.toFixed(1)}%` };
  }
  if (testScorePercentage >= 60) {
    return { grade: 'C', color: '#d97706', bgColor: '#fffbeb', label: `${testScorePercentage.toFixed(1)}%` };
  }
  if (testScorePercentage >= 50) {
    return { grade: 'D', color: '#ea580c', bgColor: '#fff7ed', label: `${testScorePercentage.toFixed(1)}%` };
  }
  return { grade: 'F', color: '#dc2626', bgColor: '#fef2f2', label: `${testScorePercentage.toFixed(1)}%` };
}
