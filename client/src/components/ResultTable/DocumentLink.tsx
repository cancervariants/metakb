import { Box, Link, Tooltip, Typography } from '@mui/material'
import type { DocumentReference } from '../../utils/documents'
interface DocumentLinkProps {
  reference: DocumentReference
  index: number
}

export function DocumentLink({ reference, index }: DocumentLinkProps) {
  return (
    <Tooltip
      arrow
      title={
        <Box>
          <Typography variant="body2" fontWeight={600}>
            {reference.header}
          </Typography>
          {reference.subheader && (
            <Typography variant="caption" color="inherit" display="block">
              {reference.subheader}
            </Typography>
          )}
        </Box>
      }
    >
      <Link href={reference.url} target="_blank" rel="noopener noreferrer">
        [{index + 1}]
      </Link>
    </Tooltip>
  )
}
