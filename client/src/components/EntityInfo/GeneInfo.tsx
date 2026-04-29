import { Box, Chip, Link, Typography } from '@mui/material'
import { MappableConcept } from '../../models/domain'
import { generateUrlForId } from '../../utils/externalLinks'
import { ExpandableText } from '../common/ExpandableText'
import { InfoRow } from './EntityInfo'
import { getExtension } from '../../utils'

type GeneInfoProps = {
  data: MappableConcept
}

const GeneInfo = ({ data }: GeneInfoProps) => {
  const longName = getExtension<string>(data, 'approved_name') ?? ''
  const aliases = getExtension<string[]>(data, 'aliases') ?? []
  const sourcedDescription = getExtension<{
    description: string
    source: string
  }>(data, 'gene_description')
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
          <Chip label="Gene" />
        </Box>
      </Box>
      <InfoRow label="Full Name" show={!!longName}>
        {longName}
      </InfoRow>
      <InfoRow label="Aliases" show={aliases.length > 0}>
        <Typography>{aliases.join(', ')}</Typography>
      </InfoRow>
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

export default GeneInfo
