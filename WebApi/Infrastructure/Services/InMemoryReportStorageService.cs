using System.Collections.Concurrent;
using Domain.Models;
using Domain.Services;

namespace Infrastructure.Services
{
    public class InMemoryReportStorageService : IReportStorageService
    {
        // Потокобезопасный словарь для хранения состояний в памяти
        private readonly ConcurrentDictionary<string, ReportState> _states = new();

        public ReportState? GetState( string correlationId )
        {
            _states.TryGetValue( correlationId, out var state );
            return state;
        }

        public void SetState( string correlationId, ReportState state )
        {
            // AddOrUpdate гарантирует потокобезопасность
            _states.AddOrUpdate( correlationId, state, ( key, oldState ) => state );
        }
    }
}
