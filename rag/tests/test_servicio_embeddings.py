from unittest.mock import MagicMock, patch
import pytest


@patch("app.services.servicio_embeddings.SentenceTransformer")
def test_generar_embedding(mock_st):
    modelo_mock = MagicMock()
    modelo_mock.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
    mock_st.return_value = modelo_mock

    from app.services.servicio_embeddings import ServicioEmbeddings
    servicio = ServicioEmbeddings()
    resultado = servicio.generar("texto de prueba")

    modelo_mock.encode.assert_called_once_with("texto de prueba")
    assert isinstance(resultado, list)


@patch("app.services.servicio_embeddings.SentenceTransformer")
def test_generar_lote(mock_st):
    modelo_mock = MagicMock()
    modelo_mock.encode.return_value = MagicMock(tolist=lambda: [[0.1], [0.2]])
    mock_st.return_value = modelo_mock

    from app.services.servicio_embeddings import ServicioEmbeddings
    servicio = ServicioEmbeddings()
    resultado = servicio.generar_lote(["texto 1", "texto 2"])

    modelo_mock.encode.assert_called_once_with(["texto 1", "texto 2"])
