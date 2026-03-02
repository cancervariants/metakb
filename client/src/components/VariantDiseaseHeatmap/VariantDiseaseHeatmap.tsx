import { scaleLinear, scaleBand } from '@visx/scale'
import { HeatmapRect } from '@visx/heatmap'
import { Group } from '@visx/group'
import { AxisBottom, AxisLeft } from '@visx/axis'
import { useTooltip, Tooltip, defaultStyles as tooltipStyles } from '@visx/tooltip'
import { NormalizedResult, buildVariantDiseaseMatrix } from '../../utils'

interface Props {
  data: NormalizedResult[]
  width?: number
  height?: number
  limitRows?: number
  limitCols?: number
}

export function VariantDiseaseHeatmap({
  data,
  width = 450,
  height = 300,
  limitRows,
  limitCols,
}: Props) {
  const { columns, variants, diseases } = buildVariantDiseaseMatrix(data, limitRows, limitCols)

  const margin = { top: 20, bottom: 120, left: 165, right: 20 }

  const xMax = width - margin.left - margin.right
  const yMax = height - margin.top - margin.bottom

  const allCounts = columns.flatMap((c) => c.bins.map((b) => b.count))
  const maxVal = Math.max(...allCounts, 0)

  const xScale = scaleBand<number>({
    domain: diseases.map((_, i) => i), // columns = diseases
    range: [0, xMax],
    padding: 0.05,
  })

  const yScale = scaleBand<number>({
    domain: variants.map((_, i) => i), // rows = variants
    range: [0, yMax],
    padding: 0.05,
  })

  const colorScale = scaleLinear({
    domain: [0, maxVal],
    range: ['#e0f2fe', '#0c4a6e'],
  })

  const { tooltipData, tooltipLeft, tooltipTop, showTooltip, hideTooltip } = useTooltip<{
    value: number
    variant: string
    disease: string
  }>()

  // don't display heatmap if there's only one cell
  if (variants.length == 1 && diseases.length == 1) {
    return <></>
  }

  function truncateLabel(label: string, maxLength = 20) {
    return label.length > maxLength ? label.slice(0, maxLength) + '…' : label
  }

  // must appease Typescript overlords
  const x = (i: number) => xScale(i)!
  const y = (i: number) => yScale(i)!

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height}>
        <Group top={margin.top} left={margin.left}>
          <HeatmapRect
            data={columns}
            xScale={x}
            yScale={y}
            colorScale={colorScale}
            binWidth={xScale.bandwidth()}
            binHeight={yScale.bandwidth()}
            gap={2}
          >
            {(heatmapData) =>
              heatmapData.map((columnCells, columnIndex) =>
                columnCells.map((cell, rowIndex) => {
                  const cellBin = cell.bin as { count: number }
                  const value = cellBin.count
                  if (value === 0) return null

                  return (
                    <rect
                      key={`${columnIndex}-${rowIndex}`}
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
                            disease: diseases[columnIndex],
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

          {/* Y axis: variants (rows) */}
          <AxisLeft
            scale={yScale}
            tickFormat={(i) => truncateLabel(variants[i])}
            tickValues={variants.map((_, i) => i)}
            tickLabelProps={() => ({
              fontSize: 11,
              textAnchor: 'end',
              dy: '0.33em',
            })}
          />

          {/* X axis: diseases (columns) */}
          <AxisBottom
            scale={xScale}
            top={yMax}
            tickFormat={(i) => truncateLabel(diseases[i])}
            tickValues={diseases.map((_, i) => i)}
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
          <div>
            {tooltipData.value} evidence {`item${tooltipData.value > 1 ? 's' : ''}`}
          </div>
        </Tooltip>
      ) : null}
    </div>
  )
}
