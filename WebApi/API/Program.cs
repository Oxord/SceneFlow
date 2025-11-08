
using Domain.Models;
using Domain.Services;
using Infrastructure.RabbitMQ;
using Infrastructure.Services;
using Microsoft.Extensions.Options;

namespace API
{
    public class Program
    {
        public static void Main( string[] args )
        {
            var builder = WebApplication.CreateBuilder( args );

            // Add services to the container.

            builder.Services.AddControllers();
            // Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
            builder.Services.AddEndpointsApiExplorer();
            builder.Services.AddSwaggerGen();

            builder.Services.Configure<CloudStorageSettings>( builder.Configuration.GetSection( "CloudStorageSettings" ) );
            builder.Services.AddSingleton<ICloudStorageService, CloudStorageService>();

            // Настройки RabbitMQ
            builder.Services.Configure<RabbitMQSettings>( builder.Configuration.GetSection( "RabbitMQSettings" ) );

            // Асинхронная регистрация RabbitMQPublisher

            builder.Services.AddSingleton<IMessageQueuePublisher>( sp =>
            {
                var settings = sp.GetRequiredService<IOptions<RabbitMQSettings>>();
                // Вызовите здесь асинхронный метод синхронно, например:
                return RabbitMQPublisher.CreateAsync( settings ).GetAwaiter().GetResult();
            } );

            var app = builder.Build();

            // Configure the HTTP request pipeline.
            if ( app.Environment.IsDevelopment() )
            {
                app.UseSwagger();
                app.UseSwaggerUI();
            }

            app.UseHttpsRedirection();

            app.UseAuthorization();


            app.MapControllers();

            app.Run();
        }
    }
}
