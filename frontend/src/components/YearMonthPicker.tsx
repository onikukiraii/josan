import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface YearMonthPickerProps {
  value: string
  onChange: (value: string) => void
}

export function YearMonthPicker({ value, onChange }: YearMonthPickerProps) {
  const [year, month] = value.split('-')

  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: 3 }, (_, i) => currentYear - 1 + i)
  const months = Array.from({ length: 12 }, (_, i) => i + 1)

  return (
    <div className="flex items-center gap-2">
      <Select
        value={year}
        onValueChange={(y) => onChange(`${y}-${month}`)}
      >
        <SelectTrigger className="w-24">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {years.map((y) => (
            <SelectItem key={y} value={String(y)}>
              {y}年
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select
        value={month}
        onValueChange={(m) => onChange(`${year}-${m}`)}
      >
        <SelectTrigger className="w-20">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {months.map((m) => (
            <SelectItem key={m} value={String(m).padStart(2, '0')}>
              {m}月
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
