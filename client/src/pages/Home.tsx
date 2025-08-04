import Header from "../components/Header";
import { Box, Typography } from "@mui/material";

const HomePage = () => {
  return (
    <>
      <Header />

      {/* Page content */}
      <main>
        <Box id="main-page-container" m={5}>
          <Typography variant="h5">
            Search harmonized data across multiple genomic knowledgebases.
          </Typography>
        </Box>
      </main>
    </>
  );
};

export default HomePage;
