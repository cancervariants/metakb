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
        evidence = []

        for ev in evidence_items:
            ev_record = self._evidence_item(self._get_dict(ev))
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
        genes_list = []
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
        variants_list = []

        for variant in variants:
            v = self._harvest_variant(self._get_dict(variant))
            variants_list.append(v)
        return variants_list

    @staticmethod
    def _get_all_molecular_profiles() -> List[civicpy.MolecularProfile]:
        """Return all Molecular Profiles

        :return: All civicpy molecular profile records
        """
        return civicpy.get_all_molecular_profiles()

    def harvest_molecular_profiles(self) -> List[Dict]:
        """Harvest all CIViC Molecular Profile records

        :return: A list of all CIViC molecular profile records
        """
        molecular_profiles = self._get_all_molecular_profiles()
        molecular_profiles_list = []

        for molecular_profile in molecular_profiles:
            mp = self._harvest_molecular_profile(self._get_dict(molecular_profile))
            molecular_profiles_list.append(mp)
        return molecular_profiles_list

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
        assertions_list = []

        for assertion in assertions:
            a = self._harvest_assertion(self._get_dict(assertion))
            assertions_list.append(a)
        return assertions_list

    def _harvest_gene(self, gene: Dict) -> Dict:
        """Harvest an individual CIViC gene record.

        :param Dict gene: A CIViC gene object represented as a dictionary
        :return: A dictionary containing CIViC gene data
        """
        def _variant(variant: Dict) -> Dict:
            """Get a gene's variant data

            :param Dict variant: CIViC variant
            :return: CIViC variant data for a gene
            """
            v = self._get_dict(variant)
            return {
                "name": v["name"],
                "id": v["id"],
                "single_variant_molecular_profile_id": v["single_variant_molecular_profile_id"]  # noqa: E501
            }

        return {
            "id": gene["id"],
            "name": gene["name"],
            "entrez_id": gene["entrez_id"],
            "description": gene["description"],
            "variants": [
                _variant(variant) for variant in gene["_variants"]
            ],
            "aliases": gene["aliases"],
            "type": gene["type"]
        }

    def _harvest_molecular_profile(self, molecular_profile: Dict) -> Dict:
        """Harvest an individual CIViC molecular profile record.

        :param Dict molecular_profile: A CIViC molecular profile represented as a
            dictionary
        :return: A dictionary containing CIViC molecular profile data
        """
        return {
            "evidence_items": [self._get_dict(ev)["id"]
                               for ev in molecular_profile["_evidence_items"]],
            "assertions": [self._get_dict(a)["id"]
                           for a in molecular_profile["_assertions"]],
            "variant_ids": molecular_profile["variant_ids"],
            "type": molecular_profile["type"],
            "id": molecular_profile["id"],
            "name": molecular_profile["name"],
            "molecular_profile_score": molecular_profile["molecular_profile_score"],
            "description": molecular_profile["description"],
            "aliases": molecular_profile["aliases"],
            "sources": molecular_profile["sources"]
        }

    def _harvest_assertion(self, assertion: Dict) -> Dict:
        """Harvest an individual CIViC assertion record.

        :param Dict assertion: A CIViC assertion object represented as a dictionary
        :return: A dictionary containing CIViC assertion data
        """
        a = self._assertion(assertion)
        a["evidence_items"] = [
            self._evidence_item(self._get_dict(evidence_item))
            for evidence_item in assertion["_evidence_items"]
        ]
        return a

    def _evidence_item(self, evidence_item: Dict) -> Dict:
        """Get evidence item data.

        :param Dict evidence_item: A CIViC Evidence record represented as a dictionary
        :return: A dictionary containing evidence item data
        """
        source = self._get_dict(evidence_item["source"])
        source = {
            "id": source["id"],
            "name": source["name"],
            "type": source["type"],
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

        return {
            "id": evidence_item["id"],
            "name": evidence_item["name"],
            "description": evidence_item["description"],
            "disease": self._disease(evidence_item["disease"]) if evidence_item["disease"] else None,  # noqa: E501
            "therapies": [
                self._therapy(self._get_dict(therapy))
                for therapy in evidence_item["therapies"]
            ],
            "rating": evidence_item["rating"],
            "evidence_level": evidence_item["evidence_level"],
            "evidence_type": evidence_item["evidence_type"],
            "significance": evidence_item["significance"],
            "evidence_direction": evidence_item["evidence_direction"],
            "variant_origin": evidence_item["variant_origin"],
            "therapy_interaction_type": evidence_item["therapy_interaction_type"],
            "status": evidence_item["status"],
            "type": evidence_item["type"],
            "source": source,
            "molecular_profile_id": evidence_item["molecular_profile_id"],
            "phenotypes": self._phenotypes(evidence_item["phenotypes"]),
            "assertions": [
                self._assertion(self._get_dict(assertion))
                for assertion in evidence_item["_assertions"]
            ]
        }

    def _phenotypes(self, phenotypes: List) -> List[Dict]:
        """Get phenotype data

        :param List phenotypes: List of civic phenotype records
        :return: List of transformed phenotypes represented as dictionaries
        """
        transformed_phenotypes = []
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

    def _harvest_variant(self, variant: Dict) -> Dict:
        """Harvest an individual CIViC variant record.

        :param Dict variant: A CIViC variant object represented as a dictionary
        :return: A dictionary containing CIViC variant data
        """
        def _variant_groups(variant_groups: List) -> List[Dict]:
            """Get variant group data

            :param List variant_groups: List of CIViC Variant Group records
            :return: List of transformed variant groups represented as dictionaries
            """
            transformed_variant_groups = []
            for vg in variant_groups:
                vg = self._get_dict(vg)
                transformed_variant_groups.append(
                    {
                        "id": vg["id"],
                        "name": vg["name"],
                        "description": vg["description"],
                        "variant_ids": vg["variant_ids"],
                        "type": vg["type"]
                    }
                )
            return transformed_variant_groups

        return {
            "id": variant["id"],
            "entrez_name": variant["entrez_name"],
            "entrez_id": variant["entrez_id"],
            "name": variant["name"],
            "gene_id": variant["gene_id"],
            "type": variant["type"],
            "variant_types": [
                self._variant_types(self._get_dict(variant_type))
                for variant_type in variant["variant_types"]
            ],
            "variant_groups": _variant_groups(variant["_variant_groups"]),
            "coordinates": self._variant_coordinates(variant),
            "single_variant_molecular_profile_id": variant["single_variant_molecular_profile_id"],  # noqa: E501
            "variant_aliases": variant["variant_aliases"],
            "hgvs_expressions": variant["hgvs_expressions"],
            "clinvar_entries": variant["clinvar_entries"],
            "allele_registry_id": variant["allele_registry_id"]
        }

    def _assertion(self, assertion: Dict) -> Dict:
        """Get assertion data.

        :param Dict assertion: A CIViC Assertion record represented as a dictionary
        :return: A dictionary containing assertion data
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
                "description": acmg_code["description"],
                "type": acmg_code["type"]
            }

        return {
            "id": assertion["id"],
            "type": assertion["type"],
            "name": assertion["name"],
            "summary": assertion["summary"],
            "description": assertion["description"],
            "molecular_profile_id": assertion["molecular_profile_id"],
            "disease": self._disease(assertion["disease"]) if assertion["disease"] else None,  # noqa: E501
            "therapies": [
                self._therapy(self._get_dict(therapy))
                for therapy in assertion["therapies"]
            ],
            "assertion_type": assertion["assertion_type"],
            "assertion_direction": assertion["assertion_direction"],
            "significance": assertion["significance"],
            "fda_regulatory_approval":
                assertion["fda_regulatory_approval"],
            "status": assertion["status"],
            "nccn_guideline": assertion["nccn_guideline"],
            "nccn_guideline_version": assertion["nccn_guideline_version"],
            "amp_level": assertion["amp_level"],
            "therapy_interaction_type": assertion["therapy_interaction_type"],
            "fda_companion_test": assertion["fda_companion_test"],
            "variant_origin": assertion["variant_origin"],
            "acmg_codes": [_acmg_code(acmg_code)
                           for acmg_code in assertion["acmg_codes"]],
            "phenotypes": self._phenotypes(assertion["phenotypes"])
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
            "reference_build": coordinates["reference_build"],
            "type": coordinates["type"]
        }

    def _variant_types(self, variant_type: Dict) -> Dict:
        """Get variant_type data.

        :param Dict variant_type: A CIViC variant_type record represented as a
            dictionary
        :return: A dictionary containing variant_type data
        """
        return {
            "id": variant_type["id"],
            "type": variant_type["type"],
            "name": variant_type["name"],
            "so_id": variant_type["so_id"],
            "description": variant_type["description"],
            "url": variant_type["url"]
        }

    def _disease(self, disease: Dict) -> Dict:
        """Get disease data

        :param Dict disease: A CIViC Disease record represented as a dictionary
        :return: A dictionary containing disease data
        """
        disease = self._get_dict(disease)
        return {
            "id": disease["id"],
            "type": disease["type"],
            "name": disease["name"],
            "display_name": disease["display_name"],
            "doid": disease["doid"],
            "disease_url": disease["disease_url"],
            "aliases": disease["aliases"]
        }

    def _therapy(self, therapy: Dict) -> Dict:
        """Get therapy data.

        :param Dict therapy: A CIViC Therapy record represented as a dictionary
        :return: A dictionary containing therapy data.
        """
        therapy = self._get_dict(therapy)
        return {
            "id": therapy["id"],
            "type": therapy["type"],
            "name": therapy["name"],
            "ncit_id": therapy["ncit_id"],
            "aliases": therapy["aliases"]
        }

    def _get_dict(self, obj: Union[Dict, civicpy.CivicRecord]) -> Dict:
        """Return the __dict__ attribute for an object.

        :param obj: The civicpy object
        :type obj: Dict or civicpy.CivicRecord
        :return: A dictionary for the object
        """
        return vars(obj) if isinstance(obj, civicpy.CivicRecord) else obj
