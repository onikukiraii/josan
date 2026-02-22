import { useState } from 'react'

function getCurrentYearMonth(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}`
}

export function useYearMonth() {
  const [yearMonth, setYearMonth] = useState(getCurrentYearMonth)
  return { yearMonth, setYearMonth }
}
