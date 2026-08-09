# fetch_tutorial_assets.ps1
#
# Downloads the Robot Setup Tutorial 6-9 manipulator sample assets
# (UR10e + Robotiq 2F-140) from the NVIDIA Isaac asset server into
# D:\ic\assets\vendor\Manipulator .
#
# Why this exists: the pip install of isaacsim ships code only. Sample
# assets live on a public S3 bucket and the Content browser cannot reach
# them without a Nucleus connection. This grabs them over plain HTTPS.
#
# NOTE (PowerShell 5.1): comments are ASCII on purpose. PS 5.1 reads .ps1
# as ANSI unless the file has a BOM, which mangles non-ASCII text and
# breaks parsing. Korean docs live in docs/ instead.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\fetch_tutorial_assets.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\fetch_tutorial_assets.ps1 -Force
#   powershell -ExecutionPolicy Bypass -File scripts\fetch_tutorial_assets.ps1 -Dest E:\ic\assets\vendor\Manipulator

[CmdletBinding()]
param(
    [string]$Dest = 'D:\ic\assets\vendor\Manipulator',
    # Overwrite files that already exist. Off by default so in-progress
    # tutorial edits saved into these files are never clobbered.
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

$Bucket = 'https://omniverse-content-production.s3-us-west-2.amazonaws.com'
$Prefix = 'Assets/Isaac/5.1/Isaac/Samples/Rigging/Manipulator/'

function Get-S3Keys {
    param([string]$KeyPrefix)
    $token = $null
    $items = @()
    do {
        $url = "$Bucket/?list-type=2&prefix=$([uri]::EscapeDataString($KeyPrefix))"
        if ($token) { $url += "&continuation-token=$([uri]::EscapeDataString($token))" }
        $resp   = Invoke-RestMethod -Uri $url -TimeoutSec 60
        $items += $resp.ListBucketResult.Contents
        $token  = $resp.ListBucketResult.NextContinuationToken
    } while ($token)
    return $items
}

Write-Host "Listing asset server ..."
$keys = Get-S3Keys $Prefix | Where-Object { $_.Key -notlike '*/.thumbs/*' -and [int]$_.Size -gt 0 }
$totalMB = ($keys | Measure-Object -Property Size -Sum).Sum / 1MB
Write-Host ("Found {0} files / {1:N1} MB" -f $keys.Count, $totalMB)
Write-Host ("Destination: {0}" -f $Dest)
Write-Host ""

$got = 0; $skipped = 0
foreach ($k in $keys) {
    $rel    = $k.Key.Substring($Prefix.Length) -replace '/', '\'
    $target = Join-Path $Dest $rel

    if ((Test-Path $target) -and -not $Force) { $skipped++; continue }

    $dir = Split-Path $target -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
    Invoke-WebRequest -Uri "$Bucket/$($k.Key)" -OutFile $target -UseBasicParsing -TimeoutSec 180
    $got++
}

Write-Host ("Downloaded {0}, skipped {1} (already present)" -f $got, $skipped)
if ($skipped -gt 0 -and -not $Force) {
    Write-Host "Re-run with -Force to overwrite. WARNING: that discards edits saved into these files."
}
Write-Host ""
Write-Host "Entry points:"
Write-Host ("  UR10e   : {0}" -f (Join-Path $Dest 'import_manipulator\ur10e\ur\ur.usd'))
Write-Host ("  Gripper : {0}" -f (Join-Path $Dest 'import_manipulator\robotiq_2f_140\robotiq_2f_140.usd'))
Write-Host ("  Answer  : {0}" -f (Join-Path $Dest 'import_manipulator\ur10e\ur\ur_gripper.usd'))
