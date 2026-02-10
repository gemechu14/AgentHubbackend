# PowerShell script to migrate agents table

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Agents Table Migration Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check current Alembic status
Write-Host "Step 1: Checking current Alembic status..." -ForegroundColor Yellow
$currentRevision = alembic current 2>&1
Write-Host $currentRevision

# Step 2: Check if migration already exists
Write-Host ""
Write-Host "Step 2: Checking for existing agents migration..." -ForegroundColor Yellow
$versionsPath = "alembic\versions"
$skipCreation = $false
if (Test-Path $versionsPath) {
    $migrationFiles = Get-ChildItem -Path $versionsPath -Filter "*agents*" -ErrorAction SilentlyContinue
    if ($migrationFiles) {
        Write-Host "Found existing migration files:" -ForegroundColor Yellow
        $migrationFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
        Write-Host ""
        $response = Read-Host 'Migration already exists. Do you want to create a new one? (y/n)'
        if ($response -ne "y") {
            Write-Host "Skipping migration creation." -ForegroundColor Yellow
            $skipCreation = $true
        } else {
            $skipCreation = $false
        }
    } else {
        Write-Host "No existing agents migration found." -ForegroundColor Green
        $skipCreation = $false
    }
} else {
    Write-Host "Versions directory doesn't exist yet. Creating it..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $versionsPath -Force | Out-Null
    Write-Host "Versions directory created." -ForegroundColor Green
    $skipCreation = $false
}

# Step 3: Create migration if needed
if (!$skipCreation) {
    Write-Host ""
    Write-Host "Step 3: Creating migration for agents table..." -ForegroundColor Yellow
    Write-Host "Running: alembic revision --autogenerate -m 'add_agents_table'" -ForegroundColor Gray
    
    # Ensure versions directory exists before running alembic
    if (!(Test-Path $versionsPath)) {
        New-Item -ItemType Directory -Path $versionsPath -Force | Out-Null
    }
    
    $migrationResult = alembic revision --autogenerate -m "add_agents_table" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Migration created successfully!" -ForegroundColor Green
        Write-Host $migrationResult
    } else {
        Write-Host "[ERROR] Failed to create migration:" -ForegroundColor Red
        Write-Host $migrationResult
        Write-Host ""
        Write-Host "Please review the error above and try again." -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "IMPORTANT: Please review the generated migration file before proceeding!" -ForegroundColor Yellow
    Write-Host "Check that it includes:" -ForegroundColor Yellow
    Write-Host "  - Table name: 'agents'" -ForegroundColor Gray
    Write-Host "  - All columns from the Agent model" -ForegroundColor Gray
    Write-Host "  - Foreign keys to 'accounts' and 'users' tables" -ForegroundColor Gray
    Write-Host '  - Enum type for connection_type (POWERBI, DB)' -ForegroundColor Gray
    Write-Host "  - Indexes on 'account_id' and 'created_by'" -ForegroundColor Gray
    Write-Host ""
    $response = Read-Host 'Have you reviewed the migration file? Ready to apply? (y/n)'
    if ($response -ne "y") {
        Write-Host "Migration creation completed. Please review and run 'alembic upgrade head' when ready." -ForegroundColor Yellow
        exit 0
    }
}

# Step 4: Apply the migration
Write-Host ""
Write-Host "Step 4: Applying migration..." -ForegroundColor Yellow
Write-Host "Running: alembic upgrade head" -ForegroundColor Gray

$upgradeResult = alembic upgrade head 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Migration applied successfully!" -ForegroundColor Green
    Write-Host $upgradeResult
} else {
    Write-Host "[ERROR] Failed to apply migration:" -ForegroundColor Red
    Write-Host $upgradeResult
    Write-Host ""
    Write-Host "If you see an 'enum already exists' error, edit the migration file to use:" -ForegroundColor Yellow
    Write-Host '  op.execute("""' -ForegroundColor Gray
    Write-Host '    DO $$ BEGIN' -ForegroundColor Gray
    Write-Host "        CREATE TYPE connectiontype AS ENUM ('POWERBI', 'DB');" -ForegroundColor Gray
    Write-Host '    EXCEPTION' -ForegroundColor Gray
    Write-Host '        WHEN duplicate_object THEN null;' -ForegroundColor Gray
    Write-Host '    END $$;' -ForegroundColor Gray
    Write-Host '  """)' -ForegroundColor Gray
    Write-Host ""
    Write-Host "Then run this script again or manually run 'alembic upgrade head'" -ForegroundColor Yellow
    exit 1
}

# Step 5: Verify migration
Write-Host ""
Write-Host "Step 5: Verifying migration..." -ForegroundColor Yellow
$verifyResult = alembic current 2>&1
Write-Host "Current Alembic revision:" -ForegroundColor Gray
Write-Host $verifyResult

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Migration completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test API endpoints in Swagger: /gibberish-xyz-123" -ForegroundColor Gray
Write-Host "  2. Create a test agent via POST /agents/{account_id}" -ForegroundColor Gray
Write-Host "  3. Verify data is stored correctly" -ForegroundColor Gray
Write-Host ""
