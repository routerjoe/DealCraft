export type FleetingScope = 'today' | 'this-week' | 'this-month' | 'since-last-run' | 'range';

export interface DateRange {
  start: string; // YYYY-MM-DD inclusive
  end: string;   // YYYY-MM-DD inclusive
  label: string;
}

export function dateStr(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function resolveRange(
  scope: FleetingScope,
  rangeArg?: string,
  since?: string,
  now: Date = new Date()
): DateRange {
  const today = dateStr(now);

  switch (scope) {
    case 'today':
      return { start: today, end: today, label: 'today' };

    case 'this-week': {
      // Monday..Sunday in local time
      const d = new Date(now);
      const day = d.getDay(); // 0=Sun..6=Sat
      const diffToMonday = (day + 6) % 7; // Sun->6, Mon->0, Tue->1, ...
      const mon = new Date(d);
      mon.setDate(d.getDate() - diffToMonday);
      const sun = new Date(mon);
      sun.setDate(mon.getDate() + 6);
      return { start: dateStr(mon), end: dateStr(sun), label: 'this week' };
    }

    case 'this-month': {
      const first = new Date(now.getFullYear(), now.getMonth(), 1);
      const last = new Date(now.getFullYear(), now.getMonth() + 1, 0);
      return { start: dateStr(first), end: dateStr(last), label: 'this month' };
    }

    case 'since-last-run': {
      const start = since || today;
      // Clamp to today instead of open-ended 9999-12-31
      const end = today;
      const label = since ? `since last run (${since}+)` : 'since last run (today)';
      return { start, end, label };
    }

    case 'range': {
      if (rangeArg) {
        const m = rangeArg.match(/^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$/);
        if (m) return { start: m[1], end: m[2], label: `range ${m[1]}..${m[2]}` };
      }
      // Fallback to today if range missing/invalid
      return { start: today, end: today, label: 'today' };
    }

    default:
      return { start: '0000-01-01', end: '9999-12-31', label: 'all' };
  }
}

export function inRange(date: string, start: string, end: string): boolean {
  return date >= start && date <= end;
}