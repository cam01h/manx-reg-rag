import pytest
from extraction_ops.definitions import attach_definitions
from extraction_ops.models import Chunk, Definition


""" <- TEST 1 -> """
test_chunks_1 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="The Risk factors should be considered.",
        terms_used=[],
    )
]

test_definitions_1 = [
    Definition(
        document="test", term="Risk Factors", definition="basic test of exact match"
    )
]

expected_1 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="The Risk factors should be considered.",
        terms_used=["Risk Factors"],
    )
]

""" <- TEST 2 -> """
test_chunks_2 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="Any relevant Risk factor should be considered.",
        terms_used=[],
    )
]

test_definitions_2 = [
    Definition(
        document="test",
        term="Risk Factors",
        definition="test that it will catch a singular from a plural",
    )
]

expected_2 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="Any relevant Risk factor should be considered.",
        terms_used=["Risk Factors"],
    )
]

""" <- TEST 3 -> """
test_chunks_3 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="ID&V should be conducted on any beneficiaries",
        terms_used=[],
    )
]

test_definitions_3 = [
    Definition(
        document="test",
        term="ID&V",
        definition="first test",
    ),
    Definition(
        document="test",
        term="beneficiary",
        definition="second test with a complicated plural to singular",
    ),
]

expected_3 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="ID&V should be conducted on any beneficiaries",
        terms_used=["ID&V", "beneficiary"],
    )
]

"""<- test 4 ->"""
test_chunks_4 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="MLROES is not a word and is overriden",
        terms_used=[],
    )
]

test_definitions_4 = [
    Definition(
        document="test",
        term="MLRO",
        definition="should not be attached",
    )
]

expected_4 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="MLROES is not a word and is overriden",
        terms_used=[],
    )
]

"""<- test 5 ->"""
test_chunks_5 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="buying fresh PEPPERS from the shop",
        terms_used=[],
    )
]

test_definitions_5 = [
    Definition(
        document="test",
        term="PEP",
        definition="testing term boundries in regex",
    )
]

expected_5 = [
    Chunk(
        chunk_id="dummy_id",
        document="test",
        hierarchy="test",
        headers=["test"],
        body="buying fresh PEPPERS from the shop",
        terms_used=[],
    )
]


ATTACH_DEFINITIONS_TEST_DATA = [
    (test_chunks_1, test_definitions_1, expected_1),
    (test_chunks_2, test_definitions_2, expected_2),
    (test_chunks_3, test_definitions_3, expected_3),
    (test_chunks_4, test_definitions_4, expected_4),
    (test_chunks_5, test_definitions_5, expected_5),
]


@pytest.mark.parametrize("chunks, definitions, expected", ATTACH_DEFINITIONS_TEST_DATA)
def test_attach_definition(
    chunks: list[Chunk], definitions: list[Definition], expected: list[Chunk]
) -> None:
    result = attach_definitions(chunks, definitions)
    assert result == expected
