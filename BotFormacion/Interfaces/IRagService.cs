using BotFormacion.Models;

namespace BotFormacion.Interfaces;

/// <summary>Contrato de comunicación entre el bot y el motor RAG externo.</summary>
public interface IRagService
{
    Task<RespuestaRag> ConsultarAsync(string pregunta, string usuarioId = "", string usuarioNombre = "", string? conversationReferenceJson = null);

    Task<RespuestaRag> GenerarCuestionarioAsync(string? tema = null);

    Task<RespuestaRag> EvaluarRespuestaAsync(string cuestionarioId, string respuesta, string empleadoId = "", string empleadoNombre = "");
}
