from unittest.mock import MagicMock, patch
import pytest


def test_consultar_sin_fragmentos():
    db_mock = MagicMock()
    recuperacion_mock = MagicMock()
    recuperacion_mock.recuperar.return_value = []

    consulta_mock = MagicMock()
    consulta_mock.id = 1

    with patch("app.services.servicio_rag.RepositorioOperacional") as MockRepo, \
         patch("app.services.servicio_rag.anthropic.Anthropic"):
        repo_instance = MockRepo.return_value
        repo_instance.registrar_consulta.return_value = consulta_mock

        from app.services.servicio_rag import ServicioRAG
        servicio = ServicioRAG(db_mock, recuperacion_mock)
        resultado = servicio.consultar("¿Qué es Python?")

    assert resultado["fragmentos_encontrados"] == 0
    assert "No encontré" in resultado["respuesta"]


def test_consultar_con_fragmentos():
    db_mock = MagicMock()
    recuperacion_mock = MagicMock()
    recuperacion_mock.recuperar.return_value = ["Python es un lenguaje de programación."]

    consulta_mock = MagicMock()
    consulta_mock.id = 2

    mensaje_mock = MagicMock()
    mensaje_mock.content = [MagicMock(text="Python es muy usado.")]

    with patch("app.services.servicio_rag.RepositorioOperacional") as MockRepo, \
         patch("app.services.servicio_rag.anthropic.Anthropic") as MockAnth:
        repo_instance = MockRepo.return_value
        repo_instance.registrar_consulta.return_value = consulta_mock
        MockAnth.return_value.messages.create.return_value = mensaje_mock

        from app.services.servicio_rag import ServicioRAG
        servicio = ServicioRAG(db_mock, recuperacion_mock)
        resultado = servicio.consultar("¿Qué es Python?")

    assert resultado["fragmentos_encontrados"] == 1
    assert resultado["respuesta"] == "Python es muy usado."
