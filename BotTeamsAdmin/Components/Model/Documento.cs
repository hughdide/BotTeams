using System.Text.Json.Serialization;

namespace BotTeamsAdmin.Components.Model
{
    public class Documento
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("nombre")]
        public string Nombre { get; set; } = "";

        [JsonPropertyName("tipo_mime")]
        public string TipoMime { get; set; } = "";

        [JsonPropertyName("tamano_bytes")]
        public long TamanoBytes { get; set; }

        [JsonPropertyName("estado")]
        public string Estado { get; set; } = "";

        [JsonPropertyName("fecha_subida")]
        public DateTime FechaSubida { get; set; }
    }
}
