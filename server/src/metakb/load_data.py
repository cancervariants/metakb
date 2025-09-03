"""Provide methods for loading data into the database."""

import json
import logging
import uuid
from pathlib import Path

from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base import (
    MembershipOperator,
    Statement,
    TherapyGroup,
)
from neo4j import Driver, ManagedTransaction

from metakb.database import get_driver
from metakb.transformers.base import NormalizerExtensionName

_logger = logging.getLogger(__name__)


def is_loadable_statement(statement: Statement) -> bool:
    """Check whether statement can be loaded to DB

    * All entity terms need to have normalized
    * For variations, that means the catvar must have a constraint
    * For StudyStatements that are supported by other statements via evidence lines,
        all supporting statements must be loadable for the overarching StudyStatement
        to be loadable

    :param statement: incoming statement from CDM. All parameters must be fully materialized,
        not simply referenced as IRIs
    :return: whether statement can be loaded given current data support policy
    """
    success = True
    if evidence_lines := statement.hasEvidenceLines:
        for evidence_line in evidence_lines:
            for evidence_item in evidence_line.hasEvidenceItems:
                if not is_loadable_statement(evidence_item):
                    _logger.debug(
                        "%s could not be loaded because %s is not supported",
                        statement.id,
                        evidence_item.id,
                    )
                    success = False
    proposition = statement.proposition
    if not proposition.subjectVariant.constraints:
        _logger.debug(
            "%s could not be loaded because subject variant object lacks constraints: %s",
            statement.id,
            proposition.subjectVariant,
        )
        success = False
    proposition_type = proposition.type
    if proposition_type == "VariantTherapeuticResponseProposition":
        if extensions := proposition.conditionQualifier.root.extensions:
            for extension in extensions:
                if extension.name == "vicc_normalizer_failure" and extension.value:
                    _logger.debug(
                        "%s could not be loaded because condition failed to normalize: %s",
                        statement.id,
                        proposition.conditionQualifier.root,
                    )
                    success = False
        if therapeutic := proposition.objectTherapeutic:
            if isinstance(therapeutic.root, MappableConcept):
                if extensions := therapeutic.root.extensions:
                    for extension in extensions:
                        if (
                            extension.name == "vicc_normalizer_failure"
                            and extension.value
                        ):
                            _logger.debug(
                                "%s could not be loaded because drug failed to normalize: %s",
                                statement.id,
                                therapeutic.root,
                            )
                            success = False
            elif isinstance(therapeutic.root, TherapyGroup):
                for drug in therapeutic.root.therapies:
                    if extensions := drug.extensions:
                        for extension in extensions:
                            if (
                                extension.name == "vicc_normalizer_failure"
                                and extension.value
                            ):
                                _logger.debug(
                                    "%s could not be loaded because drug in therapygroup failed to normalize: %s",
                                    statement.id,
                                    drug,
                                )
                                success = False
            else:
                raise TypeError
    elif proposition_type in (
        "VariantDiagnosticProposition",
        "VariantPrognosticProposition",
    ):
        if extensions := proposition.objectCondition.root.extensions:
            for extension in extensions:
                if extension.name == "vicc_normalizer_failure" and extension.value:
                    _logger.debug(
                        "%s could not be loaded because condition failed to normalize: %s",
                        statement.id,
                        proposition.objectCondition.root,
                    )
                    success = False
    else:
        msg = f"Unsupported proposition type: {proposition.type}"
        raise NotImplementedError(msg)
    if proposition.geneContextQualifier:  # noqa: SIM102
        if gene_extensions := proposition.geneContextQualifier.extensions:
            for extension in gene_extensions:
                if extension.name == "vicc_normalizer_failure" and extension.value:
                    _logger.debug(
                        "%s could not be loaded because gene failed to normalize: %s",
                        statement.id,
                        proposition.geneContextQualifier,
                    )
                    success = False
    if success:
        _logger.debug("Success. %s can be loaded.", statement.id)
    else:
        _logger.debug("Failure. %s cannot be loaded.", statement.id)
    return success


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


def _add_method(tx: ManagedTransaction, method: dict) -> None:
    """Add Method node and its relationships to DB

    :param tx: Transaction object provided to transaction functions
    :param method: CDM method object
    """
    m_keys = [_create_parameterized_query(method, ("id", "name", "methodType"))]
    m_keys = ", ".join(m_keys)

    query = f"""
    MERGE (m:Method {{ {m_keys} }})
    """

    is_reported_in = method.get("reportedIn")
    if is_reported_in:
        # Method's documents are unique and do not currently have IDs
        _add_document(tx, is_reported_in)
        doc_doi = is_reported_in["doi"]
        query += f"""
        MERGE (d:Document {{ doi:'{doc_doi}' }})
        MERGE (m) -[:IS_REPORTED_IN] -> (d)
        """

    tx.run(query, **method)


def _add_gene_or_disease(tx: ManagedTransaction, obj_in: dict) -> None:
    """Add gene or disease node and its relationships to DB

    :param tx: Transaction object provided to transaction functions
    :param obj_in: CDM gene or disease object
    :raises TypeError: When `obj_in` is not a disease or gene
    """
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
) -> None:
    """Add therapy or therapy group node and its relationships

    :param tx: Transaction object provided to transaction functions
    :param therapy: Therapy Mappable Concept or Therapy Group object
    :raises TypeError: When therapy type is invalid
    """
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
            MERGE (tg:TherapyGroup:Therapy {{id: '{therapy["id"]}'}})
            MERGE (t:Therapy {{id: '{ta["id"]}'}})
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


def _prepare_allele(allele: dict) -> dict:
    """Reformat allele to match graph representation in preparation for upload

    :param allele: allele object from CDM
    :return: reformatted object to better fit DB upload
    """
    allele_to_upload = {
        "id": allele["id"],
        "digest": allele["digest"],
        "state_object": json.dumps(allele["state"]),
        "state": allele["state"],
        "name": allele.get(
            "name", ""
        ),  # must be nonnull for use in ON CREATE statement
        "location": allele["location"],
    }
    for expr in allele.get("expressions", []):
        key = f"expression_{expr['syntax'].replace('.', '_')}"
        allele_to_upload.setdefault(key, []).append(expr["value"])
    return allele_to_upload


def _add_dac_cv(
    tx: ManagedTransaction,
    catvar: dict,
) -> None:
    """Load DefiningAlleleConstraint CatVar.

    Adds
    * CategoricalVariant node itself
    * DefiningAlleleConstraint node
    * Allele node which defines the constraint
    * Nodes for member alleles of the category
    * SequenceLocation and SequenceExpression nodes for each allele

    :param tx: neo4j transaction
    :param catvar: model dump of catvar
    """
    cv_merge_statement = """
    MERGE (cv:Variation:CategoricalVariant:ProteinSequenceConsequence { id: $cv.id })
    ON CREATE SET cv += {
        name: $cv.name,
        description: $cv.description,
        aliases: $cv.aliases,
        extensions: $cv_extensions,
        mappings: $cv_mappings
    }
    MERGE (cv) -[:HAS_CONSTRAINT]-> (constr:Constraint:DefiningAlleleConstraint { id: $constraint_id })
    ON CREATE SET cv += {
        relations: $constr.relations
    }
    MERGE (allele:Variation:MolecularVariation:Allele { id: $allele.id })
    ON CREATE SET allele += {
        name: $allele.name,
        digest: $allele.digest,
        expression_hgvs_g: $allele.expression_hgvs_g,
        expression_hgvs_c: $allele.expression_hgvs_c,
        expression_hgvs_p: $allele.expression_hgvs_p
    }
    MERGE (constr) -[:HAS_DEFINING_ALLELE]-> (allele)
    MERGE (sl:Location:SequenceLocation { id: $allele.location.id })
    ON CREATE SET sl += {
        digest: $allele.location.digest,
        start: $allele.location.start,
        end: $allele.location.end,
        refget_accession: $allele.location.sequenceReference.refgetAccession,
        sequence: $allele.location.sequence
    }
    MERGE (allele) -[:HAS_LOCATION]-> (sl)

    // handle different kinds of state objects
    FOREACH (_ IN CASE WHEN $allele.state.type = 'LiteralSequenceExpression' THEN [1] ELSE [] END |
        MERGE (lse:SequenceExpression:LiteralSequenceExpression { sequence: $allele.state.sequence })
        MERGE (allele)-[:HAS_STATE]->(lse)
    )
    FOREACH (_ IN CASE WHEN $allele.state.type = 'ReferenceLengthExpression' THEN [1] ELSE [] END |
        MERGE (rle:SequenceExpression:ReferenceLengthExpression {
            length: $allele.state.length,
            repeat_subunit_length: $allele.state.repeatSubunitLength,
            sequence: $allele.state.sequence
        })
        MERGE (allele)-[:HAS_STATE]->(rle)
    )

    WITH cv
        UNWIND $members as m
        MERGE (member_allele:Variation:MolecularVariation:Allele { id: m.id })
        ON CREATE SET member_allele += {
            name: m.name,
            digest: m.digest,
            expression_hgvs_g: m.expression_hgvs_g,
            expression_hgvs_c: m.expression_hgvs_c,
            expression_hgvs_p: m.expression_hgvs_p
        }
        MERGE (cv) -[:HAS_MEMBER]-> (member_allele)
        MERGE (member_sl:Location:SequenceLocation { id: m.location.id })
        ON CREATE SET member_sl += {
            digest: m.location.digest,
            start: m.location.start,
            end:  m.location.end,
            refget_accession: m.location.sequenceReference.refgetAccession,
            sequence: m.location.sequence
        }
        MERGE (member_allele) -[:HAS_LOCATION] -> (member_sl)

        // handle different kinds of state objects
        FOREACH (_ IN CASE WHEN m.state.type = 'LiteralSequenceExpression' THEN [1] ELSE [] END |
            MERGE (member_lse:SequenceExpression:LiteralSequenceExpression { sequence: m.state.sequence })
            MERGE (member_allele)-[:HAS_STATE]->(member_lse)
        )
        FOREACH (_ IN CASE WHEN m.state.type = 'ReferenceLengthExpression' THEN [1] ELSE [] END |
            MERGE (member_rle:SequenceExpression:ReferenceLengthExpression {
                length: m.state.length,
                repeat_subunit_length: m.state.repeatSubunitLength,
                sequence: m.state.sequence
            })
            MERGE (member_allele)-[:HAS_STATE]->(member_rle)
        )
    """

    # catvars currently support a single constraint
    constraint = catvar["constraints"][0]
    allele = _prepare_allele(constraint["allele"])

    constraint_id = f"{catvar['id']}:{constraint['type']}:{allele['id']}"

    tx.run(
        cv_merge_statement,
        cv=catvar,
        cv_extensions=json.dumps(catvar["extensions"])
        if catvar.get("extensions")
        else None,
        cv_mappings=json.dumps(catvar["mappings"]) if catvar.get("mappings") else None,
        constraint_id=constraint_id,
        constr=constraint,
        allele=allele,
        members=[_prepare_allele(a) for a in catvar.get("members", [])],
    )


def _add_categorical_variant(
    tx: ManagedTransaction,
    catvar: dict,
) -> None:
    """Add categorical variant objects to DB.

    :param tx: Transaction object provided to transaction functions
    :param catvar: Categorical variant CDM object
    """
    if catvar.get("constraints") and len(catvar["constraints"]) == 1:
        constraints = catvar["constraints"]

        if constraints[0].get("type") == "DefiningAlleleConstraint":
            _add_dac_cv(tx, catvar)
        # in the future, handle other kinds of catvars here
    else:
        msg = f"Valid CatVars should have a single constraint but `constraints` property for {catvar['id']} is {catvar.get('constraints')}"
        raise ValueError(msg)


def _add_document(tx: ManagedTransaction, document_in: dict) -> None:
    """Add Document object to DB.

    :param tx: Transaction object provided to transaction functions
    :param document: Document CDM object
    """
    # Not all document's have IDs. These are the fields that can uniquely identify
    # a document
    if "id" in document_in:
        query = "MATCH (n:Document {id:$id}) RETURN n"
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
    match_line += f"MERGE (v:CategoricalVariant {{ id: '{variant_id}' }})\n"
    rel_line += "MERGE (s) -[:HAS_SUBJECT_VARIANT] -> (v)\n"

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


def _add_statement_evidence(tx: ManagedTransaction, statement_in: dict) -> None:
    """Add statement node and its relationships for evidence records

    :param tx: Transaction object provided to transaction functions
    :param statement_in: Statement CDM object for evidence items
    """
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


def _add_statement_assertion(tx: ManagedTransaction, statement_in: dict) -> None:
    """Add statement node and its relationships for assertion records

    :param tx: Transaction object provided to transaction functions
    :param statement_in: Statement CDM object for assertions
    """
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

    :param driver: Neo4j driver instance
    :param data: contains key/value pairs for data objects to add to DB, including
        statements, variation, therapies, conditions, genes, methods, documents, etc.
    """
    loaded_stmt_count = 0
    for statement in data.get("statements_evidence", []) + data.get(
        "statements_assertions", []
    ):
        with driver.session() as session:
            validated_statement = Statement(**statement)
            if not is_loadable_statement(validated_statement):
                continue
            proposition = statement["proposition"]
            session.execute_write(
                _add_categorical_variant, proposition["subjectVariant"]
            )
            for document in [
                *statement.get("reportedIn", []),
                statement["specifiedBy"]["reportedIn"],
            ]:
                session.execute_write(_add_document, document)
            session.execute_write(_add_method, statement["specifiedBy"])
            session.execute_write(
                _add_gene_or_disease, proposition["geneContextQualifier"]
            )
            if proposition["type"] == "VariantTherapeuticResponseProposition":
                session.execute_write(
                    _add_therapy_or_group,
                    proposition["objectTherapeutic"],
                )
                session.execute_write(
                    _add_gene_or_disease,
                    proposition["conditionQualifier"],
                )
            elif proposition["type"] in (
                "VariantDiagnosticProposition",
                "VariantPrognosticProposition",
            ):
                session.execute_write(
                    _add_gene_or_disease,
                    proposition["objectCondition"],
                )
            else:
                raise ValueError
            if statement["id"].startswith("civic.aid"):
                session.execute_write(_add_statement_assertion, statement)
            else:
                session.execute_write(_add_statement_evidence, statement)

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
