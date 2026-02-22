import { useState, useEffect, useCallback, useMemo } from 'react'
import { membersApi } from '@/api/fetcher'
import { shiftRequestsApi } from '@/api/fetcher'
import { pediatricApi } from '@/api/fetcher'
import type { MemberResponse } from '@/api/constants'
import { YearMonthPicker } from '@/components/YearMonthPicker'
import { useYearMonth } from '@/hooks/useYearMonth'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'

function getMonthDates(yearMonth: string): Date[] {
  const [y, m] = yearMonth.split('-').map(Number)
  const days = new Date(y, m, 0).getDate()
  return Array.from({ length: days }, (_, i) => new Date(y, m - 1, i + 1))
}

function getDayLabel(date: Date): string {
  return ['日', '月', '火', '水', '木', '金', '土'][date.getDay()]
}

function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function MonthlySettingsPage() {
  const { yearMonth, setYearMonth } = useYearMonth()
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [requestMap, setRequestMap] = useState<Map<number, Set<string>>>(new Map())
  const [pediatricDates, setPediatricDates] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [savingCells, setSavingCells] = useState<Set<string>>(new Set())

  const dates = useMemo(() => getMonthDates(yearMonth), [yearMonth])

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [membersData, requestsData, pediatricData] = await Promise.all([
        membersApi.list(),
        shiftRequestsApi.list(yearMonth),
        pediatricApi.list(yearMonth),
      ])

      setMembers(membersData)

      const map = new Map<number, Set<string>>()
      for (const member of membersData) {
        map.set(member.id, new Set())
      }
      for (const req of requestsData) {
        const set = map.get(req.member_id)
        if (set) {
          set.add(req.date)
        }
      }
      setRequestMap(map)

      setPediatricDates(new Set(pediatricData.map((p) => p.date)))
    } finally {
      setLoading(false)
    }
  }, [yearMonth])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const toggleShiftRequest = useCallback(
    async (memberId: number, dateStr: string) => {
      const cellKey = `${memberId}-${dateStr}`
      if (savingCells.has(cellKey)) return

      const currentSet = new Set(requestMap.get(memberId) ?? [])
      if (currentSet.has(dateStr)) {
        currentSet.delete(dateStr)
      } else {
        currentSet.add(dateStr)
      }

      setRequestMap((prev) => {
        const next = new Map(prev)
        next.set(memberId, currentSet)
        return next
      })

      setSavingCells((prev) => new Set(prev).add(cellKey))
      try {
        await shiftRequestsApi.bulkUpdate({
          member_id: memberId,
          year_month: yearMonth,
          dates: Array.from(currentSet).sort(),
        })
      } catch {
        setRequestMap((prev) => {
          const reverted = new Set(currentSet)
          if (reverted.has(dateStr)) {
            reverted.delete(dateStr)
          } else {
            reverted.add(dateStr)
          }
          const next = new Map(prev)
          next.set(memberId, reverted)
          return next
        })
      } finally {
        setSavingCells((prev) => {
          const next = new Set(prev)
          next.delete(cellKey)
          return next
        })
      }
    },
    [requestMap, yearMonth, savingCells],
  )

  const togglePediatric = useCallback(
    async (dateStr: string) => {
      const cellKey = `ped-${dateStr}`
      if (savingCells.has(cellKey)) return

      const currentSet = new Set(pediatricDates)
      if (currentSet.has(dateStr)) {
        currentSet.delete(dateStr)
      } else {
        currentSet.add(dateStr)
      }

      setPediatricDates(currentSet)

      setSavingCells((prev) => new Set(prev).add(cellKey))
      try {
        await pediatricApi.bulkUpdate({
          year_month: yearMonth,
          dates: Array.from(currentSet).sort(),
        })
      } catch {
        setPediatricDates((prev) => {
          const reverted = new Set(prev)
          if (reverted.has(dateStr)) {
            reverted.delete(dateStr)
          } else {
            reverted.add(dateStr)
          }
          return reverted
        })
      } finally {
        setSavingCells((prev) => {
          const next = new Set(prev)
          next.delete(cellKey)
          return next
        })
      }
    },
    [pediatricDates, yearMonth, savingCells],
  )

  const fullTimeWarnings = useMemo(() => {
    const warnings: { memberId: number; name: string; count: number }[] = []
    for (const member of members) {
      if (member.employment_type !== 'full_time') continue
      const count = requestMap.get(member.id)?.size ?? 0
      if (count > 3) {
        warnings.push({ memberId: member.id, name: member.name, count })
      }
    }
    return warnings
  }, [members, requestMap])

  const getColumnClass = useCallback((date: Date) => {
    const day = date.getDay()
    if (day === 0) return 'bg-red-50/60'
    if (day === 6) return 'bg-blue-50/60'
    return ''
  }, [])

  const getHeaderTextClass = useCallback((date: Date) => {
    const day = date.getDay()
    if (day === 0) return 'text-red-500'
    if (day === 6) return 'text-blue-600'
    return 'text-gray-500'
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-9 w-48" />
        </div>
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-8 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold tracking-tight text-gray-900">月次設定</h1>
        <YearMonthPicker value={yearMonth} onChange={setYearMonth} />
      </div>

      <section className="space-y-4">
        <h2 className="text-base font-semibold text-gray-800">希望休設定</h2>

        {fullTimeWarnings.length > 0 && (
          <Alert variant="destructive">
            <AlertDescription>
              {fullTimeWarnings.map((w) => (
                <span key={w.memberId} className="mr-4 inline-block">
                  {w.name}: 希望休 {w.count}日（常勤は3日以内を推奨）
                </span>
              ))}
            </AlertDescription>
          </Alert>
        )}

        <div className="overflow-x-auto rounded-md border border-gray-200">
          <table className="border-collapse text-xs">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-gray-50 border-b border-r border-gray-200 px-3 py-2 text-left font-medium text-gray-700 min-w-[100px]">
                  スタッフ
                </th>
                {dates.map((date) => {
                  const dateStr = formatDate(date)
                  return (
                    <th
                      key={dateStr}
                      className={`border-b border-r border-gray-200 px-0 py-1 text-center font-normal w-8 min-w-[2rem] ${getColumnClass(date)}`}
                    >
                      <div className="text-[11px] leading-tight text-gray-700">{date.getDate()}</div>
                      <div className={`text-[10px] leading-tight ${getHeaderTextClass(date)}`}>
                        {getDayLabel(date)}
                      </div>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              {members.map((member) => {
                const memberDates = requestMap.get(member.id) ?? new Set()
                return (
                  <tr key={member.id} className="hover:bg-gray-50/50">
                    <td className="sticky left-0 z-10 bg-white border-b border-r border-gray-200 px-3 py-1.5 font-medium text-gray-700 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span>{member.name}</span>
                        {member.employment_type === 'part_time' && (
                          <span className="text-[10px] text-gray-400 font-normal">非</span>
                        )}
                      </div>
                    </td>
                    {dates.map((date) => {
                      const dateStr = formatDate(date)
                      const isActive = memberDates.has(dateStr)
                      const isSaving = savingCells.has(`${member.id}-${dateStr}`)
                      return (
                        <td
                          key={dateStr}
                          className={`border-b border-r border-gray-200 w-8 h-8 text-center cursor-pointer transition-colors duration-75 select-none ${getColumnClass(date)} ${
                            isActive
                              ? 'bg-blue-100 hover:bg-blue-200'
                              : 'hover:bg-gray-100'
                          } ${isSaving ? 'opacity-50' : ''}`}
                          onClick={() => toggleShiftRequest(member.id, dateStr)}
                        >
                          {isActive && (
                            <div className="flex items-center justify-center">
                              <div className="w-2 h-2 rounded-full bg-blue-500" />
                            </div>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-base font-semibold text-gray-800">小児科医スケジュール</h2>

        <div className="overflow-x-auto rounded-md border border-gray-200">
          <table className="border-collapse text-xs">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-gray-50 border-b border-r border-gray-200 px-3 py-2 text-left font-medium text-gray-700 min-w-[100px]">
                  日付
                </th>
                {dates.map((date) => {
                  const dateStr = formatDate(date)
                  return (
                    <th
                      key={dateStr}
                      className={`border-b border-r border-gray-200 px-0 py-1 text-center font-normal w-8 min-w-[2rem] ${getColumnClass(date)}`}
                    >
                      <div className="text-[11px] leading-tight text-gray-700">{date.getDate()}</div>
                      <div className={`text-[10px] leading-tight ${getHeaderTextClass(date)}`}>
                        {getDayLabel(date)}
                      </div>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              <tr className="hover:bg-gray-50/50">
                <td className="sticky left-0 z-10 bg-white border-b border-r border-gray-200 px-3 py-1.5 font-medium text-gray-700 whitespace-nowrap">
                  小児科医
                </td>
                {dates.map((date) => {
                  const dateStr = formatDate(date)
                  const isActive = pediatricDates.has(dateStr)
                  const isSaving = savingCells.has(`ped-${dateStr}`)
                  return (
                    <td
                      key={dateStr}
                      className={`border-b border-r border-gray-200 w-8 h-8 text-center cursor-pointer transition-colors duration-75 select-none ${getColumnClass(date)} ${
                        isActive
                          ? 'bg-emerald-100 hover:bg-emerald-200'
                          : 'hover:bg-gray-100'
                      } ${isSaving ? 'opacity-50' : ''}`}
                      onClick={() => togglePediatric(dateStr)}
                    >
                      {isActive && (
                        <div className="flex items-center justify-center">
                          <div className="w-2 h-2 rounded-full bg-emerald-500" />
                        </div>
                      )}
                    </td>
                  )
                })}
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
