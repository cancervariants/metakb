import * as React from 'react'
import Header from '../components/Header'
import { Box, Button, Link, MenuItem, Select, TextField, Typography } from '@mui/material'
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch'
import SearchIcon from '@mui/icons-material/Search'
import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Footer from '../components/Footer'
import AutoStoriesIcon from '@mui/icons-material/AutoStories'

const HomePage = () => {
  const navigate = useNavigate()

  const [searchType, setSearchType] = useState('gene')
  const [searchQuery, setSearchQuery] = useState('')
  const [stats, setStats] = useState<{
    num_conditions: number
    num_documents: number
    num_genes: number
    num_statements: number
    num_therapeutics: number
    num_variations: number
  } | null>(null)

  const doSearch = () => {
    if (!searchQuery.trim()) return
    navigate(`/search?${searchType}=${encodeURIComponent(searchQuery.trim())}`)
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') doSearch()
  }

  useEffect(() => {
    const controller = new AbortController()

    const fetchStats = async () => {
      try {
        const res = await fetch(`/api/stats`, {
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal,
        })
        if (!res.ok) throw new Error('Failed to fetch stats')
        const data = await res.json()
        setStats(data)
      } catch {
        setStats(null)
      }
    }

    fetchStats()
    return () => controller.abort()
  }, [])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Box
          id="main-page-container"
          m={5}
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            backgroundColor: 'white',
            borderRadius: '5px',
          }}
        >
          <Typography
            variant="h5"
            color="primary"
            fontWeight="bold"
            mb={4}
            sx={{
              width: '50%',
              justifyContent: 'center',
              textAlign: 'center',
              mt: '50px',
              mb: '75px',
            }}
          >
            Search harmonized data across multiple genomic knowledgebases.
          </Typography>
          {stats && (
            <Box
              id="stats-container"
              display="flex"
              justifyContent="center"
              alignItems="center"
              flexWrap="wrap"
              gap={6}
              mb={10}
            >
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {stats.num_documents?.toLocaleString()}
                </Typography>
                <Typography variant="body1">Documents</Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {stats.num_genes?.toLocaleString()}
                </Typography>
                <Typography variant="body1">Genes</Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {stats.num_variations?.toLocaleString()}
                </Typography>
                <Typography variant="body1">Variations</Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {stats.num_conditions?.toLocaleString()}
                </Typography>
                <Typography variant="body1">Tumor Types</Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {stats.num_statements?.toLocaleString()}
                </Typography>
                <Typography variant="body1">Evidence Records</Typography>
              </Box>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {stats.num_therapeutics?.toLocaleString()}
                </Typography>
                <Typography variant="body1">Drugs</Typography>
              </Box>
            </Box>
          )}

          <Box id="search-container" mb={10}>
            <Select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              label="Search Type"
            >
              <MenuItem value="gene">Gene</MenuItem>
              <MenuItem value="variation">Variant</MenuItem>
            </Select>
            <TextField
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={onKeyDown}
            ></TextField>
            <Button variant="contained" color="secondary" sx={{ marginLeft: 1 }} onClick={doSearch}>
              <SearchIcon />
              Search
            </Button>
            <Box id="example-searches" display="flex" mt={1} gap={1}>
              <Typography>Examples: </Typography>
              {searchType === 'gene' && (
                <Box id="gene-example-searches" gap={1} display="flex">
                  <Link href="/search?gene=BRAF" rel="noreferrer">
                    <span>BRAF</span>
                  </Link>
                  <Link href="/search?gene=hgnc:427" rel="noreferrer">
                    <span>hgnc:427</span>
                  </Link>
                  <Link href="/search?gene=ncbigene:5290" rel="noreferrer">
                    <span>ncbigene:5290</span>
                  </Link>
                </Box>
              )}
              {searchType === 'variation' && (
                <Box id="gene-example-searches" gap={1} display="flex">
                  <Link href="/search?variation=BRAF%20V600E" rel="noreferrer">
                    <span>BRAF V600E</span>
                  </Link>
                  <Link href="/search?variation=NC_000007.13:g.55259515T>G" rel="noreferrer">
                    <span>{'NC_000007.13:g.55259515T>G'}</span>
                  </Link>
                </Box>
              )}
            </Box>
          </Box>
          <Box id="latest-updates-section" my={8} width="100%" maxWidth={800}>
            <Typography variant="h6" color="primary" mb={2}>
              Latest Updates
            </Typography>
            <Box sx={{ bgcolor: 'grey.100', borderRadius: 1, p: 2 }}>
              <Box display="flex" alignItems="center" mb={1}>
                <RocketLaunchIcon color="secondary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Version 2.0 now in early development — improved harmonization and search accuracy.
                </Typography>
              </Box>

              <Box display="flex" alignItems="center">
                <AutoStoriesIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  More data sources coming soon!
                </Typography>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>
      <Footer />
    </Box>
  )
}

export default HomePage
