# Cross-platform build + package for Stream Live Translate.
# Windows PowerShell entry point. Builds the current host and packages
# release/<platform>/. For cross-compiling, run this on each target OS
# or use the GitHub Actions workflow at .github/workflows/release.yml.
[CmdletBinding()]
param(
    [string]$Target = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

if ($IsWindows -or $env:OS -match "Windows") {
    $defaultTarget = "x86_64-pc-windows-msvc"
} elseif ($IsMacOS) {
    if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") {
        $defaultTarget = "aarch64-apple-darwin"
    } else {
        $defaultTarget = "x86_64-apple-darwin"
    }
} else {
    $defaultTarget = "x86_64-unknown-linux-gnu"
}

if (-not $Target) { $Target = $defaultTarget }

Write-Host "==> Building for $Target"
rustup target add $Target 2>$null | Out-Null
cargo build --release --target $Target

switch -Regex ($Target) {
    "windows" {
        $outDir = "release/windows-x64"
        $ext = ".exe"
    }
    "apple-darwin" {
        if ($Target -like "*aarch64*") {
            $outDir = "release/macos-arm64"
        } else {
            $outDir = "release/macos-x64"
        }
        $ext = ""
    }
    "linux" {
        if ($Target -like "*aarch64*") {
            $outDir = "release/linux-arm64"
        } else {
            $outDir = "release/linux-x64"
        }
        $ext = ""
    }
    default {
        throw "Unknown target $Target"
    }
}

New-Item -ItemType Directory -Force -Path "$outDir/bin" | Out-Null
Copy-Item -Force "target/$Target/release/stream-live-translate$ext" "$outDir/bin/"
Copy-Item -Recurse -Force dist/overlay dist/admin $outDir/
Copy-Item -Force dist/launcher.bat $outDir/
if (Test-Path dist/launcher.sh) { Copy-Item -Force dist/launcher.sh $outDir/ }
Copy-Item -Force dist/README.txt $outDir/

$archive = "$outDir.zip"
if (Test-Path $archive) { Remove-Item $archive }
Compress-Archive -Path $outDir -DestinationPath $archive -Force
Write-Host "==> Built $(Resolve-Path $archive)"

Pop-Location
