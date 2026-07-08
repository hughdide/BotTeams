using Microsoft.Extensions.Options;
using Newtonsoft.Json;
using BotFormacion.Configuration;
using BotFormacion.Models;

namespace BotFormacion.Repositories;

/// <summary>Gestiona el estado de cuestionarios activos sincronizando con la API RAG.</summary>
public class RepositorioCuestionarios
{
    private readonly IHttpClientFactory _clientFactory;
    private readonly OpcionesRag _opciones;
    private readonly ILogger<RepositorioCuestionarios> _logger;

    public RepositorioCuestionarios(
        IHttpClientFactory clientFactory,
        IOptions<OpcionesRag> opciones,
        ILogger<RepositorioCuestionarios> logger)
    {
        _clientFactory = clientFactory;
        _opciones = opciones.Value;
        _logger = logger;
    }

    /// <summary>Devuelve los cuestionarios activos de un usuario consultando la API RAG.</summary>
    public async Task<List<ContextoUsuarioBot>> ObtenerCuestionariosActivos(string usuarioId)
    {
        try
        {
            var cliente = CrearCliente();
            var respuesta = await cliente.GetAsync($"/conversaciones/cuestionarios-activos/{Uri.EscapeDataString(usuarioId)}");
            if (!respuesta.IsSuccessStatusCode) return new();

            var json = await respuesta.Content.ReadAsStringAsync();
            var dto = JsonConvert.DeserializeObject<CuestionarioActivoDto>(json);

            if (dto?.CuestionarioId == null) return new();

            return new List<ContextoUsuarioBot>
            {
                new()
                {
                    UsuarioId = usuarioId,
                    CuestionarioActivo = dto.CuestionarioId.ToString(),
                    EstadoActual = EstadoConversacion.EsperandoRespuestaEvaluacion
                }
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al obtener cuestionarios activos para {UsuarioId}", usuarioId);
            return new();
        }
    }

    /// <summary>Registra o elimina el cuestionario activo en la API RAG según el estado indicado.</summary>
    public async Task ActualizarEstadoCuestionario(string usuarioId, string cuestionarioId, EstadoConversacion estado)
    {
        try
        {
            var cliente = CrearCliente();

            if (estado == EstadoConversacion.EsperandoRespuestaEvaluacion || estado == EstadoConversacion.CuestionarioActivo)
            {
                _ = int.TryParse(cuestionarioId, out var idNumerico);
                var cuerpo = new { empleado_id = usuarioId, cuestionario_id = idNumerico };
                await cliente.PostAsJsonAsync("/conversaciones/cuestionarios-activos", cuerpo);
            }
            else
            {
                await cliente.DeleteAsync($"/conversaciones/cuestionarios-activos/{Uri.EscapeDataString(usuarioId)}");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al actualizar estado de cuestionario para {UsuarioId}", usuarioId);
        }
    }

    /// <summary>Devuelve solo el id del cuestionario activo del usuario, o null si no tiene ninguno.</summary>
    public async Task<string?> ObtenerIdCuestionarioActivo(string usuarioId)
    {
        var lista = await ObtenerCuestionariosActivos(usuarioId);
        return lista.FirstOrDefault()?.CuestionarioActivo;
    }

    /// <summary>Crea un HttpClient configurado con la base URL y API Key del RAG.</summary>
    private HttpClient CrearCliente()
    {
        var cliente = _clientFactory.CreateClient();
        cliente.BaseAddress = new Uri(_opciones.RagUrl.TrimEnd('/'));
        cliente.DefaultRequestHeaders.Add("X-Api-Key", _opciones.RagApiKey);
        return cliente;
    }

    private class CuestionarioActivoDto
    {
        [JsonProperty("cuestionario_id")] public int? CuestionarioId { get; set; }
    }
}
