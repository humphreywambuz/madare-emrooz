// Gregorian ↔ Jalali (Solar Hijri) conversion, the same algorithm as backend/app/shared/domain/jalali.py.
// Valid for 1600–3000 CE. Months are 1-based.

export type DateParts = { year: number; month: number; day: number }

const DAYS_BEFORE_MONTH = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

export function toJalali({ year, month, day }: DateParts): DateParts {
  const gy2 = month > 2 ? year + 1 : year
  let days =
    355666 + 365 * year + Math.floor((gy2 + 3) / 4) - Math.floor((gy2 + 99) / 100) +
    Math.floor((gy2 + 399) / 400) + day + DAYS_BEFORE_MONTH[month - 1]
  let jy = -1595 + 33 * Math.floor(days / 12053)
  days %= 12053
  jy += 4 * Math.floor(days / 1461)
  days %= 1461
  if (days > 365) {
    jy += Math.floor((days - 1) / 365)
    days = (days - 1) % 365
  }
  if (days < 186) return { year: jy, month: 1 + Math.floor(days / 31), day: 1 + (days % 31) }
  return { year: jy, month: 7 + Math.floor((days - 186) / 30), day: 1 + ((days - 186) % 30) }
}

export function toGregorian({ year, month, day }: DateParts): DateParts {
  const jy = year + 1595
  let days =
    -355668 + 365 * jy + Math.floor(jy / 33) * 8 + Math.floor(((jy % 33) + 3) / 4) + day +
    (month < 7 ? (month - 1) * 31 : (month - 7) * 30 + 186)
  let gy = 400 * Math.floor(days / 146097)
  days %= 146097
  if (days > 36524) {
    days -= 1
    gy += 100 * Math.floor(days / 36524)
    days %= 36524
    if (days >= 365) days += 1
  }
  gy += 4 * Math.floor(days / 1461)
  days %= 1461
  if (days > 365) {
    gy += Math.floor((days - 1) / 365)
    days = (days - 1) % 365
  }
  let gd = days + 1
  const leap = (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0
  const monthDays = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  let gm = 0
  while (gm < 12 && gd > monthDays[gm]) gd -= monthDays[gm++]
  return { year: gy, month: gm + 1, day: gd }
}

export function jalaliMonthLength(year: number, month: number): number {
  if (month <= 6) return 31
  if (month <= 11) return 30
  // Esfand has 30 days in a leap year: day 30 survives a round trip.
  const back = toJalali(toGregorian({ year, month: 12, day: 30 }))
  return back.month === 12 && back.day === 30 ? 30 : 29
}

/** "2026-10-01" → {year: 2026, month: 10, day: 1} */
export function parseIsoDate(iso: string): DateParts {
  const [year, month, day] = iso.slice(0, 10).split('-').map(Number)
  return { year, month, day }
}

export function toIsoDate({ year, month, day }: DateParts): string {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}
