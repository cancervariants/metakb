import { scaleLinear, scaleBand } from '@visx/scale'
import { HeatmapRect } from '@visx/heatmap'
import { Group } from '@visx/group'
import { AxisBottom, AxisLeft } from '@visx/axis'
import { useTooltip, Tooltip, defaultStyles as tooltipStyles } from '@visx/tooltip'

import { buildVariantDiseaseMatrix, type NormalizedResult } from '../../utils'

interface Props {
  data: NormalizedResult[]
  width?: number
  height?: number
}

export function VariantDiseaseHeatmap({ data, width = 1000, height = 700 }: Props) {
  const { rows, variants, diseases } = buildVariantDiseaseMatrix(data)

  const margin = { top: 20, bottom: 120, left: 160, right: 20 }

  const xMax = width - margin.left - margin.right
  const yMax = height - margin.top - margin.bottom

  // Flatten all evidence counts for color scale domain
  const allCounts = rows.flatMap((r) => r.bins.map((b) => b.count))
  const maxVal = Math.max(...allCounts)

  const xScale = scaleBand<number>({
    domain: diseases.map((_, i) => i), // columns index
    range: [0, xMax],
    padding: 0.05,
  })

  const yScale = scaleBand<number>({
    domain: variants.map((_, i) => i), // rows index
    range: [0, yMax],
    padding: 0.05,
  })

  const colorScale = scaleLinear({
    domain: [0, maxVal],
    range: ['#e0f2fe', '#0c4a6e'], // light blue → dark blue
  })

  const { tooltipData, tooltipLeft, tooltipTop, showTooltip, hideTooltip } = useTooltip()

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height}>
        <Group top={margin.top} left={margin.left}>
          <HeatmapRect
            data={rows}
            xScale={xScale}
            yScale={yScale}
            colorScale={colorScale}
            binWidth={xScale.bandwidth()}
            binHeight={yScale.bandwidth()}
            gap={2}
          >
            {(heatmapData) =>
              heatmapData.map((rowCells, rowIndex) =>
                rowCells.map((cell, colIndex) => {
                  const value = cell.bin.count

                  if (value === 0) return null

                  return (
                    <rect
                      key={`${rowIndex}-${colIndex}`}
                      x={cell.x}
                      y={cell.y}
                      width={cell.width}
                      height={cell.height}
                      fill={colorScale(value)}
                      onMouseEnter={() =>
                        showTooltip({
                          tooltipLeft: cell.x + margin.left,
                          tooltipTop: cell.y + margin.top,
                          tooltipData: {
                            value,
                            variant: variants[rowIndex],
                            disease: diseases[colIndex],
                          },
                        })
                      }
                      onMouseLeave={hideTooltip}
                    />
                  )
                }),
              )
            }
          </HeatmapRect>

          <AxisLeft
            scale={yScale}
            tickFormat={(i) => diseases[i]}
            tickValues={diseases.map((_, i) => i)}
            tickLabelProps={() => ({
              fontSize: 11,
              textAnchor: 'end',
              dy: '0.33em',
            })}
          />

          <AxisBottom
            scale={xScale}
            top={yMax}
            tickFormat={(i) => variants[i]}
            tickValues={variants.map((_, i) => i)}
            tickLabelProps={() => ({
              fontSize: 11,
              angle: -45,
              textAnchor: 'end',
            })}
          />
        </Group>
      </svg>

      {tooltipData ? (
        <Tooltip top={tooltipTop} left={tooltipLeft} style={tooltipStyles}>
          <strong>{tooltipData.variant}</strong> → <strong>{tooltipData.disease}</strong>
          <div>{tooltipData.count} supporting evidence</div>
        </Tooltip>
      ) : null}
    </div>
  )
}
