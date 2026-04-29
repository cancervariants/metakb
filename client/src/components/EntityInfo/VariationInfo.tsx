import { Box, Chip, Link, Typography } from '@mui/material'
import { CategoricalVariant } from '../../models/domain'
import { InfoRow } from './EntityInfo'
import { generateUrlForId } from '../../utils/externalLinks'
import { getExtension } from '../../utils'
import { ExpandableText } from '../common/ExpandableText'

type VariantInfoProps = {
  data: CategoricalVariant
}

const VariationInfo = ({ data }: VariantInfoProps) => {
  const sourcedDescription = getExtension<{
    description: string
    source: string
  }>(data, 'variation_description')
  let cleanDescription: string | null = null
  let descriptionSource: string | null = null
  let descriptionUrl: string | null = null
  if (sourcedDescription) {
    cleanDescription = sourcedDescription.description.replace(/\s*\[[^\]]+\]\s*$/, '')
    descriptionSource = sourcedDescription.source
    descriptionUrl = generateUrlForId(descriptionSource)
  }

  const externalLinks =
    data.mappings
      ?.map((m) => {
        const url = generateUrlForId(m.coding.id)
        return url ? { conceptId: m.coding.id, url } : null
      })
      .filter((x): x is { conceptId: string; url: string } => x !== null) ?? []

  return (
    <Box id="results-info-container" sx={{ backgroundColor: 'white', padding: 5, borderRadius: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <Box>
          <Typography variant="h4" mb={2} fontWeight="bold">
            {data.name}
          </Typography>
        </Box>
        <Box>
          <Chip label="Variation" />
        </Box>
      </Box>
      <InfoRow label="Description" show={!!sourcedDescription}>
        {' '}
        <ExpandableText
          text={cleanDescription}
          suffix={
            <Link href={descriptionUrl} target="_blank" rel="noopener noreferrer">
              [Source]
            </Link>
          }
        />
      </InfoRow>

      <InfoRow label="External Resources" show={externalLinks.length > 0}>
        {' '}
        {externalLinks.map((link, idx) => (
          <span key={link.conceptId}>
            <Link href={link.url} target="_blank" rel="noopener noreferrer">
              {link.conceptId} ↗
            </Link>
            {idx < externalLinks.length - 1 && ', '}
          </span>
        ))}
      </InfoRow>
    </Box>
  )
}

export default VariationInfo
