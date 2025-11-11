using System.Web;
using Amazon.S3;
using Domain.Models;
using Domain.Services;
using Infrastructure.Services;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;


namespace Infrastructure.RabbitMQ
{
    public class BackgroundConsumerService : BackgroundService
    {
        private readonly ILogger<BackgroundConsumerService> _logger;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IMessageQueueConsumer _consumer;
        private readonly ICloudStorageService _cloudStorageService;
        private readonly IExcelGenerationService _excelGenerationService;

        // Через DI получаем наш consumer и логгер
        public BackgroundConsumerService(
            IMessageQueueConsumer consumer,
            ILogger<BackgroundConsumerService> logger,
            ICloudStorageService cloudStorageService,
            IExcelGenerationService excelGenerationService )
        {
            _consumer = consumer;
            _logger = logger;
            _cloudStorageService = cloudStorageService;
            _excelGenerationService = excelGenerationService;
        }

        // Этот метод вызывается ОДИН РАЗ при старте приложения
        protected override async Task ExecuteAsync( CancellationToken stoppingToken )
        {
            _logger.LogInformation( "Background Consumer Service is starting." );

            stoppingToken.Register( () => _logger.LogInformation( "Background Consumer Service is stopping." ) );

            try
            {
                var quorumQueueArgs = new Dictionary<string, object> { { "x-queue-type", "quorum" } };

                await _consumer.StartConsumingAsync<ScenesProcessed>(
                    queueName: "sf_scenes",
                    exchangeName: "ScenesProcessed",
                    routingKey: "sf_scenes",
                    onMessageReceived: HandleScenesProcessedEvent,
                    quorumQueueArgs
                );
                _logger.LogInformation( "Consumer for 'orders-queue' has been started." );

                while ( !stoppingToken.IsCancellationRequested )
                {
                    await Task.Delay( 1000, stoppingToken );
                }
            }
            catch ( OperationCanceledException )
            {
                // Исключение при graceful shutdown, это нормально.
                _logger.LogInformation( "Background Consumer Service was cancelled." );
            }
            catch ( Exception ex )
            {
                _logger.LogError( ex, "An unhandled exception occurred in Background Consumer Service." );
            }

            _logger.LogInformation( "Background Consumer Service has stopped." );
        }

        // Обработчик для второго типа сообщений
        private async Task HandleScenesProcessedEvent( ScenesProcessed message )
        {
            // ЛОГ 1: Исходный URL
            _logger.LogInformation( "Received message with StorageUrl: '{Url}'", message.StorageUrl );

            if ( string.IsNullOrWhiteSpace( message.StorageUrl ) )
            {
                _logger.LogWarning( "StorageUrl is empty for file '{FileName}'. Skipping.", message.CorrelationId );
                return;
            }
            try
            {
                var uri = new Uri( message.StorageUrl );
                string encodedPath = uri.AbsolutePath;
                string bucketPathPart = $"/{_cloudStorageService.GetBucketName()}/";

                // ЛОГ 2: Путь из URL и ожидаемая часть бакета
                _logger.LogInformation( "Parsed AbsolutePath: '{Path}'. Expected bucket part: '{BucketPart}'", encodedPath, bucketPathPart );

                if ( !encodedPath.StartsWith( bucketPathPart, StringComparison.OrdinalIgnoreCase ) )
                {
                    _logger.LogError( "URL path '{Path}' does not match expected bucket structure '{BucketPath}'.", encodedPath, bucketPathPart );
                    return;
                }

                string encodedObjectKey = encodedPath.Substring( bucketPathPart.Length );


                string decodedObjectKey = Uri.UnescapeDataString( encodedObjectKey ); // Ваша строка
                _logger.LogInformation( "Decoded Object Key (before trim): '{Key}'", decodedObjectKey );
                _logger.LogInformation( "Extracted Encoded Object Key: '{Key}'", encodedObjectKey );


                string objectKey = decodedObjectKey.Trim();

                _logger.LogInformation( "Attempting to download with Bucket: '{B}' and Key: '{K}'", _cloudStorageService.GetBucketName(), objectKey );

                string jsonContent;
                await using ( Stream fileStream = await _cloudStorageService.DownloadFileAsStreamAsync( objectKey ) )
                {
                    using ( var reader = new StreamReader( fileStream ) )
                    {
                        jsonContent = await reader.ReadToEndAsync();
                    }
                }
                _logger.LogInformation( "Download successful. Content length: {Length} chars.", jsonContent.Length );

                // --- НАЧАЛО НОВОЙ ЛОГИКИ ---

                // 1. Десериализуем JSON в список наших объектов
                var scenes = System.Text.Json.JsonSerializer.Deserialize<List<Scene>>( jsonContent );
                if ( scenes == null || scenes.Count == 0 )
                {
                    _logger.LogWarning( "JSON file '{Key}' is empty or could not be parsed.", objectKey );
                    return;
                }
                _logger.LogInformation( "Successfully parsed {Count} scenes from JSON.", scenes.Count );

                // 2. Генерируем Excel-файл в виде массива байтов
                byte[] excelFileBytes = _excelGenerationService.CreateSceneReport( scenes );
                _logger.LogInformation( "Excel report generated. Size: {Size} bytes.", excelFileBytes.Length );

                // Формируем имя файла, чтобы избежать перезаписи
                string originalFileName = Path.GetFileNameWithoutExtension( objectKey );
                string excelFileName = $"{originalFileName}_{DateTime.UtcNow:yyyyMMddHHmmss}.xlsx";

                // Определяем путь для сохранения. 
                // В этом примере мы создадим папку 'GeneratedReports' в директории, где запущено приложение.
                // Вы можете указать любой другой путь, например "D:\\MyReports".
                string outputDirectory = Path.Combine( AppContext.BaseDirectory, "GeneratedReports" );

                // Убедимся, что папка существует
                Directory.CreateDirectory( outputDirectory );

                // Соединяем путь к папке и имя файла
                string fullPath = Path.Combine( outputDirectory, excelFileName );

                // Асинхронно записываем все байты в файл
                await File.WriteAllBytesAsync( fullPath, excelFileBytes );

                _logger.LogInformation( "Excel report successfully saved to local path: '{Path}'", fullPath );

            }
            catch ( AmazonS3Exception ex )
            {
                _logger.LogError( ex,
                    "S3 error while downloading file. " +
                    "StatusCode: {StatusCode}, ErrorCode: {ErrorCode}, Message: {S3Message}",
                    ex.StatusCode, ex.ErrorCode, ex.Message );
            }
            catch ( Exception ex )
            {
                _logger.LogError( ex, "An unexpected error occurred while processing file." );
            }
        }
    }
}
