import { describe, expect, it } from 'vitest'

import { jalaliMonthLength, toGregorian, toIsoDate, toJalali } from '@/utils/jalali'

const known: [string, [number, number, number]][] = [
  ['2024-03-20', [1403, 1, 1]], // Nowruz 1403
  ['2025-03-21', [1404, 1, 1]],
  ['2026-10-01', [1405, 7, 9]],
  ['2025-03-20', [1403, 12, 30]], // 1403 is a leap year
  ['2000-01-01', [1378, 10, 11]],
]

describe('jalali', () => {
  it.each(known)('%s ↔ %j', (iso, [year, month, day]) => {
    const [gy, gm, gd] = iso.split('-').map(Number)
    expect(toJalali({ year: gy, month: gm, day: gd })).toEqual({ year, month, day })
    expect(toIsoDate(toGregorian({ year, month, day }))).toBe(iso)
  })

  it('round-trips every day for 30 years', () => {
    const day = new Date(Date.UTC(2000, 0, 1))
    for (let i = 0; i < 365 * 30; i++) {
      const g = { year: day.getUTCFullYear(), month: day.getUTCMonth() + 1, day: day.getUTCDate() }
      expect(toGregorian(toJalali(g))).toEqual(g)
      day.setUTCDate(day.getUTCDate() + 1)
    }
  })

  it('knows month lengths', () => {
    expect(jalaliMonthLength(1405, 1)).toBe(31)
    expect(jalaliMonthLength(1405, 7)).toBe(30)
    expect(jalaliMonthLength(1403, 12)).toBe(30)
    expect(jalaliMonthLength(1404, 12)).toBe(29)
  })
})
