const TIMEZONE_SUFFIX = /(Z|[+-]\d{2}:\d{2})$/i;

const beijingDateTimeFormatter = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  year: "numeric",
  month: "numeric",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
});

const beijingChartFormatter = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function parseUtcTimestamp(value: string): Date {
  const normalized = TIMEZONE_SUFFIX.test(value.trim()) ? value.trim() : `${value.trim()}Z`;
  return new Date(normalized);
}

export function formatBeijingDateTime(value: string): string {
  const date = parseUtcTimestamp(value);
  return Number.isNaN(date.getTime()) ? value : beijingDateTimeFormatter.format(date);
}

export function formatBeijingChartTime(value: string): string {
  const date = parseUtcTimestamp(value);
  if (Number.isNaN(date.getTime())) return value;
  const parts = Object.fromEntries(
    beijingChartFormatter.formatToParts(date).map((part) => [part.type, part.value]),
  );
  return `${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
}
