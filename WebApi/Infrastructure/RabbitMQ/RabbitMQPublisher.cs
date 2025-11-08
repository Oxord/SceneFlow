using System.Text;
using RabbitMQ.Client;

namespace Infrastructure.RabbitMQ
{
    public class RabbitMQPublisher
    {
        public async void Publish()
        {
            // 1. Создаем фабрику подключений
            // Здесь вы указываете параметры подключения к вашему RabbitMQ серверу
            var factory = new ConnectionFactory()
            {
                HostName = "rabbitmqadmin -H 82.97.240.224 -u gen_user -p 'OCwZh~#_{2:zWB' list vhosts", // Имя хоста RabbitMQ (или IP-адрес)
                Port = AmqpTcpEndpoint.UseDefaultPort, // Порт по умолчанию: 5672
                UserName = "sceneflow", // Имя пользователя по умолчанию
                Password = "srz%7t0!,mriVQ",  // Пароль по умолчанию
                VirtualHost = "default_vhost"
            };

            // 2. Создаем подключение к RabbitMQ
            // IConnection реализует IDisposable, поэтому используем using для автоматического закрытия
            using ( var connection = await factory.CreateConnectionAsync() )
            {
                // 3. Создаем канал (Channel)
                // Все операции с RabbitMQ (объявление очередей, отправка/получение сообщений) выполняются через канал.
                // IModel (канал) также реализует IDisposable.
                using ( var channel = await connection.CreateChannelAsync() )
                {
                    // 4. Объявляем очередь (Queue)
                    // Если очередь с таким именем не существует, RabbitMQ ее создаст.
                    // durable: true - очередь переживет перезапуск брокера.
                    // exclusive: false - очередь доступна для использования несколькими потребителями.
                    // autoDelete: false - очередь не будет удалена, когда последний потребитель отключается.
                    await channel.QueueDeclareAsync( queue: "my_queue",
                                         durable: false,
                                         exclusive: false,
                                         autoDelete: false,
                                         arguments: null );

                    // 5. Формируем сообщение
                    string message = "Привет, RabbitMQ из C#! Это мое первое сообщение.";
                    var body = Encoding.UTF8.GetBytes( message ); // Сообщение должно быть массивом байтов

                    // 6. Публикуем сообщение
                    // exchange: "" - использует default exchange (прямая маршрутизация в очередь, указанную в routingKey)
                    // routingKey: "my_queue" - имя очереди, куда будет отправлено сообщение
                    // basicProperties: null - дополнительные свойства сообщения (приоритет, заголовки и т.д.)
                    // body: тело сообщения

                    await channel.BasicPublishAsync(
                                        exchange: "ex",
                                        routingKey: "sf_log",
                                        body,
                                        CancellationToken.None );

                    //await channel.BasicPublishAsync( exchange: "",
                    //                     routingKey: "my_queue",
                    //                     mandatory: false,
                    //                     basicProperties: null,
                    //                     body: body );

                    Console.WriteLine( $" [x] Отправлено: '{message}'" );
                }
            }

            Console.WriteLine( "Нажмите [Enter] для выхода." );
            Console.ReadLine();
        }
    }
}
