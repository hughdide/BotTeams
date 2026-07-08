using Microsoft.Extensions.Options;
using Newtonsoft.Json;
using BotFormacion.Configuration;
using BotFormacion.Models;

namespace BotFormacion.Repositories;

/// <summary>
/// Gestiona el historial y contexto de usuarios en memoria,
/// y sincroniza las referencias de conversación con la API RAG.
/// </summary>
public class RepositorioConversaciones
{
    private readonly Dictionary<string, List<ActividadConversacional>> _historial = new();
    private readonly Dictionary<string, ContextoUsuarioBot> _contextos = new();
    private readonly IHttpClientFactory _clientFactory;
    private readonly OpcionesRag _opciones;
    private readonly ILogger<RepositorioConversaciones> _logger;

    public RepositorioConversaciones(
        IHttpClientFactory clientFactory,
        IOptions<OpcionesRag> opciones,
        ILogger<RepositorioConversaciones> logger)
    {
        _clientFactory = clientFactory;
        _opciones = opciones.Value;
        _logger = logger;
    }

    /// <summary>Devuelve los últimos N mensajes del usuario.</summary>
    public Task<List<ActividadConversacional>> ObtenerHistorial(string usuarioId, int limite = 20)
    {
        if (!_historial.TryGetValue(usuarioId, out var lista))
            return Task.FromResult(new List<ActividadConversacional>());

        return Task.FromResult(lista.TakeLast(limite).ToList());
    }

    /// <summary>Añade una actividad al historial en memoria.</summary>
    public Task GuardarActividad(ActividadConversacional actividad)
    {
        if (!_historial.ContainsKey(actividad.UsuarioId))
            _historial[actividad.UsuarioId] = new List<ActividadConversacional>();

        _historial[actividad.UsuarioId].Add(actividad);
        return Task.CompletedTask;
    }

    /// <summary>Recupera el contexto actual del usuario desde memoria.</summary>
    public Task<ContextoUsuarioBot?> ObtenerContextoUsuario(string usuarioId)
    {
        _contextos.TryGetValue(usuarioId, out var contexto);
        return Task.FromResult(contexto);
    }

    /// <summary>Actualiza el contexto del usuario en memoria.</summary>
    public Task GuardarContexto(ContextoUsuarioBot contexto)
    {
        contexto.FechaUltimaActividad = DateTime.UtcNow;
        _contextos[contexto.UsuarioId] = contexto;
        return Task.CompletedTask;
    }

    /// <summary>Persiste la referencia de conversación en la API RAG para mensajes proactivos.</summary>
    public async Task GuardarReferenciaConversacionAsync(string empleadoId, string empleadoNombre, string referenciaJson)
    {
        try
        {
            var cliente = CrearCliente();
            var cuerpo = new
            {
                empleado_id = empleadoId,
                empleado_nombre = empleadoNombre,
                conversation_reference = referenciaJson
            };
            await cliente.PostAsJsonAsync("/conversaciones", cuerpo);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al guardar referencia de conversación para {EmpleadoId}", empleadoId);
        }
    }

    /// <summary>Lista todas las referencias de conversación almacenadas en la API RAG.</summary>
    public async Task<List<(string EmpleadoId, string Nombre, string ReferenciaJson)>> ObtenerTodasLasReferenciasAsync()
    {
        try
        {
            var cliente = CrearCliente();
            var respuesta = await cliente.GetAsync("/conversaciones");
            if (!respuesta.IsSuccessStatusCode) return new();

            var json = await respuesta.Content.ReadAsStringAsync();
            var lista = JsonConvert.DeserializeObject<List<ConversacionDto>>(json);

            return lista?
                .Where(c => !string.IsNullOrEmpty(c.EmpleadoId) && c.ConversationReference != null)
                .Select(c => (c.EmpleadoId, c.EmpleadoNombre, JsonConvert.SerializeObject(c.ConversationReference)))
                .ToList() ?? new();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al obtener referencias de conversación");
            return new();
        }
    }

    /// <summary>Obtiene los usuarios registrados desde /estadisticas/usuarios, incluyendo su conversation_reference.</summary>
    public async Task<List<UsuarioEstadisticaDto>> ObtenerUsuariosAsync()
    {
        try
        {
            var cliente = CrearCliente();
            var respuesta = await cliente.GetAsync("/estadisticas/usuarios");
            if (!respuesta.IsSuccessStatusCode) return new();

            var json = await respuesta.Content.ReadAsStringAsync();
            return JsonConvert.DeserializeObject<List<UsuarioEstadisticaDto>>(json) ?? new();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error al obtener usuarios de estadísticas");
            return new();
        }
    }

    /// <summary>Crea un HttpClient configurado con la base URL y API Key del RAG.</summary>
    private HttpClient CrearCliente()
    {
        var cliente = _clientFactory.CreateClient();
        cliente.BaseAddress = new Uri(_opciones.RagUrl.TrimEnd('/'));
        cliente.DefaultRequestHeaders.Add("X-Api-Key", _opciones.RagApiKey);
        return cliente;
    }

    private class ConversacionDto
    {
        [JsonProperty("empleado_id")]   public string EmpleadoId { get; set; } = string.Empty;
        [JsonProperty("empleado_nombre")] public string EmpleadoNombre { get; set; } = string.Empty;
        [JsonProperty("conversation_reference")] public Newtonsoft.Json.Linq.JToken? ConversationReference { get; set; }
    }

    public class UsuarioEstadisticaDto
    {
        [JsonProperty("usuario_id")]    public string UsuarioId { get; set; } = string.Empty;
        [JsonProperty("usuario_nombre")] public string UsuarioNombre { get; set; } = string.Empty;
        [JsonProperty("total_consultas")] public int TotalConsultas { get; set; }
        [JsonProperty("ultima_consulta")] public DateTime? UltimaConsulta { get; set; }
        [JsonProperty("conversation_reference")] public Newtonsoft.Json.Linq.JToken? ConversationReference { get; set; }
    }
}
