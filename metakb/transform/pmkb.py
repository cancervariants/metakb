"""Transform PMKB data into Common Data Model objects."""
from metakb import PROJECT_ROOT
from metakb.normalizers import VICCNormalizers
import metakb.schemas as schemas
import logging
import json

logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


class PMKBTransform:
    """A class for transforming PMKB data into Common Data Model objects."""

    def __init__(self,
                 file_path=f"{PROJECT_ROOT}/data/pmkb/pmkb_harvester.json",
                 audit=False):
        """Initiate normalizer services and get data location.
        :param str file_path: location of harvested PMKB json file
        :param bool audit: if True, save lists of gene, variant, and disease
            terms that fail to normalize
        """
        self._file_path = file_path
        self.audit = audit
        self.vicc_normalizers = VICCNormalizers()
        self.transformed = {
            'variation_descriptors': {},  # label -> VOD
            'gene_descriptors': {},  # symbol -> VOD
            'therapy_descriptors': {},  # label -> VOD
            'disease_descriptors': {},  # (label, tissue type) -> VOD
            'statements': [],  # List of Statements
            'propositions': {},  # key -> Proposition
            'method': None,  # single Method once initialized
            'documents': {},  # cite -> Document
        }
        self.invalid_keys = {
            'variants': set(),
            'genes': set(),
            'diseases': set(),
            'therapies': set()
        }

    def _extract(self):
        """Get PMKB harvested data file."""
        with open(self._file_path, 'r') as f:
            return json.load(f)

    def _create_json(self,
                     pmkb_dir=PROJECT_ROOT / 'data' / 'pmkb' / 'transform',
                     fn='pmkb_cdm.json'):
        """Create a composite JSON for the transformed PMKB data.

        :param Path pmkb_dir: The PMKB transform data directory
        :param str fn: The file name for the transformed data
        """
        output = {
            "statements": self.transformed['statements'],
            "propositions": list(self.transformed['propositions'].values()),
            "variation_descriptors": list(
                self.transformed['variation_descriptors'].values()
            ),
            "gene_descriptors": list(
                self.transformed['gene_descriptors'].values()
            ),
            "therapy_descriptors": list(
                self.transformed['therapy_descriptors'].values()
            ),
            "disease_descriptors": list(
                self.transformed['disease_descriptors'].values()
            ),
            "methods": [self.transformed['method']],
            "documents": list(self.transformed['documents'].values())
        }

        pmkb_dir.mkdir(exist_ok=True, parents=True)
        with open(pmkb_dir / fn, 'w+') as f:
            json.dump(output, f)

        if self.audit:
            data_dir = PROJECT_ROOT / 'data' / 'pmkb'
            output = {
                'variants': list(self.invalid_keys['variants']),
                'genes': list(self.invalid_keys['genes']),
                'diseases': list(self.invalid_keys['diseases'])
            }
            with open(data_dir / 'invalid_keys.json', 'w') as f:
                json.dump(output, f)

    def transform(self, propositions_documents_ix=None):
        """Transform PMKB harvested json to common data model.
        :param Dict propositions_documents_ix: tracking data to properly
            index SupportEvidence and Propositions
        :return: Updated propositions_documents_ix object
        """
        data = self._extract()
        statements = data['statements']
        variants = {v['id']: v for v in data['variants']}
        if not propositions_documents_ix:
            propositions_documents_ix = {
                # Keep track of documents index value
                'document_index': 1,
                # {document_id: document_index}
                'documents': dict(),
                # Keep track of proposition index value
                'proposition_index': 1,
                # {tuple: proposition_index}
                'propositions': dict()
            }

        # build lookups for artificial IDs
        gene_index = {}
        disease_index = {}
        method = self._get_methods()[0]
        for pmkb_statement in statements:
            descriptors = self._get_descriptors(pmkb_statement, variants,
                                                gene_index, disease_index)
            if not all(descriptors):
                continue

            t_descriptors, d_descriptors, g_descriptors, v_descriptors = descriptors  # noqa: E501
            proposition = self._get_tr_proposition(v_descriptors,
                                                   t_descriptors,
                                                   d_descriptors,
                                                   propositions_documents_ix)

            documents = self._get_documents(pmkb_statement,
                                            propositions_documents_ix)

            cdm_statement = self._get_statement(pmkb_statement, proposition,
                                                v_descriptors, t_descriptors,
                                                d_descriptors, method,
                                                documents)
            self.transformed['statements'].append(cdm_statement)

        self._create_json()
        return propositions_documents_ix

    def _get_descriptors(self, statement, variants, gene_index, disease_index):
        """Get Descriptor objects given statement and associated data.
        :param Dict statement: PMKB interpretation formatted as a statement
        :param Dict variants: Keys are variant labels and values are all
            harvested variant objects
        :param Dict gene_index: lookup gene ID from symbol
        :param Dict disease_index: lookup disease ID from label
        :return: Tuple containing Lists of therapy, disease, gene, and
            variant descriptors (we expect each to be len == 1)
        """
        # enforce quantity restrictions
        diseases = statement['diseases']
        tissue_types = statement['tissue_types']
        variant_ids = [variant['id'] for variant in statement['variants']]
        therapies = statement['therapies']
        for field, values in (('disease', diseases),
                              ('variant', variant_ids),
                              ('therapy', therapies)):
            if len(values) != 1:
                logger.warning(f"PMKB statement {statement['id']} does not "
                               f"have exactly 1 {field}: {values}.")
                return [], [], [], []

        # get descriptors
        variant = variants.get(variant_ids[0])
        if not variant:
            logger.warning(f"Could not retrieve variant for variant ID "
                           f"{variant_ids[0]} in statement ID "
                           f"{statement['id']}")
        t_descriptors = self._get_therapy_descriptors(therapies[0])
        d_descriptors = self._get_disease_descriptors(diseases[0],
                                                      tissue_types)
        g_descriptors = self._get_gene_descriptors(variant)
        v_descriptors = self._get_variant_descriptors(statement, variant,
                                                      g_descriptors[0]['id'])
        return t_descriptors, d_descriptors, g_descriptors, v_descriptors

    def _get_therapy_descriptors(self, therapy):
        """Get therapy descriptors. Most PMKB statements have value
        ncit:C49236, but we try to grab some from the description.
        :param str therapy: label of a drug
        :return: List containing Therapeutic Procedure VOD.
        """
        invalid_keys = self.invalid_keys['therapies']
        if therapy in invalid_keys:
            return []

        vod = self.transformed['therapy_descriptors'].get(therapy)
        if vod:
            return [vod]

        response = self.vicc_normalizers.normalize_therapy([therapy])
        if not response or not response[0] or response[0]['match_type'] == 0:
            logger.warning(f"Therapy normalization of {therapy} failed.")
            invalid_keys.add(therapy)
            return []
        response = response[0]
        vod = schemas.ValueObjectDescriptor(
            id=f"pmkb.normalize.therapy:{therapy}",
            type="TherapyDescriptor",
            label=therapy,
            value=schemas.Therapy(id=response['value_object_descriptor']['value']['id'])  # noqa: E501
        ).dict(exclude_none=True)

        self.transformed['therapy_descriptors'][therapy] = vod
        return [vod]

    def _get_disease_descriptors(self, disease, tissue_types):
        """Get Disease Descriptors for given disease. Tries disease label
        concatenated with tissue type first, then disease label alone.
        :param str disease: PMKB disease name
        :param List tissue_types: types of tissue (str) specified by record
        :return: List (len == 1) containing VOD of best normalized match, or
            empty List if normalization fails
        """
        invalid_keys = self.invalid_keys['diseases']
        if disease in invalid_keys:
            return []

        disease_descriptors = self.transformed['disease_descriptors']
        vod = disease_descriptors.get(disease)
        if vod:
            return [vod]

        response = self.vicc_normalizers.normalize_disease([disease])
        if not response or not response[0] or response[0]['match_type'] == 0:
            logger.warning(f"Disease normalization of {disease} failed.")
            invalid_keys.add(disease)
            return []
        response = response[0]
        vod = schemas.ValueObjectDescriptor(
            id=f"pmkb.normalize.disease:{disease}",
            type="DiseaseDescriptor",
            label=disease,
            value=schemas.Disease(id=response['value_object_descriptor']['value']['id'])  # noqa: E501
        ).dict(exclude_none=True)

        if tissue_types:
            vod['extensions'] = [
                {
                    "type": "Extension",
                    "name": "tissue_types",
                    "value": tissue_types
                }
            ]

        self.transformed['disease_descriptors'][disease] = vod
        return [vod]

    def _get_gene_descriptors(self, variant):
        """Fetch gene descriptors.
        :param Dict variant: harvested PMKB variant object
        :return: List (len == 1) containing VOD of normalized match, or
            empty list if normalization fails
        """
        symbol = variant['gene']['name']
        invalid_keys = self.invalid_keys['genes']
        if symbol in invalid_keys:
            return []

        gene_descriptors = self.transformed['gene_descriptors']
        vod = gene_descriptors.get(symbol)
        if vod:
            return [vod]

        response, _ = self.vicc_normalizers.normalize_gene([symbol])
        if not response:
            logger.warning(f"Gene normalization of {symbol} failed.")
            invalid_keys.add(symbol)
            return []

        normalized_id = response['records'][0].concept_id

        vod = schemas.ValueObjectDescriptor(
            id=f"pmkb.normalize.gene:{symbol}",
            type="GeneDescriptor",
            label=symbol,
            value=schemas.Gene(id=normalized_id)
        ).dict(exclude_none=True)

        gene_descriptors[symbol] = vod
        return [vod]

    def _get_variant_descriptors(self, statement, variant, gene_id):
        """Fetch variant descriptors.
        :param Dict statement: PMKB statement object
        :param Dict variant: PMKB variant object
        :param str gene_id: identifier for gene_context field
        :return: List (len == 1) containing VOD of normalized match, or
            empty list if normalization fails
        """
        label = variant['name']
        invalid_keys = self.invalid_keys['variants']
        if label in invalid_keys:
            return []

        vod = self.transformed['variation_descriptors'].get(label)
        if vod:
            return [vod]

        response = self.vicc_normalizers.normalize_variant([label])
        if not response:
            logger.warning(f"Variant normalization of {label} failed.")
            invalid_keys.add(label)
            return []

        vod = schemas.VariationDescriptor(
            id=f"pmkb.variant:{variant['id']}",
            type="VariationDescriptor",
            label=label,
            value_id=response.value_id,
            value=response.value,
            gene_context=f"pmkb.gene:{variant['gene']['name']}",
            molecule_context=response.molecule_context,
            structural_type=response.structural_type,
            ref_allele_seq=response.ref_allele_seq,
        ).dict(exclude_none=True)

        # TODO extensions?
        assoc_with = []
        cosmic_id = variant.get('cosmic_id')
        if cosmic_id:
            assoc_with.append(f'{schemas.XrefSystem.COSMIC.value}:{cosmic_id}')
        ens_id = variant.get('ensembl_id')
        if ens_id:
            assoc_with.append(f'{schemas.XrefSystem.ENSEMBL.value}:{ens_id}')
        if assoc_with:
            vod['extensions'] = [
                schemas.Extension(
                    name="associated_with",
                    value=assoc_with
                ).dict()
            ]

        self.transformed['variation_descriptors'][label] = vod
        return [vod]

    def _get_methods(self):
        """Build Method object for PMKB.
        :return: List (len == 1) containing the PMKB method object, as a dict.
        """
        method = self.transformed['method']
        if not method:
            method_id = f'method:{schemas.MethodID.PMKB.value}'
            method = schemas.Method(
                id=method_id,
                label='The cancer precision medicine knowledge base for structured clinical-grade mutations and interpretations',  # noqa: E501
                url='https://academic.oup.com/jamia/article/24/3/513/2418181',
                authors='Huang et al.',
                version=schemas.Date(year=2016,
                                     month=5).dict(exclude_none=True)
            ).dict()
            self.transformed['method'] = method
        return [method]

    def _get_tr_proposition(self, v_descriptors, t_descriptors,
                            d_descriptors, propositions_documents_ix):
        """Return a proposition. All descriptor inputs should be len == 1.
        :param List v_descriptors: List of VariationDescriptors
        :param List t_descriptors: List of TherapyDescriptors
        :param List d_descriptors: List of DiseaseDescriptors
        :param Dict propositions_documents_ix: Keeps track of
            proposition and document indices
        :return: Therapeutic Response proposition (dict).
        """
        prop_type = "therapeutic_response"
        prop_predicate = "predicts_resistance_to"
        prop_subject = v_descriptors[0]['value_id']
        prop_object_q = d_descriptors[0]['value']['id']
        prop_object = t_descriptors[0]['value']['id']
        key = (prop_type, prop_predicate, prop_subject, prop_object_q,
               prop_object)

        proposition = self.transformed['propositions'].get(key)
        if proposition:
            return proposition

        prop_id = self._set_ix(propositions_documents_ix, 'propositions', key)
        proposition = schemas.TherapeuticResponseProposition(
            id=f"proposition:{prop_id}",
            type=prop_type,
            predicate=prop_predicate,
            subject=prop_subject,
            object_qualifier=prop_object_q,
            object=prop_object,
        ).dict(exclude_none=True)

        self.transformed['propositions'][key] = proposition
        return proposition

    def _get_documents(self, record, propositions_documents_ix):
        """Get Document objects from statement.
        :param Dict record: PMKB interpretation, formatted as a statement
        :param Dict propositions_documents_ix: Keeps track of
            proposition and document indices
        :return: List of Document objects
        """
        docs = self.transformed['documents']
        cites = []
        for cite in record['evidence_items']:
            doc = docs.get(cite)
            if doc:
                cites.append(doc)
                continue

            ix = self._set_ix(propositions_documents_ix, 'documents', cite)
            doc = schemas.Document(
                id=f"document:{ix}",
                label=cite,
            ).dict(exclude_none=True)
            docs[cite] = doc
            cites.append(doc)
        return cites

    def _get_statement(self, statement, proposition, v_descriptors,
                       t_descriptors, d_descriptors, method, documents):
        """Construct Statement object. All descriptor objects should be len 1.
        :param Dict statement: harvested Statement from PMKB
        :param Dict proposition: transformed Proposition
        :param List v_descriptors: Variation Descriptors connected to this
            Statement
        :param List t_descriptors: Therapy Descriptors connected to this
            Statement
        :param List d_descriptors: Disease Descriptors connected to this
            Statement
        :param Dict method: Method used in the interpretation
        :param List documents: list of Document objects supporting this
            Statement
        :return: transformed Statement object
        """
        v_descriptor = v_descriptors[0]
        statement = schemas.Statement(
            id=f"{schemas.NamespacePrefix.PMKB.value}:{statement['id']}",
            description=statement['description'],
            evidence_level=statement['pmkb_evidence_tier'],
            proposition=proposition['id'],
            variation_descriptor=v_descriptor['id'],
            therapy_descriptor=t_descriptors[0]['id'],
            disease_descriptor=d_descriptors[0]['id'],
            method=method['id'],
            supported_by=[d['id'] for d in documents],
        ).dict(exclude_none=True)
        origin = v_descriptor.get('origin')
        if origin:
            statement['variation_origin'] = origin

        return statement

    def _set_ix(self, propositions_documents_ix, dict_key, search_key):
        """Set indexes for documents or propositions.

        :param dict propositions_documents_ix: Keeps track of
            proposition and documents indexes
        :param str dict_key: one of {'sources','propositions'}
        :param Any search_key: The key to get or set
        :return: An int representing the index
        """
        if dict_key == 'documents':
            dict_key_ix = 'document_index'
        elif dict_key == 'propositions':
            dict_key_ix = 'proposition_index'
        else:
            raise KeyError("dict_key can only be `documents` or "
                           "`propositions`.")
        if propositions_documents_ix[dict_key].get(search_key):
            index = propositions_documents_ix[dict_key].get(search_key)
        else:
            index = propositions_documents_ix.get(dict_key_ix)
            propositions_documents_ix[dict_key][search_key] = index
            propositions_documents_ix[dict_key_ix] += 1
        return index
