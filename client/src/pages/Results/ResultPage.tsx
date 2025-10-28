import * as React from 'react'
import { useEffect, useMemo, useState } from 'react'
import Header from '../../components/Header'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Stack,
  Tab,
  Tabs,
  Typography,
} from '@mui/material'
import { useSearchParams } from 'react-router-dom'
import ResultTable from '../../components/ResultTable/ResultTable'
import FilterSection from '../../components/FilterSection/FilterSection'
import {
  NormalizedResult,
  buildCountMap,
  evidenceOrder,
  normalizeResults,
  applyFilters,
  buildFilterOptions,
  TAB_LABELS,
  getEntityMetadataFromProposition,
} from '../../utils'

type SearchType = 'gene' | 'variation'
const API_BASE = '/api/search/statements'

type EvidenceBuckets = {
  prognostic: NormalizedResult[]
  diagnostic: NormalizedResult[]
  therapeutic: NormalizedResult[]
}

const ResultPage = () => {
  const [params] = useSearchParams()

  const [results, setResults] = React.useState<EvidenceBuckets>({
    prognostic: [],
    diagnostic: [],
    therapeutic: [],
  })

  const [activeTab, setActiveTab] = React.useState<'prognostic' | 'diagnostic' | 'therapeutic'>(
    'therapeutic',
  )

  // Figure out which key exists in the URL: gene or variation
  const urlHasGene = params.has('gene')
  const urlHasVariation = params.has('variation')

  const typeFromUrl: SearchType | null = urlHasGene ? 'gene' : urlHasVariation ? 'variation' : null
  const queryFromUrl = typeFromUrl ? (params.get(typeFromUrl) ?? '') : ''

  const [searchQuery, setSearchQuery] = useState<string>(queryFromUrl)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedVariants, setSelectedVariants] = useState<string[]>([])
  const [selectedDiseases, setSelectedDiseases] = useState<string[]>([])
  const [selectedTherapies, setSelectedTherapies] = useState<string[]>([])
  const [selectedEvidenceLevels, setSelectedEvidenceLevels] = useState<string[]>([])
  const [selectedSignificance, setSelectedSignificance] = useState<string[]>([])
  const [selectedSources, setSelectedSources] = useState<string[]>([])

  const { description, aliases, displayName } = useMemo(() => {
    const firstWithQualifier =
      results.therapeutic[0]?.grouped_evidence?.[0]?.proposition ??
      results.prognostic[0]?.grouped_evidence?.[0]?.proposition ??
      results.diagnostic[0]?.grouped_evidence?.[0]?.proposition

    return getEntityMetadataFromProposition(firstWithQualifier, typeFromUrl as 'gene' | 'variation')
  }, [results.diagnostic, results.prognostic, results.therapeutic, typeFromUrl])

  const selectedFilters = {
    variants: selectedVariants,
    diseases: selectedDiseases,
    therapies: selectedTherapies,
    evidenceLevels: selectedEvidenceLevels,
    significance: selectedSignificance,
    sources: selectedSources,
  }

  const filteredByTab: Record<'therapeutic' | 'diagnostic' | 'prognostic', NormalizedResult[]> = {
    therapeutic: applyFilters(results.therapeutic, selectedFilters),
    diagnostic: applyFilters(results.diagnostic, selectedFilters),
    prognostic: applyFilters(results.prognostic, selectedFilters),
  }

  const filteredResults = filteredByTab[activeTab]

  const sortedResults = useMemo(() => {
    const variantCounts = buildCountMap(filteredResults, 'variant_name')

    return [...filteredResults].sort((a, b) => {
      // variant cluster by total count (desc)
      const countA = variantCounts[a.variant_name] ?? 0
      const countB = variantCounts[b.variant_name] ?? 0
      if (countA !== countB) return countB - countA

      // fallback: variant name alphabetical
      const variantCmp = a.variant_name.localeCompare(b.variant_name)
      if (variantCmp !== 0) return variantCmp

      // evidence level
      const levelA = evidenceOrder[a.evidence_level] ?? 999
      const levelB = evidenceOrder[b.evidence_level] ?? 999
      if (levelA !== levelB) return levelA - levelB

      // number of records per row
      const recordCountA = a.grouped_evidence?.length ?? 0
      const recordCountB = b.grouped_evidence?.length ?? 0
      if (recordCountA !== recordCountB) return recordCountB - recordCountA

      // disease alphabetical
      return a.disease[0].localeCompare(b.disease[0])
    })
  }, [filteredResults])

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
      } catch (e: unknown) {
        if (e instanceof Error) {
          if (e.name !== 'AbortError') {
            setError(e.message ?? 'Unknown error')
          }
        } else {
          // fallback if it's not an Error (rare, but possible)
          setError('Unknown error')
        }
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
    setSearchQuery(queryFromUrl)
  }, [queryFromUrl])

  useEffect(() => {
    if (searchQuery) {
      document.title = `${TAB_LABELS[activeTab]} results for "${searchQuery}" | VICC MetaKB`
    } else {
      document.title = 'VICC | MetaKB'
    }
  }, [activeTab, searchQuery])

  const variantOptions = buildFilterOptions(results[activeTab], 'variant_name')
  const diseaseOptions = Array.from(
    new Set(results[activeTab].flatMap((r) => r.disease).filter(Boolean)),
  )
  const therapyOptions = Array.from(
    new Set(results[activeTab].flatMap((r) => r.therapy.therapyNames).filter(Boolean)),
  )

  const evidenceLevelOptions = Array.from(
    new Set(results[activeTab].map((r) => r.evidence_level).filter(Boolean)),
  )
  const significanceOptions = Array.from(
    new Set(results[activeTab].map((r) => r.significance).filter(Boolean)),
  )

  const sourceOptions = Array.from(
    new Set(results[activeTab].flatMap((r) => r.sources).filter(Boolean)),
  )

  const clearAllFilters = () => {
    setSelectedVariants([])
    setSelectedDiseases([])
    setSelectedTherapies([])
    setSelectedEvidenceLevels([])
    setSelectedSignificance([])
    setSelectedSources([])
  }

  const activeFilters = [
    ...selectedVariants.map((v) => ({ type: 'variant', value: v })),
    ...selectedDiseases.map((d) => ({ type: 'disease', value: d })),
    ...selectedTherapies.map((t) => ({ type: 'therapy', value: t })),
    ...selectedEvidenceLevels.map((e) => ({ type: 'evidence_level', value: e })),
    ...selectedSignificance.map((s) => ({ type: 'significance', value: s })),
    ...selectedSources.map((src) => ({ type: 'source', value: src })),
  ]

  const removeFilter = (filter: { type: string; value: string }) => {
    switch (filter.type) {
      case 'variant':
        setSelectedVariants((prev) => prev.filter((v) => v !== filter.value))
        break
      case 'disease':
        setSelectedDiseases((prev) => prev.filter((d) => d !== filter.value))
        break
      case 'therapy':
        setSelectedTherapies((prev) => prev.filter((t) => t !== filter.value))
        break
      case 'evidence_level':
        setSelectedEvidenceLevels((prev) => prev.filter((e) => e !== filter.value))
        break
      case 'significance':
        setSelectedSignificance((prev) => prev.filter((s) => s !== filter.value))
        break
      case 'source':
        setSelectedSources((prev) => prev.filter((s) => s !== filter.value))
        break
    }
  }

  const hasInitialResults = results[activeTab].length > 0
  const hasFilteredResults = filteredResults.length > 0

  return (
    <>
      <Header />
      <Box id="result-page-container" m={5}>
        {loading && <CircularProgress />}
        {error && <Alert severity="error">{error}</Alert>}
        {!loading && !error && (
          <Box>
            <Typography variant="h5" color="primary" fontWeight="bold" mb={2}>
              Showing results for {typeFromUrl}: {searchQuery}
            </Typography>
            <Box
              id="results-info-container"
              sx={{ backgroundColor: 'white', padding: 5, borderRadius: 2 }}
              display={description || aliases.length ? 'block' : 'none'}
            >
              <Typography variant="h4" mb={2} fontWeight="bold">
                {displayName}
              </Typography>
              <Typography
                variant="h6"
                mb={2}
                fontWeight="bold"
                color="darkgrey"
                display={aliases.length ? 'block' : 'none'}
              >
                Aliases: {aliases.join(', ')}
              </Typography>
              <Typography variant="body1" mb={2} display={description ? 'block' : 'none'}>
                {description}
              </Typography>
            </Box>
            <Box
              id="results-table-container"
              sx={{ backgroundColor: 'white', padding: 5, borderRadius: 2, marginTop: 2 }}
            >
              <Tabs
                onChange={(_, value) => setActiveTab(value)}
                value={activeTab}
                sx={{ marginBottom: 2 }}
              >
                <Tab
                  label={`Therapeutic (${filteredByTab.therapeutic.length})`}
                  value="therapeutic"
                />
                <Tab label={`Diagnostic (${filteredByTab.diagnostic.length})`} value="diagnostic" />
                <Tab label={`Prognostic (${filteredByTab.prognostic.length})`} value="prognostic" />
              </Tabs>
              <Box id="search-type-label" m={2}>
                <Typography variant="h6" fontWeight="bold">
                  {TAB_LABELS[activeTab]} Search Results ({filteredResults?.length})
                </Typography>
              </Box>
              {hasInitialResults ? (
                <Box display="flex">
                  <Box id="filter-container">
                    <Box width={250} p={2} sx={{ borderRight: '1px solid #ddd' }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <strong>Filters</strong>
                        <Button variant="outlined" size="small" onClick={clearAllFilters}>
                          clear all
                        </Button>
                      </Box>
                      <Box id="active-filters">
                        {activeFilters.length > 0 && (
                          <Stack direction="row" flexWrap="wrap">
                            {activeFilters.map((f) => (
                              <Chip
                                key={`${f.type}-${f.value}`}
                                label={f.value}
                                onDelete={() => removeFilter(f)}
                                color="primary"
                                variant="outlined"
                              />
                            ))}
                          </Stack>
                        )}
                      </Box>
                      <hr></hr>
                      <FilterSection
                        title="Variant"
                        options={variantOptions}
                        selected={selectedVariants}
                        setSelected={setSelectedVariants}
                      />
                      <hr></hr>
                      <FilterSection
                        title="Disease"
                        options={diseaseOptions}
                        selected={selectedDiseases}
                        setSelected={setSelectedDiseases}
                      />
                      <hr></hr>
                      <FilterSection
                        title="Therapy"
                        options={therapyOptions}
                        selected={selectedTherapies}
                        setSelected={setSelectedTherapies}
                      />
                      <hr></hr>
                      <FilterSection
                        title="Evidence Level"
                        options={evidenceLevelOptions}
                        selected={selectedEvidenceLevels}
                        setSelected={setSelectedEvidenceLevels}
                      />
                      <hr></hr>
                      <FilterSection
                        title="Significance"
                        options={significanceOptions}
                        selected={selectedSignificance}
                        setSelected={setSelectedSignificance}
                      />
                      <hr />
                      <FilterSection
                        title="Source"
                        options={sourceOptions}
                        selected={selectedSources}
                        setSelected={setSelectedSources}
                      />
                    </Box>
                  </Box>
                  <Box id="results" width="100%" p={2}>
                    {hasFilteredResults ? (
                      <ResultTable results={sortedResults} resultType={activeTab} />
                    ) : (
                      <Alert severity="info" sx={{ width: '100%' }}>
                        No results match your current filters.
                      </Alert>
                    )}
                  </Box>
                </Box>
              ) : (
                <Alert severity="info">No results were found for your query.</Alert>
              )}
            </Box>
          </Box>
        )}
      </Box>
    </>
  )
}

export default ResultPage
