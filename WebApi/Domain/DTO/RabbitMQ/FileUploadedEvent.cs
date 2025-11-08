namespace Domain.DTO.RabbitMQ
{
    public class FileUploadedEvent
    {
        public string FileName { get; set; }
        public long FileSize { get; set; }
        public string StorageUrl { get; set; }
        public DateTime UploadedAt { get; set; }
        public string CorrelationId { get; set; } // Опционально: для отслеживания
    }
}
