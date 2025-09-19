import * as React from 'react'
import { useEffect } from 'react'
import Header from '../components/Header'
import { Box, CircularProgress, Tab, Tabs, Typography } from '@mui/material'
import { useSearchParams } from 'react-router-dom'
import ResultTable from '../components/ResultTable'

type SearchType = 'gene' | 'variation'
const API_BASE = '/cv-api/api/v2/search/statements'

type EvidenceBuckets = {
  prognostic: any[]
  diagnostic: any[]
  therapeutic: any[]
}

const formatTherapies = (objectTherapeutic: any): string | null => {
  if (!objectTherapeutic) return null

  // multiple therapies with operator
  if (Array.isArray(objectTherapeutic.therapies)) {
    const names = objectTherapeutic.therapies.map((t: any) => t?.name).filter(Boolean)
    if (names.length === 0) return null
    if (names.length === 1) return names[0]

    const operator = objectTherapeutic.membershipOperator?.toLowerCase() === "or" ? "or" : "and"
    return `${names.slice(0, -1).join(", ")} ${operator} ${names[names.length - 1]}`
  }

  // single therapy
  if (objectTherapeutic.conceptType === "Therapy") {
    return objectTherapeutic.name ?? null
  }

  return null
}


const normalizeResults = (data: Record<string, any[]>): any[] => {
  if (!data || Object.keys(data).length === 0) return []
  return Object.values(data).flatMap((arr) => {
    if (!Array.isArray(arr) || arr.length === 0) return []

    const first = arr[0] // use first item for metadata
    return [{
      variant_name: first?.proposition?.subjectVariant?.name ?? "Unknown",
      evidence_level: first?.strength?.primaryCoding?.code ?? "N/A",
      disease: first?.proposition?.conditionQualifier?.name 
            || first?.proposition?.objectCondition?.name 
            || "N/A",
      therapy: formatTherapies(first?.proposition?.objectTherapeutic) ?? "N/A",
      significance: first?.proposition?.predicate ?? "N/A",
      grouped_evidence: arr,
    }]
  })
}


const GeneResult = () => {
  const [params, setParams] = useSearchParams()

  const [results, setResults] = React.useState<EvidenceBuckets>({
    prognostic: [],
    diagnostic: [],
    therapeutic: [],
  })

  const [activeTab, setActiveTab] = React.useState<'prognostic' | 'diagnostic' | 'therapeutic'>(
  'prognostic'
)

  // Figure out which key exists in the URL: gene or variation
  const urlHasGene = params.has('gene')
  const urlHasVariation = params.has('variation')

  const typeFromUrl: SearchType | null = urlHasGene ? 'gene' : urlHasVariation ? 'variation' : null
  const queryFromUrl = typeFromUrl ? (params.get(typeFromUrl) ?? '') : ''

  const [searchType, setSearchType] = React.useState<SearchType>(typeFromUrl ?? 'gene')
  const [searchQuery, setSearchQuery] = React.useState<string>(queryFromUrl)
  const [loading, setLoading] = React.useState<boolean>(false)
  const [error, setError] = React.useState<string | null>(null)

  // Fetch when URL params change (source of truth is the URL)
  useEffect(() => {
    if (!typeFromUrl || !queryFromUrl.trim()) {
      setResults({ prognostic: [], diagnostic: [], therapeutic: [] })
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
        const prognostic_data = data.prognostic_statements
        const diagnostic_data = data.diagnostic_statements
        const therapeutic_data = data.therapeutic_statements

        const norm_prog_data = normalizeResults(prognostic_data)
        const norm_diag_data = normalizeResults(diagnostic_data)
        const norm_ther_data = normalizeResults(therapeutic_data)
        setResults({
          prognostic: norm_prog_data,
          diagnostic: norm_diag_data,
          therapeutic: norm_ther_data,
        })
      } catch (e: any) {
        if (e.name !== 'AbortError') setError(e.message ?? 'Unknown error')
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
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

  console.log(results)

  return (
    <>
      <Header />
      <Box id="result-page-container" m={5}>
        {loading && <CircularProgress />}
        {!loading && (
          <Box>
            <Box
              id="results-info-container"
              sx={{ backgroundColor: 'white', padding: 5, borderRadius: 2 }}
            >
              <Typography variant="h4" mb={2} fontWeight="bold">
                {searchQuery}
              </Typography>
              <Typography variant="h6" mb={2} fontWeight="bold" color="darkgrey">
                Aliases: [list of aliases]
              </Typography>
              <Typography variant="body1" mb={2}>
                Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quos blanditiis tenetur
                unde suscipit, quam beatae rerum inventore consectetur, neque doloribus, cupiditate
                numquam dignissimos laborum fugiat deleniti? Eum quasi quidem quibusdam.
              </Typography>
            </Box>
            <Box
              id="results-table-container"
              sx={{ backgroundColor: 'white', padding: 5, borderRadius: 2, marginTop: 2 }}
            >
            <Tabs onChange={(_, value) => setActiveTab(value)} value={activeTab} sx={{ marginBottom: 2 }}>
      <Tab label="Therapeutic" value="therapeutic" />
      <Tab label="Diagnostic" value="diagnostic" />
      <Tab label="Prognostic" value="prognostic" />
    </Tabs>
              <Typography variant="h6" mb={2} fontWeight="bold">
                {activeTab} Search Results ({results[activeTab]?.length})
              </Typography>
              <ResultTable results={results[activeTab]} resultType={activeTab} />
            </Box>
          </Box>
        )}
      </Box>
    </>
  )
}

export default GeneResult
