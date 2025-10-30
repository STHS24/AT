using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Media;
using Avalonia.Threading;
using LiveChartsCore;
using LiveChartsCore.SkiaSharpView;
using LiveChartsCore.SkiaSharpView.Painting;
using SkiaSharp;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using TraderDashboard.Models;
using TraderDashboard.Services;

namespace TraderDashboard;

public partial class MainWindow : Window
{
    private readonly WebSocketClient _webSocketClient;
    private readonly ObservableCollection<Position> _positions = new();
    private readonly ObservableCollection<string> _logs = new();
    private readonly ObservableCollection<double> _equityValues = new();
    private readonly int _maxLogEntries = 100;
    private readonly int _maxEquityPoints = 100;
    private bool _isDarkMode = false;

    public MainWindow()
    {
        InitializeComponent();
        
        // Initialize WebSocket client
        _webSocketClient = new WebSocketClient("ws://localhost:5000");
        _webSocketClient.MessageReceived += OnMessageReceived;
        _webSocketClient.ConnectionStatusChanged += OnConnectionStatusChanged;
        _webSocketClient.ErrorOccurred += OnErrorOccurred;

        // Set up data bindings
        PositionsTable.ItemsSource = _positions;
        LogsPanel.ItemsSource = _logs;

        // Initialize equity chart
        InitializeEquityChart();

        // Start WebSocket connection
        _ = _webSocketClient.StartAsync();

        // Handle window closing
        Closing += async (s, e) =>
        {
            await _webSocketClient.StopAsync();
        };
    }

    private void InitializeEquityChart()
    {
        var series = new LineSeries<double>
        {
            Values = _equityValues,
            Fill = null,
            GeometrySize = 0,
            LineSmoothness = 0.5,
            Stroke = new SolidColorPaint(SKColors.DodgerBlue) { StrokeThickness = 2 }
        };

        EquityChart.Series = new ISeries[] { series };
        EquityChart.XAxes = new[]
        {
            new Axis
            {
                IsVisible = false
            }
        };
        EquityChart.YAxes = new[]
        {
            new Axis
            {
                Name = "Equity ($)",
                NamePaint = new SolidColorPaint(SKColors.Gray),
                LabelsPaint = new SolidColorPaint(SKColors.Gray)
            }
        };
    }

    private void OnMessageReceived(object? sender, BotStatus status)
    {
        Dispatcher.UIThread.InvokeAsync(() =>
        {
            UpdateStatus(status);
            UpdatePositions(status);
            UpdateEquityChart(status);
            UpdateLogs(status);
        });
    }

    private void UpdateStatus(BotStatus status)
    {
        // Update status indicator
        StatusText.Text = status.StatusDisplay;
        
        var statusColor = status.Status.ToLower() switch
        {
            "running" => Brushes.LimeGreen,
            "paused" => Brushes.Orange,
            "error" => Brushes.Red,
            _ => Brushes.Gray
        };
        StatusIndicator.Fill = statusColor;

        // Update financial metrics
        BalanceText.Text = status.BalanceDisplay;
        EquityText.Text = status.EquityDisplay;
        ProfitText.Text = status.ProfitDisplay;
        ProfitPercentageText.Text = $"({status.ProfitPercentageDisplay})";

        // Color profit based on value
        var profitColor = status.Profit >= 0 ? Brushes.Green : Brushes.Red;
        ProfitText.Foreground = profitColor;
        ProfitPercentageText.Foreground = profitColor;
    }

    private void UpdatePositions(BotStatus status)
    {
        _positions.Clear();
        
        if (status.Positions.Any())
        {
            foreach (var position in status.Positions)
            {
                _positions.Add(position);
            }
            NoPositionsText.IsVisible = false;
        }
        else
        {
            NoPositionsText.IsVisible = true;
        }
    }

    private void UpdateEquityChart(BotStatus status)
    {
        _equityValues.Add(status.Equity);

        // Keep only the last N points
        while (_equityValues.Count > _maxEquityPoints)
        {
            _equityValues.RemoveAt(0);
        }
    }

    private void UpdateLogs(BotStatus status)
    {
        // Add new logs
        foreach (var log in status.Logs)
        {
            if (!_logs.Contains(log))
            {
                _logs.Insert(0, $"[{DateTime.Now:HH:mm:ss}] {log}");
            }
        }

        // Add actions as logs
        foreach (var action in status.Actions)
        {
            var logEntry = $"[{DateTime.Now:HH:mm:ss}] 🎯 {action}";
            if (!_logs.Contains(logEntry))
            {
                _logs.Insert(0, logEntry);
            }
        }

        // Keep only the last N entries
        while (_logs.Count > _maxLogEntries)
        {
            _logs.RemoveAt(_logs.Count - 1);
        }

        // Auto-scroll to top (newest entries)
        LogScrollViewer.ScrollToHome();
    }

    private void OnConnectionStatusChanged(object? sender, string status)
    {
        Dispatcher.UIThread.InvokeAsync(() =>
        {
            var logEntry = $"[{DateTime.Now:HH:mm:ss}] 🔌 Connection: {status}";
            _logs.Insert(0, logEntry);
            
            if (_logs.Count > _maxLogEntries)
            {
                _logs.RemoveAt(_logs.Count - 1);
            }
        });
    }

    private void OnErrorOccurred(object? sender, string error)
    {
        Dispatcher.UIThread.InvokeAsync(() =>
        {
            var logEntry = $"[{DateTime.Now:HH:mm:ss}] ⚠️ Error: {error}";
            _logs.Insert(0, logEntry);
            
            if (_logs.Count > _maxLogEntries)
            {
                _logs.RemoveAt(_logs.Count - 1);
            }
        });
    }

    private async void OnStartClick(object? sender, RoutedEventArgs e)
    {
        await _webSocketClient.SendCommandAsync("resume");
        _logs.Insert(0, $"[{DateTime.Now:HH:mm:ss}] ▶️ Sent START command");
    }

    private async void OnPauseClick(object? sender, RoutedEventArgs e)
    {
        await _webSocketClient.SendCommandAsync("pause");
        _logs.Insert(0, $"[{DateTime.Now:HH:mm:ss}] ⏸️ Sent PAUSE command");
    }

    private async void OnStopClick(object? sender, RoutedEventArgs e)
    {
        await _webSocketClient.SendCommandAsync("stop");
        _logs.Insert(0, $"[{DateTime.Now:HH:mm:ss}] ⏹️ Sent STOP command");
    }

    private void OnThemeToggleClick(object? sender, RoutedEventArgs e)
    {
        _isDarkMode = !_isDarkMode;
        
        if (_isDarkMode)
        {
            Application.Current!.RequestedThemeVariant = Avalonia.Styling.ThemeVariant.Dark;
            ThemeToggle.Content = "☀️ LIGHT MODE";
        }
        else
        {
            Application.Current!.RequestedThemeVariant = Avalonia.Styling.ThemeVariant.Light;
            ThemeToggle.Content = "🌙 DARK MODE";
        }
    }
}

