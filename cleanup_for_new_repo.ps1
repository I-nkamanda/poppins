# Cleanup script for Pop-pins2
# Removes temporary files, caches, and logs to prepare for a clean git push.

Write-Host "Starting cleanup..."

# Define directories to remove
$dirsToRemove = @(
    "__pycache__",
    ".pytest_cache",
    "logs",
    "app/__pycache__",
    "frontend/node_modules",
    "frontend/dist",
    "frontend/.vite"
)

# Define file patterns to remove
$filesToRemove = @(
    "*.log",
    "*.tmp",
    ".DS_Store",
    "Thumbs.db"
)

# Remove directories
foreach ($dir in $dirsToRemove) {
    if (Test-Path $dir) {
        Write-Host "Removing directory: $dir"
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Remove files recursively
foreach ($pattern in $filesToRemove) {
    Get-ChildItem -Path . -Include $pattern -Recurse -File | ForEach-Object {
        Write-Host "Removing file: $($_.FullName)"
        Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Cleanup complete! You can now initialize a new git repository."
