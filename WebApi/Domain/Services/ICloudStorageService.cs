namespace Domain.Services
{
    public interface ICloudStorageService
    {
        /// <summary>
        /// Загружает файл в облачное хранилище.
        /// </summary>
        /// <param name="fileStream">Поток с содержимым файла.</param>
        /// <param name="fileName">Имя файла (для сохранения в хранилище).</param>
        /// <param name="contentType">Тип контента (MIME-тип) файла.</param>
        /// <returns>URL загруженного файла.</returns>
        Task<string> UploadFileAsync( Stream fileStream, string fileName, string contentType );
    }
}
