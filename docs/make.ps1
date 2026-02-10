# PowerShell script for building Sphinx documentation

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

$SPHINXOPTS = ""
$SOURCEDIR = "."
$BUILDDIR = "_build"

# Check if sphinx-build is available
$sphinxBuild = Get-Command sphinx-build -ErrorAction SilentlyContinue
if (-not $sphinxBuild) {
    Write-Host ""
    Write-Host "The 'sphinx-build' command was not found. Make sure you have Sphinx" -ForegroundColor Red
    Write-Host "installed. Install it with: pip install -r requirements-docs.txt" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "If you don't have Sphinx installed, grab it from" -ForegroundColor Red
    Write-Host "https://sphinx-doc.org/" -ForegroundColor Yellow
    exit 1
}

if ($args.Count -eq 0) {
    sphinx-build -M help $SOURCEDIR $BUILDDIR $SPHINXOPTS
} else {
    $target = $args[0]
    sphinx-build -M $target $SOURCEDIR $BUILDDIR $SPHINXOPTS
}

