using System.Text;
using System.Text.Json;
using Domain.Models;
using Domain.Services;
using Microsoft.Extensions.Options;
using RabbitMQ.Client;

namespace Infrastructure.RabbitMQ
{
    public class RabbitMQPublisher : IMessageQueuePublisher, IDisposable
    {
        private IConnection _connection;
        private IChannel _channel;
        private readonly RabbitMQSettings _settings;

        private RabbitMQPublisher( IOptions<RabbitMQSettings> settings )
        {
            _settings = settings.Value;
        }

        public static async Task<RabbitMQPublisher> CreateAsync( IOptions<RabbitMQSettings> settings )
        {
            var publisher = new RabbitMQPublisher( settings );
            await publisher.InitializeAsync();
            return publisher;
        }

        private async Task InitializeAsync()
        {
            var factory = new ConnectionFactory()
            {
                HostName = _settings.HostName,
                Port = _settings.Port,
                UserName = _settings.UserName,
                Password = _settings.Password,
                VirtualHost = _settings.VirtualHost
            };

            try
            {
                _connection = await factory.CreateConnectionAsync();
                _channel = await _connection.CreateChannelAsync();
                var arguments = new Dictionary<string, string> { { "x-queue-type", "quorum" } };

                await _channel.QueueDeclareAsync( queue: _settings.QueueName,
                                         durable: true,
                                         exclusive: false,
                                         autoDelete: false,
                                         arguments.ToDictionary( kvp => kvp.Key, kvp => ( object? )kvp.Value ) );
            }
            catch ( Exception ex )
            {
                // В продакшене здесь можно добавить логику повторных попыток или обработку фатальной ошибки
                throw; // Перебрасываем исключение, чтобы приложение не стартовало без RabbitMQ
            }
        }

        public async Task PublishAsync<T>( T message, string queueName ) where T : class
        {
            if ( _channel == null || _connection == null || !_connection.IsOpen )
            {
                // Можно добавить логику для восстановления соединения или повторной попытки
                throw new InvalidOperationException( "RabbitMQ connection is not established." );
            }

            var json = JsonSerializer.Serialize( message );
            var body = Encoding.UTF8.GetBytes( json );

            await _channel.BasicPublishAsync(
                exchange: "FileUploadedEvent",
                routingKey: "sf_scenarios",
                body,
                CancellationToken.None );
        }

        public void Dispose()
        {
            _channel?.Dispose();
            _connection?.Dispose();
        }
    }
}
