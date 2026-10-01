import { describe, expect, it } from 'vitest'

import { asciiDigits, formatDate, formatMobile, localDigits, localMidnight } from '@/utils/format'

describe('format', () => {
  it('converts digits both ways', () => {
    expect(localDigits('0912', 'fa')).toBe('۰۹۱۲')
    expect(localDigits('0912', 'en')).toBe('0912')
    expect(asciiDigits('۰۹۱۲ ٣٤')).toBe('0912 34')
  })

  it('writes mobiles the local way', () => {
    expect(formatMobile('+989121234567', 'en')).toBe('0912 123 4567')
    expect(formatMobile('+989121234567', 'fa')).toBe('۰۹۱۲ ۱۲۳ ۴۵۶۷')
  })

  it('shows dates in the Jalali calendar in Persian', () => {
    expect(formatDate('2026-10-01', 'fa')).toContain('مهر')
    expect(formatDate('2026-10-01', 'fa')).toContain('۱۴۰۵')
    expect(formatDate('2026-10-01', 'en')).toBe('1 October 2026')
  })

  it('sends local midnight with an offset', () => {
    expect(localMidnight('2026-09-20')).toMatch(/^2026-09-20T00:00:00[+-]\d{2}:\d{2}$/)
  })
})
