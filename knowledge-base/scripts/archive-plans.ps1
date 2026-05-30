<#
.SYNOPSIS
    Archives pipeline run artifacts from knowledge-base/plans/active/ into
    knowledge-base/plans/archive/.

.DESCRIPTION
    Supports two modes:

    Named-run mode (-RunId):
        Archives the single TICKET_KEY-scoped subdirectory
        active/<RunId>/ to archive/<RunId>/.
        Use this after a namespaced pipeline run completes successfully.

    Bulk mode (no -RunId):
        Iterates all immediate subdirectories inside active/ and archives
        each to archive/<subdirname>/. Loose files at the active/ root are
        legacy flat-mode artifacts and are NOT moved by this mode; the
        developer archives them manually.

    The -ProjectName parameter is retained for backward compatibility and
    labelling but is not used to derive the archive path in either mode.

.PARAMETER ProjectName
    Mandatory. Human-readable project name for log messages.
    Sanitized to lowercase, spaces replaced with hyphens, non-alphanumeric
    characters (except hyphens) stripped.

.PARAMETER RepoRoot
    Optional. Absolute path to the repository root. Defaults to two directories
    above the script's own location (i.e., the workspace root when the script
    lives at knowledge-base/scripts/).

.PARAMETER RunId
    Optional. A validated TICKET_KEY (e.g., PROJ-42) identifying the specific
    pipeline run subdirectory to archive. Must match [A-Z][A-Z0-9]+-[1-9][0-9]*.
    When supplied, only that subdirectory is archived. When omitted,
    all subdirectories in active/ are archived (bulk mode).

.EXAMPLE
    # Archive a specific named run:
    .\knowledge-base\scripts\archive-plans.ps1 -ProjectName "my-project" -RunId "PROJ-42"

.EXAMPLE
    # Bulk-archive all subdirectories in active/:
    .\knowledge-base\scripts\archive-plans.ps1 -ProjectName "my-project"

.EXAMPLE
    # Explicit repo root:
    .\knowledge-base\scripts\archive-plans.ps1 -ProjectName "My Project" -RepoRoot "C:\repos\my-repo" -RunId "TT-7"

.NOTES
    Exit codes:
        0 - Success (items archived, or nothing found to archive)
        1 - Invalid parameter (empty ProjectName or RunId fails pattern check)
        2 - active/ directory does not exist
        3 - Named-run subdirectory not found (RunId specified but directory missing)
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ProjectName,

    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,

    [Parameter(Mandatory = $false)]
    [string]$RunId = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Sanitize project name for log messages
$sanitizedName = $ProjectName.ToLowerInvariant()
$sanitizedName = $sanitizedName -replace '\s+', '-'
$sanitizedName = $sanitizedName -replace '[^a-z0-9\-]', ''

if ([string]::IsNullOrWhiteSpace($sanitizedName)) {
    Write-Error "ProjectName '$ProjectName' produced an empty string after sanitization. Use alphanumeric characters or spaces."
    exit 1
}

# Validate RunId pattern when supplied (OWASP A03 - path traversal mitigation)
if (-not [string]::IsNullOrWhiteSpace($RunId)) {
    if ($RunId -notmatch '^[A-Z][A-Z0-9]+-[1-9][0-9]*$') {
        Write-Error "RunId '$RunId' does not match the required pattern ^[A-Z][A-Z0-9]+-[1-9][0-9]*$. Aborting to prevent path traversal."
        exit 1
    }
}

# Build base paths
$activeDir   = Join-Path $RepoRoot 'knowledge-base\plans\active'
$archiveBase = Join-Path $RepoRoot 'knowledge-base\plans\archive'

# Verify active/ exists
if (-not (Test-Path $activeDir -PathType Container)) {
    Write-Error "Active plans directory not found: $activeDir"
    exit 2
}

# Ensure archive base exists
New-Item -ItemType Directory -Path $archiveBase -Force | Out-Null

# --- Named-run mode ---
if (-not [string]::IsNullOrWhiteSpace($RunId)) {
    $sourceDir  = Join-Path $activeDir $RunId
    $targetDir  = Join-Path $archiveBase $RunId

    if (-not (Test-Path $sourceDir -PathType Container)) {
        Write-Error "Named-run directory not found: $sourceDir"
        exit 3
    }

    Move-Item -Path $sourceDir -Destination $targetDir -Force
    Write-Host "Archived run '$RunId' to: $targetDir"
    exit 0
}

# --- Bulk mode ---
$subDirs = @(Get-ChildItem -Path $activeDir -Directory)

if ($subDirs.Count -eq 0) {
    Write-Host "No subdirectories found in '$activeDir'. Nothing to archive."
    exit 0
}

$archivedCount = 0
foreach ($dir in $subDirs) {
    $targetDir = Join-Path $archiveBase $dir.Name
    Move-Item -Path $dir.FullName -Destination $targetDir -Force
    $archivedCount++
    Write-Host "Archived subdirectory '$($dir.Name)' to: $targetDir"
}

Write-Host "Bulk archive complete: $archivedCount subdirector$(if ($archivedCount -eq 1) { 'y' } else { 'ies' }) archived for project '$sanitizedName'."
exit 0
