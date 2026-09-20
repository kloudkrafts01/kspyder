from common.protocols import DocumentStore, Extractor
from tests.conftest import FakeDocumentStore, FakeExtractor


def test_fake_extractor_satisfies_extractor_protocol():
    assert isinstance(FakeExtractor(), Extractor)


def test_fake_document_store_satisfies_document_store_protocol():
    assert isinstance(FakeDocumentStore(), DocumentStore)


def test_extractor_protocol_rejects_unrelated_object():
    class NotAnExtractor:
        schema = "notAnExtractor"
        # missing get_data

    assert isinstance(NotAnExtractor(), Extractor) is False


def test_document_store_protocol_rejects_unrelated_object():
    class NotADocumentStore:
        schema = "notADocumentStore"
        # missing upsert_dataset

    assert isinstance(NotADocumentStore(), DocumentStore) is False
