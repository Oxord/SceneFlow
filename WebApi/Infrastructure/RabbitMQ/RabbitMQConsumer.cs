using System.Text;
using System.Text.Json;
using Domain.Models;
using Domain.Services;
using Microsoft.Extensions.Options;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

namespace Infrastructure.RabbitMQ
{
    public class RabbitMQConsumer : IMessageQueueConsumer
    {
        private IConnection _connection;
        private IChannel _channel;
        // Настройки теперь используются только для подключения, а не для имени очереди
        private readonly RabbitMQSettings _settings;

        private RabbitMQConsumer( IOptions<RabbitMQSettings> settings )
        {
            _settings = settings.Value;
        }

        public static async Task<RabbitMQConsumer> CreateAsync( IOptions<RabbitMQSettings> settings )
        {
            var consumer = new RabbitMQConsumer( settings );
            await consumer.InitializeAsync();
            return consumer;
        }

        // ИЗМЕНЕНИЕ: InitializeAsync теперь ТОЛЬКО подключается
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

                // Вся логика объявления очередей и привязок отсюда УБРАНА
            }
            catch ( Exception ex )
            {
                Console.WriteLine( $"Error initializing RabbitMQ Connection: {ex.Message}" );
                throw;
            }
        }

        // ИЗМЕНЕНИЕ: Основная логика теперь здесь
        public async Task StartConsumingAsync<T>(
            string queueName,
            string exchangeName,
            string routingKey,
            Func<T, Task> onMessageReceived,
            Dictionary<string, object>? queueArguments = null ) where T : class
        {
            if ( _channel == null )
            {
                throw new InvalidOperationException( "RabbitMQ connection is not established." );
            }

            // --- ШАГ 1: Объявляем топологию для ЭТОГО конкретного потребителя ---

            // Объявляем Exchange
            await _channel.ExchangeDeclareAsync( exchangeName, ExchangeType.Direct, durable: true );

            // Объявляем Очередь
            await _channel.QueueDeclareAsync(
                queue: queueName,
                durable: true,
                exclusive: false,
                autoDelete: false,
                arguments: queueArguments );

            // Связываем их
            await _channel.QueueBindAsync(
                queue: queueName,
                exchange: exchangeName,
                routingKey: routingKey );

            // --- ШАГ 2: Настраиваем и запускаем потребителя ---

            await _channel.BasicQosAsync( prefetchSize: 0, prefetchCount: 1, global: false );

            var consumer = new AsyncEventingBasicConsumer( _channel );

            consumer.ReceivedAsync += async ( sender, ea ) =>
            {
                // Эта логика остается без изменений
                var body = ea.Body.ToArray();
                var jsonMessage = Encoding.UTF8.GetString( body );

                try
                {
                    T? message = JsonSerializer.Deserialize<T>( jsonMessage );
                    if ( message == null )
                    {
                        await _channel.BasicNackAsync( ea.DeliveryTag, false, false );
                        return;
                    }
                    await onMessageReceived( message );
                    await _channel.BasicAckAsync( ea.DeliveryTag, false );
                }
                catch ( Exception ex )
                {
                    Console.WriteLine( $"Error processing message from queue '{queueName}': {ex.Message}" );
                    await _channel.BasicNackAsync( ea.DeliveryTag, false, false );
                }
            };

            await _channel.BasicConsumeAsync(
                queue: queueName,
                autoAck: false,
                consumer: consumer );

            Console.WriteLine( $"Started consuming from queue: '{queueName}'" );
        }

        public void Dispose()
        {
            _channel?.Dispose();
            _connection?.Dispose();
        }
    }
}