#Requires -Version 5.1
<#
Prepare official Forge 2.0.15 and seven SHA-pinned Commander decks locally,
then preflight or run genuine four-player Commander AI games.
Requires authenticated gh CLI, Python 3.10+, JDK21, tar.exe and HTTPS.
Does not fabricate wins or overwrite modified decks.
#>
[CmdletBinding()]
param(
  [ValidateSet("both","aristo","artifact")][string]$Pod="both",
  [ValidateSet("v17_strict","v19_removal","v20_shadow",
               "critical_counter","v23_cooldown","v24_trigger_prune",
               "v30_exact_rules","v30_shadow_verify")][string]$Policy="v17_strict",
  [ValidateSet("Default","Experimental","Cautious","Reckless")][string]$AiProfile="Default",
  [ValidateRange(1,5)][int]$GamesPerRotation=1,
  [ValidateRange(1,4)][int]$Parallel=2,
  [ValidateSet(360,420,480)][int]$Clock=420,
  [int]$SeedBase=20261027,
  [switch]$Paired,
  [ValidateSet("v17_strict","v19_removal","v20_shadow",
               "critical_counter","v23_cooldown","v24_trigger_prune",
               "v30_exact_rules","v30_shadow_verify")][string]$ReferencePolicy="v17_strict",
  [switch]$PreflightOnly,
  [switch]$CompileOnly,
  [switch]$Jfr,
  [switch]$SkipForgeDownload,
  [string]$ForgeArchive="",
  [string]$ForgeRuntimeDir=""
)

$ErrorActionPreference="Stop"
$repoRoot=(Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot
foreach ($cmd in @("gh","python","java","javac","jar","tar")) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    throw "Missing executable $cmd on PATH. Install prerequisites first."
  }
}
$javaText=(cmd /c "java -version 2>&1" | Out-String)
if ($javaText -notmatch 'version "21(\.|"|\+)') {
  throw "JDK 21 required. Actual java -version: $javaText"
}
if ($Clock -eq 480 -and $GamesPerRotation -gt 3) {
  throw "480s clock is limited to <=3 games per rotation"
}
& gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
  throw "Private repo GitHub CLI authentication required: run gh auth login manually."
}

$archiveUrl="https://github.com/Card-Forge/forge/releases/download/forge-2.0.15/forge-installer-2.0.15.tar.bz2"
$expectedForgeSha="4468f182b60f6ca62d89697baa208981085af744f116781af751c611826db600"
$runtime=if($ForgeRuntimeDir){$ForgeRuntimeDir}else{Join-Path $repoRoot ".forge-v2.0.15"}
$archive=if($ForgeArchive){$ForgeArchive}else{Join-Path $repoRoot "forge-installer-2.0.15.tar.bz2"}
if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
  if ($SkipForgeDownload) {throw "Missing original Forge archive $archive"}
  Write-Host "Downloading original Forge 2.0.15 archive..."
  Invoke-WebRequest -Uri $archiveUrl -OutFile $archive
}
$foundSha=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($foundSha -ne $expectedForgeSha) {
  throw "Forge installer SHA256 mismatch: $foundSha"
}
Write-Host "FORGE_OFFICIAL_ARCHIVE_SHA256_OK $foundSha"
$jarFile=Get-ChildItem -LiteralPath $runtime -Recurse -File -Filter "forge-gui-desktop-*-jar-with-dependencies.jar" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $jarFile) {
  New-Item -ItemType Directory -Force -Path $runtime | Out-Null
  & tar -xjf $archive -C $runtime
  if ($LASTEXITCODE -ne 0) {throw "Forge original installer extraction failed"}
  $jarFile=Get-ChildItem -LiteralPath $runtime -Recurse -File -Filter "forge-gui-desktop-*-jar-with-dependencies.jar" | Select-Object -First 1
}
if (-not $jarFile) {throw "No Forge desktop fat JAR found in $runtime"}
if ($CompileOnly) {
  Write-Host "Compiling Forge 2.0.15 V24 from pinned sources, verifying JAR bytecode and 16 Java assertions..."
  & python scripts/verify_v24_real_jar_compile.py --jar $jarFile.FullName
  if ($LASTEXITCODE -ne 0) {throw "Forge V24 Java compilation or invariants FAILED"}
  return
}

$artifactPath=Join-Path $repoRoot "canonical"
$sourceDecks=Join-Path $artifactPath "forge_normalized"
$reportPath=Join-Path $artifactPath "results/forge_normalization/report.json"
if (-not (Test-Path $reportPath) -or -not (Test-Path $sourceDecks)) {
  New-Item -ItemType Directory -Force -Path $artifactPath | Out-Null
  Write-Host "Retrieving SHA-pinned original seven Commander decks..."
  & gh run download 37966009166 --repo Toko177/brimaz-forge-lab --name forge-seven-decks-canonical-verified --dir $artifactPath
  if ($LASTEXITCODE -ne 0) {throw "Canonical deck artifact unavailable; check gh auth and artifact retention"}
}
if (-not (Test-Path $reportPath)) {throw "Canonical normalization report missing"}
$report=Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
if (@($report.errors).Count -gt 0 -or @($report.decks).Count -ne 7) {
  throw "Canonical report contains errors or not seven decks"
}
$decksDir=Join-Path $repoRoot "forge_decks"
New-Item -ItemType Directory -Force -Path $decksDir | Out-Null
foreach($deck in @($report.decks)) {
  $name=[string]$deck.deck
  if ($name -notmatch '^(Brimaz_V3|Kaal_[0-9]+)$') {
    throw "Unexpected deck name in original normalization: $name"
  }
  $src=Join-Path $sourceDecks "$name.dck"
  $dst=Join-Path $decksDir "$name.dck"
  if (-not (Test-Path $src)) {throw "Missing deck: $src"}
  $expected=([string]$deck.normalized_sha256).ToLowerInvariant()
  $actual=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne $expected) {throw "Original GitHub deck SHA256 mismatch: $name"}
  if (Test-Path $dst) {
    $previous=(Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($previous -ne $expected) {throw "Refuse to overwrite modified deck $dst"}
  } else {
    Copy-Item -LiteralPath $src -Destination $dst
  }
}
Write-Host "ALL_SEVEN_COMMANDER_DECKS_SHA256_VERIFIED"

$entrypoint=if($Paired){"scripts/run_paired_four_ai.py"}else{"scripts/run_local_four_ai.py"}
$params=@($entrypoint,"--jar",$jarFile.FullName,
          "--pod",$Pod,"--policy",$Policy,"--profile",$AiProfile,
          "--games-per-rotation","$GamesPerRotation","--parallel","$Parallel",
          "--clock","$Clock","--seed-base","$SeedBase")
if ($Paired) {
  $params = @($params | Where-Object {$_ -ne "--policy"})
  # Rebuild using the paired runner's distinct policy argument names.
  $params=@($entrypoint,"--jar",$jarFile.FullName,
            "--pod",$Pod,"--reference-policy",$ReferencePolicy,
            "--experiment-policy",$Policy,"--profile",$AiProfile,
            "--games-per-rotation","$GamesPerRotation","--parallel","$Parallel",
            "--clock","$Clock","--seed-base","$SeedBase")
}
if ($PreflightOnly) {$params+="--preflight-only"}
if ($Jfr) {$params+="--jfr"}
Write-Host "USING_OFFICIAL_FORGE_RUNTIME $($jarFile.DirectoryName)"
& python @params
if ($LASTEXITCODE -ne 0) {
  throw "Real Forge four-seat runner failed; check preserved logs (exit $LASTEXITCODE)"
}
