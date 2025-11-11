using System.Text.Json.Serialization;

namespace Domain.Models
{
    public class Scene
    {
        [JsonPropertyName( "id" )]
        public string Id { get; set; }

        [JsonPropertyName( "text" )]
        public string Text { get; set; }

        [JsonPropertyName( "metadata" )]
        public Metadata Metadata { get; set; }

        [JsonPropertyName( "production_data" )]
        public ProductionData ProductionData { get; set; }
    }

    public class Metadata
    {
        [JsonPropertyName( "scene_number" )]
        public string SceneNumber { get; set; }

        [JsonPropertyName( "setting" )]
        public string Setting { get; set; }

        [JsonPropertyName( "location_details" )]
        public string LocationDetails { get; set; }

        [JsonPropertyName( "characters_present" )]
        public List<string> CharactersPresent { get; set; }

        [JsonPropertyName( "key_events_summary" )]
        public string KeyEventsSummary { get; set; }

        [JsonPropertyName( "emotional_tone" )]
        public string EmotionalTone { get; set; }
    }

    public class ProductionData
    {
        [JsonPropertyName( "costume" )]
        public string Costume { get; set; }

        // Используем 'object', так как в данных это поле может быть как строкой, так и массивом []
        [JsonPropertyName( "makeup_and_hair" )]
        public object MakeupAndHair { get; set; }

        [JsonPropertyName( "props" )]
        public List<string> Props { get; set; }

        // Используем 'object', так как в данных это поле может быть как пустой строкой "", так и массивом []
        [JsonPropertyName( "extras" )]
        public object Extras { get; set; }

        // Используем 'object', так как в данных это поле может быть как пустой строкой "", так и массивом []
        [JsonPropertyName( "stunts" )]
        public object Stunts { get; set; }

        // Используем 'object', так как в данных это поле может быть как строкой, так и массивом строк
        [JsonPropertyName( "special_effects" )]
        public object SpecialEffects { get; set; }

        // Используем 'object', так как в данных это поле может быть как пустой строкой "", так и массивом []
        [JsonPropertyName( "music" )]
        public object Music { get; set; }
    }
}
