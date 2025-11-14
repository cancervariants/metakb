import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import { ThemeProvider } from '@mui/material'
import theme from './theme'
import ResultPage from './pages/Results/ResultPage'
import Layout from './Layout'

function App() {
  return (
    <ThemeProvider theme={theme}>
      <Router>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<ResultPage />} />
            {/* Fallback for invalid routes */}
            <Route path="*" element={<Home />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
