/** 将表格数据导出为 CSV（UTF-8 BOM，Excel 可打开） */

function escapeCell(v: unknown): string {
  if (v === null || v === undefined) return "";
  const s = String(v);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function exportCsv(
  rows: Record<string, unknown>[],
  columns: { field: string; label: string }[],
  filename: string
) {
  const fields = columns.length ? columns : inferColumns(rows);
  const header = fields.map((c) => escapeCell(c.label)).join(",");
  const lines = [header];
  for (const row of rows) {
    lines.push(fields.map((c) => escapeCell(row[c.field])).join(","));
  }
  const blob = new Blob(["\ufeff" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename.replace(/\.csv$/i, "")}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function inferColumns(rows: Record<string, unknown>[]): { field: string; label: string }[] {
  const first = rows[0];
  if (!first) return [];
  return Object.keys(first).map((k) => ({ field: k, label: k }));
}
