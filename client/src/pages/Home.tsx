import './Home.css'
import { useState } from 'react'

export default function Home() {

    const [genes, setGenes] = useState('BRAF')
    const [results, setResults] = useState ([])

    const handleQuery = async () => {
        const res = await fetch('http://localhost:3001/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                genes: genes.split(',').map(g => g.trim()),
                diseases: ['Solid Tumor', 'Cancer'],
                alleles: ['L597Q', 'L597R', 'L597S', 'L597V']
            })
        })
        const data = await res.json()
        setResults(data.data || [])
    }

    return (
        <div>
        <h1>MetaKB Jr.</h1>
        <input type='text' value={genes} onChange={
            e => setGenes(e.target.value)} placeholder="Enter genes, comma separated" />
            <button onClick={handleQuery}>Run Query</button>

            <pre>{JSON.stringify(results, null, 2)}</pre>

      </div>
    )
}
