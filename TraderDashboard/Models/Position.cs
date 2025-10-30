using System;
using System.Text.Json.Serialization;

namespace TraderDashboard.Models;

public class Position
{
    [JsonPropertyName("symbol")]
    public string Symbol { get; set; } = string.Empty;

    [JsonPropertyName("side")]
    public string Side { get; set; } = string.Empty;

    [JsonPropertyName("profit")]
    public double Profit { get; set; }

    public string SideDisplay => Side.ToUpper();
    
    public string ProfitDisplay => Profit >= 0 ? $"+${Profit:F2}" : $"-${Math.Abs(Profit):F2}";
}

