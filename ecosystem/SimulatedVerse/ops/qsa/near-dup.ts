// Tiny shingle-based similarity (0..1)
export function jaccardSimilarity(a: string, b: string, k = 5): number {
  const A = new Set<string>(), B = new Set<string>();
  for (let i=0;i<=a.length-k;i++) A.add(a.slice(i,i+k));
  for (let i=0;i<=b.length-k;i++) B.add(b.slice(i,i+k));
  let inter = 0;
  for (const s of A) if (B.has(s)) inter++;
  const uni = A.size + B.size - inter;
  return uni === 0 ? 1 : inter / uni;
}