from unittest.mock import MagicMock, patch


@patch("app.repositories.repositorio_vectorial.chromadb.HttpClient")
def test_buscar_similares_vacio(mock_client):
    coleccion_mock = MagicMock()
    coleccion_mock.query.return_value = {"documents": [[]], "distances": [[]], "metadatas": [[]]}
    mock_client.return_value.get_or_create_collection.return_value = coleccion_mock

    from app.repositories.repositorio_vectorial import RepositorioVectorial
    repo = RepositorioVectorial()
    resultado = repo.buscar_similares([0.1, 0.2], top_k=3)

    assert resultado == []


@patch("app.repositories.repositorio_vectorial.chromadb.HttpClient")
def test_buscar_similares_con_resultados(mock_client):
    coleccion_mock = MagicMock()
    coleccion_mock.query.return_value = {
        "documents": [["fragmento relevante"]],
        "distances": [[0.3]],
        "metadatas": [[{"documento_id": 1}]],
    }
    mock_client.return_value.get_or_create_collection.return_value = coleccion_mock

    from app.repositories.repositorio_vectorial import RepositorioVectorial
    repo = RepositorioVectorial()
    resultado = repo.buscar_similares([0.1, 0.2], top_k=3)

    assert len(resultado) == 1
    assert resultado[0]["texto"] == "fragmento relevante"
    assert resultado[0]["distancia"] == 0.3
