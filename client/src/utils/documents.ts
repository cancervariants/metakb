import { Document } from '../models/domain'

export interface DocumentReference {
  header: string
  subheader?: string
  url: string
}

/**
 * Converts a domain `Document` into a UI-friendly reference for display.
 *
 * The returned `DocumentReference` contains the text and URL needed to render
 * a citation tooltip and external link. Because document metadata differs by
 * upstream source, this function applies source-specific formatting and returns
 * `null` for document types that cannot be represented as a reference.
 */
export const toDocumentReference = (document: Document): DocumentReference | null => {
  if (document.id?.startsWith('pubmed:')) {
    // MCI documents -- they just include PMIDs
    return {
      header: `PMID: ${document.pmid}`,
      url: `https://pubmed.ncbi.nlm.nih.gov/${document.pmid}/`,
    }
  } else if (document.id?.startsWith('civic.sid:')) {
    // CIViC EID documents -- they include a brief author citation under `document.name`
    if (document.title && document.name && document.pmid) {
      return {
        header: document.title,
        subheader: document.name,
        url: `https://pubmed.ncbi.nlm.nih.gov/${document.pmid}/`,
      }
    }
  } else if (document.id?.startsWith('moa.source:')) {
    // MOA documents -- `document.title` is a little too wordy for us
    const url = document.urls?.length && document.urls.length > 0 && document.urls[0]
    const titleText = document.title
    if (typeof titleText !== 'string' || typeof url !== 'string') {
      return null
    }
    let header: string
    if (titleText.includes('[package insert]')) {
      header = 'U.S. FDA prescribing information (package insert)'
    } else if (titleText.includes('NCCN Clinical Practice Guidelines')) {
      header = 'NCCN Clinical Practice Guidelines®'
    } else {
      return null
    }

    return {
      header: header,
      url: url,
    }
  }
  return null
}
