namespace Domain.Models
{
    public class ReportGenerationState
    {
        public string Status { get; set; }
        public string? ReportUrl { get; set; }
        public string? ErrorMessage { get; set; }
    }
}
