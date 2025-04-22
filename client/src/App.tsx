import './App.css'
import { Route, Router, Routes } from 'react-router-dom';

function App() {
  return (
    <Router location={''} navigator={undefined}>
      <Routes>
        <Route path="/" element={<Home />} />
        {/* Other routes like <Route path="/search" element={<Search />} /> */}
      </Routes>
    </Router>
  );
}

export default App
