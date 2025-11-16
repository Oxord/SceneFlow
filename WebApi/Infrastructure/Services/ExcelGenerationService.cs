using System.Text.Json;
using Domain.Models;
using Domain.Services;
using NPOI.SS.UserModel;
using NPOI.XSSF.UserModel;


public class ExcelGenerationService : IExcelGenerationService
{
    private readonly ICloudStorageService _cloudStorageService;

    public ExcelGenerationService( ICloudStorageService cloudStorageService )
    {
        _cloudStorageService = cloudStorageService;
    }

    public byte[] CreateSceneReport( IEnumerable<Scene> scenes )
    {
        IWorkbook workbook = new XSSFWorkbook();
        ISheet worksheet = workbook.CreateSheet( "Сцены" );
        var headers = new List<string>
        {
            "Серия", "Сцена", "Режим", "Инт / нат", "Объект / Подобъект / Синопсис",
            "Время года / Примечание", "Персонажи", "Массовка", "Групповка", "Грим",
            "Костюм", "Реквизит", "Игровой транспорт", "Декорация", "Пиротехника",
            "Каскадер / Трюк", "Музыка", "Спецэффект", "Спец. оборудование"
        };

        IFont headerFont = workbook.CreateFont();
        headerFont.IsBold = true;
        ICellStyle headerStyle = workbook.CreateCellStyle();
        headerStyle.SetFont( headerFont );
        headerStyle.FillForegroundColor = IndexedColors.Grey25Percent.Index;
        headerStyle.FillPattern = FillPattern.SolidForeground;

        IRow headerRow = worksheet.CreateRow( 0 );
        for ( int i = 0; i < headers.Count; i++ )
        {
            ICell cell = headerRow.CreateCell( i );
            cell.SetCellValue( headers[ i ] );
            cell.CellStyle = headerStyle;
        }

        int currentRowIndex = 1;
        foreach ( var scene in scenes )
        {
            IRow dataRow = worksheet.CreateRow( currentRowIndex );
            var settingParts = scene.Metadata?.Setting?.Split( new[] { ' ', '.' }, StringSplitOptions.RemoveEmptyEntries ) ?? Array.Empty<string>();
            var locationType = settingParts.FirstOrDefault() ?? "";
            var mode = settingParts.LastOrDefault() ?? "";
            var seriesNumber = scene.Metadata?.SceneNumber?.Split( '-' ).FirstOrDefault() ?? "";

            dataRow.CreateCell( 0 ).SetCellValue( seriesNumber );
            dataRow.CreateCell( 1 ).SetCellValue( scene.Metadata?.SceneNumber );
            dataRow.CreateCell( 2 ).SetCellValue( mode );
            dataRow.CreateCell( 3 ).SetCellValue( locationType );
            dataRow.CreateCell( 4 ).SetCellValue( $"{scene.Metadata?.Setting} / {scene.Metadata?.KeyEventsSummary}" );
            dataRow.CreateCell( 5 ).SetCellValue( scene.Metadata?.LocationDetails );
            dataRow.CreateCell( 6 ).SetCellValue( scene.Metadata.CharactersPresent != null ? string.Join( ", ", scene.Metadata.CharactersPresent ) : "" );
            dataRow.CreateCell( 7 ).SetCellValue( FormatDynamicField( scene.ProductionData?.Extras ) );
            dataRow.CreateCell( 8 ).SetCellValue( "" ); // Групповка
            dataRow.CreateCell( 9 ).SetCellValue( FormatDynamicField( scene.ProductionData?.MakeupAndHair ) );
            //dataRow.CreateCell( 10 ).SetCellValue( scene.ProductionData?.Costume != null ? string.Join( ", ", scene.ProductionData.Costume ) : "" );
            dataRow.CreateCell( 11 ).SetCellValue( scene.ProductionData?.Props != null ? string.Join( ", ", scene.ProductionData.Props ) : "" );
            dataRow.CreateCell( 12 ).SetCellValue( "" ); // Игровой транспорт
            dataRow.CreateCell( 13 ).SetCellValue( "" ); // Декорация
            dataRow.CreateCell( 14 ).SetCellValue( "" ); // Пиротехника
            dataRow.CreateCell( 15 ).SetCellValue( FormatDynamicField( scene.ProductionData?.Stunts ) );
            dataRow.CreateCell( 16 ).SetCellValue( FormatDynamicField( scene.ProductionData?.Music ) );
            dataRow.CreateCell( 17 ).SetCellValue( FormatDynamicField( scene.ProductionData?.SpecialEffects ) );
            dataRow.CreateCell( 18 ).SetCellValue( "" ); // Спец. оборудование
            currentRowIndex++;
        }

        for ( int i = 0; i < headers.Count; i++ )
        {
            worksheet.AutoSizeColumn( i );
        }

        using ( var stream = new MemoryStream() )
        {
            workbook.Write( stream );
            return stream.ToArray();
        }
    }

    private string FormatDynamicField( object field )
    {
        if ( field == null ) return "";
        if ( field is JsonElement jsonElement )
        {
            if ( jsonElement.ValueKind == JsonValueKind.Array )
            {
                return string.Join( ", ", jsonElement.EnumerateArray().Select( e => e.ToString() ) );
            }
            return jsonElement.ToString();
        }
        return field.ToString();
    }
}