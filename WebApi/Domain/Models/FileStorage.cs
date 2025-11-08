namespace Domain.Models;

public class FileStorage
{
    public string FileName { get; set; }
    public long FileSize { get; set; }
    public string StorageUrl { get; set; } // Добавлено: URL файла в облаке
    public DateTime UploadedAt { get; set; } = DateTime.UtcNow; // Добавлено: Время загрузки

    // Конструктор
    public FileStorage( string fileName, long fileSize, string storageUrl )
    {
        FileName = fileName;
        FileSize = fileSize;
        StorageUrl = storageUrl;
    }
}