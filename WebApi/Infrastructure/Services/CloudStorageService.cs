using Amazon.S3;
using Amazon.S3.Model;
using Domain.Models;
using Domain.Services;
using Microsoft.Extensions.Options;

namespace Infrastructure.Services
{
    public class CloudStorageService : ICloudStorageService
    {
        private readonly IAmazonS3 _s3Client;
        private readonly CloudStorageSettings _settings;

        public CloudStorageService( IOptions<CloudStorageSettings> settings )
        {
            _settings = settings.Value;

            var config = new AmazonS3Config
            {
                ServiceURL = _settings.ServiceUrl,
                AuthenticationRegion = _settings.Region, // Для Yandex.Cloud обычно ru-central1
                ForcePathStyle = true // Важно для многих S3-совместимых хранилищ
            };

            _s3Client = new AmazonS3Client( _settings.AccessKey, _settings.SecretKey, config );
        }

        public async Task<string> UploadFileAsync( Stream fileStream, string fileName, string contentType )
        {
            var objectKey = $"{Guid.NewGuid().ToString()}_{fileName}";

            var request = new PutObjectRequest
            {
                BucketName = _settings.BucketName,
                Key = objectKey,
                InputStream = fileStream,
                ContentType = contentType,
                CannedACL = S3CannedACL.PublicRead // Если хотите, чтобы файл был публично доступен
            };

            await _s3Client.PutObjectAsync( request );
            // Возвращаем URL к загруженному файлу
            // Для S3-совместимых хранилищ обычно такой формат: ServiceURL/BucketName/Key
            return $"{_settings.ServiceUrl}/{_settings.BucketName}/{objectKey}";
        }
    }
}
