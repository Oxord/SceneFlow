using System.Text.Json;
using ClosedXML.Excel;
using Domain.Models;
using Domain.Services;

namespace Infrastructure.Services
{
    public class ExcelGenerationService : IExcelGenerationService
    {
        public byte[] CreateSceneReport( IEnumerable<Scene> scenes )
        {
            using ( var workbook = new XLWorkbook() )
            {
                var worksheet = workbook.Worksheets.Add( "Сцены" );
                var headers = new List<string>
            {
                "Серия", "Сцена", "Режим", "Инт / нат", "Объект / Подобъект / Синопсис",
                "Время года / Примечание", "Персонажи", "Массовка", "Групповка", "Грим",
                "Костюм", "Реквизит", "Игровой транспорт", "Декорация", "Пиротехника",
                "Каскадер / Трюк", "Музыка", "Спецэффект", "Спец. оборудование"
            };

                for ( int i = 0; i < headers.Count; i++ )
                {
                    worksheet.Cell( 1, i + 1 ).Value = headers[ i ];
                }

                var headerRange = worksheet.Range( 1, 1, 1, headers.Count );
                headerRange.Style.Font.Bold = true;
                headerRange.Style.Fill.BackgroundColor = XLColor.LightGray;

                int currentRow = 2;
                foreach ( var scene in scenes )
                {
                    // Разбор строки "setting" для получения Режима и Инт/Нат
                    var settingParts = scene.Metadata?.Setting?.Split( new[] { ' ', '.' }, StringSplitOptions.RemoveEmptyEntries ) ?? new string[ 0 ];
                    var locationType = settingParts.FirstOrDefault() ?? ""; // ИНТ или НАТ
                    var mode = settingParts.LastOrDefault() ?? ""; // НОЧЬ или ДЕНЬ

                    // Разбор номера сцены для получения номера серии
                    var seriesNumber = scene.Metadata?.SceneNumber?.Split( '-' ).FirstOrDefault() ?? "";

                    // Заполняем ячейки, обращаясь к правильным вложенным свойствам
                    worksheet.Cell( currentRow, 1 ).Value = seriesNumber;
                    worksheet.Cell( currentRow, 2 ).Value = scene.Metadata?.SceneNumber;
                    worksheet.Cell( currentRow, 3 ).Value = mode;
                    worksheet.Cell( currentRow, 4 ).Value = locationType;
                    worksheet.Cell( currentRow, 5 ).Value = $"{scene.Metadata?.Setting} / {scene.Metadata?.KeyEventsSummary}";
                    worksheet.Cell( currentRow, 6 ).Value = scene.Metadata?.LocationDetails;
                    worksheet.Cell( currentRow, 7 ).Value = scene.Metadata.CharactersPresent != null ? string.Join( ", ", scene.Metadata.CharactersPresent ) : "";
                    worksheet.Cell( currentRow, 8 ).Value = FormatDynamicField( scene.ProductionData?.Extras );
                    worksheet.Cell( currentRow, 9 ).Value = ""; // Групповка - нет данных в JSON
                    worksheet.Cell( currentRow, 10 ).Value = FormatDynamicField( scene.ProductionData?.MakeupAndHair );
                    worksheet.Cell( currentRow, 11 ).Value = scene.ProductionData?.Costume;
                    worksheet.Cell( currentRow, 12 ).Value = scene.ProductionData?.Props != null ? string.Join( ", ", scene.ProductionData.Props ) : "";
                    worksheet.Cell( currentRow, 13 ).Value = ""; // Игровой транспорт - нет данных
                    worksheet.Cell( currentRow, 14 ).Value = ""; // Декорация - нет данных
                    worksheet.Cell( currentRow, 15 ).Value = ""; // Пиротехника - нет данных
                    worksheet.Cell( currentRow, 16 ).Value = FormatDynamicField( scene.ProductionData?.Stunts );
                    worksheet.Cell( currentRow, 17 ).Value = FormatDynamicField( scene.ProductionData?.Music );
                    worksheet.Cell( currentRow, 18 ).Value = FormatDynamicField( scene.ProductionData?.SpecialEffects );
                    worksheet.Cell( currentRow, 19 ).Value = ""; // Спец. оборудование - нет данных

                    currentRow++;
                }

                worksheet.Columns().AdjustToContents();

                using ( var stream = new MemoryStream() )
                {
                    workbook.SaveAs( stream );
                    return stream.ToArray();
                }
            }
        }

        /// <summary>
        /// Вспомогательный метод для форматирования полей, которые могут быть
        /// строкой или массивом строк (десериализованным как JsonElement).
        /// </summary>
        private string FormatDynamicField( object field )
        {
            if ( field == null ) return "";

            if ( field is JsonElement jsonElement )
            {
                if ( jsonElement.ValueKind == JsonValueKind.Array )
                {
                    // Если это массив, объединяем его элементы в строку
                    return string.Join( ", ", jsonElement.EnumerateArray().Select( e => e.ToString() ) );
                }
                // Если это не массив (например, строка), просто возвращаем его значение
                return jsonElement.ToString();
            }

            // На случай, если тип уже является строкой
            return field.ToString();
        }
    }
}
