using Microsoft.Bot.Builder;
using Microsoft.Bot.Schema;
using BotFormacion.Interfaces;
using BotFormacion.Models;
using BotFormacion.Repositories;

namespace BotFormacion.Bots;

/// <summary>Lógica principal del bot: detecta la intención del usuario y coordina las llamadas al RAG.</summary>
public class BotConversacional : ActivityHandler
{
    private readonly IRagService _ragService;
    private readonly RepositorioConversaciones _repoConversaciones;
    private readonly RepositorioCuestionarios _repoCuestionarios;
    private readonly ILogger<BotConversacional> _logger;

    public BotConversacional(
        IRagService ragService,
        RepositorioConversaciones repoConversaciones,
        RepositorioCuestionarios repoCuestionarios,
        ILogger<BotConversacional> logger)
    {
        _ragService = ragService;
        _repoConversaciones = repoConversaciones;
        _repoCuestionarios = repoCuestionarios;
        _logger = logger;
    }

    /// <summary>Punto de entrada para cada mensaje recibido del usuario.</summary>
    protected override async Task OnMessageActivityAsync(
        ITurnContext<IMessageActivity> turnContext,
        CancellationToken cancellationToken)
    {
        var usuarioId = turnContext.Activity.From.Id;
        var usuarioNombre = turnContext.Activity.From.Name;
        var texto = turnContext.Activity.Text?.Trim() ?? string.Empty;

        // Persistir la referencia de conversación para poder enviar mensajes proactivos
        var referenciaJson = System.Text.Json.JsonSerializer.Serialize(
            turnContext.Activity.GetConversationReference());
        await _repoConversaciones.GuardarReferenciaConversacionAsync(usuarioId, usuarioNombre, referenciaJson);

        // Cargar el contexto en memoria o crear uno nuevo
        var contexto = await _repoConversaciones.ObtenerContextoUsuario(usuarioId)
            ?? new ContextoUsuarioBot { UsuarioId = usuarioId, ConversacionId = turnContext.Activity.Conversation.Id };

        // Si la memoria no tiene cuestionario activo, consultar la API RAG como fallback
        // (cubre reinicios del bot o cuestionarios enviados de forma proactiva por el admin)
        if (!NecesitaEvaluacion(contexto))
        {
            var cuestionarioApiId = await _repoCuestionarios.ObtenerIdCuestionarioActivo(usuarioId);
            if (!string.IsNullOrEmpty(cuestionarioApiId))
            {
                contexto.CuestionarioActivo = cuestionarioApiId;
                contexto.EstadoActual = EstadoConversacion.EsperandoRespuestaEvaluacion;
            }
        }

        string respuestaTexto;

        try
        {
            if (NecesitaEvaluacion(contexto))
            {
                respuestaTexto = await ProcesarEvaluacion(contexto, texto, usuarioId, usuarioNombre);
                contexto.EstadoActual = EstadoConversacion.ConversacionLibre;
                contexto.CuestionarioActivo = null;
            }
            else if (SolicitaCuestionario(texto))
            {
                respuestaTexto = await ProcesarCuestionario(contexto, ExtraerTema(texto), usuarioId);
            }
            else
            {
                var resultado = await _ragService.ConsultarAsync(texto, usuarioId, usuarioNombre, referenciaJson);
                respuestaTexto = resultado.Mensaje ?? "No encontré información relevante.";
                contexto.EstadoActual = EstadoConversacion.ConversacionLibre;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al procesar mensaje del usuario {UsuarioId}", usuarioId);
            respuestaTexto = "No he podido procesar la solicitud en este momento. Inténtalo de nuevo más tarde.";
        }

        await turnContext.SendActivityAsync(MessageFactory.Text(respuestaTexto), cancellationToken);

        // Guardar contexto actualizado e historial
        await _repoConversaciones.GuardarContexto(contexto);
        await _repoConversaciones.GuardarActividad(new ActividadConversacional
        {
            UsuarioId = usuarioId,
            ConversacionId = contexto.ConversacionId,
            MensajeUsuario = texto,
            RespuestaBot = respuestaTexto
        });
    }

    /// <summary>Envía un saludo al usuario cuando se une al chat por primera vez.</summary>
    protected override async Task OnMembersAddedAsync(
        IList<ChannelAccount> membersAdded,
        ITurnContext<IConversationUpdateActivity> turnContext,
        CancellationToken cancellationToken)
    {
        foreach (var miembro in membersAdded)
        {
            if (miembro.Id != turnContext.Activity.Recipient.Id)
            {
                await turnContext.SendActivityAsync(
                    MessageFactory.Text(
                        "¡Hola! Soy el bot de formación de la empresa. " +
                        "Puedes preguntarme cualquier cosa sobre la empresa o pedir un cuestionario escribiendo \"cuestionario\"."),
                    cancellationToken);
            }
        }
    }

    /// <summary>Devuelve true si el usuario tiene un cuestionario pendiente de responder.</summary>
    private bool NecesitaEvaluacion(ContextoUsuarioBot contexto) =>
        contexto.EstadoActual == EstadoConversacion.EsperandoRespuestaEvaluacion
        && !string.IsNullOrEmpty(contexto.CuestionarioActivo);

    /// <summary>Devuelve true si el mensaje del usuario solicita un cuestionario.</summary>
    private bool SolicitaCuestionario(string texto)
    {
        var lower = texto.ToLowerInvariant();
        return lower.Contains("cuestionario") || lower.Contains("quiz") || lower.Contains("pregúntame");
    }

    /// <summary>Extrae el tema del mensaje si el usuario lo especificó (ej. "cuestionario sobre seguridad").</summary>
    private string ExtraerTema(string texto)
    {
        var palabrasClave = new[] { "cuestionario sobre", "quiz sobre", "cuestionario de", "quiz de" };
        var lower = texto.ToLowerInvariant();
        foreach (var clave in palabrasClave)
        {
            var pos = lower.IndexOf(clave);
            if (pos >= 0)
            {
                var tema = texto[(pos + clave.Length)..].Trim();
                if (!string.IsNullOrEmpty(tema)) return tema;
            }
        }
        return string.Empty;
    }

    /// <summary>Genera un cuestionario, lo envía al usuario y actualiza el estado a EsperandoRespuesta.</summary>
    private async Task<string> ProcesarCuestionario(ContextoUsuarioBot contexto, string tema, string usuarioId)
    {
        var resultado = await _ragService.GenerarCuestionarioAsync(tema);

        if (!resultado.Exito || string.IsNullOrEmpty(resultado.Pregunta))
            return resultado.Mensaje ?? "No pude generar el cuestionario en este momento.";

        contexto.EstadoActual = EstadoConversacion.EsperandoRespuestaEvaluacion;
        contexto.CuestionarioActivo = resultado.CuestionarioId;

        await _repoCuestionarios.ActualizarEstadoCuestionario(
            usuarioId, resultado.CuestionarioId ?? string.Empty, EstadoConversacion.EsperandoRespuestaEvaluacion);

        return $"🧠 **Cuestionario de formación**\n\n{resultado.Pregunta}\n\nEscribe tu respuesta:";
    }

    /// <summary>Evalúa la respuesta del usuario, limpia el cuestionario activo y devuelve el resultado.</summary>
    private async Task<string> ProcesarEvaluacion(ContextoUsuarioBot contexto, string respuesta, string usuarioId, string usuarioNombre)
    {
        var resultado = await _ragService.EvaluarRespuestaAsync(
            contexto.CuestionarioActivo!, respuesta, usuarioId, usuarioNombre);

        await _repoCuestionarios.ActualizarEstadoCuestionario(
            usuarioId, contexto.CuestionarioActivo!, EstadoConversacion.ConversacionLibre);

        if (!resultado.Exito)
            return resultado.Mensaje ?? "Recibí tu respuesta pero no pude evaluarla en este momento.";

        var emoji = resultado.Mensaje switch
        {
            "correcto" => "✅",
            "parcial"  => "🟡",
            _          => "❌"
        };

        return $"{emoji} **{resultado.Mensaje?.ToUpperInvariant()}**\n\n" +
               $"{resultado.Retroalimentacion}\n\n" +
               $"**Respuesta correcta:** {resultado.RespuestaCorrecta}";
    }
}
