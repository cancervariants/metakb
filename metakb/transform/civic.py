"""A module for to transform CIViC."""
from metakb import PROJECT_ROOT
import json
import logging
import metakb.models.schemas as schemas
logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class CIViCTransform:
    """A class for transforming CIViC to the common data model."""

    def __init__(self, fn='civic_harvester.json'):
        """Initialize CIViCTransform class.

        :param str fn: The file name of the composite JSON to transform.
        """
        self._fn = fn

    def _extract(self):
        """Extract the CIViC composite JSON file."""
        with open(f"{PROJECT_ROOT}/data/civic/{self._fn}", 'r') as f:
            return json.load(f)

    def tranform(self):
        """Transform CIViC harvested json to common data model."""
        data = self._extract()
        response = dict()
        evidence_items = data['evidence']
        genes = data['genes']
        variants = data['variants']
        for evidence in evidence_items:
            if evidence['id'] == 3017:
                self._add_evidence(evidence, variants, genes, response)
                break
        print(response)

    def _add_evidence(self, e, variants, genes, response):
        """Add evidence to therapeutic response.

        :param dict e: Harvested CIViC evidence
        """
        evidence = {
            'id': f"{schemas.NamespacePrefix.CIVIC.value}:{e['name']}",
            'type': 'evidence',  # Should this be GksTherapeuticResponse
            'molecular_profile':
                f"{schemas.NamespacePrefix.CIVIC.value}:VID{e['variant_id']}",
            'disease':
                f"{schemas.NamespacePrefix.CIVIC.value}:"
                f"DiseaseID{e['disease']['id']}",
            'variant_origin':
                schemas.VariantOrigin[e['variant_origin'].upper()].value,
            'clinical_significance': self._add_clinical_significance(e),
            'drugs': [self._add_drug(drug) for drug in e['drugs']],
            'evidence_level': e['evidence_level'],
            'variant': self._add_variant(variants, e['variant_id']),
            'gene': self._add_gene(genes, e['gene_id'])
            # 'gene': f"{schemas.NamespacePrefix.CIVIC.value}:{e['gene_id']}"
        }
        response['evidence'] = evidence

    def _add_clinical_significance(self, e):
        """Return clinical significance for a given evidence item.

        :param dict e: Harvested CIViC evidence
        :return: A string giving the clinical significance for an evidence item
        """
        clin_sig = None
        if 'clinical_significance' in e and e['clinical_significance']:
            clin_sig = e['clinical_significance']
            if clin_sig == 'Sensitivity/Response':
                clin_sig = schemas.ClinicalSignificance.SENSITIVITY.value
        return clin_sig

    def _add_drug(self, drug):
        """Return drug data.

        :param dict drug: A CIViC drug record
        """
        return {
            'id': f"{schemas.NamespacePrefix.NCIT.value}:{drug['id']}",
            'label': drug['name']
        }

    def _add_variant(self, variants, variant_id):
        """Add variant data to the response.

        :param dict variants: Harvested CIViC variants
        :param str variant_id: The variant's ID
        :param dict response: The response object
        :return: A dictionary containing variant data
        """
        v = self._get_record(variant_id, variants)
        return {
            'id': f"{schemas.NamespacePrefix.CIVIC.value}:VID{v['id']}",
            'type': 'variant',  # Should this be AlleleDescriptor?
            'label': f"{v['entrez_name']} {v['name']}",
            'gene': f"{schemas.NamespacePrefix.CIVIC.value}:GID{v['gene_id']}",
            'hgvs_descriptions': v['hgvs_expressions'],
            'xref': self._add_variant_xrefs(v),
            'aliases': [alias for alias in v['variant_aliases']
                        if not alias.startswith('RS')]
        }

    def _get_record(self, record_id, records):
        """Get a CIViC record by ID.

        :param str record_id: The ID of the record we are searching for
        :param dict records: A dict of records for a given CIViC record type
        """
        for r in records:
            if r['id'] == record_id:
                return r

    def _add_gene(self, genes, gene_id):
        """Add gene data to the response.

        :param dict genes: Harvested CIViC genes
        :param str gene_id: The gene's ID
        :return: A dictionary containing gene data
        """
        g = self._get_record(gene_id, genes)
        return {
            'id': f"{schemas.NamespacePrefix.CIVIC.value}:GID{g['id']}",
            'type': 'gene',  # Should this be GeneDescriptor
            'label': g['name'],
            'description': g['description'],
            'xrefs': self._add_gene_xrefs(g),
            'aliases': g['aliases']
        }

    def _add_gene_xrefs(self, g):
        """Get a list of xrefs for a gene.

        :param dict g: A CIViC gene record
        """
        xrefs = [self._add_xref(
            schemas.XrefSystem.NCBI.value, g['entrez_id'])]
        return xrefs

    def _add_variant_xrefs(self, v):
        """Get a list of xrefs for a variant.

        :param dict v: A CIViC variant record
        :return: A dictionary of xrefs
        """
        xrefs = []
        for xref in ['clinvar_entries', 'allele_registry_id',
                     'variant_aliases']:
            if xref == 'clinvar_entries':
                for clinvar_entry in v['clinvar_entries']:
                    xrefs.append(self._add_xref(
                        schemas.XrefSystem.CLINVAR.value, clinvar_entry,
                        xref_type='variation'))

            elif xref == 'allele_registry_id':
                xrefs.append(self._add_xref(schemas.XrefSystem.CLINGEN.value,
                                            v['allele_registry_id']))
            elif xref == 'variant_aliases':
                dbsnp_xrefs = [item for item in v['variant_aliases']
                               if item.startswith('RS')]
                for dbsnp_xref in dbsnp_xrefs:
                    xrefs.append(self._add_xref(
                        schemas.XrefSystem.DB_SNP.value,
                        dbsnp_xref.split('RS')[-1],
                        xref_type='rs'))
        return xrefs

    def _add_xref(self, system, system_id, xref_type=None):
        """Return xref data.

        :param str system: The name of the system
        :param str system_id: The system's ID for the concept
        :param str xref_type: The type of the xref
        """
        xref = {
            'system': system,
            'id': system_id
        }
        if xref_type:
            xref['type'] = xref_type
        return xref


CIViCTransform().tranform()
