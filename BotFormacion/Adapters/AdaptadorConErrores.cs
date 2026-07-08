using Microsoft.Bot.Builder.Integration.AspNet.Core;
using Microsoft.Bot.Builder.TraceExtensions;

namespace BotFormacion.Adapters;

/// <summary>CloudAdapter con manejo centralizado de errores no controlados.</summary>
public class AdaptadorConErrores : CloudAdapter
{
    public AdaptadorConErrores(IConfiguration configuration, ILogger<AdaptadorConErrores> logger)
        : base(new ConfigurationBotFrameworkAuthentication(configuration), logger)
    {
        OnTurnError = async (turnContext, exception) =>
        {
            logger.LogError(exception, "Error no controlado en el turno de conversación");

            await turnContext.SendActivityAsync(
                "Lo sentimos, se ha producido un error. Inténtalo de nuevo más tarde.");

            await turnContext.TraceActivityAsync(
                "OnTurnError Trace",
                exception.Message,
                "https://www.botframework.com/schemas/error",
                "TurnError");
        };
    }
}
