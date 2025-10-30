using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace TraderDashboard.Models;

public class BotStatus
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = "disconnected";

    [JsonPropertyName("balance")]
    public double Balance { get; set; }

    [JsonPropertyName("equity")]
    public double Equity { get; set; }

    [JsonPropertyName("profit")]
    public double Profit { get; set; }

    [JsonPropertyName("positions")]
    public List<Position> Positions { get; set; } = new();

    [JsonPropertyName("actions")]
    public List<string> Actions { get; set; } = new();

    [JsonPropertyName("logs")]
    public List<string> Logs { get; set; } = new();

    public string StatusDisplay => Status.ToUpper();
    
    public string BalanceDisplay => $"${Balance:F2}";
    
    public string EquityDisplay => $"${Equity:F2}";
    
    public string ProfitDisplay => Profit >= 0 ? $"+${Profit:F2}" : $"-${Math.Abs(Profit):F2}";
    
    public double ProfitPercentage => Balance > 0 ? (Profit / Balance) * 100 : 0;
    
    public string ProfitPercentageDisplay => $"{(ProfitPercentage >= 0 ? "+" : "")}{ProfitPercentage:F2}%";
}

