"""A module for the CIViC harvester."""
import logging
from typing import Dict, List, Optional, Union

from civicpy import civic as civicpy

from metakb.harvesters.base import Harvester  # noqa: I202

logger = logging.getLogger("metakb.harvesters.civic")
logger.setLevel(logging.DEBUG)


class CIViCHarvester(Harvester):
    """A class for the CIViC harvester."""

    def harvest(self, filename: Optional[str] = None,
                update_cache: bool = False) -> bool:
        """Retrieve and store evidence, gene, variant, and assertion
        records from CIViC in composite and individual JSON files.

        :param Optional[str] filename: File name for composite json
        :param bool update_cache: `True` if civicpy cache should be updated. Note
            this will take several minutes. `False` if to use local cache.
        :return: `True` if operation was successful, `False` otherwise.
        :rtype: bool
        """
        try:
            if update_cache:
                civicpy.update_cache(from_remote_cache=False)

            civicpy.load_cache(on_stale="ignore")

            self.evidence = self.harvest_evidence()
            self.genes = self.harvest_genes()
            self.variants = self.harvest_variants()
            self.assertions = self.harvest_assertions()

            json_created = self.create_json(
                {
                    "evidence": self.evidence,
                    "genes": self.genes,
                    "variants": self.variants,
                    "assertions": self.assertions
                },
                filename
            )
            if not json_created:
                logger.error("CIViC Harvester was not successful.")
                return False
        except Exception as e:  # noqa: E722
            logger.error(f"CIViC Harvester was not successful: {e}")
            return False
        else:
            logger.info("CIViC Harvester was successful.")
            return True

    @staticmethod
    def _get_all_evidence() -> List[civicpy.Evidence]:
        """Return all evidence item records.

        :return: All civicpy evidence item records
        """
        return civicpy.get_all_evidence()

    def harvest_evidence(self) -> List[Dict]:
        """Harvest all CIViC evidence item records.

        :return: A list of all CIViC evidence item records.
        """
        evidence_items = self._get_all_evidence()
        evidence = list()

        for ev in evidence_items:
            ev_record = self._evidence_item(self._get_dict(ev), is_evidence=True)
            evidence.append(ev_record)
        return evidence

    @staticmethod
    def _get_all_genes() -> List[civicpy.Gene]:
        """Return all gene records.

        :return: All civicpy gene records
        """
        return civicpy.get_all_genes()

    def harvest_genes(self) -> List[Dict]:
        """Harvest all CIViC gene records.

        :return: A list of all CIViC gene records.
        """
        genes = self._get_all_genes()
        genes_list = list()
        for gene in genes:
            g = self._harvest_gene(self._get_dict(gene))
            genes_list.append(g)
        return genes_list

    @staticmethod
    def _get_all_variants() -> List[civicpy.Variant]:
        """Return all variant records.

        :return: All civicpy variant records
        """
        return civicpy.get_all_variants()

    def harvest_variants(self) -> List[Dict]:
        """Harvest all CIViC variant records.

        :return: A list of all CIViC variant records.
        """
        variants = self._get_all_variants()
        variants_list = list()

        for variant in variants:
            v = self._harvest_variant(self._get_dict(variant))
            variants_list.append(v)
        return variants_list

    @staticmethod
    def _get_all_assertions() -> List[civicpy.Assertion]:
        """Return all assertion records.

        :return: All civicpy assertion records
        """
        return civicpy.get_all_assertions()

    def harvest_assertions(self) -> List[Dict]:
        """Harvest all CIViC assertion records.

        :return: A list of all CIViC assertion records.
        """
        assertions = self._get_all_assertions()
        assertions_list = list()

        for assertion in assertions:
            a = self._harvest_assertion(self._get_dict(assertion))
            assertions_list.append(a)
        return assertions_list

    def _harvest_gene(self, gene: Dict) -> Dict:
        """Harvest an individual CIViC gene record.

        :param Dict gene: A CIViC gene object represented as a dictionary
        :return: A dictionary containing CIViC gene data
        """
        g = {
            "id": gene["id"],
            "name": gene["name"],
            "entrez_id": gene["entrez_id"],
            "description": gene["description"],
            "variants": [
                {
                    "name": self._get_dict(variant)["name"],
                    "id": self._get_dict(variant)["id"],
                    "evidence_items": self._get_dict(variant)["_evidence_items"]
                }
                for variant in gene["_variants"]
            ],
            "aliases": gene["aliases"],
            # TODO: Add lifecycle_actions, sources
            "type": gene["type"]
        }

        for v in g["variants"]:
            evidence_items = {
                "accepted_count": 0,
                "rejected_count": 0,
                "submitted_count": 0
            }
            for e in v["evidence_items"]:
                e = self._get_dict(e)
                if e["status"] == "submitted":
                    evidence_items["submitted_count"] += 1
                elif e["status"] == "rejected":
                    evidence_items["rejected_count"] += 1
                elif e["status"] == "accepted":
                    evidence_items["accepted_count"] += 1
            v["evidence_items"] = evidence_items

        return g

    def _harvest_variant(self, variant: Dict) -> Dict:
        """Harvest an individual CIViC variant record.

        :param Dict variant: A CIViC variant object represented as a dictionary
        :return: A dictionary containing CIViC variant data
        """
        v = self._variant(variant)

        # Add more attributes to variant data
        v_extra = {
            "evidence_items": [
                self._evidence_item(self._get_dict(evidence_item))
                for evidence_item in variant["_evidence_items"]
            ],
            "variant_groups": [
                {
                    "id": self._get_dict(variant_group)["id"],
                    "name": self._get_dict(variant_group)["name"],
                    "description":
                        self._get_dict(variant_group)["description"],
                    "variants": [
                        self._variant(self._get_dict(variant))
                        for variant in self._get_dict(variant_group)["_variants"]
                    ],
                    "type": self._get_dict(variant_group)["type"]
                }
                for variant_group in variant["_variant_groups"]
            ],
            "assertions": [
                self._assertion(self._get_dict(assertion))
                for assertion in variant["_assertions"]
            ],
            "variant_aliases": variant["variant_aliases"],
            "hgvs_expressions": variant["hgvs_expressions"],
            "clinvar_entries": variant["clinvar_entries"],
            # TODO: Add lifecycle_actions
            "allele_registry_id": variant["allele_registry_id"],
            # TODO: Add allele_registry_hgvs
        }
        v.update(v_extra)
        return v

    def _harvest_assertion(self, assertion: Dict) -> Dict:
        """Harvest an individual CIViC assertion record.

        :param Dict assertion: A CIViC assertion object represented as a dictionary
        :return: A dictionary containing CIViC assertion data
        """
        def _acmg_code(obj: civicpy.CivicAttribute) -> Dict:
            """Get dictionary representation of CIViC ACMG Code

            :param civicpy.CivicAttribute obj: CIViC ACMG Code
            :return: ACMG Code represented as a dictionary
            """
            acmg_code = self._get_dict(obj)
            return {
                "id": acmg_code["id"],
                "code": acmg_code["code"],
                "description": acmg_code["description"]
            }

        a = self._assertion(assertion)

        # Add more attributes to assertion data
        a_extra = {
            "nccn_guideline": assertion["nccn_guideline"],
            "nccn_guideline_version": assertion["nccn_guideline_version"],
            "amp_level": assertion["amp_level"],
            "evidence_items": [
                self._evidence_item(self._get_dict(evidence_item), is_assertion=True)
                for evidence_item in assertion["_evidence_items"]
            ],
            "acmg_codes": [_acmg_code(acmg_code)
                           for acmg_code in assertion["acmg_codes"]],
            "drug_interaction_type": assertion["drug_interaction_type"],
            "fda_companion_test": assertion["fda_companion_test"],
            "phenotypes": self._phenotypes(assertion["phenotypes"]),
            "variant_origin": assertion["variant_origin"]
            # TODO: Add lifecycle_actions
        }
        a.update(a_extra)
        return a

    def _evidence_item(self, evidence_item: Dict, is_evidence: bool = False,
                       is_assertion: bool = False) -> Dict:
        """Get evidence item data.

        :param Dict evidence_item: A CIViC Evidence record represented as a dictionary
        :param bool is_evidence: Whether or not the evidence item is
                                 being harvested in an evidence record
        :param bool is_assertion: Whether or not the evidence item is
                                  being harvested in an assertion record
        :return: A dictionary containing evidence item data
        """
        disease = self._get_dict(evidence_item["disease"])
        if not disease:
            disease = None
        else:
            disease = {
                "id": disease["id"],
                "name": disease["name"],
                "display_name": disease["display_name"],
                "doid": disease["doid"],
                "disease_url": disease["disease_url"]
            }

        source = self._get_dict(evidence_item["source"])
        source = {
            "id": source["id"],
            "name": source["name"],
            "citation": source["citation"],
            "citation_id": source["citation_id"],
            "source_type": source["source_type"],
            "asco_abstract_id": source["asco_abstract_id"],
            "source_url": source["source_url"],
            "pmc_id": source["pmc_id"],
            "publication_date": source["publication_date"],
            "journal": source["journal"],
            "full_journal_title": source["full_journal_title"],
            "clinical_trials": [ct for ct in source["clinical_trials"]]
        }

        e = {
            "id": evidence_item["id"],
            "name": evidence_item["name"],
            "description": evidence_item["description"],
            "disease": disease,
            "drugs": [
                self._drug(self._get_dict(drug))
                for drug in evidence_item["drugs"]
            ],
            "rating": evidence_item["rating"],
            "evidence_level": evidence_item["evidence_level"],
            "evidence_type": evidence_item["evidence_type"],
            "clinical_significance": evidence_item["clinical_significance"],
            "evidence_direction": evidence_item["evidence_direction"],
            "variant_origin": evidence_item["variant_origin"],
            "drug_interaction_type": evidence_item["drug_interaction_type"],
            "status": evidence_item["status"],
            # TODO: Add open_change_count
            "type": evidence_item["type"],
            "source": source,
            "variant_id": evidence_item["variant_id"],
            "phenotypes": self._phenotypes(evidence_item["phenotypes"])
        }

        # Assertions and Evidence Items contain more attributes
        if is_assertion or is_evidence:
            e["assertions"] = [
                self._assertion(self._get_dict(assertion))
                for assertion in evidence_item["_assertions"]
            ]
            # TODO: Add lifecycle_actions, fields_with_pending_changes
            e["gene_id"] = evidence_item["gene_id"]
            if is_assertion:
                # TODO: Add state_params
                pass

        return e

    def _phenotypes(self, phenotypes: List) -> List[Dict]:
        """Get phenotype data

        :param List phenotypes: List of civic phenotype records
        :return: List of transformed phenotypes represented as dictionaries
        """
        transformed_phenotypes = list()
        for p in phenotypes:
            p = self._get_dict(p)
            transformed_phenotypes.append({
                "id": p["id"],
                "name": p["name"],
                "hpo_id": p["hpo_id"],
                "url": p["url"],
                "type": p["type"]
            })
        return transformed_phenotypes

    def _variant(self, variant: Dict) -> Dict:
        """Get basic variant data.

        :param Dict variant: A CIViC Variant record represented as a dictionary
        :return: A dictionary containing variant data
        """
        return {
            "id": variant["id"],
            "entrez_name": variant["entrez_name"],
            "entrez_id": variant["entrez_id"],
            "name": variant["name"],
            "description": variant["description"],
            "gene_id": variant["gene_id"],
            "type": variant["type"],
            "variant_types": [
                self._variant_types(self._get_dict(variant_type))
                for variant_type in variant["variant_types"]
            ],
            "civic_actionability_score":
                int(variant["civic_actionability_score"]) if int(variant["civic_actionability_score"]) == variant["civic_actionability_score"] else variant["civic_actionability_score"],  # noqa: E501
            "coordinates": self._variant_coordinates(variant)
        }

    def _assertion(self, assertion: Dict) -> Dict:
        """Get assertion data.

        :param Dict assertion: A CIViC Assertion record represented as a dictionary
        :return: A dictionary containing assertion data
        """
        disease = self._get_dict(assertion["disease"])
        return {
            "id": assertion["id"],
            "type": assertion["type"],
            "name": assertion["name"],
            "summary": assertion["summary"],
            "description": assertion["description"],
            "gene_id": assertion["gene_id"],
            "variant_id": assertion["variant_id"],
            "disease": {
                "id": disease["id"],
                "name": disease["name"],
                "display_name": disease["display_name"],
                "doid": disease["doid"],
                "disease_url": disease["disease_url"]
            },
            "drugs": [
                self._drug(self._get_dict(drug))
                for drug in assertion["drugs"]
            ],
            "evidence_type": assertion["evidence_type"],
            "evidence_direction": assertion["evidence_direction"],
            "clinical_significance": assertion["clinical_significance"],
            # TODO: Add evidence_item_count
            "fda_regulatory_approval":
                assertion["fda_regulatory_approval"],
            "status": assertion["status"],
            # TODO: Add open_change_count, pending_evidence_count
        }

    def _variant_coordinates(self, variant: Dict) -> Dict:
        """Get a variant's coordinates.

        :param Dict variant: A CIViC variant record represented as a dictionary
        :return: A dictionary containing a variant's coordinates
        """
        coordinates = self._get_dict(variant["coordinates"])
        return {
            "chromosome": coordinates["chromosome"],
            "start": coordinates["start"],
            "stop": coordinates["stop"],
            "reference_bases": coordinates["reference_bases"],
            "variant_bases": coordinates["variant_bases"],
            "representative_transcript": coordinates["representative_transcript"],
            "chromosome2": coordinates["chromosome2"],
            "start2": coordinates["start2"],
            "stop2": coordinates["stop2"],
            "representative_transcript2": coordinates["representative_transcript2"],
            "ensembl_version": coordinates["ensembl_version"],
            "reference_build": coordinates["reference_build"]
        }

    def _variant_types(self, variant_type: Dict) -> Dict:
        """Get variant_type data.

        :param Dict variant_type: A CIViC variant_type record represented as a
            dictionary
        :return: A dictionary containing variant_type data
        """
        return {
            "id": variant_type["id"],
            "name": variant_type["name"],
            "so_id": variant_type["so_id"],
            "description": variant_type["description"],
            "url": variant_type["url"]
        }

    def _drug(self, drug: Dict) -> Dict:
        """Get drug data.

        :param Dict drug: A CIViC Drug record represented as a dictionary
        :return: A dictionary containing drug data.
        """
        drug = self._get_dict(drug)
        return {
            "id": drug["id"],
            "name": drug["name"],
            "ncit_id": drug["ncit_id"],
            "aliases": drug["aliases"]
        }

    def _get_dict(self, obj: Union[Dict, civicpy.CivicRecord]) -> Dict:
        """Return the __dict__ attribute for an object.

        :param obj: The civicpy object
        :type obj: Dict or civicpy.CivicRecord
        :return: A dictionary for the object
        """
        return vars(obj) if isinstance(obj, civicpy.CivicRecord) else obj
