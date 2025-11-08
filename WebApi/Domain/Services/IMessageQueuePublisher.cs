namespace Domain.Services
{
    public interface IMessageQueuePublisher
    {
        Task PublishAsync<T>( T message, string queueName ) where T : class;
    }
}