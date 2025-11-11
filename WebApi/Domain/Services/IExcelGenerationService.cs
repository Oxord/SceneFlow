using Domain.Models;

namespace Domain.Services
{
    public interface IExcelGenerationService
    {
        byte[] CreateSceneReport( IEnumerable<Scene> scenes );
    }
}
