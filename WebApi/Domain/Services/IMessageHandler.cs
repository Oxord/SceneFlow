namespace Domain.Services
{
    public interface IMessageHandler
    {
        Task HandleMessageAsync<T>( T message ) where T : class;
    }
}
