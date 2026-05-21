import { Typography, Box, Stack, Link, Divider } from '@mui/material'
import DocsLayout from '../../../components/docs/DocsLayout/DocsLayout'

// TODO: Make this an external component and import it
export default function PublicationsPage() {
  return (
    <DocsLayout>
      <Typography variant="h4" mb={2} fontWeight="bold">
        Publications
      </Typography>

      <Typography component="p" sx={{ mb: 2 }}>
  MetaKB Jr builds upon prior work in cancer knowledge aggregation, clinical
  interpretation standards, and biomedical data harmonization. While there is
  not yet a dedicated MetaKB Jr publication, this project extends concepts and
  infrastructure developed through our previous work. Publications, technical
  details, and related resources will be added here as the project evolves.
      </Typography>

      <Stack spacing={3} sx={{ mt: 3 }}>
        <Box>
          <Typography
            component={Link}
            href="https://www.nature.com/articles/s41588-020-0603-8"
            target="_blank"
            rel="noopener"
            variant="h6"
            sx={{ textDecoration: 'none' }}
          >
            A harmonized meta-knowledgebase of clinical interpretations of somatic genomic variants
            in cancer
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Nature Genetics
          </Typography>

          <Typography variant="body2" sx={{ mt: 1 }}>
            Wagner, A.H., Walsh, B., Mayfield, G. et al. A harmonized meta-knowledgebase of clinical
            interpretations of somatic genomic variants in cancer. <i>Nat Genet</i> 52, 448–457
            (2020). https://doi.org/10.1038/s41588-020-0603-8
          </Typography>
        </Box>

        <Divider />

        <Box>
          <Typography
            component={Link}
            href="https://www.sciencedirect.com/science/article/pii/S2666979X21000343"
            target="_blank"
            rel="noopener"
            variant="h6"
            sx={{ textDecoration: 'none' }}
          >
            The GA4GH Variation Representation Specification: A computational framework for
            variation representation and federated identification
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Cell Genomics
          </Typography>

          <Typography variant="body2" sx={{ mt: 1 }}>
            Wagner AH, Babb L, Alterovitz G, Baudis M, Brush M, Cameron DL, Cline M, Griffith M,
            Griffith OL, Hunt SE, Kreda D, Lee JM, Li S, Lopez J, Moyer E, Nelson T, Patel RY,
            Riehle K, Robinson PN, Rynearson S, Schuilenburg H, Tsukanov K, Walsh B, Konopko M, Rehm
            HL, Yates AD, Freimuth RR, Hart RK. The GA4GH Variation Representation Specification: A
            computational framework for variation representation and federated identification.{' '}
            <i>Cell Genom.</i> 2021 Nov 10;1(2):100027. doi: 10.1016/j.xgen.2021.100027. PMID:
            35311178; PMCID: PMC8929418.
          </Typography>
        </Box>

        <Divider />
      </Stack>
    </DocsLayout>
  )
}
