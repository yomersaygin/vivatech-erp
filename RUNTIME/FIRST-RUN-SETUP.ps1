$ErrorActionPreference = 'Stop'

$AppRoot = Split-Path -Parent $PSScriptRoot
$RuntimeRoot = $PSScriptRoot
$FrappeDir = Join-Path $RuntimeRoot 'frappe_docker'
$BundledZip = Join-Path $RuntimeRoot 'BUNDLED\frappe_docker.zip'
$DownloadZip = Join-Path $RuntimeRoot 'frappe_docker.zip'
$ExtractRoot = Join-Path $RuntimeRoot '_frappe_extract'
$AppsJson = Join-Path $RuntimeRoot 'apps.json'
$LogPath = Join-Path $RuntimeRoot 'first-run.log'
$MarkerPath = Join-Path $RuntimeRoot '.vivatech-installed'
$Project = 'vivatech'
$Site = 'vivatech.localhost'
$DbPassword = 'admin'
$AdminPassword = 'admin'

function Log([string]$Message) {
    $line = "$(Get-Date -Format s) $Message"
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    Write-Host $Message
}

function Require-Docker {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        throw "Docker Desktop bulunamadi. Once Docker Desktop'i kurup baslatin."
    }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (Test-Path $desktop) {
            Start-Process $desktop | Out-Null
            Log 'Docker Desktop baslatiliyor...'
            for ($i=0; $i -lt 60; $i++) {
                Start-Sleep -Seconds 3
                docker info *> $null
                if ($LASTEXITCODE -eq 0) { return }
            }
        }
        throw 'Docker servisi hazir degil.'
    }
}

function Ensure-FrappeDocker {
    if (Test-Path (Join-Path $FrappeDir 'compose.yaml')) { return }

    Remove-Item $ExtractRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $DownloadZip -Force -ErrorAction SilentlyContinue

    $zipToUse = $null
    if (Test-Path $BundledZip) {
        Log 'Paket icindeki Frappe Docker dosyalari kullaniliyor...'
        $zipToUse = $BundledZip
    } else {
        Log 'Paketlenmis runtime bulunamadi, Frappe Docker indiriliyor...'
        Invoke-WebRequest -Uri 'https://github.com/frappe/frappe_docker/archive/refs/heads/main.zip' -OutFile $DownloadZip
        $zipToUse = $DownloadZip
    }

    Expand-Archive -Path $zipToUse -DestinationPath $ExtractRoot -Force
    $source = Get-ChildItem $ExtractRoot -Directory | Select-Object -First 1
    if (-not $source) { throw 'frappe_docker arsivi acilamadi.' }
    Remove-Item $FrappeDir -Recurse -Force -ErrorAction SilentlyContinue
    Move-Item $source.FullName $FrappeDir
    Remove-Item $ExtractRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $DownloadZip -Force -ErrorAction SilentlyContinue
}

function Build-VivatechImage {
    docker image inspect vivatech-erp:local *> $null
    if ($LASTEXITCODE -eq 0) {
        Log 'Vivatech ERP Docker image mevcut, tekrar build edilmiyor.'
        return
    }

    $apps = @'
[
  {"url":"https://github.com/frappe/erpnext","branch":"version-16"},
  {"url":"https://github.com/yomersaygin/vivatech-erp.git","branch":"main"}
]
'@
    Set-Content -Path $AppsJson -Value $apps -Encoding UTF8
    Log 'Vivatech ERP Docker image olusturuluyor...'
    docker build --secret "id=apps_json,src=$AppsJson" --build-arg FRAPPE_PATH=https://github.com/frappe/frappe --build-arg FRAPPE_BRANCH=version-16 -t vivatech-erp:local -f (Join-Path $FrappeDir 'images\layered\Containerfile') $FrappeDir
    if ($LASTEXITCODE -ne 0) { throw 'Vivatech ERP image build basarisiz.' }
}

function Prepare-Compose {
    $composeOut = Join-Path $FrappeDir 'compose.vivatech.yaml'
    if (Test-Path $composeOut) { return }

    $envFile = Join-Path $FrappeDir '.env'
    @"
CUSTOM_IMAGE=vivatech-erp
CUSTOM_TAG=local
PULL_POLICY=never
DB_PASSWORD=$DbPassword
FRAPPE_SITE_NAME_HEADER=$Site
HTTP_PUBLISH_PORT=8080
"@ | Set-Content -Path $envFile -Encoding UTF8

    Push-Location $FrappeDir
    try {
        docker compose --env-file .env -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.noproxy.yaml config | Set-Content -Path compose.vivatech.yaml -Encoding UTF8
        if ($LASTEXITCODE -ne 0) { throw 'Docker compose dosyasi olusturulamadi.' }
    } finally { Pop-Location }
}

function Start-Stack {
    Push-Location $FrappeDir
    try {
        docker compose -p $Project -f compose.vivatech.yaml up -d --remove-orphans
        if ($LASTEXITCODE -ne 0) { throw 'ERP servisleri baslatilamadi.' }
        Log 'ERP servislerinin hazir olmasi bekleniyor...'
        for ($i=0; $i -lt 90; $i++) {
            docker compose -p $Project -f compose.vivatech.yaml exec -T backend bench --version *> $null
            if ($LASTEXITCODE -eq 0) { return }
            Start-Sleep -Seconds 4
        }
        throw 'ERP backend zamaninda hazir olmadi.'
    } finally { Pop-Location }
}

function Ensure-Site {
    Push-Location $FrappeDir
    try {
        $sites = docker compose -p $Project -f compose.vivatech.yaml exec -T backend bench list-sites 2>$null
        $siteText = ($sites -join "`n")
        if ($siteText -notmatch [regex]::Escape($Site)) {
            Log 'Vivatech ERP sitesi olusturuluyor...'
            docker compose -p $Project -f compose.vivatech.yaml exec -T backend bench new-site $Site --db-host db --db-root-username root --db-root-password $DbPassword --admin-password $AdminPassword --no-mariadb-socket
            if ($LASTEXITCODE -ne 0) { throw 'Site olusturulamadi.' }
        }

        $apps = docker compose -p $Project -f compose.vivatech.yaml exec -T backend bench --site $Site list-apps 2>$null
        $appsText = ($apps -join "`n")
        if ($appsText -notmatch '(?m)^erpnext\s*$') {
            docker compose -p $Project -f compose.vivatech.yaml exec -T backend bench --site $Site install-app erpnext
            if ($LASTEXITCODE -ne 0) { throw 'ERPNext kurulumu basarisiz.' }
        }

        $apps = docker compose -p $Project -f compose.vivatech.yaml exec -T backend bench --site $Site list-apps 2>$null
        $appsText = ($apps -join "`n")
        if ($appsText -notmatch '(?m)^vivatech_erp\s*$') {
            docker compose -p $Project -f compose.vivatech.yaml exec -T backend bench --site $Site install-app vivatech_erp
            if ($LASTEXITCODE -ne 0) { throw 'Vivatech ERP uygulamasi kurulamadi.' }
        }

        docker compose -p $Project -f compose.vivatech.yaml exec -T backend bench --site $Site migrate
        if ($LASTEXITCODE -ne 0) { throw 'Migration basarisiz.' }
    } finally { Pop-Location }
}

try {
    New-Item -ItemType Directory -Force $RuntimeRoot | Out-Null
    if (Test-Path $MarkerPath) {
        Log 'Vivatech ERP ilk kurulumu daha once tamamlanmis.'
        exit 0
    }

    Set-Content -Path $LogPath -Value "Vivatech ERP ilk kurulum - $(Get-Date -Format s)" -Encoding UTF8
    Require-Docker
    Ensure-FrappeDocker
    Build-VivatechImage
    Prepare-Compose
    Start-Stack
    Ensure-Site
    Set-Content -Path $MarkerPath -Value (Get-Date -Format s) -Encoding UTF8
    Log 'Vivatech ERP ilk kurulumu tamamlandi.'
    exit 0
} catch {
    Remove-Item $MarkerPath -Force -ErrorAction SilentlyContinue
    Log ("HATA: " + $_.Exception.Message)
    Write-Error $_
    exit 1
}
