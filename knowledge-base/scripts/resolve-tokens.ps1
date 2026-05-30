<#
.SYNOPSIS
    Resolves static configuration placeholder tokens across all .github/ agent and prompt files.

.DESCRIPTION
    Replaces {{TOKEN}} placeholders that represent project-specific static configuration
    (language, framework, database, deployment target, Jira, GitHub) with their resolved
    values for the FullStackPortfolio project.

    Runtime input tokens are intentionally left untouched - they are filled by the user
    at pipeline execution time. The following token categories are NOT replaced:
        - User input tokens:  {{BUG_DESCRIPTION}}, {{FEATURE_DESCRIPTION}}, {{EPIC_IDEA}},
                              {{ARCHITECTURE_CONCERNS}}, {{PRIOR_TICKET_KEY}}
        - Code template vars: {{EntityName}}, {{EventName}}, {{DtoName}}, {{ControllerName}},
                              {{ServiceName}}, {{QueryName}}, {{bounded_context}}
        - Example/doc labels: {{PLACEHOLDER_NAME}}, {{PLACEHOLDER}}, {{CONFIG_PLACEHOLDER}},
                              {{DESCRIPTIVE_NAME}}, {{ENV_VAR_NAME}}
        - Operational runbook: {{ESCALATION_CONTACT}}, {{BACKUP_COMMAND}}, {{ONCALL_ROLE}}, etc.
        - Prompt runtime args: {{artifactPath}}, {{phaseName}}, {{requiredFields}}, {{layer}}

.PARAMETER DryRun
    Reports what would be replaced without writing any files. Use this first to review
    changes before applying them.

.EXAMPLE
    # Preview all replacements without writing
    .\knowledge-base\scripts\resolve-tokens.ps1 -DryRun

    # Apply all replacements
    .\knowledge-base\scripts\resolve-tokens.ps1

.NOTES
    Run from the repository root. All paths are relative to the repo root.
    Script category: Maintenance
    Created: 2026-05-29
#>

[CmdletBinding()]
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Static Token Configuration
# To change a value: edit the $Tokens hashtable below, then re-run the script.
# DO NOT add runtime user-input tokens here.
# ---------------------------------------------------------------------------
$Tokens = [ordered]@{
    '{{DOMAIN_NAME}}'               = 'personal-portfolio'
    '{{TARGET_LANGUAGE}}'           = 'Python'
    '{{FRAMEWORK_NAME}}'            = 'Django'
    '{{FRAMEWORK_NAME_LOWER}}'      = 'django'
    '{{DATABASE_ENGINE}}'           = 'MySQL'
    '{{DEPLOYMENT_TARGET}}'         = 'Google App Engine'
    '{{JIRA_PROJECT_KEY}}'          = 'FSP'
    '{{JIRA_CLOUD_ID}}'             = '93a7d59f-0d17-4391-a277-a7218e22a692'
    '{{JIRA_SITE_URL}}'             = 'https://ai-minion.atlassian.net'
    '{{GITHUB_REPO}}'               = 'DedRozs/FullStackPortfolio'
    '{{GITHUB_BASE_BRANCH}}'        = 'main'
    '{{TARGET_LANGUAGE_EXTENSION}}' = 'py'
}

# ---------------------------------------------------------------------------
# Scan scope - all markdown files under .github/
# ---------------------------------------------------------------------------
$SearchRoot = Join-Path (Get-Location).Path '.github'

if (-not (Test-Path $SearchRoot)) {
    Write-Error "Search root not found: $SearchRoot. Run this script from the repository root."
    exit 1
}

Write-Host "Scanning: $SearchRoot" -ForegroundColor DarkGray
if ($DryRun) {
    Write-Host "[DRY RUN] No files will be modified.`n" -ForegroundColor Yellow
} else {
    Write-Host ''
}

$totalReplacements = 0
$filesModified = 0

$files = Get-ChildItem -Path $SearchRoot -Filter '*.md' -Recurse | Sort-Object FullName

foreach ($file in $files) {
    $original = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
    $content = $original
    $fileReplacements = 0
    $fileLog = [System.Collections.Generic.List[string]]::new()

    foreach ($entry in $Tokens.GetEnumerator()) {
        $escaped = [regex]::Escape($entry.Key)
        $matches = [regex]::Matches($content, $escaped)
        $count = $matches.Count
        if ($count -gt 0) {
            $content = $content.Replace($entry.Key, $entry.Value)
            $fileReplacements += $count
            $occurrences = if ($count -eq 1) { '1 occurrence' } else { "$count occurrences" }
            $fileLog.Add("  $($entry.Key) -> $($entry.Value)  ($occurrences)")
        }
    }

    if ($fileReplacements -gt 0) {
        $relativePath = $file.FullName.Replace((Get-Location).Path + '\', '')
        $label = if ($fileReplacements -eq 1) { '1 replacement' } else { "$fileReplacements replacements" }
        Write-Host "$relativePath  [$label]" -ForegroundColor White
        foreach ($line in $fileLog) {
            Write-Host $line -ForegroundColor Cyan
        }
        Write-Host ''

        if (-not $DryRun) {
            [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.Encoding]::UTF8)
        }

        $filesModified++
        $totalReplacements += $fileReplacements
    }
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
$filesLabel = if ($filesModified -eq 1) { '1 file' } else { "$filesModified files" }
$replacementsLabel = if ($totalReplacements -eq 1) { '1 replacement' } else { "$totalReplacements replacements" }

Write-Host "---"
if ($DryRun) {
    Write-Host "Dry run complete: $replacementsLabel across $filesLabel would be applied." -ForegroundColor Yellow
    Write-Host "Run without -DryRun to apply changes." -ForegroundColor Yellow
} else {
    Write-Host "Done: $replacementsLabel across $filesLabel." -ForegroundColor Green
}
