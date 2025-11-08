namespace Domain.Models
{
    public class CloudStorageSettings
    {
        public string ServiceUrl { get; set; }
        public string AccessKey { get; set; }
        public string SecretKey { get; set; }
        public string BucketName { get; set; }
        public string Region { get; set; }
    }
}
