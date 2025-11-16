using Domain.Models;

namespace Domain.Services
{
    public interface IReportStorageService
    {
        void SetState( string correlationId, ReportState state );
        ReportState? GetState( string correlationId );
    }
}
