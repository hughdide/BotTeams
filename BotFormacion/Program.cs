using Microsoft.Bot.Builder;
using Microsoft.Bot.Builder.Integration.AspNet.Core;
using BotFormacion.Adapters;
using BotFormacion.Bots;
using BotFormacion.Configuration;
using BotFormacion.Interfaces;
using BotFormacion.Repositories;
using BotFormacion.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddHttpClient();

// Configuración del servicio RAG
builder.Services.Configure<OpcionesRag>(builder.Configuration.GetSection("Rag"));

// Bot Framework
builder.Services.AddSingleton<IBotFrameworkHttpAdapter, AdaptadorConErrores>();
builder.Services.AddTransient<IBot, BotConversacional>();

// Servicio RAG con HttpClient tipado
builder.Services.AddHttpClient<IRagService, ServicioRag>();

// Repositorios (en memoria + sincronización con API RAG)
builder.Services.AddSingleton<RepositorioConversaciones>();
builder.Services.AddSingleton<RepositorioCuestionarios>();

var app = builder.Build();

app.UseHttpsRedirection();
app.UseWebSockets();
app.UseRouting();
app.MapControllers();

app.MapGet("/", () => Results.Ok("Bot de formación en funcionamiento."));
app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

// Endpoint de administración: envía un cuestionario a todos los empleados registrados
app.MapPost("/admin/send-quiz", async (
    IRagService ragService,
    RepositorioConversaciones repoConversaciones,
    RepositorioCuestionarios repoCuestionarios,
    IBotFrameworkHttpAdapter adaptador,
    IConfiguration config,
    HttpRequest req,
    ILogger<Program> logger) =>
{
    var claveAdmin = req.Headers["x-admin-key"].ToString();
    if (claveAdmin != config["AdminApiKey"])
        return Results.Unauthorized();

    var cuestionario = await ragService.GenerarCuestionarioAsync();
    if (!cuestionario.Exito || string.IsNullOrEmpty(cuestionario.Pregunta))
        return Results.Problem("No se pudo generar el cuestionario.");

    // /estadisticas/usuarios ya incluye conversation_reference: fuente única para el envío
    var usuarios = await repoConversaciones.ObtenerUsuariosAsync();
    if (usuarios.Count == 0)
        return Results.Problem("No hay usuarios registrados en el sistema.");

    var enviados = 0;
    var sinReferencia = new List<string>();
    var errores = new List<string>();

    foreach (var usuario in usuarios)
    {
        if (string.IsNullOrEmpty(usuario.UsuarioId)) continue;

        if (usuario.ConversationReference == null)
        {
            sinReferencia.Add(usuario.UsuarioNombre);
            continue;
        }

        try
        {
            await repoCuestionarios.ActualizarEstadoCuestionario(
                usuario.UsuarioId,
                cuestionario.CuestionarioId ?? string.Empty,
                BotFormacion.Models.EstadoConversacion.EsperandoRespuestaEvaluacion);

            var convRef = Newtonsoft.Json.JsonConvert
                .DeserializeObject<Microsoft.Bot.Schema.ConversationReference>(
                    usuario.ConversationReference.ToString());

            var cloudAdapter = (CloudAdapter)adaptador;
            await cloudAdapter.ContinueConversationAsync(
                config["MicrosoftAppId"],
                convRef,
                async (context, ct) =>
                {
                    await context.SendActivityAsync(
                        $"🧠 **Cuestionario de formación**\n\n{cuestionario.Pregunta}\n\nEscribe tu respuesta:");
                },
                CancellationToken.None);

            enviados++;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error enviando cuestionario a {EmpleadoId}", usuario.UsuarioId);
            errores.Add($"{usuario.UsuarioNombre}: {ex.Message}");
        }
    }

    return Results.Ok(new
    {
        mensaje = $"Cuestionario enviado a {enviados} de {usuarios.Count} empleados",
        cuestionario_id = cuestionario.CuestionarioId,
        sin_referencia = sinReferencia,
        errores
    });
});

app.Run();
