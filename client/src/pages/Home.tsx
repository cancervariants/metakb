import './Home.css'
import { useState } from 'react'

export default function Home() {
  const [genes, setGenes] = useState('KRAS G12C') 
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [normalizedMessage, setNormalizedMessage] = useState('')
  const [constraintType, setConstraintType] = useState('Allele')


  const handleQuery = async () => {
    setLoading(true)
    setNormalizedMessage('') 
    const rawAlleles = genes.split(',').map((g) => g.trim())
  
    const normRes = await fetch('http://localhost:3001/normalize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alleles: rawAlleles })
    })
  
    const normData = await normRes.json()
    const normalizedIds = normData.alleles || []
    if (normalizedIds.length > 0) {
        setNormalizedMessage(`Normalizer ID Found! ${normalizedIds.join(', ')}`)
      }
    const queryRes = await fetch('http://localhost:3001/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        genes: [], // still optional
        diseases: ['Solid Tumor', 'Cancer'],
        alleles: normalizedIds
      })
    })
  
    const queryData = await queryRes.json()
    setResults(queryData.data || [])
    setLoading(false)
  }
  
  return (
    <div className="home-container">
      <h1>MetaKB Jr.</h1>

      <div className="query-bar" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <div className="dropdown-container">
        <label htmlFor="constraint-select" style={{ fontWeight: 'bold' }}>Search Type:</label>
        <select
        id="constraint-select"
        value={constraintType}
        onChange={(e) => setConstraintType(e.target.value)}
        style={{ marginLeft: '0.5rem', padding: '0.3rem' }}
        >
        <option value="Allele">Allele</option>
        <option value="Gene Name">Gene Name</option>
        <option value="Gain-of-Function">Gain-of-Function</option>
        <option value="Loss-of-Function">Loss-of-Function</option>
        <option value="Copy Number Change">Copy Number Change</option>
        <option value="Fusion">Fusion (Help)</option>
        </select>
    </div>
        <input
          type="text"
          value={genes}
          onChange={(e) => setGenes(e.target.value)}
          placeholder="Enter allele(s), e.g. KRAS G12C"
        />
        <button onClick={handleQuery} disabled={loading}>
          {loading ? 'Loading...' : 'Run Query'}
        </button>
      </div>
        {normalizedMessage && (
        <div className="normalizer-msg" style={{ marginTop: '1rem', color: 'green' }}>
            {normalizedMessage}
        </div>
)}

      <div className="results">
        {results.length === 0 ? (
          <p>No results yet.</p>
        ) : (
          results.map((r, i) => (
            <div key={i} className="result-card">
              <h3>{r.Study?.description?.slice(0, 100) || 'Untitled Study'}...</h3>
              <p><strong>Gene:</strong> {r.Gene?.name}</p>
              <p><strong>Variant:</strong> {r.Variant?.name}</p>
              <p><strong>Allele:</strong> {r.Allele?.name}</p>
              <p><strong>Condition:</strong> {r.Condition?.name}</p>
              <p><strong>Therapy:</strong> {r.Therapy?.name}</p>
              <p><strong>Evidence Strength:</strong> {r.Strength?.name}</p>
              <p><strong>Source:</strong> {r.Document?.name}</p>
              <details>
                <summary>Full Study Description</summary>
                <p style={{ whiteSpace: 'pre-wrap' }}>{r.Study?.description}</p>
              </details>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
