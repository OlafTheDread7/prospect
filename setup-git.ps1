# =====================================================
# PROSPECT — initial git setup + push to GitHub
# =====================================================
# One-shot: clean any prior git state, init, commit, push.
# Run from PowerShell in the AI SaaS Model folder.
#
#   cd "C:\Users\jakec\Documents\Projects\Claude\AI SaaS Model"
#   .\setup-git.ps1
#
# The first push opens a browser window for GitHub auth.
# =====================================================

$ErrorActionPreference = "Stop"

$RepoUrl  = "https://github.com/OlafTheDread7/prospect.git"
$UserName = "Jake Chaney"
$UserMail = "jakechaney12783@gmail.com"

Write-Host "== Cleaning any prior .git state ==" -ForegroundColor Cyan
if (Test-Path ".git") {
    Remove-Item -Recurse -Force ".git"
}

Write-Host "== git init (main branch) ==" -ForegroundColor Cyan
git init -b main | Out-Null

git config user.name  $UserName
git config user.email $UserMail

Write-Host "== Staging files (honoring .gitignore) ==" -ForegroundColor Cyan
git add .

Write-Host "== First commit ==" -ForegroundColor Cyan
git commit -m "Initial commit: PROSPECT agent + frontend + docs"

Write-Host "== Adding GitHub remote ==" -ForegroundColor Cyan
git remote remove origin 2>$null
git remote add origin $RepoUrl

Write-Host "== Pushing to $RepoUrl ==" -ForegroundColor Cyan
Write-Host "If this is your first push from this machine, a browser window will open for GitHub auth." -ForegroundColor Yellow
git push -u origin main

Write-Host ""
Write-Host "Done. Visit $RepoUrl to see your code on GitHub." -ForegroundColor Green
