namespace BotFormacion.Configuration;

/// <summary>Parámetros de conexión a la API RAG, mapeados desde la sección "Rag" de appsettings.json.</summary>
public class OpcionesRag
{
    public string RagUrl { get; set; } = string.Empty;
    public string RagApiKey { get; set; } = string.Empty;
}
