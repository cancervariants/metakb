import Header from "../components/Header";
import { Box, Button, Select, TextField, Typography } from "@mui/material";
import SearchIcon from '@mui/icons-material/Search';

const HomePage = () => {
  return (
    <>
      <Header />
      <main>
        <Box id="main-page-container" m={5} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Typography variant="h5" color="primary" fontWeight="bold" mb={2} sx={{width: '50%', justifyContent: 'center', textAlign: 'center'}}>
            Search harmonized data across multiple genomic knowledgebases.
          </Typography>
          <Box id="search-container">
            <Select></Select>
            <TextField></TextField>
            <Button variant="contained" color="secondary" sx={{ marginLeft: 1 }}>
              <SearchIcon />
              Search
            </Button>
          </Box>
        </Box>
      </main>
    </>
  );
};

export default HomePage;
