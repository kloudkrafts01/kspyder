import pytest

from common.clientHandler import clientHandler
from common.protocols import DocumentStore, Extractor


def test_get_client_unknown_source_raises_value_error():
    with pytest.raises(ValueError):
        clientHandler().get_client("not_a_real_connector")


def test_get_client_mongodb_returns_document_store():
    client = clientHandler().get_client("mongoDB")

    assert client.schema == "mongoDBConnector"
    assert isinstance(client, DocumentStore)


def test_get_client_azure_retail_prices_returns_extractor():
    client = clientHandler().get_client("azureRetailPrices")

    assert isinstance(client, Extractor)
