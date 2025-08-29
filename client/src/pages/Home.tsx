import * as React from 'react'
import Header from '../components/Header'
import { Box, Button, InputLabel, MenuItem, Select, TextField, Typography } from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'

const HomePage = () => {
  const [searchType, setSearchType] = React.useState('')
  const [searchQuery, setSearchQuery] = React.useState('')

  return (
    <>
      <Header />
      <main style={{height: '90%'}}>
        <Box
          id="main-page-container"
          mx={5}
          sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', backgroundColor: 'white', height: '100%'}}
        >
          <Typography
            variant="h5"
            color="primary"
            fontWeight="bold"
            my={5}
            sx={{ width: '50%', justifyContent: 'center', textAlign: 'center' }}
          >
            Search harmonized data across multiple genomic knowledgebases.
          </Typography>
          <Box id="search-container">
              <InputLabel id="search-type-select-label">Search Type</InputLabel>
            <Select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              label="Search Type"
              labelId='search-type-select-label'
              sx={{ minWidth: 120, marginRight: 1 }}
            >
              <MenuItem value="gene">Gene</MenuItem>
              <MenuItem value="variant">Variant</MenuItem>
            </Select>
            <TextField
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            ></TextField>
            <Button variant="contained" color="secondary" sx={{ marginLeft: 1 }}>
              <SearchIcon />
              Search
            </Button>
          </Box>
        </Box>
      </main>
    </>
  )
}

export default HomePage
