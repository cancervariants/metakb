"""Provide phenotype constants for help with transforming age of onset qualifiers into HPO concepts"""

from ga4gh.core.models import Coding, Extension, MappableConcept, code

PEDIATRIC_ONSET = MappableConcept(
    id="HP:0410280",
    name="Pediatric onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0410280"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease manifestations before adulthood, defined here as before the age of 16 years, but excluding neonatal or congenital onset.",
        )
    ],
    conceptType="Phenotype",
)
NEONATAL_ONSET = MappableConcept(
    id="HP:0003623",
    name="Neonatal onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0003623"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of signs or symptoms of disease within the first 28 days of life.",
        )
    ],
    conceptType="Phenotype",
)
CHILDHOOD_ONSET = MappableConcept(
    id="HP:0011463",
    name="Childhood onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0011463"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease at the age of between 1 and 5 years.",
        )
    ],
    conceptType="Phenotype",
)
INFANTILE_ONSET = MappableConcept(
    id="HP:0003593",
    name="Infantile onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/", code=code("HP:0003593")
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of signs or symptoms of disease between 28 days to one year of life.",
        )
    ],
    conceptType="Phenotype",
)
JUVENILE_ONSET = MappableConcept(
    id="HP:0003621",
    name="Juvenile onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0003621"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of signs or symptoms of disease between the age of 5 and 15 years.",
        )
    ],
    conceptType="Phenotype",
)
EARLY_YOUNG_ADULT_ONSET = MappableConcept(
    id="HP:0025708",
    name="Early young adult onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0025708"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease at an age of greater than or equal to 16 to under 19 years.",
        )
    ],
)
YOUNG_ADULT_ONSET = MappableConcept(
    id="HP:0011462",
    name="Young adult onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0011462"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease at the age of between 16 and 40 years.",
        )
    ],
)
INTERMEDIATE_YOUNG_ADULT_ONSET = MappableConcept(
    id="HP:0025709",
    name="Intermediate young adult onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0025709"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease at an age of greater than or equal to 19 to under 25 years.",
        )
    ],
    conceptType="Phenotype",
)
ADULT_ONSET = MappableConcept(
    id="HP:0003581",
    name="Adult onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0003581"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="Onset of disease manifestations in adulthood, defined here as at the age of 16 years or later.",
        )
    ],
    conceptType="Phenotype",
)
MIDDLE_AGE_ONSET = MappableConcept(
    id="HP:0003596",
    name="Middle age onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0003596"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="A type of adult onset with onset of symptoms at the age of 40 to 60 years.",
        )
    ],
    conceptType="Phenotype",
)
LATE_ONSET = MappableConcept(
    id="HP:0003584",
    name="Late onset",
    primaryCoding=Coding(
        system="https://hpo.jax.org/app/browse/term/",
        code=code("HP:0003584"),
    ),
    extensions=[
        Extension(
            name="definition",
            value="A type of adult onset with onset of symptoms after the age of 60 years.",
        )
    ],
    conceptType="Phenotype",
)

ONSET_LOOKUP = {
    PEDIATRIC_ONSET.id: PEDIATRIC_ONSET,
    NEONATAL_ONSET.id: NEONATAL_ONSET,
    CHILDHOOD_ONSET.id: CHILDHOOD_ONSET,
    INFANTILE_ONSET.id: INFANTILE_ONSET,
    JUVENILE_ONSET.id: JUVENILE_ONSET,
    EARLY_YOUNG_ADULT_ONSET.id: EARLY_YOUNG_ADULT_ONSET,
    YOUNG_ADULT_ONSET.id: YOUNG_ADULT_ONSET,
    INTERMEDIATE_YOUNG_ADULT_ONSET.id: INTERMEDIATE_YOUNG_ADULT_ONSET,
    ADULT_ONSET.id: ADULT_ONSET,
    MIDDLE_AGE_ONSET.id: MIDDLE_AGE_ONSET,
    LATE_ONSET.id: LATE_ONSET,
}
