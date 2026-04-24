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
