// Pure business logic, kept separate from UI so it can be unit-tested.
export const CATEGORIES = ["Market", "Fatura", "Ulaşım", "Eğitim", "Eğlence", "Diğer"];
export function addTx(list, { amount, category, note = "", type = "gider", date = new Date().toISOString() }) {
  const value = Number(String(amount).replace(",", "."));
  if (!Number.isFinite(value) || value <= 0) throw new Error("Geçerli bir tutar girin");
  return [{ id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), amount: value, category, note, type, date }, ...list];
}
export function summary(list, month = new Date().toISOString().slice(0, 7)) {
  const m = list.filter(t => t.date.startsWith(month));
  const gelir = m.filter(t => t.type === "gelir").reduce((s, t) => s + t.amount, 0);
  const gider = m.filter(t => t.type === "gider").reduce((s, t) => s + t.amount, 0);
  const byCat = {};
  m.filter(t => t.type === "gider").forEach(t => (byCat[t.category] = (byCat[t.category] || 0) + t.amount));
  return { gelir, gider, bakiye: gelir - gider, byCat };
}
export const tl = n => n.toLocaleString("tr-TR", { style: "currency", currency: "TRY" });
