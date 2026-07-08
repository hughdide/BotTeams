from unittest.mock import MagicMock, patch
import pytest


def test_evaluar_cuestionario_no_existe():
    db_mock = MagicMock()

    with patch("app.services.servicio_evaluacion.RepositorioOperacional") as MockRepo, \
         patch("app.services.servicio_evaluacion.anthropic.Anthropic"):
        MockRepo.return_value.obtener_cuestionario.return_value = None

        from app.services.servicio_evaluacion import ServicioEvaluacion
        servicio = ServicioEvaluacion(db_mock)

        with pytest.raises(ValueError, match="no encontrado"):
            servicio.evaluar(999, "emp1", "Juan", "mi respuesta")


def test_evaluar_respuesta_correcta():
    db_mock = MagicMock()
    cuestionario_mock = MagicMock()
    cuestionario_mock.pregunta = "¿Cuál es la capital de España?"
    cuestionario_mock.respuesta_correcta = "Madrid"

    mensaje_mock = MagicMock()
    mensaje_mock.content = [MagicMock(text='{"score": "correcto", "feedback": "Respuesta exacta."}')]

    with patch("app.services.servicio_evaluacion.RepositorioOperacional") as MockRepo, \
         patch("app.services.servicio_evaluacion.anthropic.Anthropic") as MockAnth:
        MockRepo.return_value.obtener_cuestionario.return_value = cuestionario_mock
        MockAnth.return_value.messages.create.return_value = mensaje_mock

        from app.services.servicio_evaluacion import ServicioEvaluacion
        servicio = ServicioEvaluacion(db_mock)
        resultado = servicio.evaluar(1, "emp1", "Juan", "Madrid")

    assert resultado["score"] == "correcto"
    assert resultado["respuesta_correcta"] == "Madrid"
