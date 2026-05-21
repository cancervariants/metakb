import { Typography, Box, Divider, Link, IconButton, Grid } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'
import EmailIcon from '@mui/icons-material/Email'

// TODO: Move this to an external component and import
function TeamMember({
  name,
  role,
  affiliation,
  email,
}: {
  name: string
  role: string
  affiliation: string
  email: string
}) {
  return (
    <Box sx={{ py: 1.5 }}>
      <Typography variant="h6" fontWeight={600}>
        {name}
      </Typography>

      <Typography variant="body1">{role}</Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 0 }}>
        {affiliation}
      </Typography>

      <IconButton component={Link} href={`mailto:${email}`} size="small" sx={{ p: 0 }}>
        <EmailIcon />
      </IconButton>
    </Box>
  )
}

export default function TeamPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        Development Team
      </Typography>

      <Typography component="p" sx={{ mb: 2 }}>
        MetaKB Jr is maintained by contributors focused on improving interoperability and
        accessibility for cancer genomics knowledge resources.
      </Typography>
      <Typography component="p" sx={{ mb: 2 }}>
        The project combines expertise in:
      </Typography>

      <Box component="ul" sx={{ pl: 4, mt: 0 }}>
        <li>
          <Typography>Cancer genomics</Typography>
        </li>

        <li>
          <Typography>Bioinformatics</Typography>
        </li>

        <li>
          <Typography>Clinical variant classification</Typography>
        </li>

        <li>
          <Typography>Open-source software engineering</Typography>
        </li>
      </Box>
      <Divider sx={{ my: 4 }} />
      <Typography variant="h4" mb={2} fontWeight="bold">
        Current Contributors
      </Typography>

      <Grid container spacing={1}>
        <Grid size={{ xs: 1, md: 5 }}>
          <TeamMember
            name="Alex Wagner"
            role="Creator, Project Leader"
            affiliation="Nationwide Children's Hospital"
            email="Alex.Wagner@nationwidechildrens.org"
          />
        </Grid>

        <Grid size={{ xs: 1, md: 5 }}>
          <TeamMember
            name="Brian Walsh"
            role="Project Leader"
            affiliation="Oregon Health & Science University"
            email="fill in"
          />
        </Grid>

        <Grid size={{ xs: 1, md: 5 }}>
          <TeamMember
            name="Xuelu (Jeff) Liu"
            role="Project Leader"
            affiliation="Dana-Farber Cancer Institute"
            email="fill in"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="Matthew Cannon"
            role="Bioinformatics Scientist"
            affiliation="Nationwide Children's Hospital"
            email="Matthew.Cannon2@nationwidechildrens.org"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="James Stevenson"
            role="Software Developer"
            affiliation="Nationwide Children's Hospital"
            email="James.Stevenson@nationwidechildrens.org"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="Kathryn Perry"
            role="Software Developer"
            affiliation="Nationwide Children's Hospital"
            email="Kathryn.Stahl@nationwidechildrens.org"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="Anastasia Bratulin"
            role="Graduate Student"
            affiliation="Nationwide Children's Hospital"
            email="Anastasia.Bratulin@nationwidechildrens.org"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="Daniel Puthawala"
            role="Post-Doctoral Scientist"
            affiliation="Nationwide Children's Hospital"
            email="Daniel.Puthawala@nationwidechildrens.org"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="Heather Costello"
            role="Bioinformatics Scientist"
            affiliation="Nationwide Children's Hospital"
            email="Heather.Costello@nationwidechildrens.org"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="Kathleen Schieffer"
            role="Clinical Director"
            affiliation="Nationwide Children's Hospital"
            email=""
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="Wesley Goar"
            role="Bioinformatics Scientist"
            affiliation="Nationwide Children's Hospital"
            email="Wesley.Goar@nationwidechildrens.org"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <TeamMember
            name="Kori Kuzma"
            role="Software Developer"
            affiliation="Nationwide Children's Hospital"
            email="Kori.Kuzma@nationwidechildrens.org"
          />
        </Grid>
      </Grid>
    </DocsLayout>
  )
}
