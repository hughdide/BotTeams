using Microsoft.AspNetCore.Identity;

namespace BotTeamsAdmin.Data;

public static class DbSeeder
{
    public static async Task SeedAsync(IServiceProvider services)
    {
        var userManager = services.GetRequiredService<UserManager<ApplicationUser>>();

        var adminEmail = "hugo.d@galsoft.es";
        var adminUser = await userManager.FindByEmailAsync(adminEmail);

        Console.WriteLine($"Usuario encontrado: {adminUser != null}");

        if (adminUser == null)
        {
            adminUser = new ApplicationUser
            {
                UserName = adminEmail,
                Email = adminEmail,
                EmailConfirmed = true
            };

            var result = await userManager.CreateAsync(adminUser, "Admin1234!");

            Console.WriteLine($"Resultado creación: {result.Succeeded}");

            if (!result.Succeeded)
            {
                foreach (var error in result.Errors)
                {
                    Console.WriteLine($"Error: {error.Description}");
                }
            }
        }
    }
}