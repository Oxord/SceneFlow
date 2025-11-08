namespace API.Controllers
{
    using Domain.Models;
    using Microsoft.AspNetCore.Mvc;

    [ApiController]
    [Route( "api/[controller]" )]
    public class FileUploadController : ControllerBase
    {
        private static List<FileStorage> _fileStorageList = new List<FileStorage>();

        [HttpPost]
        public async Task<IActionResult> UploadFile( IFormFile file )
        {
            if ( file == null || file.Length == 0 )
            {
                return BadRequest( "No file uploaded." );
            }

            using ( var memoryStream = new MemoryStream() )
            {
                await file.CopyToAsync( memoryStream );
                var fileContent = memoryStream.ToArray();
                var fileStorage = new FileStorage( file.FileName, file.Length, fileContent );
                _fileStorageList.Add( fileStorage ); // Сохраняем файл в списке

                return Ok( new { fileStorage.FileName, fileStorage.FileSize } );
            }
        }
    }
}
