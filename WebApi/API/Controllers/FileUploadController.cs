using System.Threading.Tasks;
using Domain.DTO.RabbitMQ;
using Domain.Models;
using Domain.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;

namespace API.Controllers
{
    [ApiController]
    [Route( "api/[controller]" )]
    public class FileUploadController : ControllerBase
    {
        private static List<FileStorage> _fileStorageList = new List<FileStorage>();
        private IMessageQueuePublisher _rabbitMQPublisher;
        private readonly ICloudStorageService _cloudStorageService;
        private readonly IMessageQueuePublisher _messageQueuePublisher;
        private readonly RabbitMQSettings _rabbitMQSettings;

        public FileUploadController(
            ICloudStorageService cloudStorageService,
            IMessageQueuePublisher messageQueuePublisher,
            IOptions<RabbitMQSettings> rabbitMQSettingsOptions
        )
        {
            _cloudStorageService = cloudStorageService;
            _messageQueuePublisher = messageQueuePublisher;
            _rabbitMQSettings = rabbitMQSettingsOptions.Value;
        }

        [HttpPost]
        public async Task<IActionResult> UploadFile( IFormFile file )
        {
            if ( file == null || file.Length == 0 )
            {
                return BadRequest( "No file uploaded." );
            }

            try
            {
                using ( var fileStream = file.OpenReadStream() )
                {
                    string storageUrl = await _cloudStorageService.UploadFileAsync(
                        fileStream,
                        file.FileName,
                        file.ContentType
                    );

                    var fileStorage = new FileStorage( file.FileName, file.Length, storageUrl );
                    _fileStorageList.Add( fileStorage );

                    var correlationId = Guid.NewGuid().ToString();
                    var uploadEvent = new FileUploadedEvent
                    {
                        FileName = fileStorage.FileName,
                        FileSize = fileStorage.FileSize,
                        StorageUrl = fileStorage.StorageUrl,
                        UploadedAt = fileStorage.UploadedAt,
                        CorrelationId = correlationId
                    };

                    await _messageQueuePublisher.PublishAsync( uploadEvent, _rabbitMQSettings.QueueName );

                    return Accepted( new { CorrelationId = correlationId } );
                }
            }
            catch ( Exception ex )
            {
                return StatusCode( 500, $"Internal server error: {ex.Message}" );
            }
        }
    }
}
