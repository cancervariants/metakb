"""Provide methods for loading data into the database."""

import json
import logging
import uuid
from pathlib import Path

from ga4gh.va_spec.base import MembershipOperator
from neo4j import Driver, ManagedTransaction

from metakb.database import get_driver
from metakb.transformers.base import NormalizerExtensionName

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

    :param obj: Object to update with mappings and extensions (if found).
        If ``obj`` has Disease, Gene, or Therapy ``conceptType``, then ``normalizer_id``
        will also be added.
    :param obj_keys: Parameterized queries. This will be mutated if mappings and
        extensions exists
    """
    mappings = obj.get("mappings", [])
    if mappings:
        concept_type = obj.get("conceptType")
        if concept_type in {"Disease", "Gene", "Therapy"}:
            normalizer_id = None
            for mapping in obj["mappings"]:
                extensions = mapping.get("extensions") or []
                for ext in extensions:
                    if ext["name"] == NormalizerExtensionName.PRIORITY and ext["value"]:
                        if mapping["coding"]["id"].startswith("MONDO"):
                            normalizer_id = mapping["coding"]["code"]
                        else:
                            normalizer_id = mapping["coding"]["id"]
                        obj["normalizer_id"] = normalizer_id
                        obj_keys.append("normalizer_id:$normalizer_id")
                        break

                if normalizer_id:
                    break

        obj["mappings"] = json.dumps(mappings)
        obj_keys.append("mappings:$mappings")

    extensions = obj.get("extensions", [])
    for ext in extensions:
        name = "_".join(ext["name"].split()).lower()
        val = ext["value"]
        if isinstance(val, (dict | list)):
            obj[name] = json.dumps(val)
        else:
            obj[name] = val
        obj_keys.append(f"{name}:${name}")


def _add_method(tx: ManagedTransaction, method: dict, ids_to_load: set[str]) -> None:
    """Add Method node and its relationships to DB

    :param tx: Transaction object provided to transaction functions
    :param method: CDM method object
    :param ids_to_load: IDs to load into the DB
    """
    if method["id"] not in ids_to_load:
        return

    m_keys = [_create_parameterized_query(method, ("id", "name", "methodType"))]
    m_keys = ", ".join(m_keys)

    query = f"""
    MERGE (m:Method {{ {m_keys} }})
    """

    is_reported_in = method.get("reportedIn")
    if is_reported_in:
        # Method's documents are unique and do not currently have IDs
        _add_document(tx, is_reported_in, ids_to_load)
        doc_doi = is_reported_in["doi"]
        query += f"""
        MERGE (d:Document {{ doi:'{doc_doi}' }})
        MERGE (m) -[:IS_REPORTED_IN] -> (d)
        """

    tx.run(query, **method)


def _add_gene_or_disease(
    tx: ManagedTransaction, obj_in: dict, ids_to_load: set[str]
) -> None:
    """Add gene or disease node and its relationships to DB

    :param tx: Transaction object provided to transaction functions
    :param obj_in: CDM gene or disease object
    :param ids_to_load: IDs to load into the DB
    :raises TypeError: When `obj_in` is not a disease or gene
    """
    if obj_in["id"] not in ids_to_load:
        return

    obj = obj_in.copy()

    obj_type = obj["conceptType"]
    if obj_type not in {"Gene", "Disease"}:
        msg = f"Invalid object type: {obj_type}"
        raise TypeError(msg)

    obj["conceptType"] = obj_type
    obj_keys = [_create_parameterized_query(obj, ("id", "name", "conceptType"))]

    _add_mappings_and_exts_to_obj(obj, obj_keys)
    obj_keys = ", ".join(obj_keys)

    if obj_type == "Gene":
        query = f"MERGE (g:Gene {{ {obj_keys} }});"
    else:
        query = f"MERGE (d:Disease:Condition {{ {obj_keys} }});"
    tx.run(query, **obj)


def _add_therapy_or_group(
    tx: ManagedTransaction,
    therapy_in: dict,
    ids_to_load: set[str],
) -> None:
    """Add therapy or therapy group node and its relationships

    :param tx: Transaction object provided to transaction functions
    :param therapy: Therapy Mappable Concept or Therapy Group object
    :param ids_to_load: IDs to load into the DB
    :raises TypeError: When therapy type is invalid
    """
    if therapy_in["id"] not in ids_to_load:
        return

    therapy = therapy_in.copy()
    concept_type = therapy.get("conceptType")
    membership_op = therapy.get("membershipOperator")

    if concept_type:
        _add_therapy(tx, therapy)
    elif membership_op in MembershipOperator.__members__.values():
        keys = [_create_parameterized_query(therapy, ("id", "membershipOperator"))]

        _add_mappings_and_exts_to_obj(therapy, keys)
        keys = ", ".join(keys)

        query = f"MERGE (tg:TherapyGroup:Therapy {{ {keys} }})"
        tx.run(query, **therapy)

        for ta in therapy["therapies"]:
            _add_therapy(tx, ta)
            query = f"""
            MERGE (tg:TherapyGroup:Therapy {{id: '{therapy['id']}'}})
            MERGE (t:Therapy {{id: '{ta['id']}'}})
            """

            if membership_op == MembershipOperator.AND:
                query += "MERGE (tg) -[:HAS_COMPONENTS] -> (t)"
            else:
                query += "MERGE (tg) -[:HAS_SUBSTITUTES] -> (t)"

            tx.run(query)
    else:
        msg = f"Therapy `conceptType` not provided and invalid `membershipOperator` provided: {membership_op}"
        raise TypeError(msg)


def _add_therapy(tx: ManagedTransaction, therapy_in: dict) -> None:
    """Add therapy node and its relationships

    :param tx: Transaction object provided to transaction functions
    :param therapy_in: Therapy CDM object
    """
    therapy = therapy_in.copy()
    nonnull_keys = [_create_parameterized_query(therapy, ("id", "name", "conceptType"))]

    _add_mappings_and_exts_to_obj(therapy, nonnull_keys)
    nonnull_keys = ", ".join(nonnull_keys)

    query = f"""
    MERGE (t:Therapy {{ {nonnull_keys} }})
    """
    tx.run(query, **therapy)


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
    loc["sequenceReference"] = json.dumps(loc["sequenceReference"])
    loc_keys.append("loc.sequenceReference=$sequenceReference")
    loc_keys = ", ".join(loc_keys)

    query = f"""
    MERGE (loc:{loc["type"]}:Location {{ id: '{loc["id"]}' }})
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
        f"v.{key}=${key}" for key in ("id", "name", "digest", "type") if v.get(key)
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
    MERGE (v:{v["type"]}:Variation {{ id: '{v["id"]}' }})
    ON CREATE SET {v_keys}
    """

    loc = v.get("location")
    if loc:
        _add_location(tx, loc)
        query += f"""
        MERGE (loc:{loc["type"]}:Location {{ id: '{loc["id"]}' }})
        MERGE (v) -[:HAS_LOCATION] -> (loc)
        """

    tx.run(query, **v)


def _add_categorical_variant(
    tx: ManagedTransaction,
    categorical_variant_in: dict,
    ids_to_load: set[str],
) -> None:
    """Add categorical variant objects to DB.

    :param tx: Transaction object provided to transaction functions
    :param categorical_variant_in: Categorical variant CDM object
    :param ids_to_load: IDs to load into the DB
    """
    if categorical_variant_in["id"] not in ids_to_load:
        return

    cv = categorical_variant_in.copy()

    mp_nonnull_keys = [
        _create_parameterized_query(cv, ("id", "name", "description", "type"))
    ]

    if "aliases" in cv:
        cv["aliases"] = json.dumps(cv["aliases"])
        mp_nonnull_keys.append("aliases:$aliases")

    _add_mappings_and_exts_to_obj(cv, mp_nonnull_keys)
    mp_keys = ", ".join(mp_nonnull_keys)

    defining_context = cv["constraints"][0]["allele"]
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
    MERGE (cv:Variation:{dc_type} {{ id: '{defining_context["id"]}' }})
    MERGE (cv) -[:HAS_LOCATION] -> (loc)
    MERGE (v:Variation:{cv["type"]} {{ {mp_keys} }})
    MERGE (v) -[:HAS_DEFINING_CONTEXT] -> (cv)
    {members_relation}
    """
    tx.run(query, **cv)


def _add_document(
    tx: ManagedTransaction, document_in: dict, ids_to_load: set[str]
) -> None:
    """Add Document object to DB.

    :param tx: Transaction object provided to transaction functions
    :param document: Document CDM object
    :param ids_to_load: IDs to load into the DB
    """
    # Not all document's have IDs. These are the fields that can uniquely identify
    # a document
    if "id" in document_in:
        query = "MATCH (n:Document {id:$id}) RETURN n"
        if document_in["id"] not in ids_to_load:
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
                document, ("id", "name", "title", "pmid", "urls", "doi")
            )
        ]

        _add_mappings_and_exts_to_obj(document, formatted_keys)
        formatted_keys = ", ".join(formatted_keys)

        query = f"""
        MERGE (n:Document {{ {formatted_keys} }});
        """
        tx.run(query, **document)


def _get_ids_to_load(
    statements: list[dict], ids_to_load: set[str] | None = None
) -> None:
    """Get unique IDs to load into the DB

    :param statements: List of statements
    :param ids_to_load: IDS to load into the DB (will be mutated)
    """

    def _added_ids(statement: dict, ids_to_load: set[str]) -> set[str]:
        """Add IDs to load into the DB (mutates ``ids_to_load``)

        IDs should be loaded if all concepts (gene/variant/disease/therapy) are
        normalizable

        :param statement: Statement object
        :param ids_to_load: IDs to load into the DB. This will be mutated.
        :return: ``True`` if statement and all nodes should be loaded. ``False`` if
            statement and nodes should NOT be loaded into the DB (due to concept(s)
            failing to normalize)
        """
        added_ids = set()

        if "hasEvidenceLines" in statement:
            for el in statement["hasEvidenceLines"]:
                for ev in el["hasEvidenceItems"]:
                    if ev["id"] not in ids_to_load:
                        return added_ids

        proposition = statement["proposition"]
        variant = proposition["subjectVariant"]
        if not variant.get("constraints"):
            return added_ids

        gene = proposition.get("geneContextQualifier", {})
        disease = proposition.get("conditionQualifier", {}) or proposition.get(
            "objectCondition", {}
        )
        concept_objs = [variant, gene, disease]
        for concept in concept_objs:
            if concept and _failed_to_normalize(concept):
                return added_ids

        if proposition["type"] == "VariantTherapeuticResponseProposition":
            therapy = proposition.get("objectTherapeutic", {})
            if "therapies" in therapy:
                if any(_failed_to_normalize(tp) for tp in therapy["therapies"]):
                    return added_ids
            else:
                if _failed_to_normalize(therapy):
                    return added_ids

            added_ids.add(therapy["id"])

        for concept in [*concept_objs, statement]:
            added_ids.add(concept["id"])

        return added_ids

    def _failed_to_normalize(obj: dict) -> bool:
        """Check if variant, gene, disease, or therapy failed to normalize

        For now, we will only load records that are able to normalize

        :param obj: Variant, gene, disease, or therapy object
        :return: Whether record failed to normalize
        """
        extensions = obj.get("extensions", [])
        return any(
            ext for ext in extensions if ext["name"] == NormalizerExtensionName.FAILURE
        )

    def _add_obj_id_to_set(obj: dict, ids_set: set[str]) -> None:
        """Add object id to set of IDs

        :param obj: Object to get ID for
        :param ids_set: IDs found in statements. This will be mutated.
        """
        obj_id = obj.get("id")
        if obj_id:
            ids_set.add(obj_id)

    if not ids_to_load:
        ids_to_load = set()

    new_ids_to_load = set()
    for statement in statements:
        added_ids = _added_ids(statement, ids_to_load)
        if not added_ids:
            continue

        new_ids_to_load.update(added_ids)

        for obj in [
            statement.get("specifiedBy"),  # method
            statement.get("reportedIn"),
        ]:
            if obj:
                if isinstance(obj, list):
                    for item in obj:
                        _add_obj_id_to_set(item, new_ids_to_load)
                else:  # This is a dictionary
                    _add_obj_id_to_set(obj, new_ids_to_load)
    return new_ids_to_load


def _get_statement_query(statement: dict, is_evidence: bool) -> str:
    """Generate the initial Cypher query to create a statement node and its
    relationships, based on shared properties of evidence and assertion records.

    :param statement: Statement record
    :param is_evidence: Whether or not ``statement`` is an evidence or assertion record
    :return: The base Cypher query string for creating the statement node and
    relationships
    """
    match_line = ""
    rel_line = ""

    strength = statement.get("strength")
    if strength:
        strength_prefix = "strength_"
        if strength.get("name"):
            strength_keys = [
                _create_parameterized_query(
                    strength, ("name",), entity_param_prefix=strength_prefix
                )
            ]
            statement[f"{strength_prefix}name"] = strength["name"]
        else:
            strength_keys = []

        for k in ("primaryCoding", "mappings"):
            v = strength.get(k)
            if v:
                statement[f"{strength_prefix}{k}"] = json.dumps(v)
                strength_keys.append(f"{k}:${strength_prefix}{k}")
        strength_keys = ", ".join(strength_keys)

        match_line += f"MERGE (strength:Strength {{ {strength_keys} }})"
        rel_line += "MERGE (s) -[:HAS_STRENGTH] -> (strength)"

    proposition = statement["proposition"]
    statement["propositionType"] = proposition["type"]
    match_line += "SET s.propositionType=$propositionType\n"

    allele_origin = proposition.get("alleleOriginQualifier")
    if allele_origin:
        statement["alleleOriginQualifier"] = allele_origin["name"]
        match_line += "SET s.alleleOriginQualifier=$alleleOriginQualifier\n"

    predicate = proposition.get("predicate")
    if predicate:
        statement["predicate"] = predicate
        match_line += "SET s.predicate=$predicate\n"

    gene_context_id = proposition.get("geneContextQualifier", {}).get("id")
    if gene_context_id:
        match_line += f"MERGE (g:Gene {{id: '{gene_context_id}'}})\n"
        rel_line += "MERGE (s) -[:HAS_GENE_CONTEXT] -> (g)\n"

    method_id = statement["specifiedBy"]["id"]
    match_line += f"MERGE (m {{ id: '{method_id}' }})\n"
    rel_line += "MERGE (s) -[:IS_SPECIFIED_BY] -> (m)\n"

    variant_id = proposition["subjectVariant"]["id"]
    match_line += f"MERGE (v:Variation {{ id: '{variant_id}' }})\n"
    rel_line += "MERGE (s) -[:HAS_VARIANT] -> (v)\n"

    therapeutic = proposition.get("objectTherapeutic")
    if therapeutic:
        therapeutic_id = therapeutic["id"]
        match_line += f"MERGE (t:Therapy {{ id: '{therapeutic_id}' }})\n"
        rel_line += "MERGE (s) -[:HAS_THERAPEUTIC] -> (t)\n"

    tumor_type = proposition.get("conditionQualifier") or proposition.get(
        "objectCondition"
    )
    tumor_type_id = tumor_type["id"]
    match_line += f"MERGE (tt:Condition {{ id: '{tumor_type_id}' }})\n"
    rel_line += "MERGE (s) -[:HAS_TUMOR_TYPE] -> (tt)\n"

    statement_keys = _create_parameterized_query(
        statement, ("id", "description", "direction", "type")
    )

    statement_type = "Statement" if is_evidence else "StudyStatement:Statement"
    return f"""
    MERGE (s:{statement_type} {{ {statement_keys} }})
    {match_line}
    {rel_line}\n
    """


def _add_statement_evidence(
    tx: ManagedTransaction, statement_in: dict, ids_to_load: set[str]
) -> None:
    """Add statement node and its relationships for evidence records

    :param tx: Transaction object provided to transaction functions
    :param statement_in: Statement CDM object for evidence items
    """
    if statement_in["id"] not in ids_to_load:
        return

    statement = statement_in.copy()
    query = _get_statement_query(statement, is_evidence=True)

    is_reported_in_docs = statement.get("reportedIn", [])
    for ri_doc in is_reported_in_docs:
        ri_doc_id = ri_doc["id"]
        name = f"doc_{ri_doc_id.split(':')[-1]}"
        query += f"""
        MERGE ({name} {{ id: '{ri_doc_id}'}})
        MERGE (s) -[:IS_REPORTED_IN] -> ({name})
        """
    tx.run(query, **statement)


def _add_statement_assertion(
    tx: ManagedTransaction, statement_in: dict, ids_to_load: set[str]
) -> None:
    """Add statement node and its relationships for assertion records

    :param tx: Transaction object provided to transaction functions
    :param statement_in: Statement CDM object for assertions
    """
    if statement_in["id"] not in ids_to_load:
        return

    statement = statement_in.copy()
    query = _get_statement_query(statement, is_evidence=False)

    classification = statement["classification"]
    classification_keys = []
    primary_coding = classification.get("primaryCoding")
    if primary_coding:
        statement["classification_primaryCoding"] = json.dumps(primary_coding)
        classification_keys.append("primaryCoding:$classification_primaryCoding")

    _add_mappings_and_exts_to_obj(classification, classification_keys)
    statement.update(classification)
    classification_keys = ", ".join(classification_keys)

    query += f"""
    MERGE (classification:Classification {{ {classification_keys} }})
    MERGE (s) -[:HAS_CLASSIFICATION] -> (classification)
    """

    evidence_lines = statement.get("hasEvidenceLines", [])
    if evidence_lines:
        for el in evidence_lines:
            el["evidence_line_id"] = str(uuid.uuid4())
            el["evidence_item_ids"] = [ev["id"] for ev in el["hasEvidenceItems"]]

        query += """
        WITH s
        UNWIND $hasEvidenceLines AS el
        MERGE (evidence_line:EvidenceLine {id: el.evidence_line_id, direction: el.directionOfEvidenceProvided})
        MERGE (s)-[:HAS_EVIDENCE_LINE]->(evidence_line)
        WITH evidence_line, el.evidence_item_ids AS evidence_item_ids
        UNWIND evidence_item_ids AS evidence_item_id
        MERGE (evidence:Statement {id: evidence_item_id})
        MERGE (evidence_line)-[:HAS_EVIDENCE_ITEM]->(evidence)
        """

    tx.run(query, **statement)


def add_transformed_data(driver: Driver, data: dict) -> None:
    """Add set of data formatted per Common Data Model to DB.

    :param data: contains key/value pairs for data objects to add to DB, including
        statements, variation, therapies, conditions, genes, methods, documents, etc.
    """
    # Used to keep track of IDs to load. This is used to prevent adding nodes that
    # aren't associated to supported statements or nodes with no relationships
    statements_evidence = data.get("statements_evidence", [])
    ids_to_load = _get_ids_to_load(statements_evidence)

    statements_assertions = data.get("statements_assertions", [])
    ids_to_load.update(_get_ids_to_load(statements_assertions, ids_to_load=ids_to_load))

    with driver.session() as session:
        loaded_stmt_count = 0

        for cv in data.get("categorical_variants", []):
            session.execute_write(_add_categorical_variant, cv, ids_to_load)

        for doc in data.get("documents", []):
            session.execute_write(_add_document, doc, ids_to_load)

        for method in data.get("methods", []):
            session.execute_write(_add_method, method, ids_to_load)

        for obj_type in ("genes", "conditions"):
            for obj in data.get(obj_type, []):
                session.execute_write(_add_gene_or_disease, obj, ids_to_load)

        for tp in data.get("therapies", []):
            session.execute_write(_add_therapy_or_group, tp, ids_to_load)

        # This should always be done last
        for statement_evidence_item in statements_evidence:
            session.execute_write(
                _add_statement_evidence, statement_evidence_item, ids_to_load
            )
            loaded_stmt_count += 1

        for statement_assertion in statements_assertions:
            session.execute_write(
                _add_statement_assertion, statement_assertion, ids_to_load
            )
            loaded_stmt_count += 1

        _logger.info("Successfully loaded %s statements.", loaded_stmt_count)


def load_from_json(src_transformed_cdm: Path, driver: Driver | None = None) -> None:
    """Load evidence into DB from given CDM JSON file.

    :param src_transformed_cdm: path to file for a source's transformed data to
        common data model containing statements, variation, therapies, conditions,
        genes, methods, documents, etc.
    :param driver: Neo4j graph driver, if available
    """
    _logger.info("Loading data from %s", src_transformed_cdm)
    if not driver:
        driver = get_driver()
    with src_transformed_cdm.open() as f:
        items = json.load(f)
        add_transformed_data(driver, items)
