import * as React from 'react'
import { useEffect, useMemo, useState } from 'react'
import Header from '../components/Header'
import { Box, Button, Chip, CircularProgress, Stack, Tab, Tabs, Typography } from '@mui/material'
import { useSearchParams } from 'react-router-dom'
import ResultTable from '../components/ResultTable'
import FilterSection from '../components/FilterSection'

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

    const operator = objectTherapeutic.membershipOperator?.toLowerCase() === 'or' ? 'or' : 'and'
    return `${names.slice(0, -1).join(', ')} ${operator} ${names[names.length - 1]}`
  }

  // single therapy
  if (objectTherapeutic.conceptType === 'Therapy') {
    return objectTherapeutic.name ?? null
  }

  return null
}
// aliases and description in geneContextQualifier

const formatSignificance = (predicate: string): string => {
  if (predicate === 'predictsSensitivityTo') {
    return 'Sensitivity'
  }
  if (predicate === 'predictsResistanceTo') {
    return 'Resistance'
  }
  if (predicate === 'isDiagnosticInclusionCriterionFor') {
    return 'Inclusion Criterion'
  }
  if (predicate === 'isDiagnosticExclusionCriterionFor') {
    return 'Exclusion Criterion'
  }
  if (predicate === 'associatedWithWorseOutcomeFor') {
    return 'Worse Outcome'
  }
  if (predicate === 'associatedWithBetterOutcomeFor') {
    return 'Better Outcome'
  }
  return ''
}

const normalizeResults = (data: Record<string, any[]>): any[] => {
  if (!data || Object.keys(data).length === 0) return []
  return Object.values(data).flatMap((arr) => {
    if (!Array.isArray(arr) || arr.length === 0) return []

    const first = arr[0] // use first item for metadata
    return [
      {
        variant_name: first?.proposition?.subjectVariant?.name ?? 'Unknown',
        evidence_level: first?.strength?.primaryCoding?.code ?? 'N/A',
        disease:
          first?.proposition?.conditionQualifier?.name ||
          first?.proposition?.objectCondition?.name ||
          'N/A',
        therapy: formatTherapies(first?.proposition?.objectTherapeutic) ?? 'N/A',
        significance: first?.proposition?.predicate
          ? formatSignificance(first?.proposition?.predicate)
          : 'N/A',
        grouped_evidence: arr,
      },
    ]
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
    'therapeutic',
  )

  // Figure out which key exists in the URL: gene or variation
  const urlHasGene = params.has('gene')
  const urlHasVariation = params.has('variation')

  const typeFromUrl: SearchType | null = urlHasGene ? 'gene' : urlHasVariation ? 'variation' : null
  const queryFromUrl = typeFromUrl ? (params.get(typeFromUrl) ?? '') : ''

  const [searchType, setSearchType] = useState<SearchType>(typeFromUrl ?? 'gene')
  const [searchQuery, setSearchQuery] = useState<string>(queryFromUrl)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedVariants, setSelectedVariants] = useState<string[]>([])
  const [selectedDiseases, setSelectedDiseases] = useState<string[]>([])
  const [selectedTherapies, setSelectedTherapies] = useState<string[]>([])
  const [selectedEvidenceLevels, setSelectedEvidenceLevels] = useState<string[]>([])
  const [selectedSignificance, setSelectedSignificance] = useState<string[]>([])

  const { description, aliases } = useMemo(() => {
    const exts =
      results.therapeutic[0]?.grouped_evidence?.[0]?.proposition?.geneContextQualifier
        ?.extensions ??
      results.prognostic[0]?.grouped_evidence?.[0]?.proposition?.geneContextQualifier?.extensions ??
      results.diagnostic[0]?.grouped_evidence?.[0]?.proposition?.geneContextQualifier?.extensions ??
      []

    const descriptionExt = exts.find((e) => e.name === 'description')
    const aliasesExt = exts.find((e) => e.name === 'aliases')

    return {
      description: descriptionExt?.value ?? null,
      aliases: aliasesExt?.value ?? [],
    }
  }, [results])

  const applyFilters = (
    items: any[],
    selected: {
      variants: string[]
      diseases: string[]
      therapies: string[]
      evidenceLevels: string[]
      significance: string[]
    },
  ): any[] => {
    return items.filter((r) => {
      const variantMatch =
        selected.variants.length === 0 || selected.variants.includes(r.variant_name)
      const diseaseMatch = selected.diseases.length === 0 || selected.diseases.includes(r.disease)
      const therapyMatch = selected.therapies.length === 0 || selected.therapies.includes(r.therapy)
      const levelMatch =
        selected.evidenceLevels.length === 0 || selected.evidenceLevels.includes(r.evidence_level)
      const significanceMatch =
        selected.significance.length === 0 || selected.significance.includes(r.significance)

      return variantMatch && diseaseMatch && therapyMatch && levelMatch && significanceMatch
    })
  }

  const selectedFilters = {
    variants: selectedVariants,
    diseases: selectedDiseases,
    therapies: selectedTherapies,
    evidenceLevels: selectedEvidenceLevels,
    significance: selectedSignificance,
  }

  const filteredByTab: Record<'therapeutic' | 'diagnostic' | 'prognostic', any[]> = {
    therapeutic: applyFilters(results.therapeutic, selectedFilters),
    diagnostic: applyFilters(results.diagnostic, selectedFilters),
    prognostic: applyFilters(results.prognostic, selectedFilters),
  }

  const filteredResults = filteredByTab[activeTab]

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

  const buildFilterOptions = (results: any[], key: keyof any): string[] => {
    const counts = results.reduce((acc: Record<string, number>, item: any) => {
      const val = item[key]
      if (val) {
        acc[val] = (acc[val] || 0) + 1
      }
      return acc
    }, {})

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1]) // sort by count desc
      .map(([value]) => value)
  }

  const variantOptions = buildFilterOptions(results[activeTab], 'variant_name')
  const diseaseOptions = buildFilterOptions(results[activeTab], 'disease')
  const therapyOptions = buildFilterOptions(results[activeTab], 'therapy')

  const evidenceLevelOptions = Array.from(
    new Set(results[activeTab].map((r) => r.evidence_level).filter(Boolean)),
  )
  const significanceOptions = Array.from(
    new Set(results[activeTab].map((r) => r.significance).filter(Boolean)),
  )

  const clearAllFilters = () => {
    setSelectedVariants([])
    setSelectedDiseases([])
    setSelectedTherapies([])
    setSelectedEvidenceLevels([])
    setSelectedSignificance([])
  }

  const activeFilters = [
    ...selectedVariants.map((v) => ({ type: 'variant', value: v })),
    ...selectedDiseases.map((d) => ({ type: 'disease', value: d })),
    ...selectedTherapies.map((t) => ({ type: 'therapy', value: t })),
    ...selectedEvidenceLevels.map((e) => ({ type: 'evidence_level', value: e })),
    ...selectedSignificance.map((s) => ({ type: 'significance', value: s })),
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
    }
  }

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
                Aliases: {aliases.join(', ')}
              </Typography>
              <Typography variant="body1" mb={2}>
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
              <Typography variant="h6" mb={2} fontWeight="bold">
                {activeTab} Search Results ({filteredResults?.length})
              </Typography>
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
                  </Box>
                </Box>
                <Box>
                  <ResultTable results={filteredResults} resultType={activeTab} />
                </Box>
              </Box>
            </Box>
          </Box>
        )}
      </Box>
    </>
  )
}

export default GeneResult
