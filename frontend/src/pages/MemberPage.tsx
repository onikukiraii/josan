import { useState, useEffect, useCallback } from 'react'
import { membersApi } from '@/api/fetcher'
import type {
  MemberResponse,
  MemberCreateParams,
  Qualification,
  EmploymentType,
  CapabilityType,
} from '@/api/constants'
import {
  QUALIFICATION_LABEL,
  EMPLOYMENT_TYPE_LABEL,
  CAPABILITY_LABEL,
} from '@/api/constants'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'

const ALL_CAPABILITIES: CapabilityType[] = [
  'outpatient_leader',
  'ward_leader',
  'night_leader',
  'day_shift',
  'night_shift',
  'beauty',
  'mw_outpatient',
  'ward_staff',
  'rookie',
]

const QUALIFICATIONS: Qualification[] = ['nurse', 'associate_nurse', 'midwife']
const EMPLOYMENT_TYPES: EmploymentType[] = ['full_time', 'part_time']
const MAX_NIGHT_SHIFT_OPTIONS = [2, 3, 4]

interface FormState {
  name: string
  qualification: Qualification
  employment_type: EmploymentType
  max_night_shifts: number
  capabilities: CapabilityType[]
}

const INITIAL_FORM: FormState = {
  name: '',
  qualification: 'nurse',
  employment_type: 'full_time',
  max_night_shifts: 4,
  capabilities: [],
}

export function MemberPage() {
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingMember, setEditingMember] = useState<MemberResponse | null>(null)
  const [form, setForm] = useState<FormState>(INITIAL_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<MemberResponse | null>(null)

  const fetchMembers = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await membersApi.list()
      setMembers(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : '読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMembers()
  }, [fetchMembers])

  const openCreateDialog = useCallback(() => {
    setEditingMember(null)
    setForm(INITIAL_FORM)
    setDialogOpen(true)
  }, [])

  const openEditDialog = useCallback((member: MemberResponse) => {
    setEditingMember(member)
    setForm({
      name: member.name,
      qualification: member.qualification,
      employment_type: member.employment_type,
      max_night_shifts: member.max_night_shifts,
      capabilities: [...member.capabilities],
    })
    setDialogOpen(true)
  }, [])

  const handleSubmit = useCallback(async () => {
    if (!form.name.trim()) return

    try {
      setSubmitting(true)
      setError(null)

      const params: MemberCreateParams = {
        name: form.name.trim(),
        qualification: form.qualification,
        employment_type: form.employment_type,
        max_night_shifts: form.max_night_shifts,
        capabilities: form.capabilities,
      }

      if (editingMember) {
        await membersApi.update(editingMember.id, params)
      } else {
        await membersApi.create(params)
      }

      setDialogOpen(false)
      await fetchMembers()
    } catch (e) {
      setError(e instanceof Error ? e.message : '保存に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }, [form, editingMember, fetchMembers])

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return

    try {
      setError(null)
      await membersApi.delete(deleteTarget.id)
      setDeleteTarget(null)
      await fetchMembers()
    } catch (e) {
      setError(e instanceof Error ? e.message : '削除に失敗しました')
      setDeleteTarget(null)
    }
  }, [deleteTarget, fetchMembers])

  const handleCopy = useCallback(async (member: MemberResponse) => {
    try {
      setError(null)
      await membersApi.create({
        name: `${member.name}（コピー）`,
        qualification: member.qualification,
        employment_type: member.employment_type,
        max_night_shifts: member.max_night_shifts,
        capabilities: [...member.capabilities],
      })
      await fetchMembers()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'コピーに失敗しました')
    }
  }, [fetchMembers])

  const toggleCapability = useCallback((cap: CapabilityType) => {
    setForm(prev => ({
      ...prev,
      capabilities: prev.capabilities.includes(cap)
        ? prev.capabilities.filter(c => c !== cap)
        : [...prev.capabilities, cap],
    }))
  }, [])

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-warm-gray-900">
            メンバー管理
          </h1>
          <p className="mt-1 text-sm text-warm-gray-500">
            スタッフの登録・編集・削除を行います
          </p>
        </div>
        <Button onClick={openCreateDialog} className="bg-brand-600 hover:bg-brand-700">
          新規登録
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading ? (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[140px]">名前</TableHead>
                <TableHead className="w-[100px]">職能</TableHead>
                <TableHead className="w-[100px]">雇用形態</TableHead>
                <TableHead className="w-[100px]">夜勤上限</TableHead>
                <TableHead>能力</TableHead>
                <TableHead className="w-[180px] text-right">アクション</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-10" /></TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Skeleton className="h-5 w-14" />
                      <Skeleton className="h-5 w-14" />
                      <Skeleton className="h-5 w-14" />
                    </div>
                  </TableCell>
                  <TableCell><Skeleton className="ml-auto h-8 w-24" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : members.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-warm-gray-500">
          <p className="text-lg font-medium">メンバーが登録されていません</p>
          <p className="mt-1 text-sm">「新規登録」ボタンからスタッフを追加してください</p>
        </div>
      ) : (
        <div className="rounded-lg border shadow-sm">
          <Table>
            <TableHeader>
              <TableRow className="bg-warm-gray-50/80">
                <TableHead className="w-[140px] font-semibold text-warm-gray-700">名前</TableHead>
                <TableHead className="w-[100px] font-semibold text-warm-gray-700">職能</TableHead>
                <TableHead className="w-[100px] font-semibold text-warm-gray-700">雇用形態</TableHead>
                <TableHead className="w-[100px] font-semibold text-warm-gray-700">夜勤上限</TableHead>
                <TableHead className="font-semibold text-warm-gray-700">能力</TableHead>
                <TableHead className="w-[180px] text-right font-semibold text-warm-gray-700">アクション</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.map(member => (
                <TableRow
                  key={member.id}
                  className="transition-colors hover:bg-brand-50/50"
                >
                  <TableCell className="font-medium text-warm-gray-900">
                    {member.name}
                  </TableCell>
                  <TableCell className="text-warm-gray-600">
                    {QUALIFICATION_LABEL[member.qualification]}
                  </TableCell>
                  <TableCell className="text-warm-gray-600">
                    {EMPLOYMENT_TYPE_LABEL[member.employment_type]}
                  </TableCell>
                  <TableCell className="text-warm-gray-600">
                    {member.max_night_shifts}回
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {[...member.capabilities].sort((a, b) => ALL_CAPABILITIES.indexOf(a) - ALL_CAPABILITIES.indexOf(b)).map(cap => (
                        <Badge
                          key={cap}
                          variant="secondary"
                          className="bg-brand-50 text-xs text-brand-700 hover:bg-brand-100"
                        >
                          {CAPABILITY_LABEL[cap]}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(member)}
                        className="text-warm-gray-600 hover:text-brand-600"
                      >
                        編集
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(member)}
                        className="text-warm-gray-600 hover:text-brand-600"
                      >
                        コピー
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteTarget(member)}
                        className="text-warm-gray-600 hover:text-error"
                      >
                        削除
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <p className="text-right text-sm text-warm-gray-400">
        {!loading && `${members.length} 名登録済み`}
      </p>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-warm-gray-900">
              {editingMember ? 'メンバー編集' : 'メンバー新規登録'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-5 py-4">
            <div className="space-y-2">
              <Label htmlFor="member-name" className="text-warm-gray-700">
                名前
              </Label>
              <Input
                id="member-name"
                value={form.name}
                onChange={e => setForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="スタッフ名を入力"
                className="focus-visible:ring-brand-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-warm-gray-700">職能</Label>
                <Select
                  value={form.qualification}
                  onValueChange={(v: Qualification) =>
                    setForm(prev => ({ ...prev, qualification: v }))
                  }
                >
                  <SelectTrigger className="focus:ring-brand-500">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {QUALIFICATIONS.map(q => (
                      <SelectItem key={q} value={q}>
                        {QUALIFICATION_LABEL[q]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-warm-gray-700">雇用形態</Label>
                <Select
                  value={form.employment_type}
                  onValueChange={(v: EmploymentType) =>
                    setForm(prev => ({ ...prev, employment_type: v }))
                  }
                >
                  <SelectTrigger className="focus:ring-brand-500">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EMPLOYMENT_TYPES.map(et => (
                      <SelectItem key={et} value={et}>
                        {EMPLOYMENT_TYPE_LABEL[et]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-warm-gray-700">夜勤上限（月あたり）</Label>
              <Select
                value={String(form.max_night_shifts)}
                onValueChange={v =>
                  setForm(prev => ({ ...prev, max_night_shifts: Number(v) }))
                }
              >
                <SelectTrigger className="w-[120px] focus:ring-brand-500">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MAX_NIGHT_SHIFT_OPTIONS.map(n => (
                    <SelectItem key={n} value={String(n)}>
                      {n}回
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label className="text-warm-gray-700">能力</Label>
              <div className="grid grid-cols-3 gap-3">
                {ALL_CAPABILITIES.map(cap => (
                  <div key={cap} className="flex items-center space-x-2">
                    <Checkbox
                      id={`cap-${cap}`}
                      checked={form.capabilities.includes(cap)}
                      onCheckedChange={() => toggleCapability(cap)}
                      className="data-[state=checked]:border-brand-600 data-[state=checked]:bg-brand-600"
                    />
                    <Label
                      htmlFor={`cap-${cap}`}
                      className="cursor-pointer text-sm font-normal text-warm-gray-600"
                    >
                      {CAPABILITY_LABEL[cap]}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={submitting}
            >
              キャンセル
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={submitting || !form.name.trim()}
              className="bg-brand-600 hover:bg-brand-700"
            >
              {submitting ? '保存中...' : editingMember ? '更新' : '登録'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteTarget} onOpenChange={open => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>メンバーを削除しますか？</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteTarget && `「${deleteTarget.name}」を削除します。この操作は取り消せません。`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>キャンセル</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-error hover:bg-error/90"
            >
              削除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
