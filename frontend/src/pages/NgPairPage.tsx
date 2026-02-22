import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import { membersApi } from '@/api/fetcher'
import { ngPairsApi } from '@/api/fetcher'
import type { MemberResponse, NgPairResponse } from '@/api/constants'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Skeleton } from '@/components/ui/skeleton'

function formatDate(iso: string): string {
  const d = new Date(iso)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}/${m}/${day}`
}

export function NgPairPage() {
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [ngPairs, setNgPairs] = useState<NgPairResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [member1, setMember1] = useState<string>('')
  const [member2, setMember2] = useState<string>('')
  const [adding, setAdding] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<NgPairResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const [membersData, pairsData] = await Promise.all([
        membersApi.list(),
        ngPairsApi.list(),
      ])
      setMembers(membersData)
      setNgPairs(pairsData)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'データの取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleAdd = useCallback(async () => {
    if (!member1 || !member2) return
    try {
      setAdding(true)
      await ngPairsApi.create({
        member_id_1: Number(member1),
        member_id_2: Number(member2),
      })
      setMember1('')
      setMember2('')
      toast.success('NGペアを追加しました')
      await fetchData()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'NGペアの追加に失敗しました')
    } finally {
      setAdding(false)
    }
  }, [member1, member2, fetchData])

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return
    try {
      setDeleting(true)
      await ngPairsApi.delete(deleteTarget.id)
      setDeleteTarget(null)
      toast.success('NGペアを削除しました')
      await fetchData()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'NGペアの削除に失敗しました')
    } finally {
      setDeleting(false)
    }
  }, [deleteTarget, fetchData])

  const member2Options = members.filter(
    (m) => m.id !== Number(member1),
  )

  const canAdd = member1 !== '' && member2 !== '' && member1 !== member2

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-warm-gray-900">
          NGペア管理
        </h1>
        <p className="text-sm text-warm-gray-400 mt-1">
          同じシフトに入れないメンバーの組み合わせを管理します
        </p>
      </div>

      <div className="flex items-end gap-3 rounded-2xl border-0 soft-shadow-md bg-white p-4">
        <div className="flex-1 space-y-1.5">
          <label className="text-sm font-medium text-warm-gray-700">メンバー1</label>
          <Select value={member1} onValueChange={setMember1}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="メンバーを選択" />
            </SelectTrigger>
            <SelectContent>
              {members.map((m) => (
                <SelectItem key={m.id} value={String(m.id)}>
                  {m.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 space-y-1.5">
          <label className="text-sm font-medium text-warm-gray-700">メンバー2</label>
          <Select
            value={member2}
            onValueChange={setMember2}
            disabled={!member1}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="メンバーを選択" />
            </SelectTrigger>
            <SelectContent>
              {member2Options.map((m) => (
                <SelectItem key={m.id} value={String(m.id)}>
                  {m.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          onClick={handleAdd}
          disabled={!canAdd || adding}
          className="shrink-0 bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 shadow-sm"
        >
          {adding ? '追加中...' : '追加'}
        </Button>
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : (
        <div className="rounded-2xl border-0 soft-shadow-md bg-white animate-in fade-in">
          <Table>
            <TableHeader>
              <TableRow className="bg-brand-50/60">
                <TableHead className="font-semibold text-brand-800">メンバー1</TableHead>
                <TableHead className="font-semibold text-brand-800">メンバー2</TableHead>
                <TableHead className="font-semibold text-brand-800">登録日</TableHead>
                <TableHead className="font-semibold text-brand-800 text-right">アクション</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ngPairs.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="h-24 text-center text-warm-gray-500"
                  >
                    NGペアが登録されていません
                  </TableCell>
                </TableRow>
              ) : (
                ngPairs.map((pair) => (
                  <TableRow key={pair.id} className="hover:bg-brand-50/30">
                    <TableCell className="text-warm-gray-900">{pair.member_name_1}</TableCell>
                    <TableCell className="text-warm-gray-900">{pair.member_name_2}</TableCell>
                    <TableCell className="text-warm-gray-600">{formatDate(pair.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => setDeleteTarget(pair)}
                      >
                        削除
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}

      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>NGペアを削除しますか？</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteTarget && (
                <>
                  {deleteTarget.member_name_1} と {deleteTarget.member_name_2} のNGペアを削除します。この操作は取り消せません。
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>キャンセル</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-error hover:bg-error/90"
            >
              {deleting ? '削除中...' : '削除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
