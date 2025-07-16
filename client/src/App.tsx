import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'

import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

// function App() {
//   const [count, setCount] = useState(0)

export default function App() {  
  return (
    <div>
      <nav>
        <Link to='/'>Home</Link>
      </nav>
      <Routes>
        <Route path='/' element={<Home />} />
      </Routes>
    </div>
  )
}
