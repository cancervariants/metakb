import * as React from 'react'
import Header from '../components/Header'
import { Box, CircularProgress, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material'
import { useSearchParams } from 'react-router-dom'
import { useEffect } from 'react'

type SearchType = 'gene' | 'variation'
const API_BASE = '/cv-api/api/v2/search/statements'

const GeneResult = () => {
  const [params, setParams] = useSearchParams()

  // Figure out which key exists in the URL: gene or variation
  const urlHasGene = params.has('gene')
  const urlHasVariation = params.has('variation')

  const typeFromUrl: SearchType | null = urlHasGene ? 'gene' : urlHasVariation ? 'variation' : null
  const queryFromUrl = typeFromUrl ? (params.get(typeFromUrl) ?? '') : ''

  const [searchType, setSearchType] = React.useState<SearchType>(typeFromUrl ?? 'gene')
  const [searchQuery, setSearchQuery] = React.useState<string>(queryFromUrl)
  const [results, setResults] = React.useState<any[]>([])
  const [loading, setLoading] = React.useState<boolean>(false)
  const [error, setError] = React.useState<string | null>(null)

  // Fetch when URL params change (source of truth is the URL)
  useEffect(() => {
    if (!typeFromUrl || !queryFromUrl.trim()) {
      setResults([])
      return
    }
    setLoading(true)

    const controller = new AbortController()
    const run = async () => {
      try {
        setError(null)
        const url = `${API_BASE}?${typeFromUrl}=${encodeURIComponent(queryFromUrl.trim())}`
        const res = await fetch(url, {
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal,
        })
        if (!res.ok) throw new Error(`Request failed: ${res.status}`)
        const data = await res.json()
        setResults(Array.isArray(data?.statements) ? data.statements : [])
      } catch (e: any) {
        if (e.name !== 'AbortError') setError(e.message ?? 'Unknown error')
      } finally {
          if (!controller.signal.aborted) {
            setLoading(false);
            }
      }
    }
    run()

    return () => controller.abort()
    // Only re-run when URL-derived values change:
  }, [typeFromUrl, queryFromUrl])

  // Keep the controls in sync if the user lands directly on /search?gene=TP53
  useEffect(() => {
    if (typeFromUrl) setSearchType(typeFromUrl)
    setSearchQuery(queryFromUrl)
  }, [typeFromUrl, queryFromUrl])

  const columns = [
    { field: 'id', headerName: 'ID', width: 90 },
    {
      field: 'direction',
      headerName: 'Direction',
      width: 150,
    },
    {
      field: 'description',
      headerName: 'Description',
      width: 150,
      editable: true,
    },
  ]

  return (
    <>
      <Header />
      <Box
        id="result-page-container"
        m={5}
        sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}
      >
        {loading && <CircularProgress />}
        {!loading && (
          <Table>
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell key={column.field} style={{ width: column.width }}>
                    {column.headerName}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
            {results.map((row) => (
              <TableRow key={row.id}>
                {columns.map((column) => {
                  const value = row[column.field]
                  return (
                    <TableCell key={column.field} style={{ width: column.width }}>
                      {value}
                    </TableCell>
                  )
                })}
              </TableRow>
            ))}
            </TableBody>
          </Table>
        )}
      </Box>
    </>
  )
}

export default GeneResult
