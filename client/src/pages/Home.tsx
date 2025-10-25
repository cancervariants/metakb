import * as React from 'react'
import Header from '../components/Header'
import { Box, Button, Link, MenuItem, Select, TextField, Typography } from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'

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
        const res = await fetch(`/api/v2/stats`, {
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
    <>
      <Header />
      <main>
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
            mb={2}
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
              mb={6}
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

          <Box id="search-container" mb={50}>
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
        </Box>
      </main>
    </>
  )
}

export default HomePage
