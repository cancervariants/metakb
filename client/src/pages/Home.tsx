import * as React from 'react'
import Header from '../components/Header'
import { Box, Button, Link, MenuItem, Select, TextField, Typography } from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import { useNavigate } from 'react-router-dom'

const HomePage = () => {
  const navigate = useNavigate()

  const [searchType, setSearchType] = React.useState('gene')
  const [searchQuery, setSearchQuery] = React.useState('')

  const doSearch = () => {
    if (!searchQuery.trim()) return
    navigate(`/search?${searchType}=${encodeURIComponent(searchQuery.trim())}`)
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') doSearch()
  }

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
                  {/* TODO: other types of variant searches? */}
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
