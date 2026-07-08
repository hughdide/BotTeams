using Microsoft.Extensions.Options;
using System.Text.Json;
using BotFormacion.Configuration;
using BotFormacion.Interfaces;
using BotFormacion.Models;

namespace BotFormacion.Services;

/// <summary>Implementa IRagService comunicándose con la API RAG externa via HTTP.</summary>
public class ServicioRag : IRagService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<ServicioRag> _logger;

    public ServicioRag(HttpClient httpClient, IOptions<OpcionesRag> opciones, ILogger<ServicioRag> logger)
    {
        _httpClient = httpClient;
        _logger = logger;

        var opts = opciones.Value;
        _httpClient.BaseAddress = new Uri(opts.RagUrl.TrimEnd('/'));
        _httpClient.DefaultRequestHeaders.Add("X-Api-Key", opts.RagApiKey);
    }

    /// <summary>Envía una pregunta al RAG. Incluye conversation_reference si está disponible.</summary>
    public async Task<RespuestaRag> ConsultarAsync(string pregunta, string usuarioId = "", string usuarioNombre = "", string? conversationReferenceJson = null)
    {
        try
        {
            object cuerpo;
            if (!string.IsNullOrEmpty(conversationReferenceJson))
            {
                // Parsear a JsonElement para que se serialice como objeto, no como cadena
                var convRefObj = JsonDocument.Parse(conversationReferenceJson).RootElement;
                cuerpo = new { pregunta, usuario_id = usuarioId, usuario_nombre = usuarioNombre, conversation_reference = convRefObj };
            }
            else
            {
                cuerpo = new { pregunta, usuario_id = usuarioId, usuario_nombre = usuarioNombre };
            }

            var respuesta = await _httpClient.PostAsJsonAsync("/consultas", cuerpo);

            if (!respuesta.IsSuccessStatusCode)
                return Fallido("No pude encontrar información sobre eso.");

            var json = await respuesta.Content.ReadAsStringAsync();
            var doc = JsonDocument.Parse(json).RootElement;

            return new RespuestaRag
            {
                Exito = true,
                Mensaje = doc.TryGetProperty("respuesta", out var r) ? r.GetString() : "Sin respuesta.",
                Datos = doc
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al consultar el servicio RAG");
            return Fallido("No he podido procesar la solicitud en este momento. Inténtalo de nuevo más tarde.");
        }
    }

    /// <summary>Genera una pregunta de cuestionario, opcionalmente filtrada por tema.</summary>
    public async Task<RespuestaRag> GenerarCuestionarioAsync(string? tema = null)
    {
        try
        {
            object cuerpo = string.IsNullOrWhiteSpace(tema) ? new { } : new { tema };
            var respuesta = await _httpClient.PostAsJsonAsync("/cuestionarios/generar", cuerpo);

            if (!respuesta.IsSuccessStatusCode)
                return Fallido("No pude generar el cuestionario.");

            var json = await respuesta.Content.ReadAsStringAsync();
            var doc = JsonDocument.Parse(json).RootElement;

            return new RespuestaRag
            {
                Exito = true,
                CuestionarioId = doc.TryGetProperty("cuestionario_id", out var id) ? id.ToString() : null,
                Pregunta = doc.TryGetProperty("pregunta", out var p) ? p.GetString() : null,
                Datos = doc
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al generar cuestionario");
            return Fallido("No he podido generar el cuestionario en este momento. Inténtalo de nuevo más tarde.");
        }
    }

    /// <summary>Evalúa la respuesta del empleado a un cuestionario activo.</summary>
    public async Task<RespuestaRag> EvaluarRespuestaAsync(string cuestionarioId, string respuesta, string empleadoId = "", string empleadoNombre = "")
    {
        try
        {
            _ = int.TryParse(cuestionarioId, out var idNumerico);
            var cuerpo = new
            {
                cuestionario_id = idNumerico,
                empleado_id = empleadoId,
                empleado_nombre = empleadoNombre,
                respuesta
            };
            var httpRespuesta = await _httpClient.PostAsJsonAsync("/evaluaciones", cuerpo);

            if (!httpRespuesta.IsSuccessStatusCode)
                return Fallido("No pude evaluar tu respuesta.");

            var json = await httpRespuesta.Content.ReadAsStringAsync();
            var doc = JsonDocument.Parse(json).RootElement;

            var score = doc.TryGetProperty("score", out var s) ? s.GetString() : null;
            double? puntuacion = score switch
            {
                "correcto" => 1.0,
                "parcial"  => 0.5,
                _          => 0.0
            };

            return new RespuestaRag
            {
                Exito = true,
                Mensaje = score,
                Puntuacion = puntuacion,
                Retroalimentacion = doc.TryGetProperty("feedback", out var fb) ? fb.GetString() : null,
                RespuestaCorrecta = doc.TryGetProperty("respuesta_correcta", out var rc) ? rc.GetString() : null,
                Datos = doc
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al evaluar respuesta del cuestionario {Id}", cuestionarioId);
            return Fallido("No he podido evaluar tu respuesta en este momento. Inténtalo de nuevo más tarde.");
        }
    }

    /// <summary>Devuelve una RespuestaRag de error con el mensaje indicado.</summary>
    private static RespuestaRag Fallido(string mensaje) => new() { Exito = false, Mensaje = mensaje };
}
