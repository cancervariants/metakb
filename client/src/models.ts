/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * The syntax used to describe the variation. The value should be one of the supported syntaxes.
 */
export type Syntax = "hgvs.c" | "hgvs.p" | "hgvs.g" | "hgvs.m" | "hgvs.n" | "hgvs.r" | "iscn" | "gnomad" | "spdi";
/**
 * An IRI Reference (either an IRI or a relative-reference), according to `RFC3986 section 4.1 <https://datatracker.ietf.org/doc/html/rfc3986#section-4.1>`_ and `RFC3987 section 2.1 <https://datatracker.ietf.org/doc/html/rfc3987#section-2.1>`_. MAY be a JSON Pointer as an IRI fragment, as described by `RFC6901 section 6 <https://datatracker.ietf.org/doc/html/rfc6901#section-6>`_.
 */
export type IriReference = string;
/**
 * The interpretation of the character codes referred to by the refget accession,
 * where "aa" specifies an amino acid character set, and "na" specifies a nucleic acid
 * character set.
 */
export type ResidueAlphabet = "aa" | "na";
/**
 * A character string of Residues that represents a biological sequence using the conventional sequence order (5'-to-3' for nucleic acid sequences, and amino-to-carboxyl for amino acid sequences). IUPAC ambiguity codes are permitted in Sequence Strings.
 */
export type SequenceString = string;
/**
 * Molecule types as `defined by RefSeq <https://www.ncbi.nlm.nih.gov/books/NBK21091/>`_ (see Table 1).
 */
export type MoleculeType = "genomic" | "RNA" | "mRNA" | "protein";
/**
 * An inclusive range of values bounded by one or more integers.
 *
 * @minItems 2
 * @maxItems 2
 */
export type Range = [number | null, number | null];
/**
 * A character string of Residues that represents a biological sequence using the conventional sequence order (5'-to-3' for nucleic acid sequences, and amino-to-carboxyl for amino acid sequences). IUPAC ambiguity codes are permitted in Sequence Strings.
 */
export type SequenceString1 = string;
/**
 * A representation of the state of one or more biomolecules.
 */
export type Variation =
  | Allele
  | CisPhasedBlock
  | Adjacency
  | Terminus
  | DerivativeMolecule
  | CopyNumberChange
  | CopyNumberCount;
/**
 * The orientation of the molecular variation component.
 */
export type Orientation = "forward" | "reverse_complement";
/**
 * MUST use one of the defined enumerations that are based on the corresponding EFO ontological terms for copy number variation. See Implementation Guidance for more details.
 */
export type CopyChange =
  | "complete genomic loss"
  | "high-level loss"
  | "low-level loss"
  | "loss"
  | "regional base ploidy"
  | "gain"
  | "low-level gain"
  | "high-level gain";
/**
 * Constraints are used to construct an intensional semantics of categorical variant types.
 */
export type Constraint =
  | DefiningAlleleConstraint
  | DefiningLocationConstraint
  | CopyCountConstraint
  | CopyChangeConstraint
  | FeatureContextConstraint;
/**
 * Indicates that the value is taken from a set of controlled strings defined elsewhere. Technically, a code is restricted to a string which has at least one character and no leading or  trailing whitespace, and where there is no whitespace other than single spaces in the contents.
 */
export type Code = string;
/**
 * A mapping relation between concepts as defined by the Simple Knowledge Organization System (SKOS).
 */
export type Relation = "closeMatch" | "exactMatch" | "broadMatch" | "narrowMatch" | "relatedMatch";
/**
 * The relative assessment of the change in copies that members of this categorical variant satisfies.
 */
export type CopyChange1 =
  | "complete genomic loss"
  | "high-level loss"
  | "low-level loss"
  | "loss"
  | "regional base ploidy"
  | "gain"
  | "low-level gain"
  | "high-level gain";
/**
 * A `variation` on a contiguous molecule.
 */
export type MolecularVariation = Allele | CisPhasedBlock | Adjacency | Terminus | DerivativeMolecule;
/**
 * A `Proposition` that has a variant as the subject.
 */
export type SubjectVariantProposition =
  | ExperimentalVariantFunctionalImpactProposition
  | VariantPathogenicityProposition
  | VariantDiagnosticProposition
  | VariantPrognosticProposition
  | VariantOncogenicityProposition
  | VariantTherapeuticResponseProposition;
/**
 * A single condition (disease, phenotype, or trait), or a set of conditions (ConditionSet).
 */
export type Condition = ConditionSet | MappableConcept;
/**
 * The logical relationship between members of the set, that indicates how they manifest in patients/research subjects. The value 'AND' indicates that all conditions in the set co-occur together in a given patient or subject. The value 'OR' indicates that only one condition in the set manifests in each participant interrogated in a given study.
 */
export type MembershipOperator = "AND" | "OR";
/**
 * Define constraints for diagnostic predicate
 */
export type DiagnosticPredicate = "isDiagnosticInclusionCriterionFor" | "isDiagnosticExclusionCriterionFor";
/**
 * Define constraints for prognostic predicate
 */
export type PrognosticPredicate = "associatedWithBetterOutcomeFor" | "associatedWithWorseOutcomeFor";
/**
 * Define constraints for therapeutic response predicate
 */
export type TherapeuticResponsePredicate = "predictsSensitivityTo" | "predictsResistanceTo";
/**
 * An individual therapy (drug, procedure, behavioral intervention, etc.), or group of therapies (TherapyGroup).
 */
export type Therapeutic = TherapyGroup | MappableConcept;
/**
 * The logical relationship between members of the group, that indicates how they were applied in treating participants in a study.  The value 'AND' indicates that all therapies in the group were applied in combination to a given patient or subject. The value 'OR' indicates that each therapy was applied individually to a distinct subset of participants in the cohort that was interrogated in a given study.
 */
export type MembershipOperator1 = "AND" | "OR";
/**
 * The direction of support that the Evidence Line is determined to provide toward its target Proposition (supports, disputes, neutral)
 */
export type Direction = "supports" | "neutral" | "disputes";
/**
 * A term indicating whether the Statement supports, disputes, or remains neutral w.r.t. the validity of the Proposition it evaluates.
 */
export type Direction1 = "supports" | "neutral" | "disputes";

/**
 * An autonomous actor (person, organization, or software agent) that bears some
 * form of responsibility for an activity taking place, for the existence of an entity,
 * or for another agent's activity.
 */
export interface Agent {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'Agent'.
   */
  type?: "Agent";
  /**
   * The given name of the Agent.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specific type of agent the Agent object represents. Recommended subtypes include codes for `person`, `organization`, or `software`.
   */
  agentType?: string | null;
}
/**
 * The Extension class provides entities with a means to include additional
 * attributes that are outside of the specified standard but needed by a given content
 * provider or system implementer. These extensions are not expected to be natively
 * understood, but may be used for pre-negotiated exchange of message attributes
 * between systems.
 */
export interface Extension {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A name for the Extension. Should be indicative of its meaning and/or the type of information it value represents.
   */
  name: string;
  /**
   * The value of the Extension - can be any primitive or structured object
   */
  value:
    | number
    | string
    | boolean
    | {
        [k: string]: unknown;
      }
    | unknown[]
    | null;
  /**
   * A description of the meaning or utility of the Extension, to explain the type of information it is meant to hold.
   */
  description?: string | null;
}
/**
 * The state of a molecule at a `Location`.
 */
export interface Allele {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "Allele"
   */
  type?: "Allele";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A sha512t24u digest created using the VRS Computed Identifier algorithm.
   */
  digest?: string | null;
  expressions?: Expression[] | null;
  /**
   * The location of the Allele
   */
  location: IriReference | SequenceLocation;
  /**
   * An expression of the sequence state
   */
  state: LiteralSequenceExpression | ReferenceLengthExpression | LengthExpression;
}
/**
 * Representation of a variation by a specified nomenclature or syntax for a
 * Variation object. Common examples of expressions for the description of molecular
 * variation include the HGVS and ISCN nomenclatures.
 */
export interface Expression {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  syntax: Syntax;
  /**
   * The expression of the variation in the specified syntax. The value should be a valid expression in the specified syntax.
   */
  value: string;
  /**
   * The version of the syntax used to describe the variation. This is particularly important for HGVS expressions, as the syntax has evolved over time.
   */
  syntax_version?: string | null;
}
/**
 * A `Location` defined by an interval on a `Sequence`.
 */
export interface SequenceLocation {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "SequenceLocation"
   */
  type?: "SequenceLocation";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A sha512t24u digest created using the VRS Computed Identifier algorithm.
   */
  digest?: string | null;
  /**
   * A reference to a SequenceReference on which the location is defined.
   */
  sequenceReference?: IriReference | SequenceReference | null;
  /**
   * The start coordinate or range of the SequenceLocation. The minimum value of this coordinate or range is 0. For locations on linear sequences, this MUST represent a coordinate or range less than or equal to the value of `end`. For circular sequences, `start` is greater than `end` when the location spans the sequence 0 coordinate.
   */
  start?: Range | number | null;
  /**
   * The end coordinate or range of the SequenceLocation. The minimum value of this coordinate or range is 0. For locations on linear sequences, this MUST represent a coordinate or range greater than or equal to the value of `start`. For circular sequences, `end` is less than `start` when the location spans the sequence 0 coordinate.
   */
  end?: Range | number | null;
  /**
   * The literal sequence encoded by the `sequenceReference` at these coordinates.
   */
  sequence?: SequenceString | null;
}
/**
 * A sequence of nucleic or amino acid character codes.
 */
export interface SequenceReference {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "SequenceReference"
   */
  type?: "SequenceReference";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A [GA4GH RefGet](http://samtools.github.io/hts-specs/refget.html) identifier for the referenced sequence, using the sha512t24u digest.
   */
  refgetAccession: string;
  /**
   * The interpretation of the character codes referred to by the refget accession, where "aa" specifies an amino acid character set, and "na" specifies a nucleic acid character set.
   */
  residueAlphabet?: ResidueAlphabet | null;
  /**
   * A boolean indicating whether the molecule represented by the sequence is circular (true) or linear (false).
   */
  circular?: boolean | null;
  /**
   * A sequenceString that is a literal representation of the referenced sequence.
   */
  sequence?: SequenceString | null;
  /**
   * Molecule types as [defined by RefSeq](https://www.ncbi.nlm.nih.gov/books/NBK21091/) (see Table 1). MUST be one of 'genomic', 'RNA', 'mRNA', or 'protein'.
   */
  moleculeType?: MoleculeType | null;
}
/**
 * An explicit expression of a Sequence.
 */
export interface LiteralSequenceExpression {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "LiteralSequenceExpression"
   */
  type?: "LiteralSequenceExpression";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  sequence: SequenceString1;
}
/**
 * An expression of a length of a sequence from a repeating reference.
 */
export interface ReferenceLengthExpression {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "ReferenceLengthExpression"
   */
  type?: "ReferenceLengthExpression";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The number of residues in the expressed sequence.
   */
  length: Range | number;
  /**
   * the literal Sequence encoded by the Reference Length Expression.
   */
  sequence?: SequenceString | null;
  /**
   * The number of residues in the repeat subunit.
   */
  repeatSubunitLength: number;
}
/**
 * A sequence expressed only by its length.
 */
export interface LengthExpression {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "LengthExpression"
   */
  type?: "LengthExpression";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The length of the sequence.
   */
  length?: Range | number | null;
}
/**
 * Base Pydantic model class with extra attributes forbidden.
 */
export interface BaseModelForbidExtra {}
/**
 * A representation of a categorically-defined domain for variation, in which
 * individual Constraintual variation instances may be members of the domain.
 */
export interface CategoricalVariant {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'CategoricalVariant'
   */
  type?: "CategoricalVariant";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A non-exhaustive list of VRS variation Constraints that satisfy the constraints of this categorical variant.
   */
  members?: (Variation | IriReference)[] | null;
  constraints?: Constraint[] | null;
  /**
   * A list of mappings to concepts in terminologies or code systems. Each mapping should include a coding and a relation.
   */
  mappings?: ConceptMapping[] | null;
}
/**
 * An ordered set of co-occurring `Variation` on the same molecule.
 */
export interface CisPhasedBlock {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "CisPhasedBlock"
   */
  type?: "CisPhasedBlock";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A sha512t24u digest created using the VRS Computed Identifier algorithm.
   */
  digest?: string | null;
  expressions?: Expression[] | null;
  /**
   * A list of Alleles that are found in-cis on a shared molecule.
   *
   * @minItems 2
   */
  members: [Allele | IriReference, Allele | IriReference, ...(Allele | IriReference)[]];
  /**
   * An optional Sequence Reference on which all of the in-cis Alleles are found. When defined, this may be used to implicitly define the `sequenceReference` attribute for each of the CisPhasedBlock member Alleles.
   */
  sequenceReference?: SequenceReference | null;
}
/**
 * The `Adjacency` class represents the adjoining of the end of a sequence with the
 * beginning of an adjacent sequence, potentially with an intervening linker sequence.
 */
export interface Adjacency {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "Adjacency".
   */
  type?: "Adjacency";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A sha512t24u digest created using the VRS Computed Identifier algorithm.
   */
  digest?: string | null;
  expressions?: Expression[] | null;
  /**
   * The terminal sequence or pair of adjoined sequences that defines in the adjacency.
   *
   * @minItems 2
   * @maxItems 2
   */
  adjoinedSequences: [IriReference | SequenceLocation, IriReference | SequenceLocation];
  /**
   * The sequence found between adjoined sequences.
   */
  linker?: LiteralSequenceExpression | ReferenceLengthExpression | LengthExpression | null;
  /**
   * A flag indicating if coordinate ambiguity in the adjoined sequences is from sequence homology (true) or other uncertainty, such as instrument ambiguity (false).
   */
  homology?: boolean | null;
}
/**
 * The `Terminus` data class provides a structure for describing the end
 * (terminus) of a sequence. Structurally similar to Adjacency but the linker sequence
 * is not allowed and it removes the unnecessary array structure.
 */
export interface Terminus {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "Terminus".
   */
  type?: "Terminus";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A sha512t24u digest created using the VRS Computed Identifier algorithm.
   */
  digest?: string | null;
  expressions?: Expression[] | null;
  /**
   * The location of the terminus.
   */
  location: IriReference | SequenceLocation;
}
/**
 * The "Derivative Molecule" data class is a structure for describing a derivate
 * molecule composed from multiple sequence components.
 */
export interface DerivativeMolecule {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "DerivativeMolecule".
   */
  type?: "DerivativeMolecule";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A sha512t24u digest created using the VRS Computed Identifier algorithm.
   */
  digest?: string | null;
  expressions?: Expression[] | null;
  /**
   * The molecular components that constitute the derivative molecule.
   *
   * @minItems 2
   */
  components: [
    IriReference | Allele | CisPhasedBlock | Terminus | TraversalBlock,
    IriReference | Allele | CisPhasedBlock | Terminus | TraversalBlock,
    ...(IriReference | Allele | CisPhasedBlock | Terminus | TraversalBlock)[]
  ];
  /**
   * A boolean indicating whether the molecule represented by the sequence is circular (true) or linear (false).
   */
  circular?: boolean | null;
}
/**
 * A component used to describe the orientation of applicable molecular variation
 * within a DerivativeMolecule.
 */
export interface TraversalBlock {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "TraversalBlock".
   */
  type?: "TraversalBlock";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The orientation of the molecular variation component.
   */
  orientation?: Orientation | null;
  /**
   * The unoriented molecular variation component.
   */
  component?: Adjacency | null;
}
/**
 * An assessment of the copy number of a `Location` within a system
 * (e.g. genome, cell, etc.) relative to a baseline ploidy.
 */
export interface CopyNumberChange {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "CopyNumberChange"
   */
  type?: "CopyNumberChange";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A sha512t24u digest created using the VRS Computed Identifier algorithm.
   */
  digest?: string | null;
  expressions?: Expression[] | null;
  /**
   * The location of the subject of the copy change.
   */
  location: IriReference | SequenceLocation;
  copyChange: CopyChange;
}
/**
 * The absolute count of discrete copies of a `Location`, within a system
 * (e.g. genome, cell, etc.).
 */
export interface CopyNumberCount {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be "CopyNumberCount"
   */
  type?: "CopyNumberCount";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A sha512t24u digest created using the VRS Computed Identifier algorithm.
   */
  digest?: string | null;
  expressions?: Expression[] | null;
  /**
   * The location of the subject of the copy count.
   */
  location: IriReference | SequenceLocation;
  /**
   * The integral number of copies of the subject in a system
   */
  copies: Range | number;
}
/**
 * The defining allele and its associated relationships that are congruent with
 * member variants.
 */
export interface DefiningAlleleConstraint {
  /**
   * MUST be 'DefiningAlleleConstraint'
   */
  type?: "DefiningAlleleConstraint";
  allele: Allele | IriReference;
  /**
   * Defined relationships from which members relate to the defining allele.
   */
  relations?: MappableConcept[] | null;
}
/**
 * A concept based on a primaryCoding and/or name that may be mapped to one or more other `Codings`.
 */
export interface MappableConcept {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A term indicating the type of concept being represented by the MappableConcept.
   */
  conceptType?: string | null;
  /**
   * A primary name for the concept.
   */
  name?: string | null;
  /**
   * A primary coding for the concept.
   */
  primaryCoding?: Coding | null;
  /**
   * A list of mappings to concepts in terminologies or code systems. Each mapping should include a coding and a relation.
   */
  mappings?: ConceptMapping[] | null;
}
/**
 * A structured representation of a code for a defined concept in a terminology or
 * code system.
 */
export interface Coding {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The human-readable name for the coded concept, as defined by the code system.
   */
  name?: string | null;
  /**
   * The terminology/code system that defined the code. May be reported as a free-text name (e.g. 'Sequence Ontology'), but it is preferable to provide a uri/url for the system.
   */
  system: string;
  /**
   * Version of the terminology or code system that provided the code.
   */
  systemVersion?: string | null;
  code: Code;
  /**
   * A list of IRIs that are associated with the coding. This can be used to provide additional context or to link to additional information about the concept.
   */
  iris?: IriReference[] | null;
}
/**
 * A mapping to a concept in a terminology or code system.
 */
export interface ConceptMapping {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  coding: Coding1;
  relation: Relation;
}
/**
 * A structured representation of a code for a defined concept in a terminology or
 * code system.
 */
export interface Coding1 {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The human-readable name for the coded concept, as defined by the code system.
   */
  name?: string | null;
  /**
   * The terminology/code system that defined the code. May be reported as a free-text name (e.g. 'Sequence Ontology'), but it is preferable to provide a uri/url for the system.
   */
  system: string;
  /**
   * Version of the terminology or code system that provided the code.
   */
  systemVersion?: string | null;
  code: Code;
  /**
   * A list of IRIs that are associated with the coding. This can be used to provide additional context or to link to additional information about the concept.
   */
  iris?: IriReference[] | null;
}
/**
 * The defining location and its associated relationships that are congruent with
 * member locations.
 */
export interface DefiningLocationConstraint {
  /**
   * MUST be 'DefiningLocationConstraint'
   */
  type?: "DefiningLocationConstraint";
  location: SequenceLocation | IriReference;
  /**
   * Defined relationships from which members relate to the defining location.
   */
  relations?: MappableConcept[] | null;
  matchCharacteristic: MappableConcept1;
}
/**
 * A concept based on a primaryCoding and/or name that may be mapped to one or more other `Codings`.
 */
export interface MappableConcept1 {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A term indicating the type of concept being represented by the MappableConcept.
   */
  conceptType?: string | null;
  /**
   * A primary name for the concept.
   */
  name?: string | null;
  /**
   * A primary coding for the concept.
   */
  primaryCoding?: Coding | null;
  /**
   * A list of mappings to concepts in terminologies or code systems. Each mapping should include a coding and a relation.
   */
  mappings?: ConceptMapping[] | null;
}
/**
 * The exact or range of copies that members of this categorical variant must
 * satisfy.
 */
export interface CopyCountConstraint {
  /**
   * MUST be 'CopyCountConstraint'
   */
  type?: "CopyCountConstraint";
  /**
   * The precise value or range of copies members of this categorical variant must satisfy.
   */
  copies: number | Range;
}
/**
 * A representation of copy number change
 */
export interface CopyChangeConstraint {
  /**
   * MUST be 'CopyChangeConstraint'
   */
  type?: "CopyChangeConstraint";
  copyChange: CopyChange1;
}
/**
 * The feature that members of this categorical variant are associated with.
 */
export interface FeatureContextConstraint {
  /**
   * MUST be 'FeatureContextConstraint'
   */
  type?: "FeatureContextConstraint";
  featureContext: MappableConcept2;
}
/**
 * A concept based on a primaryCoding and/or name that may be mapped to one or more other `Codings`.
 */
export interface MappableConcept2 {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A term indicating the type of concept being represented by the MappableConcept.
   */
  conceptType?: string | null;
  /**
   * A primary name for the concept.
   */
  name?: string | null;
  /**
   * A primary coding for the concept.
   */
  primaryCoding?: Coding | null;
  /**
   * A list of mappings to concepts in terminologies or code systems. Each mapping should include a coding and a relation.
   */
  mappings?: ConceptMapping[] | null;
}
/**
 * A proposition for use in describing the effect of variants in human subjects.
 */
export interface ClinicalVariantProposition {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * The name of the class that is instantiated by a data object representing the Entity.
   */
  type: string;
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A variant that is the subject of the Proposition.
   */
  subjectVariant: MolecularVariation | CategoricalVariant | IriReference;
  /**
   * Reports a gene impacted by the variant, which may contribute to the association described in the Proposition.
   */
  geneContextQualifier?: MappableConcept | IriReference | null;
  /**
   * Reports whether the Proposition should be interpreted in the context of an inherited (germline) variant, an acquired (somatic) mutation, or another more nuanced concept. Consider using terms or codes from community terminologies here, e.g. terms from the 'allele origin' branch of the GENO ontology such as GENO:0000882 (somatic allele origin).
   */
  alleleOriginQualifier?: MappableConcept | IriReference | null;
}
/**
 * A StudyResult that reports measures related to the frequency of an Allele in a cohort
 */
export interface CohortAlleleFrequencyStudyResult {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'CohortAlleleFrequencyStudyResult'.
   */
  type?: "CohortAlleleFrequencyStudyResult";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specification that describes all or part of the process that led to creation of the Information Entity
   */
  specifiedBy?: Method | IriReference | null;
  /**
   * Specific actions taken by an Agent toward the creation, modification, validation, or deprecation of an Information Entity.
   */
  contributions?: Contribution[] | null;
  /**
   * A document in which the the Information Entity is reported.
   */
  reportedIn?: Document[] | IriReference | null;
  /**
   * The dataset from which the CohortAlleleFrequencyStudyResult was reported.
   */
  sourceDataSet?: DataSet | null;
  /**
   * An object in which implementers can define custom fields to capture additional results derived from analysis of primary data items captured in standard attributes in the main body of the Study Result. e.g. in a Cohort Allele Frequency Study Result, this maybe a grpMaxFAF95 calculation, or homozygote/heterozygote calls derived from analyzing raw allele count data.
   */
  ancillaryResults?: {
    [k: string]: unknown;
  } | null;
  /**
   * An object in which implementers can define custom fields to capture metadata about the quality/provenance of the primary data items captured in standard attributes in the main body of the Study Result. e.g. a sequencing coverage metric in a Cohort Allele Frequency Study Result.
   */
  qualityMeasures?: {
    [k: string]: unknown;
  } | null;
  /**
   * The Allele for which frequency results are reported.
   */
  focusAllele: Allele | IriReference;
  /**
   * The number of occurrences of the focusAllele in the cohort.
   */
  focusAlleleCount: number;
  /**
   * The number of occurrences of all alleles at the locus in the cohort.
   */
  locusAlleleCount: number;
  /**
   * The frequency of the focusAllele in the cohort.
   */
  focusAlleleFrequency: number;
  cohort: StudyGroup;
  /**
   * A list of CohortAlleleFrequency objects describing subcohorts of the cohort currently being described. Subcohorts can be further subdivided into more subcohorts. This enables, for example, the description of different ancestry groups and sexes among those ancestry groups.
   */
  subCohortFrequency?: CohortAlleleFrequencyStudyResult[] | null;
}
/**
 * A set of instructions that specify how to achieve some objective.
 */
export interface Method {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'Method'.
   */
  type?: "Method";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specific type of method that a Method instance represents (e.g. 'Variant Interpretation Guideline', or 'Experimental Protocol').
   */
  methodType?: string | null;
  /**
   * A document in which the the Method is reported.
   */
  reportedIn?: Document | IriReference | null;
}
/**
 * A collection of information, usually in a text-based or graphic human-readable
 * form, intended to be read and understood together as a whole.
 */
export interface Document {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * Must be 'Document'
   */
  type?: "Document";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specific type of document that a Document instance represents (e.g.  'publication', 'patent', 'pathology report')
   */
  documentType?: string | null;
  /**
   * The official title given to the document by its authors.
   */
  title?: string | null;
  /**
   * One or more URLs from which the content of the Document can be retrieved.
   */
  urls?: string[] | null;
  /**
   * A [Digital Object Identifier](https://www.doi.org/the-identifier/what-is-a-doi/) for the document.
   */
  doi?: string | null;
  /**
   * A [PubMed unique identifier](https://en.wikipedia.org/wiki/PubMed#PubMed_identifier) for the document.
   */
  pmid?: number | null;
}
/**
 * An action taken by an agent in contributing to the creation, modification,
 * assessment, or deprecation of a particular entity (e.g. a Statement, EvidenceLine,
 * DataSet, Publication, etc.)
 */
export interface Contribution {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'Contribution'.
   */
  type?: "Contribution";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The agent that made the contribution.
   */
  contributor?: Agent | null;
  /**
   * The specific type of activity performed or role played by an agent in making the contribution (e.g. for a publication, agents may contribute as a primary author, editor, figure designer, data generator, etc.). Values of this property may be framed as activities, or as contribution roles (e.g. using terms from the Contribution Role Ontology (CRO)).
   */
  activityType?: string | null;
  /**
   * When the contributing activity was completed.
   */
  date?: string | null;
}
/**
 * A collection of related data items or records that are organized together in a
 * common format or structure, to enable their computational manipulation as a unit.
 */
export interface DataSet {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'DataSet'.
   */
  type?: "DataSet";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specific type of data set the DataSet instance represents (e.g. a 'clinical data set', a 'sequencing data set', a 'gene expression data set', a 'genome annotation data set')
   */
  datasetType?: string | null;
  /**
   * A document in which the the Method is reported.
   */
  reportedIn?: Document | IriReference | null;
  /**
   * Indicates the date a version of a DataSet was formally released.
   */
  releaseDate?: string | null;
  /**
   * The version of the DataSet, as assigned by its creator.
   */
  version?: string | null;
  /**
   * A specific license that dictates legal permissions for how a data set can be used (by whom, where, for what purposes, with what additional requirements, etc.)
   */
  license?: MappableConcept | null;
}
/**
 * The cohort from which the frequency was derived.
 */
export interface StudyGroup {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * Must be 'StudyGroup'
   */
  type?: "StudyGroup";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The total number of individual members in the StudyGroup.
   */
  memberCount?: number | null;
  /**
   * A feature or role shared by all members of the StudyGroup, representing a criterion for membership in the group.
   */
  characteristics?: MappableConcept[] | null;
}
/**
 * Anything that exists, has existed, or will exist.
 *
 * Abstract base class to be extended by other classes. Do NOT instantiate directly.
 */
export interface Entity {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * The name of the class that is instantiated by a data object representing the Entity.
   */
  type: string;
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
}
/**
 * An independent, evidence-based argument that may support or refute the validity
 * of a specific Proposition. The strength and direction of this argument is based on
 * an interpretation of one or more pieces of information as evidence for or against
 * the target Proposition.
 */
export interface EvidenceLine {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'EvidenceLine'.
   */
  type?: "EvidenceLine";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specification that describes all or part of the process that led to creation of the Information Entity
   */
  specifiedBy?: Method | IriReference | null;
  /**
   * Specific actions taken by an Agent toward the creation, modification, validation, or deprecation of an Information Entity.
   */
  contributions?: Contribution[] | null;
  /**
   * A document in which the the Information Entity is reported.
   */
  reportedIn?: Document[] | IriReference | null;
  /**
   * The possible fact against which evidence items contained in an Evidence Line were collectively evaluated, in determining the overall strength and direction of support they provide. For example, in an ACMG Guideline-based assessment of variant pathogenicity, the support provided by distinct lines of evidence are assessed against a target proposition that the variant is pathogenic for a specific disease.
   */
  targetProposition?: Proposition | SubjectVariantProposition | null;
  /**
   * An individual piece of information that was evaluated as evidence in building the argument represented by an Evidence Line.
   */
  hasEvidenceItems?: unknown[] | null;
  directionOfEvidenceProvided: Direction;
  /**
   * The strength of support that an Evidence Line is determined to provide for or against its target Proposition, evaluated relative to the direction indicated by the directionOfEvidenceProvided value.
   */
  strengthOfEvidenceProvided?: MappableConcept | null;
  /**
   * A quantitative score indicating the strength of support that an Evidence Line is determined to provide for or against its target Proposition, evaluated relative to the direction indicated by the directionOfEvidenceProvided value.
   */
  scoreOfEvidenceProvided?: number | null;
  /**
   * A term summarizing the overall outcome of the evidence assessment represented by the Evidence Line, in terms of the direction and strength of support it provides for or against the target Proposition.
   */
  evidenceOutcome?: MappableConcept | null;
}
/**
 * An abstract entity representing a possible fact that may be true or false. As
 * abstract entities, Propositions capture a 'sharable' piece of meaning whose identify
 * and existence is independent of space and time, or whether it is ever asserted to be
 * true by some agent.
 */
export interface Proposition {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * The name of the class that is instantiated by a data object representing the Entity.
   */
  type: string;
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The Entity or concept about which the Proposition is made.
   */
  subject: {
    [k: string]: unknown;
  };
  /**
   * The relationship declared to hold between the subject and the object of the Proposition.
   */
  predicate: string;
  /**
   * An Entity or concept that is related to the subject of a Proposition via its predicate.
   */
  object: {
    [k: string]: unknown;
  };
}
/**
 * A Proposition describing the impact of a variant on the function sequence feature
 * (typically a gene or gene product).
 */
export interface ExperimentalVariantFunctionalImpactProposition {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'ExperimentalVariantFunctionalImpactProposition'.
   */
  type?: "ExperimentalVariantFunctionalImpactProposition";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A variant that is the subject of the Proposition.
   */
  subjectVariant: MolecularVariation | CategoricalVariant | IriReference;
  /**
   * The relationship the Proposition describes between the subject variant and object sequence feature whose function it may alter.
   */
  predicate?: string;
  /**
   * The sequence feature (typically a gene or gene product) on whose function the impact of the subject variant is reported.
   */
  objectSequenceFeature: IriReference | MappableConcept;
  /**
   * An assay in which the reported variant functional impact was determined - providing a specific experimental context in which this effect is asserted to hold.
   */
  experimentalContextQualifier?:
    | IriReference
    | Document
    | {
        [k: string]: unknown;
      }
    | null;
}
/**
 * A proposition describing the role of a variant in causing a heritable condition.
 */
export interface VariantPathogenicityProposition {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * Must be 'VariantPathogenicityProposition'
   */
  type?: "VariantPathogenicityProposition";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A variant that is the subject of the Proposition.
   */
  subjectVariant: MolecularVariation | CategoricalVariant | IriReference;
  /**
   * Reports a gene impacted by the variant, which may contribute to the association described in the Proposition.
   */
  geneContextQualifier?: MappableConcept | IriReference | null;
  /**
   * Reports whether the Proposition should be interpreted in the context of an inherited (germline) variant, an acquired (somatic) mutation, or another more nuanced concept. Consider using terms or codes from community terminologies here, e.g. terms from the 'allele origin' branch of the GENO ontology such as GENO:0000882 (somatic allele origin).
   */
  alleleOriginQualifier?: MappableConcept | IriReference | null;
  predicate?: string;
  /**
   * The Condition for which the variant impact is stated.
   */
  objectCondition: Condition | IriReference;
  /**
   * Reports the penetrance of the pathogenic effect - i.e. the extent to which the variant impact is expressed by individuals carrying it as a measure of the proportion of carriers exhibiting the condition.
   */
  penetranceQualifier?: MappableConcept | null;
  /**
   * Reports a pattern of inheritance expected for the pathogenic effect of the variant. Consider using terms or codes from community terminologies here - e.g. terms from the 'Mode of inheritance' branch of the Human Phenotype Ontology such as HP:0000006 (autosomal dominant inheritance).
   */
  modeOfInheritanceQualifier?: MappableConcept | null;
}
/**
 * A set of conditions (diseases, phenotypes, traits).
 * A set of two or more conditions that co-occur in the same patient/subject, or are
 * manifest individually in a different subset of participants in a research study.
 */
export interface ConditionSet {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A list of conditions (diseases, phenotypes, traits) that are co-occurring.
   *
   * @minItems 2
   */
  conditions: [MappableConcept, MappableConcept, ...MappableConcept[]];
  membershipOperator: MembershipOperator;
}
/**
 * A Proposition about whether a variant is associated with a disease (a diagnostic
 * inclusion criterion), or absence of a disease (diagnostic exclusion criterion).
 */
export interface VariantDiagnosticProposition {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'VariantDiagnosticProposition'.
   */
  type?: "VariantDiagnosticProposition";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A variant that is the subject of the Proposition.
   */
  subjectVariant: MolecularVariation | CategoricalVariant | IriReference;
  /**
   * Reports a gene impacted by the variant, which may contribute to the association described in the Proposition.
   */
  geneContextQualifier?: MappableConcept | IriReference | null;
  /**
   * Reports whether the Proposition should be interpreted in the context of an inherited (germline) variant, an acquired (somatic) mutation, or another more nuanced concept. Consider using terms or codes from community terminologies here, e.g. terms from the 'allele origin' branch of the GENO ontology such as GENO:0000882 (somatic allele origin).
   */
  alleleOriginQualifier?: MappableConcept | IriReference | null;
  predicate: DiagnosticPredicate;
  /**
   * The disease that is evaluated for diagnosis.
   */
  objectCondition: Condition | IriReference;
}
/**
 * A Proposition about whether a variant is associated with an improved or worse outcome for a disease.
 */
export interface VariantPrognosticProposition {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'VariantPrognosticProposition'.
   */
  type?: "VariantPrognosticProposition";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A variant that is the subject of the Proposition.
   */
  subjectVariant: MolecularVariation | CategoricalVariant | IriReference;
  /**
   * Reports a gene impacted by the variant, which may contribute to the association described in the Proposition.
   */
  geneContextQualifier?: MappableConcept | IriReference | null;
  /**
   * Reports whether the Proposition should be interpreted in the context of an inherited (germline) variant, an acquired (somatic) mutation, or another more nuanced concept. Consider using terms or codes from community terminologies here, e.g. terms from the 'allele origin' branch of the GENO ontology such as GENO:0000882 (somatic allele origin).
   */
  alleleOriginQualifier?: MappableConcept | IriReference | null;
  predicate: PrognosticPredicate;
  /**
   * The disease that is evaluated for outcome.
   */
  objectCondition: Condition | IriReference;
}
/**
 * A proposition describing the role of a variant in causing a tumor type.
 */
export interface VariantOncogenicityProposition {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'VariantOncogenicityProposition'.
   */
  type?: "VariantOncogenicityProposition";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A variant that is the subject of the Proposition.
   */
  subjectVariant: MolecularVariation | CategoricalVariant | IriReference;
  /**
   * Reports a gene impacted by the variant, which may contribute to the association described in the Proposition.
   */
  geneContextQualifier?: MappableConcept | IriReference | null;
  /**
   * Reports whether the Proposition should be interpreted in the context of an inherited (germline) variant, an acquired (somatic) mutation, or another more nuanced concept. Consider using terms or codes from community terminologies here, e.g. terms from the 'allele origin' branch of the GENO ontology such as GENO:0000882 (somatic allele origin).
   */
  alleleOriginQualifier?: MappableConcept | IriReference | null;
  predicate?: string;
  /**
   * The tumor type for which the variant impact is evaluated.
   */
  objectTumorType: Condition | IriReference;
}
/**
 * A Proposition about the role of a variant in modulating the response of a neoplasm to drug
 * administration or other therapeutic procedures.
 */
export interface VariantTherapeuticResponseProposition {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'VariantTherapeuticResponseProposition'.
   */
  type?: "VariantTherapeuticResponseProposition";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A variant that is the subject of the Proposition.
   */
  subjectVariant: MolecularVariation | CategoricalVariant | IriReference;
  /**
   * Reports a gene impacted by the variant, which may contribute to the association described in the Proposition.
   */
  geneContextQualifier?: MappableConcept | IriReference | null;
  /**
   * Reports whether the Proposition should be interpreted in the context of an inherited (germline) variant, an acquired (somatic) mutation, or another more nuanced concept. Consider using terms or codes from community terminologies here, e.g. terms from the 'allele origin' branch of the GENO ontology such as GENO:0000882 (somatic allele origin).
   */
  alleleOriginQualifier?: MappableConcept | IriReference | null;
  predicate: TherapeuticResponsePredicate;
  /**
   * A drug administration or other therapeutic procedure that the neoplasm is intended to respond to.
   */
  objectTherapeutic: Therapeutic | IriReference;
  /**
   * Reports the disease context in which the variant's association with therapeutic sensitivity or resistance is evaluated. Note that this is a required qualifier in therapeutic response propositions.
   */
  conditionQualifier: Condition | IriReference;
}
/**
 * A group of two or more therapies that are applied in combination to a single
 * patient/subject, or applied individually to a different subset of participants in a
 * research study
 */
export interface TherapyGroup {
  /**
   * The 'logical' identifier of the data element in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A list of therapies that are applied to treat a condition.
   *
   * @minItems 2
   */
  therapies: [MappableConcept, MappableConcept, ...MappableConcept[]];
  membershipOperator: MembershipOperator1;
}
/**
 * A StudyResult that reports a functional impact score from a variant functional assay or study.
 */
export interface ExperimentalVariantFunctionalImpactStudyResult {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'ExperimentalVariantFunctionalImpactStudyResult'.
   */
  type?: "ExperimentalVariantFunctionalImpactStudyResult";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The assay that was performed to generate the reported functional impact score.
   */
  specifiedBy?: Method | IriReference | null;
  /**
   * Specific actions taken by an Agent toward the creation, modification, validation, or deprecation of an Information Entity.
   */
  contributions?: Contribution[] | null;
  /**
   * A document in which the the Information Entity is reported.
   */
  reportedIn?: Document[] | IriReference | null;
  /**
   * The full data set that provided the reported the functional impact score.
   */
  sourceDataSet?: DataSet | null;
  /**
   * An object in which implementers can define custom fields to capture additional results derived from analysis of primary data items captured in standard attributes in the main body of the Study Result. e.g. in a Cohort Allele Frequency Study Result, this maybe a grpMaxFAF95 calculation, or homozygote/heterozygote calls derived from analyzing raw allele count data.
   */
  ancillaryResults?: {
    [k: string]: unknown;
  } | null;
  /**
   * An object in which implementers can define custom fields to capture metadata about the quality/provenance of the primary data items captured in standard attributes in the main body of the Study Result. e.g. a sequencing coverage metric in a Cohort Allele Frequency Study Result.
   */
  qualityMeasures?: {
    [k: string]: unknown;
  } | null;
  /**
   * The genetic variant for which a functional impact score is generated.
   */
  focusVariant: MolecularVariation | IriReference;
  /**
   * The score of the variant impact measured in the assay or study.
   */
  functionalImpactScore?: number | null;
}
/**
 * An abstract (non-physical) entity that represents 'information content' carried by
 * physical or digital information artifacts such as books, web pages, data sets, or
 * images.
 */
export interface InformationEntity {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * The name of the class that is instantiated by a data object representing the Entity.
   */
  type: string;
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specification that describes all or part of the process that led to creation of the Information Entity
   */
  specifiedBy?: Method | IriReference | null;
  /**
   * Specific actions taken by an Agent toward the creation, modification, validation, or deprecation of an Information Entity.
   */
  contributions?: Contribution[] | null;
  /**
   * A document in which the the Information Entity is reported.
   */
  reportedIn?: Document[] | IriReference | null;
}
/**
 * A claim of purported truth as made by a particular agent, on a particular
 * occasion. Statements may be used to put forth a possible fact (i.e. a 'Proposition')
 * as true or false, or to provide a more nuanced assessment of the level of confidence
 * or evidence supporting a particular Proposition.
 */
export interface Statement {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'Statement'.
   */
  type?: "Statement";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specification that describes all or part of the process that led to creation of the Information Entity
   */
  specifiedBy?: Method | IriReference | null;
  /**
   * Specific actions taken by an Agent toward the creation, modification, validation, or deprecation of an Information Entity.
   */
  contributions?: Contribution[] | null;
  /**
   * A document in which the the Information Entity is reported.
   */
  reportedIn?: Document[] | IriReference | null;
  /**
   * A possible fact, the validity of which is assessed and reported by the Statement. A Statement can put forth the proposition as being true, false, or uncertain, and may provide an assessment of the level of confidence/evidence supporting this claim.
   */
  proposition:
    VariantDiagnosticProposition
    | VariantOncogenicityProposition
    | VariantPathogenicityProposition
    | VariantPrognosticProposition
    | VariantTherapeuticResponseProposition;
  direction: Direction1;
  /**
   * A term used to report the strength of a Proposition's assessment in the direction indicated (i.e. how strongly supported or disputed the Proposition is believed to be).  Implementers may choose to frame a strength assessment in terms of how *confident* an agent is that the Proposition is true or false, or in terms of the *strength of all evidence* they believe supports or disputes it.
   */
  strength?: MappableConcept | null;
  /**
   * A quantitative score that indicates the strength of a Proposition's assessment in the direction indicated (i.e. how strongly supported or disputed the Proposition is believed to be). Depending on its implementation, a score may reflect how *confident* that agent is that the Proposition is true or false, or the *strength of evidence* they believe supports or disputes it. Instructions for how to interpret the meaning of a given score may be gleaned from the method or document referenced in 'specifiedBy' attribute.
   */
  score?: number | null;
  /**
   * A single term or phrase summarizing the outcome of direction and strength assessments of a Statement's Proposition, in terms of a classification of its subject.
   */
  classification?: MappableConcept | null;
  /**
   * An evidence-based argument that supports or disputes the validity of the proposition that a Statement assesses or puts forth as true. The strength and direction of this argument (whether it supports or disputes the proposition, and how strongly) is based on an interpretation of one or more pieces of information as evidence (i.e. 'Evidence Items).
   */
  hasEvidenceLines?: (EvidenceLine | IriReference)[] | null;
}
/**
 * A collection of individuals or specimens from the same taxonomic class, selected
 * for analysis in a scientific study based on their exhibiting one or more common
 * characteristics  (e.g. species, race, age, gender, disease state, income). May be
 * referred to as a 'cohort' or 'population' in specific research settings.
 */
export interface StudyGroup1 {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * Must be 'StudyGroup'
   */
  type?: "StudyGroup";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * The total number of individual members in the StudyGroup.
   */
  memberCount?: number | null;
  /**
   * A feature or role shared by all members of the StudyGroup, representing a criterion for membership in the group.
   */
  characteristics?: MappableConcept[] | null;
}
/**
 * A Study Result that reports measures related to the frequency of an variant
 * across different tumor types.
 */
export interface TumorVariantFrequencyStudyResult {
  /**
   * The 'logical' identifier of the Entity in the system of record, e.g. a UUID.  This 'id' is unique within a given system, but may or may not be globally unique outside the system. It is used within a system to reference an object from another.
   */
  id?: string | null;
  /**
   * MUST be 'TumorVariantFrequencyStudyResult'.
   */
  type?: "TumorVariantFrequencyStudyResult";
  /**
   * A primary name for the entity.
   */
  name?: string | null;
  /**
   * A free-text description of the Entity.
   */
  description?: string | null;
  /**
   * Alternative name(s) for the Entity.
   */
  aliases?: string[] | null;
  /**
   * A list of extensions to the Entity, that allow for capture of information not directly supported by elements defined in the model.
   */
  extensions?: Extension[] | null;
  /**
   * A specification that describes all or part of the process that led to creation of the Information Entity
   */
  specifiedBy?: Method | IriReference | null;
  /**
   * Specific actions taken by an Agent toward the creation, modification, validation, or deprecation of an Information Entity.
   */
  contributions?: Contribution[] | null;
  /**
   * A document in which the the Information Entity is reported.
   */
  reportedIn?: Document[] | IriReference | null;
  /**
   * The dataset from which data in the Tumor Variant Frequency Study Result was taken.
   */
  sourceDataSet?: DataSet | null;
  /**
   * An object in which implementers can define custom fields to capture additional results derived from analysis of primary data items captured in standard attributes in the main body of the Study Result. e.g. in a Cohort Allele Frequency Study Result, this maybe a grpMaxFAF95 calculation, or homozygote/heterozygote calls derived from analyzing raw allele count data.
   */
  ancillaryResults?: {
    [k: string]: unknown;
  } | null;
  /**
   * An object in which implementers can define custom fields to capture metadata about the quality/provenance of the primary data items captured in standard attributes in the main body of the Study Result. e.g. a sequencing coverage metric in a Cohort Allele Frequency Study Result.
   */
  qualityMeasures?: {
    [k: string]: unknown;
  } | null;
  /**
   * The variant for which frequency data is reported in the Study Result.
   */
  focusVariant: Allele | CategoricalVariant | IriReference;
  /**
   * The number of tumor samples in the sample group that contain the focus variant.
   */
  affectedSampleCount: number;
  /**
   * The total number of tumor samples in the sample group.
   */
  totalSampleCount: number;
  /**
   * The frequency of tumor samples that include the focus variant in the sample group.
   */
  affectedFrequency: number;
  /**
   * The set of samples about which the frequency data was generated.
   */
  sampleGroup?: StudyGroup1 | null;
  /**
   * A list of Tumor Variant Frequency Study Result objects describing variant frequency in different subsets of larger sample group described in the root Study Result. Subgroups can be further subdivided into more subgroups. This enables, for example, further breakdown of frequency measures in sample groups with a narrower categorical variant than the root focus variant, or sample groups with a more specific tumor type.
   */
  subGroupFrequency?: TumorVariantFrequencyStudyResult[] | null;
}
