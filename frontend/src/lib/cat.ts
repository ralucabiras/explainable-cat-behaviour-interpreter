export function formatCatAge(dateOfBirth?: string | null, now = new Date()): string | null {
  if (!dateOfBirth) return null;
  const birth = new Date(`${dateOfBirth}T00:00:00`);
  if (Number.isNaN(birth.getTime()) || birth > now) return null;

  let years = now.getFullYear() - birth.getFullYear();
  let months = now.getMonth() - birth.getMonth();
  if (now.getDate() < birth.getDate()) months -= 1;
  if (months < 0) {
    years -= 1;
    months += 12;
  }
  if (years === 0 && months === 0) return "Less than 1 month old";
  if (years === 0) return `${months} ${months === 1 ? "month" : "months"} old`;
  if (months === 0) return `${years} ${years === 1 ? "year" : "years"} old`;
  return `${years} ${years === 1 ? "year" : "years"}, ${months} ${months === 1 ? "month" : "months"} old`;
}
