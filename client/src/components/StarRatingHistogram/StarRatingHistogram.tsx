import { Typography, useTheme } from '@mui/material'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AssertionResult } from '../../utils'

interface Props {
  data: AssertionResult[]
}

export function StarRatingHistogram({ data }: Props) {
  const theme = useTheme()

  const starCounts = data.reduce(
    (acc, result) => {
      const rating = result.star_rating.starRating

      if (rating >= 1 && rating <= 4) {
        acc[rating] += 1
      }

      return acc
    },
    { 1: 0, 2: 0, 3: 0, 4: 0 } as Record<number, number>,
  )
  const chartData = Object.entries(starCounts).map(([stars, count]) => ({
    stars: `${stars}★`,
    count,
  }))

  const axisTextStyle = {
    fill: theme.palette.text.primary,
    fontFamily: theme.typography.fontFamily,
    fontSize: Number(theme.typography.body2.fontSize) || 14,
  }

  const axisLabelStyle = {
    ...axisTextStyle,
    fontSize: Number(theme.typography.body1.fontSize) || 14,
    fontWeight: theme.typography.fontWeightMedium,
  }

  const axisLineStyle = {
    stroke: theme.palette.text.primary,
  }

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        maxWidth: 560,
        height: 260,
        marginBottom: 24,
        marginInline: 'auto',
      }}
    >
      <Typography
        variant="subtitle2"
        fontWeight="bold"
        align="center"
        sx={{ mb: 1, color: theme.palette.text.primary }}
      >
        Assertions by Star Rating
      </Typography>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 16, left: 24, bottom: 24 }}>
          <XAxis
            dataKey="stars"
            tick={axisTextStyle}
            axisLine={axisLineStyle}
            tickLine={axisLineStyle}
            label={{
              value: 'Star Rating',
              position: 'insideBottom',
              offset: -10,
              style: axisLabelStyle,
            }}
          />
          <YAxis
            allowDecimals={false}
            tick={axisTextStyle}
            axisLine={axisLineStyle}
            tickLine={axisLineStyle}
            label={{
              value: '# of assertions',
              angle: -90,
              position: 'insideLeft',
              style: axisLabelStyle,
            }}
          />
          <Tooltip />
          <Bar dataKey="count" fill="#0c4a6e" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
