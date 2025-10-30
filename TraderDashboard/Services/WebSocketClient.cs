using System;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using TraderDashboard.Models;

namespace TraderDashboard.Services;

public class WebSocketClient : IDisposable
{
    private readonly string _uri;
    private ClientWebSocket? _webSocket;
    private CancellationTokenSource? _cancellationTokenSource;
    private bool _isRunning;
    private readonly int _reconnectDelayMs = 5000;

    public event EventHandler<BotStatus>? MessageReceived;
    public event EventHandler<string>? ConnectionStatusChanged;
    public event EventHandler<string>? ErrorOccurred;

    public bool IsConnected => _webSocket?.State == WebSocketState.Open;

    public WebSocketClient(string uri = "ws://localhost:5000")
    {
        _uri = uri;
    }

    public async Task StartAsync()
    {
        if (_isRunning)
            return;

        _isRunning = true;
        _cancellationTokenSource = new CancellationTokenSource();

        _ = Task.Run(async () => await ConnectLoopAsync(_cancellationTokenSource.Token));
    }

    private async Task ConnectLoopAsync(CancellationToken cancellationToken)
    {
        while (_isRunning && !cancellationToken.IsCancellationRequested)
        {
            try
            {
                ConnectionStatusChanged?.Invoke(this, "Connecting...");
                
                _webSocket = new ClientWebSocket();
                await _webSocket.ConnectAsync(new Uri(_uri), cancellationToken);
                
                ConnectionStatusChanged?.Invoke(this, "Connected");
                
                await ReceiveLoopAsync(cancellationToken);
            }
            catch (Exception ex)
            {
                ErrorOccurred?.Invoke(this, $"Connection error: {ex.Message}");
                ConnectionStatusChanged?.Invoke(this, "Disconnected");
            }

            if (_isRunning && !cancellationToken.IsCancellationRequested)
            {
                ConnectionStatusChanged?.Invoke(this, $"Reconnecting in {_reconnectDelayMs / 1000}s...");
                await Task.Delay(_reconnectDelayMs, cancellationToken);
            }
        }
    }

    private async Task ReceiveLoopAsync(CancellationToken cancellationToken)
    {
        var buffer = new byte[1024 * 4];
        var messageBuilder = new StringBuilder();

        while (_webSocket?.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
        {
            try
            {
                var result = await _webSocket.ReceiveAsync(
                    new ArraySegment<byte>(buffer), 
                    cancellationToken);

                if (result.MessageType == WebSocketMessageType.Close)
                {
                    await _webSocket.CloseAsync(
                        WebSocketCloseStatus.NormalClosure, 
                        "Closing", 
                        cancellationToken);
                    break;
                }

                var messageChunk = Encoding.UTF8.GetString(buffer, 0, result.Count);
                messageBuilder.Append(messageChunk);

                if (result.EndOfMessage)
                {
                    var message = messageBuilder.ToString();
                    messageBuilder.Clear();

                    try
                    {
                        var botStatus = JsonSerializer.Deserialize<BotStatus>(message);
                        if (botStatus != null)
                        {
                            MessageReceived?.Invoke(this, botStatus);
                        }
                    }
                    catch (JsonException ex)
                    {
                        ErrorOccurred?.Invoke(this, $"JSON parse error: {ex.Message}");
                    }
                }
            }
            catch (WebSocketException)
            {
                break;
            }
            catch (Exception ex)
            {
                ErrorOccurred?.Invoke(this, $"Receive error: {ex.Message}");
            }
        }
    }

    public async Task SendCommandAsync(string command)
    {
        if (_webSocket?.State != WebSocketState.Open)
        {
            ErrorOccurred?.Invoke(this, "Cannot send command: not connected");
            return;
        }

        try
        {
            var json = JsonSerializer.Serialize(new { command });
            var bytes = Encoding.UTF8.GetBytes(json);
            await _webSocket.SendAsync(
                new ArraySegment<byte>(bytes), 
                WebSocketMessageType.Text, 
                true, 
                CancellationToken.None);
        }
        catch (Exception ex)
        {
            ErrorOccurred?.Invoke(this, $"Send error: {ex.Message}");
        }
    }

    public async Task StopAsync()
    {
        _isRunning = false;
        _cancellationTokenSource?.Cancel();

        if (_webSocket?.State == WebSocketState.Open)
        {
            try
            {
                await _webSocket.CloseAsync(
                    WebSocketCloseStatus.NormalClosure, 
                    "Client closing", 
                    CancellationToken.None);
            }
            catch
            {
                // Ignore errors during shutdown
            }
        }

        _webSocket?.Dispose();
        _cancellationTokenSource?.Dispose();
    }

    public void Dispose()
    {
        StopAsync().GetAwaiter().GetResult();
    }
}

