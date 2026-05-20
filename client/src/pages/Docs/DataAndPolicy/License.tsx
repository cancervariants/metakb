import { Typography } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

export default function LicensePage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        Data Licensing
      </Typography>
    
    <Typography component="p" sx={{ mb: 2 }}>MetaKB Jr software, documentation, and derived datasets are distributed under open-source and open-data principles whenever possible.</Typography>

    <Typography component="p" sx={{ mb: 2 }}>However, individual integrated resources may have separate licensing terms that users must respect.
    </Typography>

    <Typography component="p" sx={{ mb: 2 }}>Users are responsible for reviewing and complying with the licenses of upstream data providers before redistribution or commercial use.

    </Typography>


      <Typography></Typography>
    </DocsLayout>
  )
}
