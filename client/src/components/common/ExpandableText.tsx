import { useState } from 'react'
import { Link } from '@mui/material'

type ExpandableTextProps = {
  text: string
  suffix?: React.ReactNode
  maxLength?: number
}

export function ExpandableText({ text, suffix, maxLength = 300 }: ExpandableTextProps) {
  const [expanded, setExpanded] = useState(false)

  const isLong = text.length > maxLength
  const truncated = text.slice(0, maxLength)
  const displayText =
    expanded || !isLong ? text : truncated.slice(0, truncated.lastIndexOf(' ')) + '...'
  return (
    <>
      {displayText}
      {suffix && (expanded || !isLong) && <> {suffix} </>}
      {isLong && (
        <Link component="button" onClick={() => setExpanded((prev) => !prev)} underline="hover">
          {expanded ? 'Show less' : 'Show more'}
        </Link>
      )}
    </>
  )
}
