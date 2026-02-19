# Quick validation script for Windows PowerShell
# Usage: .\scripts\quick_check.ps1

$ErrorActionPreference = "Stop"

Write-Host "🔍 Running quick validation checks..." -ForegroundColor Cyan
Write-Host ""

# Backend checks
Write-Host "📦 Backend: Checking Python lint..." -ForegroundColor Yellow
python -m ruff check --no-cache api services scripts tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend lint failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Backend lint passed" -ForegroundColor Green
Write-Host ""

# Frontend checks
Write-Host "📦 Frontend: Checking TypeScript types..." -ForegroundColor Yellow
Set-Location frontend
npm run typecheck
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend type check failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Frontend type check passed" -ForegroundColor Green
Write-Host ""

Write-Host "📦 Frontend: Checking ESLint..." -ForegroundColor Yellow
npm run lint
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend lint failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Frontend lint passed" -ForegroundColor Green
Write-Host ""

Set-Location ..

Write-Host "✨ All checks passed! Ready to commit." -ForegroundColor Green