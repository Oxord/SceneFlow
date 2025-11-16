using System.Threading.Tasks;
using Amazon.S3;
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
        private readonly IExcelGenerationService _excelGenerationService;
        private readonly IReportStorageService _reportStorageService;
        private readonly ILogger<FileUploadController> _logger;

        public FileUploadController(
            ICloudStorageService cloudStorageService,
            IMessageQueuePublisher messageQueuePublisher,
            IOptions<RabbitMQSettings> rabbitMQSettingsOptions,
            IExcelGenerationService excelGenerationService,
            IReportStorageService reportStorageService,
            ILogger<FileUploadController> logger
        )
        {
            _cloudStorageService = cloudStorageService;
            _messageQueuePublisher = messageQueuePublisher;
            _rabbitMQSettings = rabbitMQSettingsOptions.Value;
            _excelGenerationService = excelGenerationService;
            _reportStorageService = reportStorageService;
            _logger = logger;
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

                    _reportStorageService.SetState( correlationId, new ReportState { Status = "Queued" } );

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

        [HttpGet]
        public async Task<IActionResult> GetReport( [FromQuery] string correlationId )
        {
            var state = _reportStorageService.GetState( correlationId );
            if ( state == null )
            {
                return NotFound( new { message = "Report with this ID not found." } );
            }

            switch ( state.Status )
            {
                case "Queued":
                case "Processing":
                    return Ok( new { status = state.Status, message = "Report generation is in progress." } );

                case "Completed":
                    string objectKey = null; // Выносим для логирования
                    try
                    {
                        // --- НАЧАЛО ИЗМЕНЕНИЙ ---

                        // state.Url содержит полный URL, например: "http://s3.yandex.net/my-bucket/guid_report.xlsx"
                        // Нам нужно извлечь из него только ключ: "guid_report.xlsx"

                        if ( string.IsNullOrEmpty( state.Url ) )
                        {
                            _logger.LogWarning( "Report for CorrelationId {Id} is completed but has no URL.", correlationId );
                            return StatusCode( 500, "Report data is inconsistent." );
                        }

                        // 1. Используем класс Uri для надежного парсинга URL
                        var reportUri = new Uri( state.Url );

                        // 2. Формируем префикс пути, который нужно удалить: "/имя_бакета/"
                        var pathPrefix = $"/{_cloudStorageService.GetBucketName()}/";

                        // 3. Проверяем, что путь в URL соответствует ожидаемому формату
                        if ( !reportUri.AbsolutePath.StartsWith( pathPrefix, StringComparison.OrdinalIgnoreCase ) )
                        {
                            throw new InvalidOperationException( $"Could not extract object key from URL. Path '{reportUri.AbsolutePath}' does not start with expected prefix '{pathPrefix}'." );
                        }

                        // 4. "Отрезаем" префикс, чтобы получить закодированный ключ
                        var encodedObjectKey = reportUri.AbsolutePath.Substring( pathPrefix.Length );

                        // 5. Декодируем ключ на случай, если в нем были спецсимволы (например, пробелы)
                        objectKey = Uri.UnescapeDataString( encodedObjectKey );

                        // --- КОНЕЦ ИЗМЕНЕНИЙ ---


                        _logger.LogInformation( "Attempting to download report for CorrelationId {Id} with extracted S3 key: '{Key}'", correlationId, objectKey );

                        var fileStream = await _cloudStorageService.DownloadFileAsStreamAsync( objectKey );

                        _logger.LogInformation( "Successfully downloaded stream for S3 key: '{Key}'", objectKey );

                        var userFileName = $"scene_report_{correlationId.Substring( 0, 8 )}.xlsx";

                        // ВАЖНО: Третьим параметром передаем имя файла для пользователя, а не URL
                        return File( fileStream, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", userFileName );
                    }
                    catch ( AmazonS3Exception ex ) // <-- Ловим КОНКРЕТНОЕ исключение S3
                    {
                        _logger.LogInformation( state.Url );
                        //_logger.LogError( ex,
                        //    "FAILED to download report. AWS Error Code: '{ErrorCode}', Status Code: {StatusCode}. CorrelationId: {Id}, Key: '{Key}'",
                        //    ex.ErrorCode,  // <-- 'AccessDenied', 'NoSuchKey', etc.
                        //    ex.StatusCode, // <-- HttpStatusCode.Forbidden, HttpStatusCode.NotFound, etc.
                        //    correlationId,
                        //    objectKey );

                        return StatusCode( 500, $"Failed to retrieve report. S3 Error: {ex.ErrorCode}" );
                    }
                    catch ( Exception ex )
                    {
                        _logger.LogError( ex, "Generic error while getting report for CorrelationId {Id}", correlationId );
                        return StatusCode( 500, "An unexpected error occurred." );
                    }

                case "Failed":
                    return StatusCode( 500, new { status = state.Status, error = state.ErrorMessage } );

                default:
                    return StatusCode( 500, "Unknown report status." );
            }
        }
    }
}
