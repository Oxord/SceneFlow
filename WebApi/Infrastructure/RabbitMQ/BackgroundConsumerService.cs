using System.Text.Json; // Убедитесь, что этот using есть
using Amazon.S3;
using Domain.Models;
using Domain.Services;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Infrastructure.RabbitMQ
{
    public class BackgroundConsumerService : BackgroundService
    {
        private readonly ILogger<BackgroundConsumerService> _logger;
        private readonly IMessageQueueConsumer _consumer;
        private readonly ICloudStorageService _cloudStorageService;
        private readonly IExcelGenerationService _excelGenerationService;
        private readonly IReportStorageService _reportStorageService; // <-- ДОБАВЛЕНО

        public BackgroundConsumerService(
            IMessageQueueConsumer consumer,
            ILogger<BackgroundConsumerService> logger,
            ICloudStorageService cloudStorageService,
            IExcelGenerationService excelGenerationService,
            IReportStorageService reportStorageService ) // <-- ДОБАВЛЕНО
        {
            _consumer = consumer;
            _logger = logger;
            _cloudStorageService = cloudStorageService;
            _excelGenerationService = excelGenerationService;
            _reportStorageService = reportStorageService; // <-- ДОБАВЛЕНО
        }

        protected override async Task ExecuteAsync( CancellationToken stoppingToken )
        {
            // ... ваш код ExecuteAsync остается без изменений ...
            // Убедитесь, что вы обрабатываете тип сообщения ScenesProcessed,
            // который, как я предполагаю, содержит CorrelationId.
            // Если он называется по-другому, поправьте.
            // Пример:
            // public class ScenesProcessed {
            //     public string CorrelationId { get; set; }
            //     public string StorageUrl { get; set; }
            // }

            _logger.LogInformation( "Background Consumer Service is starting." );
            stoppingToken.Register( () => _logger.LogInformation( "Background Consumer Service is stopping." ) );
            try
            {
                var quorumQueueArgs = new Dictionary<string, object> { { "x-queue-type", "quorum" } };
                // Убедитесь, что тип сообщения ScenesProcessed содержит CorrelationId
                await _consumer.StartConsumingAsync<ScenesProcessed>(
                    queueName: "sf_scenes",
                    exchangeName: "ScenesProcessed",
                    routingKey: "sf_scenes",
                    onMessageReceived: HandleScenesProcessedEvent,
                    quorumQueueArgs
                );

                while ( !stoppingToken.IsCancellationRequested )
                {
                    await Task.Delay( 1000, stoppingToken );
                }
            }
            catch ( OperationCanceledException ) { /* ... */ }
            catch ( Exception ex ) { /* ... */ }
            _logger.LogInformation( "Background Consumer Service has stopped." );
        }

        private async Task HandleScenesProcessedEvent( ScenesProcessed message )
        {
            // Используем CorrelationId из сообщения для отслеживания и именования файла
            var correlationId = message.CorrelationId;
            if ( string.IsNullOrEmpty( correlationId ) )
            {
                _logger.LogError( "Received message without a CorrelationId. Cannot process." );
                return; // Выходим, если нет ID
            }

            _logger.LogInformation( "[{CorrelationId}] - Starting report generation.", correlationId );

            // 1. Устанавливаем статус "В обработке"
            _reportStorageService.SetState( correlationId, new ReportState { Status = "Processing" } );

            try
            {
                // 2. Получаем ключ исходного JSON-файла из URL
                // (Ваш код для парсинга URL здесь, он был корректным)
                var uri = new Uri( message.StorageUrl );
                string bucketPathPart = $"/{_cloudStorageService.GetBucketName()}/";
                if ( !uri.AbsolutePath.StartsWith( bucketPathPart, StringComparison.OrdinalIgnoreCase ) )
                {
                    throw new InvalidOperationException( $"URL path '{uri.AbsolutePath}' does not match expected bucket structure '{bucketPathPart}'." );
                }
                string encodedObjectKey = uri.AbsolutePath.Substring( bucketPathPart.Length );
                string sourceObjectKey = Uri.UnescapeDataString( encodedObjectKey ).Trim();

                // 3. Скачиваем и десериализуем JSON
                _logger.LogInformation( "[{CorrelationId}] - Downloading source JSON from key: {Key}", correlationId, sourceObjectKey );
                string jsonContent;
                await using ( Stream fileStream = await _cloudStorageService.DownloadFileAsStreamAsync( sourceObjectKey ) )
                {
                    using ( var reader = new StreamReader( fileStream ) )
                    {
                        jsonContent = await reader.ReadToEndAsync();
                    }
                }

                var scenes = JsonSerializer.Deserialize<List<Scene>>( jsonContent ); // Убедитесь, что модель Scene и ее дочерние классы соответствуют JSON
                if ( scenes == null || scenes.Count == 0 )
                {
                    throw new InvalidDataException( "Source JSON file is empty or could not be parsed into scenes." );
                }
                _logger.LogInformation( "[{CorrelationId}] - Successfully parsed {Count} scenes.", correlationId, scenes.Count );

                // 4. Генерируем Excel-отчет в виде массива байтов
                byte[] excelFileBytes = _excelGenerationService.CreateSceneReport( scenes );
                _logger.LogInformation( "[{CorrelationId}] - Excel report generated, size: {Size} bytes.", correlationId, excelFileBytes.Length );

                // --- ВОТ КЛЮЧЕВОЙ МОМЕНТ ---

                // 5. Формируем ключ (путь и имя) для нового файла отчета в S3
                var contentType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

                // 6. Загружаем байты отчета в облако (S3)
                string url;
                using ( var reportStream = new MemoryStream( excelFileBytes ) )
                {
                    url = await _cloudStorageService.UploadFileAsync( reportStream, correlationId, contentType );
                }
                _logger.LogInformation( url );
                _logger.LogInformation( "[{CorrelationId}] - Excel report successfully uploaded to S3 with key", correlationId );

                // 7. Устанавливаем финальный статус "Завершено"
                _reportStorageService.SetState( correlationId, new ReportState { Status = "Completed", Url = url } );
            }
            catch ( Exception ex )
            {
                _logger.LogError( ex, "[{CorrelationId}] - Failed to process report.", correlationId );

                // В случае любой ошибки устанавливаем статус "Ошибка"
                _reportStorageService.SetState( correlationId, new ReportState
                {
                    Status = "Failed",
                    ErrorMessage = ex.Message
                } );
            }
        }
    }
}