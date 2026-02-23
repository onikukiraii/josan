import { useState, useEffect, useCallback, useMemo } from 'react'
import { toast } from 'sonner'
import { membersApi } from '@/api/fetcher'
import { shiftRequestsApi } from '@/api/fetcher'
import { pediatricApi } from '@/api/fetcher'
import type { MemberResponse, RequestType } from '@/api/constants'
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
  const [requestMap, setRequestMap] = useState<Map<number, Map<string, RequestType>>>(new Map())
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

      const map = new Map<number, Map<string, RequestType>>()
      for (const member of membersData) {
        map.set(member.id, new Map())
      }
      for (const req of requestsData) {
        const memberMap = map.get(req.member_id)
        if (memberMap) {
          memberMap.set(req.date, req.request_type)
        }
      }
      setRequestMap(map)

      setPediatricDates(new Set(pediatricData.map((p) => p.date)))
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'データの取得に失敗しました')
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

      const currentMap = new Map(requestMap.get(memberId) ?? [])
      const prevMap = new Map(currentMap)
      const currentType = currentMap.get(dateStr)

      // 3状態サイクル: 空 → 公休 → 有給 → 空
      if (!currentType) {
        currentMap.set(dateStr, 'day_off')
      } else if (currentType === 'day_off') {
        currentMap.set(dateStr, 'paid_leave')
      } else {
        currentMap.delete(dateStr)
      }

      setRequestMap((prev) => {
        const next = new Map(prev)
        next.set(memberId, currentMap)
        return next
      })

      setSavingCells((prev) => new Set(prev).add(cellKey))
      try {
        const entries = Array.from(currentMap.entries())
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([date, request_type]) => ({ date, request_type }))
        await shiftRequestsApi.bulkUpdate({
          member_id: memberId,
          year_month: yearMonth,
          entries,
        })
      } catch (e) {
        toast.error(e instanceof Error ? e.message : '希望休の更新に失敗しました')
        setRequestMap((prev) => {
          const next = new Map(prev)
          next.set(memberId, prevMap)
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
      } catch (e) {
        toast.error(e instanceof Error ? e.message : '小児科医スケジュールの更新に失敗しました')
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
    if (day === 0) return 'bg-sunday-bg/60'
    if (day === 6) return 'bg-saturday-bg/60'
    return ''
  }, [])

  const getHeaderTextClass = useCallback((date: Date) => {
    const day = date.getDay()
    if (day === 0) return 'text-sunday'
    if (day === 6) return 'text-saturday'
    return 'text-warm-gray-500'
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
        <h1 className="text-2xl font-bold tracking-tight text-warm-gray-900">月次設定</h1>
        <YearMonthPicker value={yearMonth} onChange={setYearMonth} />
      </div>

      <section className="space-y-4">
        <div className="flex items-center gap-4">
          <h2 className="text-base font-semibold text-warm-gray-800">希望休設定</h2>
          <div className="flex items-center gap-3 text-xs text-warm-gray-500">
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-brand-500" />
              公休希望
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-orange-500" />
              有給希望
            </span>
          </div>
        </div>

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

        <div className="overflow-x-auto rounded-2xl soft-shadow-md bg-white">
          <table className="border-collapse text-xs">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-brand-50/60 border-b border-r border-warm-gray-200 px-3 py-2 text-left font-medium text-brand-800 min-w-[100px]">
                  スタッフ
                </th>
                {dates.map((date) => {
                  const dateStr = formatDate(date)
                  return (
                    <th
                      key={dateStr}
                      className={`border-b border-r border-warm-gray-200 px-0 py-1 text-center font-normal w-8 min-w-[2rem] ${getColumnClass(date)}`}
                    >
                      <div className="text-[11px] leading-tight text-warm-gray-700">{date.getDate()}</div>
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
                const memberDates = requestMap.get(member.id) ?? new Map()
                return (
                  <tr key={member.id} className="hover:bg-brand-50/30">
                    <td className="sticky left-0 z-10 bg-white border-b border-r border-warm-gray-200 px-3 py-1.5 font-medium text-warm-gray-700 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span>{member.name}</span>
                        {member.employment_type === 'part_time' && (
                          <span className="text-[10px] text-warm-gray-400 font-normal">非</span>
                        )}
                      </div>
                    </td>
                    {dates.map((date) => {
                      const dateStr = formatDate(date)
                      const requestType = memberDates.get(dateStr)
                      const isSaving = savingCells.has(`${member.id}-${dateStr}`)
                      return (
                        <td
                          key={dateStr}
                          className={`border-b border-r border-warm-gray-200 w-8 h-8 text-center cursor-pointer transition-colors duration-75 select-none ${getColumnClass(date)} ${
                            requestType === 'day_off'
                              ? 'bg-brand-100 hover:bg-brand-200'
                              : requestType === 'paid_leave'
                                ? 'bg-orange-50 hover:bg-orange-100'
                                : 'hover:bg-warm-gray-100'
                          } ${isSaving ? 'opacity-50' : ''}`}
                          onClick={() => toggleShiftRequest(member.id, dateStr)}
                        >
                          {requestType && (
                            <div className="flex items-center justify-center">
                              <div className={`w-2 h-2 rounded-full ${
                                requestType === 'paid_leave' ? 'bg-orange-500' : 'bg-brand-500'
                              }`} />
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
        <h2 className="text-base font-semibold text-warm-gray-800">小児科医スケジュール</h2>

        <div className="overflow-x-auto rounded-2xl soft-shadow-md bg-white">
          <table className="border-collapse text-xs">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-brand-50/60 border-b border-r border-warm-gray-200 px-3 py-2 text-left font-medium text-brand-800 min-w-[100px]">
                  日付
                </th>
                {dates.map((date) => {
                  const dateStr = formatDate(date)
                  return (
                    <th
                      key={dateStr}
                      className={`border-b border-r border-warm-gray-200 px-0 py-1 text-center font-normal w-8 min-w-[2rem] ${getColumnClass(date)}`}
                    >
                      <div className="text-[11px] leading-tight text-warm-gray-700">{date.getDate()}</div>
                      <div className={`text-[10px] leading-tight ${getHeaderTextClass(date)}`}>
                        {getDayLabel(date)}
                      </div>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              <tr className="hover:bg-brand-50/30">
                <td className="sticky left-0 z-10 bg-white border-b border-r border-warm-gray-200 px-3 py-1.5 font-medium text-warm-gray-700 whitespace-nowrap">
                  小児科医
                </td>
                {dates.map((date) => {
                  const dateStr = formatDate(date)
                  const isActive = pediatricDates.has(dateStr)
                  const isSaving = savingCells.has(`ped-${dateStr}`)
                  return (
                    <td
                      key={dateStr}
                      className={`border-b border-r border-warm-gray-200 w-8 h-8 text-center cursor-pointer transition-colors duration-75 select-none ${getColumnClass(date)} ${
                        isActive
                          ? 'bg-sage-100 hover:bg-sage-200'
                          : 'hover:bg-warm-gray-100'
                      } ${isSaving ? 'opacity-50' : ''}`}
                      onClick={() => togglePediatric(dateStr)}
                    >
                      {isActive && (
                        <div className="flex items-center justify-center">
                          <div className="w-2 h-2 rounded-full bg-sage-500" />
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
