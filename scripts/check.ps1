$ErrorActionPreference = "Stop"

function Run-Step {
	param(
		[string]$Name,
		[scriptblock]$Command
	)

	Write-Host "Running $Name..." -ForegroundColor Cyan
	& $Command
	if ($LASTEXITCODE -ne 0) {
		Write-Error "$Name failed with exit code $LASTEXITCODE"
		exit $LASTEXITCODE
	}
}

Run-Step "Ruff" { python -m ruff check src tests }

Run-Step "MyPy" { python -m mypy src tests }

Run-Step "Pytest" { python -m pytest }

Write-Host "All checks passed." -ForegroundColor Green
