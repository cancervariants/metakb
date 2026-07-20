import { Box, Tooltip, useTheme } from '@mui/material'
import { Cell, Pie, PieChart } from 'recharts'

import { EvidenceLevel } from '../../models/codings'
import { getEvidenceGrade } from '../../utils/results'
import { AssertionResult } from '../../utils'

interface EvidenceSummaryCellProps {
  value: AssertionResult
}

export function EvidenceSummaryCell({ value }: EvidenceSummaryCellProps) {
  const theme = useTheme()
  const supportingEvidence = value.grouped_evidence

  const counts = supportingEvidence.reduce<Record<EvidenceLevel, number>>(
    (acc, evidence) => {
      const code = getEvidenceGrade(evidence.strengthOfEvidenceProvided)

      if (code && Object.values(EvidenceLevel).includes(code as EvidenceLevel)) {
        acc[code as EvidenceLevel] += 1
      }

      return acc
    },
    { A: 0, B: 0, C: 0, D: 0, E: 0 },
  )

  const data = Object.entries(counts)
    .filter(([, count]) => count > 0)
    .map(([level, count]) => ({
      name: level as EvidenceLevel,
      value: count,
    }))

  const levelColor = theme.palette.evidence
  return (
    <Box id="evidence-level-container" display="flex" flexDirection="row">
      <Tooltip
        arrow
        followCursor
        enterDelay={100}
        title={
          <Box id="evidence-level-breakdown-tooltip">
            {data.map((d) => (
              <div key={d.name}>
                {d.name}: {d.value}
              </div>
            ))}
          </Box>
        }
      >
        <Box
          sx={{
            position: 'relative',
            width: 40,
            height: 40,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            paddingRight: '10px',
          }}
        >
          <PieChart width={40} height={40}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={12}
              outerRadius={20}
              paddingAngle={2}
              label={false}
              animationDuration={200}
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={levelColor[entry.name]} />
              ))}
            </Pie>
          </PieChart>

          <Box
            sx={{
              position: 'absolute',
              fontSize: 12,
              fontWeight: 600,
              pointerEvents: 'none',
              color: theme.palette.text.primary,
            }}
          >
            {value.evidence_level}
          </Box>
        </Box>
      </Tooltip>
      <Box display="flex" flexDirection="column" justifyContent="space-between">
        <Box sx={{ fontSize: 12, color: theme.palette.text.secondary }}>
          {supportingEvidence.length} {`record${supportingEvidence.length === 1 ? '' : 's'}`}
        </Box>
        <Box sx={{ fontSize: 12, color: theme.palette.text.secondary }}>{value.direction}</Box>
      </Box>
    </Box>
  )
}
