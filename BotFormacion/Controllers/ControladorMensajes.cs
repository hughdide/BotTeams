using Microsoft.AspNetCore.Mvc;
using Microsoft.Bot.Builder;
using Microsoft.Bot.Builder.Integration.AspNet.Core;

namespace BotFormacion.Controllers;

/// <summary>Punto de entrada HTTP para los mensajes del Bot Framework.</summary>
[ApiController]
[Route("api/messages")]
public class ControladorMensajes : ControllerBase
{
    private readonly IBotFrameworkHttpAdapter _adaptador;
    private readonly IBot _bot;
    private readonly ILogger<ControladorMensajes> _logger;

    public ControladorMensajes(
        IBotFrameworkHttpAdapter adaptador,
        IBot bot,
        ILogger<ControladorMensajes> logger)
    {
        _adaptador = adaptador;
        _bot = bot;
        _logger = logger;
    }

    /// <summary>Recibe la actividad de Teams y la delega al adaptador.</summary>
    [HttpPost]
    public async Task Mensajes()
    {
        try
        {
            await _adaptador.ProcessAsync(Request, Response, _bot);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al procesar la actividad entrante");
            throw;
        }
    }

    /// <summary>Comprueba que el controlador está activo.</summary>
    [HttpGet]
    public IActionResult ProcesarActividad() => Ok("El controlador de mensajes está activo.");
}
