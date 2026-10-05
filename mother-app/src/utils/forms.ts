// Small helpers for turning typed form text into the values the API expects.
import { ApiError } from '@/api/client'

import { asciiDigits } from './format'

/** "۶۲٫۵" or " 62.5 " → 62.5; empty → null. */
export function toNumber(text: string): number | null {
  const clean = asciiDigits(text.trim()).replace(/[٫,]/g, '.')
  return clean ? Number(clean) : null
}

export const toText = (text: string): string | null => text.trim() || null

/** The backend's message for one field of a rejected form, if any. */
export const fieldErrorOf = (error: unknown, name: string): string | undefined =>
  error instanceof ApiError ? error.fieldErrors[name] : undefined
