namespace Domain.Services
{
    public interface IMessageQueueConsumer : IDisposable
    {
        Task StartConsumingAsync<T>(
        string queueName,
        string exchangeName,
        string routingKey,
        Func<T, Task> onMessageReceived,
        Dictionary<string, object>? queueArguments = null ) where T : class;
    }
}
