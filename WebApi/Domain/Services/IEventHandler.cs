namespace Domain.Services
{
    public interface IEventHandler
    {
        Task HandleEventAsync<T>( T message ) where T : class;
    }
}
