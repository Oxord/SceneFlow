namespace Domain.Models;

public class FileStorage
{
    public string FileName { get; set; }
    public long FileSize { get; set; }
    public byte[] FileContent { get; set; }

    public FileStorage(string fileName, long fileSize, byte[] fileContent)
    {
        FileName = fileName;
        FileSize = fileSize;
        FileContent = fileContent;
    }
}