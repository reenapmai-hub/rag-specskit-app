# Check if port 5001 is in use (Windows PowerShell)
# Usage: .\scripts\check_port.ps1 -Port 5001
param(
    [int]$Port = 5001
)

try {
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($null -ne $conn) {
        Write-Output "Port $Port is in use by the following process(es):"
        $conn | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess | Format-Table -AutoSize
        exit 1
    } else {
        Write-Output "Port $Port appears available"
        exit 0
    }
} catch {
    # Fallback to netstat parsing if Get-NetTCPConnection not available
    $out = netstat -ano | Select-String ":$Port\s"
    if ($out) {
        Write-Output "Port $Port is in use (netstat shows entries):"
        $out
        exit 1
    } else {
        Write-Output "Port $Port appears available (netstat fallback)"
        exit 0
    }
}
