export function normalizeEvaluations(summary) {
  const result = [];
  collectEvaluations(summary, result);
  return dedupeGrades(result);
}

export function computeSubjectStats(grades) {
  const bySubject = new Map();

  for (const grade of grades) {
    const subject = grade.subject || "Без предмета";
    if (!bySubject.has(subject)) {
      bySubject.set(subject, {
        subject,
        numericValues: [],
        allValues: [],
        latest: null,
      });
    }

    const stat = bySubject.get(subject);
    stat.allValues.push(grade.value);
    if (!stat.latest || gradeSortValue(grade) > gradeSortValue(stat.latest)) {
      stat.latest = grade;
    }

    const numeric = parseNumericGrade(grade.value);
    if (numeric !== null) stat.numericValues.push(numeric);
  }

  return Array.from(bySubject.values())
    .map((stat) => ({
      subject: stat.subject,
      average:
        stat.numericValues.length > 0
          ? round2(stat.numericValues.reduce((sum, value) => sum + value, 0) / stat.numericValues.length)
          : null,
      numericCount: stat.numericValues.length,
      totalCount: stat.allValues.length,
      latest: stat.latest,
      values: stat.allValues,
    }))
    .sort((a, b) => a.subject.localeCompare(b.subject, "lv"));
}

export function findNewGrades(currentGrades, knownIds) {
  const known = new Set(knownIds || []);
  return currentGrades.filter((grade) => grade.id !== null && !known.has(String(grade.id)));
}

export function gradeIds(grades) {
  return grades
    .map((grade) => grade.id)
    .filter((id) => id !== null && id !== undefined)
    .map(String);
}

export function formatGrade(grade) {
  const parts = [
    `Предмет: ${grade.subject || "неизвестно"}`,
    `Оценка: ${grade.value || "неизвестно"}`,
  ];
  if (grade.date) parts.push(`Дата: ${formatDate(grade.date)}`);
  return parts.join("\n");
}

export function formatStats(stats) {
  if (stats.length === 0) return "Пока нет оценок для статистики.";

  return stats
    .map((stat) => {
      const avg = stat.average === null ? "нет числовых оценок" : stat.average.toFixed(2);
      const latest = stat.latest?.value ? `, последняя: ${stat.latest.value}` : "";
      return `${stat.subject}: средняя ${avg} (${stat.numericCount}/${stat.totalCount})${latest}`;
    })
    .join("\n");
}

export function sortGradesByDateDesc(grades) {
  return [...grades].sort((a, b) => gradeSortValue(b) - gradeSortValue(a));
}

export function formatGradesByDate(grades) {
  if (grades.length === 0) return "Пока нет оценок.";

  return sortGradesByDateDesc(grades)
    .map((grade) => {
      const visibleDate = grade.raw?.timeCreated ? formatDate(grade.raw.timeCreated) : "без даты появления";
      const workDate = grade.date ? `, работа: ${formatDate(grade.date)}` : "";
      const subject = grade.subject || "неизвестный предмет";
      const value = grade.value || "неизвестно";
      return `${visibleDate} | ${subject}: ${value}${workDate}`;
    })
    .join("\n");
}

export function splitTelegramText(text, maxLength = 3900) {
  if (text.length <= maxLength) return [text];

  const chunks = [];
  let current = "";
  for (const line of text.split("\n")) {
    if (`${current}\n${line}`.length > maxLength) {
      if (current) chunks.push(current);
      current = line;
    } else {
      current = current ? `${current}\n${line}` : line;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

function collectEvaluations(value, result) {
  if (Array.isArray(value)) {
    for (const item of value) collectEvaluations(item, result);
    return;
  }

  if (!value || typeof value !== "object") return;

  if (Array.isArray(value.evaluations)) {
    for (const evaluation of value.evaluations) {
      result.push({
        id: evaluation.id ?? null,
        value: evaluation.value ?? evaluation.studentEvaluation ?? null,
        subject:
          evaluation.lesson?.lessonSubject?.name ??
          evaluation.lessonSubject?.name ??
          evaluation.disciplineName ??
          value.disciplineName ??
          value.name ??
          null,
        date: evaluation.lesson?.date ?? evaluation.lesson?.lessonDate ?? evaluation.lessonDate ?? null,
        raw: evaluation,
      });
    }
  }

  for (const nested of Object.values(value)) {
    collectEvaluations(nested, result);
  }
}

function dedupeGrades(grades) {
  const seen = new Set();
  const result = [];
  for (const grade of grades) {
    const key = grade.id === null ? JSON.stringify(grade.raw) : String(grade.id);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(grade);
  }
  return result;
}

function parseNumericGrade(value) {
  if (typeof value !== "string" && typeof value !== "number") return null;
  const text = String(value).trim().replace(",", ".");
  if (!/^\d+(\.\d+)?$/.test(text)) return null;
  const numeric = Number(text);
  if (!Number.isFinite(numeric) || numeric < 1 || numeric > 10) return null;
  return numeric;
}

function round2(value) {
  return Math.round(value * 100) / 100;
}

function gradeSortValue(grade) {
  const time = Date.parse(grade.raw?.timeCreated || grade.date || "");
  return Number.isNaN(time) ? 0 : time;
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("lv-LV");
}
