"""Provide methods for loading data into the database."""

import json
import logging
from pathlib import Path

from neo4j import Driver, ManagedTransaction

from metakb.database import get_driver
from metakb.normalizers import VICC_NORMALIZER_DATA, ViccDiseaseNormalizerData

_logger = logging.getLogger(__name__)


def _create_parameterized_query(
    entity: dict, params: tuple[str, ...], entity_param_prefix: str = ""
) -> str:
    """Create parameterized query string for requested params if non-null in entity.

    :param entity: entity to check against, eg a Variation or Statement
    :param params: Parameter names to check
    :param entity_param_prefix: Prefix for parameter names in entity object
    :return: Parameterized query, such as (`name:$name`)
    """
    nonnull_keys = [
        f"{key}:${entity_param_prefix}{key}" for key in params if entity.get(key)
    ]
    return ", ".join(nonnull_keys)


def _add_mappings_and_exts_to_obj(obj: dict, obj_keys: list[str]) -> None:
    """Get mappings and extensions from object and add to `obj` and `obj_keys`

    :param obj: Object to update with mappings and extensions (if found)
    :param obj_keys: Parameterized queries. This will be mutated if mappings and
        extensions exists
    """
    mappings = obj.get("mappings", [])
    if mappings:
        obj["mappings"] = json.dumps(mappings)
        obj_keys.append("mappings:$mappings")

    extensions = obj.get("extensions", [])
    for ext in extensions:
        if ext["name"] == VICC_NORMALIZER_DATA:
            for normalized_field in ViccDiseaseNormalizerData.model_fields:
                normalized_val = ext["value"].get(normalized_field)
                if normalized_val is None:
                    continue

                name = f"normalizer_{normalized_field}"
                obj[name] = normalized_val
                obj_keys.append(f"{name}:${name}")
        else:
            name = "_".join(ext["name"].split()).lower()
            val = ext["value"]
            if isinstance(val, (dict | list)):
                obj[name] = json.dumps(val)
            else:
                obj[name] = val
            obj_keys.append(f"{name}:${name}")


def _add_method(tx: ManagedTransaction, method: dict, ids_in_studies: set[str]) -> None:
    """Add Method node and its relationships to DB

    :param tx: Transaction object provided to transaction functions
    :param method: CDM method object
    :param ids_in_studies: IDs found in studies
    """
    if method["id"] not in ids_in_studies:
        return

    query = """
    MERGE (m:Method {id:$id, label:$label})
    """

    is_reported_in = method.get("reportedIn")
    if is_reported_in:
        # Method's documents are unique and do not currently have IDs
        # They also only have one document
        document = is_reported_in[0]
        _add_document(tx, document, ids_in_studies)
        doc_doi = document["doi"]
        query += f"""
        MERGE (d:Document {{ doi:'{doc_doi}' }})
        MERGE (m) -[:IS_REPORTED_IN] -> (d)
        """

    tx.run(query, **method)


def _add_gene_or_disease(
    tx: ManagedTransaction, obj_in: dict, ids_in_studies: set[str]
) -> None:
    """Add gene or disease node and its relationships to DB

    :param tx: Transaction object provided to transaction functions
    :param obj_in: CDM gene or disease object
    :param ids_in_studies: IDs found in studies
    :raises TypeError: When `obj_in` is not a disease or gene
    """
    if obj_in["id"] not in ids_in_studies:
        return

    obj = obj_in.copy()

    obj_type = obj["type"]
    if obj_type not in {"Gene", "Disease"}:
        msg = f"Invalid object type: {obj_type}"
        raise TypeError(msg)

    obj_keys = [
        _create_parameterized_query(
            obj, ("id", "label", "description", "alternativeLabels", "type")
        )
    ]

    _add_mappings_and_exts_to_obj(obj, obj_keys)
    obj_keys = ", ".join(obj_keys)

    if obj_type == "Gene":
        query = f"MERGE (g:Gene {{ {obj_keys} }});"
    else:
        query = f"MERGE (d:Disease:Condition {{ {obj_keys} }});"
    tx.run(query, **obj)


def _add_therapeutic_procedure(
    tx: ManagedTransaction,
    therapeutic_procedure: dict,
    ids_in_studies: set[str],
) -> None:
    """Add therapeutic procedure node and its relationships

    :param tx: Transaction object provided to transaction functions
    :param therapeutic_procedure: Therapeutic procedure CDM object
    :param ids_in_studies: IDs found in studies
    :raises TypeError: When therapeutic procedure type is invalid
    """
    if therapeutic_procedure["id"] not in ids_in_studies:
        return

    tp = therapeutic_procedure.copy()

    tp_type = tp["type"]
    if tp_type == "TherapeuticAgent":
        _add_therapeutic_agent(tx, tp)
    elif tp_type in {"CombinationTherapy", "TherapeuticSubstituteGroup"}:
        keys = [_create_parameterized_query(tp, ("id", "type"))]

        _add_mappings_and_exts_to_obj(tp, keys)
        keys = ", ".join(keys)

        query = f"MERGE (tp:{tp_type}:TherapeuticProcedure {{ {keys} }})"
        tx.run(query, **tp)

        tas = tp["components"] if tp_type == "CombinationTherapy" else tp["substitutes"]
        for ta in tas:
            _add_therapeutic_agent(tx, ta)
            query = f"""
            MERGE (tp:{tp_type}:TherapeuticProcedure {{id: '{tp['id']}'}})
            MERGE (ta:TherapeuticAgent:TherapeuticProcedure {{id: '{ta['id']}'}})
            """

            if tp_type == "CombinationTherapy":
                query += "MERGE (tp) -[:HAS_COMPONENTS] -> (ta)"
            else:
                query += "MERGE (tp) -[:HAS_SUBSTITUTES] -> (ta)"

            tx.run(query)
    else:
        msg = f"Invalid therapeutic procedure type: {tp_type}"
        raise TypeError(msg)


def _add_therapeutic_agent(tx: ManagedTransaction, therapeutic_agent: dict) -> None:
    """Add therapeutic agent node and its relationships

    :param tx: Transaction object provided to transaction functions
    :param therapeutic_agent: Therapeutic Agent CDM object
    """
    ta = therapeutic_agent.copy()
    nonnull_keys = [
        _create_parameterized_query(ta, ("id", "label", "alternativeLabels", "type"))
    ]

    _add_mappings_and_exts_to_obj(ta, nonnull_keys)
    nonnull_keys = ", ".join(nonnull_keys)

    query = f"""
    MERGE (ta:TherapeuticAgent:TherapeuticProcedure {{ {nonnull_keys} }})
    """
    tx.run(query, **ta)


def _add_location(tx: ManagedTransaction, location_in: dict) -> None:
    """Add location node and its relationships

    :param tx: Transaction object provided to transaction functions
    :param location_in: Location CDM object
    """
    loc = location_in.copy()
    loc_keys = [
        f"loc.{key}=${key}"
        for key in ("id", "digest", "start", "end", "sequence", "type")
        if loc.get(key) is not None  # start could be 0
    ]
    loc["sequence_reference"] = json.dumps(loc["sequenceReference"])
    loc_keys.append("loc.sequence_reference=$sequence_reference")
    loc_keys = ", ".join(loc_keys)

    query = f"""
    MERGE (loc:{loc['type']}:Location {{ id: '{loc['id']}' }})
    ON CREATE SET {loc_keys}
    """
    tx.run(query, **loc)


def _add_variation(tx: ManagedTransaction, variation_in: dict) -> None:
    """Add variation node and its relationships

    :param tx: Transaction object provided to transaction functions
    :param variation_in: Variation CDM object
    """
    v = variation_in.copy()
    v_keys = [
        f"v.{key}=${key}" for key in ("id", "label", "digest", "type") if v.get(key)
    ]

    expressions = v.get("expressions", [])
    for expr in expressions:
        syntax = expr["syntax"].replace(".", "_")
        key = f"expression_{syntax}"
        if key in v:
            v[key].append(expr["value"])
        else:
            v_keys.append(f"v.{key}=${key}")
            v[key] = [expr["value"]]

    state = v.get("state")
    if state:
        v["state"] = json.dumps(state)
        v_keys.append("v.state=$state")

    v_keys = ", ".join(v_keys)

    query = f"""
    MERGE (v:{v['type']}:Variation {{ id: '{v['id']}' }})
    ON CREATE SET {v_keys}
    """

    loc = v.get("location")
    if loc:
        _add_location(tx, loc)
        query += f"""
        MERGE (loc:{loc['type']}:Location {{ id: '{loc['id']}' }})
        MERGE (v) -[:HAS_LOCATION] -> (loc)
        """

    tx.run(query, **v)


def _add_categorical_variation(
    tx: ManagedTransaction,
    categorical_variation_in: dict,
    ids_in_studies: set[str],
) -> None:
    """Add categorical variation objects to DB.

    :param tx: Transaction object provided to transaction functions
    :param categorical_variation_in: Categorical variation CDM object
    :param ids_in_studies: IDs found in studies
    """
    if categorical_variation_in["id"] not in ids_in_studies:
        return

    cv = categorical_variation_in.copy()

    mp_nonnull_keys = [
        _create_parameterized_query(
            cv, ("id", "label", "description", "alternativeLabels", "type")
        )
    ]

    _add_mappings_and_exts_to_obj(cv, mp_nonnull_keys)
    mp_keys = ", ".join(mp_nonnull_keys)

    defining_context = cv["constraints"][0]["definingContext"]
    _add_variation(tx, defining_context)
    dc_type = defining_context["type"]

    members_match = ""
    members_relation = ""
    for ix, member in enumerate(cv.get("members", [])):
        _add_variation(tx, member)
        name = f"member_{ix}"
        cv[name] = member
        members_match += f"MERGE ({name} {{ id: '{member['id']}' }})\n"
        members_relation += f"MERGE (v) -[:HAS_MEMBERS] -> ({name})\n"

    query = f"""
    {members_match}
    MERGE (dc:Variation:{dc_type} {{ id: '{defining_context['id']}' }})
    MERGE (dc) -[:HAS_LOCATION] -> (loc)
    MERGE (v:Variation:{cv['type']} {{ {mp_keys} }})
    MERGE (v) -[:HAS_DEFINING_CONTEXT] -> (dc)
    {members_relation}
    """
    tx.run(query, **cv)


def _add_document(
    tx: ManagedTransaction, document_in: dict, ids_in_studies: set[str]
) -> None:
    """Add Document object to DB.

    :param tx: Transaction object provided to transaction functions
    :param document: Document CDM object
    :param ids_in_studies: IDs found in studies
    """
    # Not all document's have IDs. These are the fields that can uniquely identify
    # a document
    if "id" in document_in:
        query = "MATCH (n:Document {id:$id}) RETURN n"
        if document_in["id"] not in ids_in_studies:
            return
    elif "doi" in document_in:
        query = "MATCH (n:Document {doi:$doi}) RETURN n"
    elif "pmid" in document_in:
        query = "MATCH (n:Document {pmid:$pmid}) RETURN n"
    else:
        query = None

    result = tx.run(query, **document_in) if query else None

    if (not result) or (result and not result.single()):
        document = document_in.copy()
        formatted_keys = [
            _create_parameterized_query(
                document, ("id", "label", "title", "pmid", "urls", "doi")
            )
        ]

        _add_mappings_and_exts_to_obj(document, formatted_keys)
        formatted_keys = ", ".join(formatted_keys)

        query = f"""
        MERGE (n:Document {{ {formatted_keys} }});
        """
        tx.run(query, **document)


def _get_ids_from_studies(studies: list[dict]) -> set[str]:
    """Get unique IDs from studies

    :param studies: List of studies
    :return: Set of IDs found in studies
    """

    def _add_obj_id_to_set(obj: dict, ids_set: set[str]) -> None:
        """Add object id to set of IDs

        :param obj: Object to get ID for
        :param ids_set: IDs found in studies. This will be mutated.
        """
        obj_id = obj.get("id")
        if obj_id:
            ids_set.add(obj_id)

    ids_in_studies = set()

    for study in studies:
        for obj in [
            study.get("specifiedBy"),  # method
            study.get("reportedIn"),
            study.get("subjectVariant"),
            study.get("objectTherapeutic"),
            study.get("conditionQualifier"),
            study.get("geneContextQualifier"),
        ]:
            if obj:
                if isinstance(obj, list):
                    for item in obj:
                        _add_obj_id_to_set(item, ids_in_studies)
                else:  # This is a dictionary
                    _add_obj_id_to_set(obj, ids_in_studies)

    return ids_in_studies


def _add_study(tx: ManagedTransaction, study_in: dict) -> None:
    """Add study node and its relationships

    :param tx: Transaction object provided to transaction functions
    :param study_in: Statement CDM object
    """
    study = study_in.copy()
    study_type = study["type"]
    study_keys = _create_parameterized_query(
        study, ("id", "description", "direction", "predicate", "type")
    )

    match_line = ""
    rel_line = ""

    is_reported_in_docs = study.get("reportedIn", [])
    for ri_doc in is_reported_in_docs:
        ri_doc_id = ri_doc["id"]
        name = f"doc_{ri_doc_id.split(':')[-1]}"
        match_line += f"MERGE ({name} {{ id: '{ri_doc_id}'}})\n"
        rel_line += f"MERGE (s) -[:IS_REPORTED_IN] -> ({name})\n"

    allele_origin = study.get("alleleOriginQualifier")
    if allele_origin:
        study["alleleOriginQualifier"] = allele_origin
        match_line += "SET s.alleleOriginQualifier=$alleleOriginQualifier\n"

    gene_context_id = study.get("geneContextQualifier", {}).get("id")
    if gene_context_id:
        match_line += f"MERGE (g:Gene {{id: '{gene_context_id}'}})\n"
        rel_line += "MERGE (s) -[:HAS_GENE_CONTEXT] -> (g)\n"

    method_id = study["specifiedBy"]["id"]
    match_line += f"MERGE (m {{ id: '{method_id}' }})\n"
    rel_line += "MERGE (s) -[:IS_SPECIFIED_BY] -> (m)\n"

    coding = study.get("strength")
    if coding:
        coding_key_fields = ("code", "label", "system")

        coding_keys = _create_parameterized_query(
            coding, coding_key_fields, entity_param_prefix="coding_"
        )
        for k in coding_key_fields:
            v = coding.get(k)
            if v:
                study[f"coding_{k}"] = v

        match_line += f"MERGE (c:Coding {{ {coding_keys} }})\n"
        rel_line += "MERGE (s) -[:HAS_STRENGTH] -> (c)\n"

    variant_id = study["subjectVariant"]["id"]
    match_line += f"MERGE (v:Variation {{ id: '{variant_id}' }})\n"
    rel_line += "MERGE (s) -[:HAS_VARIANT] -> (v)\n"

    therapeutic_id = study["objectTherapeutic"]["id"]
    match_line += f"MERGE (t:TherapeuticProcedure {{ id: '{therapeutic_id}' }})\n"
    rel_line += "MERGE (s) -[:HAS_THERAPEUTIC] -> (t)\n"

    tumor_type_id = study["conditionQualifier"]["id"]
    match_line += f"MERGE (tt:Condition {{ id: '{tumor_type_id}' }})\n"
    rel_line += "MERGE (s) -[:HAS_TUMOR_TYPE] -> (tt)\n"

    query = f"""
    MERGE (s:{study_type}:StudyStatement:Statement {{ {study_keys} }})
    {match_line}
    {rel_line}
    """

    tx.run(query, **study)


def add_transformed_data(driver: Driver, data: dict) -> None:
    """Add set of data formatted per Common Data Model to DB.

    :param data: contains key/value pairs for data objects to add to DB, including
        studies, variation, therapeutic procedures, conditions, genes, methods,
        documents, etc.
    """
    # Used to keep track of IDs that are in studies. This is used to prevent adding
    # nodes that aren't associated to studies
    ids_in_studies = _get_ids_from_studies(data.get("studies", []))

    with driver.session() as session:
        loaded_study_count = 0

        for cv in data.get("categorical_variants", []):
            session.execute_write(_add_categorical_variation, cv, ids_in_studies)

        for doc in data.get("documents", []):
            session.execute_write(_add_document, doc, ids_in_studies)

        for method in data.get("methods", []):
            session.execute_write(_add_method, method, ids_in_studies)

        for obj_type in {"genes", "conditions"}:
            for obj in data.get(obj_type, []):
                session.execute_write(_add_gene_or_disease, obj, ids_in_studies)

        for tp in data.get("therapeutic_procedures", []):
            session.execute_write(_add_therapeutic_procedure, tp, ids_in_studies)

        # This should always be done last
        for study in data.get("studies", []):
            session.execute_write(_add_study, study)
            loaded_study_count += 1

        _logger.info("Successfully loaded %s studies.", loaded_study_count)


def load_from_json(src_transformed_cdm: Path, driver: Driver | None = None) -> None:
    """Load evidence into DB from given CDM JSON file.

    :param src_transformed_cdm: path to file for a source's transformed data to
        common data model containing studies, variation, therapeutic procedures,
        conditions, genes, methods, documents, etc.
    :param driver: Neo4j graph driver, if available
    """
    _logger.info("Loading data from %s", src_transformed_cdm)
    if not driver:
        driver = get_driver()
    with src_transformed_cdm.open() as f:
        items = json.load(f)
        add_transformed_data(driver, items)
