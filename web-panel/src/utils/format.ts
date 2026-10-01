// Numbers and dates for the current language: Persian digits and the Jalali calendar in fa,
// Western digits and the Gregorian calendar in en.
import { parseIsoDate } from './jalali'

export type Locale = 'fa' | 'en'

const intlLocale = (locale: Locale) => (locale === 'fa' ? 'fa-IR-u-ca-persian-nu-arabext' : 'en-GB')

export function formatNumber(value: number | string | null | undefined, locale: Locale): string {
  if (value === null || value === undefined || value === '') return '—'
  const n = typeof value === 'number' ? value : Number(value)
  if (Number.isNaN(n)) return String(value)
  return new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en-GB', { maximumFractionDigits: 2 }).format(n)
}

/** Replace Western digits in a string (e.g. a mobile number) with Persian ones in fa. */
export function localDigits(text: string | null | undefined, locale: Locale): string {
  if (!text) return '—'
  return locale === 'fa' ? text.replace(/\d/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[Number(d)]) : text
}

/** Persian or Arabic-Indic digits typed by the user → Western digits for the API. */
export function asciiDigits(text: string): string {
  return text
    .replace(/[۰-۹]/g, (d) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)))
    .replace(/[٠-٩]/g, (d) => String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)))
}

/** A date-only value ("2026-10-01"), shown without any timezone shift. */
export function formatDate(iso: string | null | undefined, locale: Locale): string {
  if (!iso) return '—'
  const { year, month, day } = parseIsoDate(iso)
  const utcNoon = new Date(Date.UTC(year, month - 1, day, 12))
  return new Intl.DateTimeFormat(intlLocale(locale), {
    year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC',
  }).format(utcNoon)
}

/** A timestamp, in the viewer's time zone. */
export function formatDateTime(iso: string | null | undefined, locale: Locale): string {
  if (!iso) return '—'
  return new Intl.DateTimeFormat(intlLocale(locale), {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(iso))
}

/** +989121234567 → 0912 123 4567 (how people in Iran write it). */
export function formatMobile(mobile: string | null | undefined, locale: Locale): string {
  if (!mobile) return '—'
  const local = mobile.startsWith('+98') ? '0' + mobile.slice(3) : mobile
  const spaced = local.length === 11 ? `${local.slice(0, 4)} ${local.slice(4, 7)} ${local.slice(7)}` : local
  return localDigits(spaced, locale)
}

/** Local midnight of a date with the browser's UTC offset, e.g. 2026-09-20T00:00:00+03:30. */
export function localMidnight(isoDate: string): string {
  const { year, month, day } = parseIsoDate(isoDate)
  const offset = -new Date(year, month - 1, day).getTimezoneOffset()
  const sign = offset >= 0 ? '+' : '-'
  const abs = Math.abs(offset)
  const hh = String(Math.floor(abs / 60)).padStart(2, '0')
  const mm = String(abs % 60).padStart(2, '0')
  return `${isoDate}T00:00:00${sign}${hh}:${mm}`
}
