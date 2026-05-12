import { Typography } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

export default function DownloadsPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        Data Downloads
      </Typography>

      <Typography>
        We intend to provide timestamped snapshots of aggregated MetaKB assertions. At this time,
        however, public data downloads are unavailable.
      </Typography>
    </DocsLayout>
  )
}
