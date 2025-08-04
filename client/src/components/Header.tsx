import { AppBar, Typography } from "@mui/material";

const Header = () => {
  return (
    <AppBar position="static" color="header" sx={{ padding: 2 }}>
      <Typography variant="h4" fontWeight="bold">MetaKB</Typography></AppBar>
  );
};

export default Header;
