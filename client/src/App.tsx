import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import { ThemeProvider } from '@mui/material'
import theme from './theme'
import ResultPage from './pages/Results/ResultPage'
import Layout from './Layout'
import { docsSections } from './routes/docsConfig'

function App() {
  return (
    <ThemeProvider theme={theme}>
      <Router>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<ResultPage />} />

            {docsSections.flatMap((section) =>
              section.pages.map((page) => (
                <Route key={page.path} path={page.path} element={page.element} />
              )),
            )}
            {/* Fallback for invalid routes */}
            <Route path="*" element={<Home />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
