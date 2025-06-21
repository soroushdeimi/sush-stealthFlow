# StealthFlow Client Installer for Windows
# Automated installer for StealthFlow client on Windows systems

param(
    [string]$InstallPath = "$env:USERPROFILE\StealthFlow",
    [switch]$SkipXray = $false,
    [switch]$Help = $false,
    [switch]$Force = $false,
    [string]$Version = "latest"
)

# Display help information
if ($Help) {
    Write-Host @"
StealthFlow Client Installer for Windows

USAGE:
    .\install-client.ps1 [OPTIONS]

OPTIONS:
    -InstallPath <path>   Installation directory (default: $env:USERPROFILE\StealthFlow)
    -SkipXray            Skip Xray installation
    -Force               Force installation even if already exists
    -Version <version>   Install specific version (default: latest)
    -Help                Show this help message

EXAMPLES:
    .\install-client.ps1
    .\install-client.ps1 -InstallPath "C:\Tools\StealthFlow"
    .\install-client.ps1 -SkipXray -Force
    .\install-client.ps1 -Version "1.2.0"
"@
    exit 0
}

# Color functions for better output
function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    
    $originalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Host $Text
    $Host.UI.RawUI.ForegroundColor = $originalColor
}

function Write-Info {
    param([string]$Message)
    Write-ColorText "[INFO] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorText "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorText "[ERROR] $Message" "Red"
}

function Write-Success {
    param([string]$Message)
    Write-ColorText "[SUCCESS] $Message" "Green"
}

# Check if running as administrator
function Test-Administrator {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check system requirements
function Test-SystemRequirements {
    Write-Info "Checking system requirements..."
    
    $requirements = @{
        "PowerShell" = $PSVersionTable.PSVersion.Major -ge 5
        "Windows" = $true
        "Architecture" = $env:PROCESSOR_ARCHITECTURE -eq "AMD64"
        "DotNet" = $true
    }
    
    # Check .NET Framework
    try {
        $dotNetVersion = Get-ItemProperty "HKLM:SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full\" -Name Release -ErrorAction Stop
        $requirements["DotNet"] = $dotNetVersion.Release -ge 461808
    } catch {
        $requirements["DotNet"] = $false
    }
    
    $allMet = $true
    foreach ($req in $requirements.GetEnumerator()) {
        if ($req.Value) {
            Write-Info "[OK] $($req.Key): Passed"
        } else {
            Write-Error "[FAIL] $($req.Key): Failed"
            $allMet = $false
        }
    }
    
    return $allMet
}

# Download file with progress
function Download-File {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Description = "Downloading file"
    )
    
    try {
        Write-Info "$Description from $Url"
        
        # Use .NET WebClient for better progress reporting
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $OutputPath)
        
        Write-Success "Downloaded successfully to $OutputPath"
        return $true
    } catch {
        Write-Error "Failed to download $Url`: $($_.Exception.Message)"
        return $false
    }
}

# Extract ZIP archive
function Expand-Archive {
    param(
        [string]$Path,
        [string]$DestinationPath
    )
    
    try {
        Write-Info "Extracting $Path to $DestinationPath"
        
        if (Get-Command Expand-Archive -ErrorAction SilentlyContinue) {
            Microsoft.PowerShell.Archive\Expand-Archive -Path $Path -DestinationPath $DestinationPath -Force
        } else {
            # Fallback to .NET ZipFile
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            [System.IO.Compression.ZipFile]::ExtractToDirectory($Path, $DestinationPath)
        }
        
        Write-Success "Extraction completed"
        return $true
    } catch {
        Write-Error "Failed to extract archive: $($_.Exception.Message)"
        return $false
    }
}

# Install Python dependencies
function Install-PythonDependencies {
    param([string]$RequirementsPath)
    
    Write-Info "Installing Python dependencies..."
    
    try {
        # Check if pip is available
        $pipCommand = Get-Command pip -ErrorAction SilentlyContinue
        if (-not $pipCommand) {
            $pipCommand = Get-Command pip3 -ErrorAction SilentlyContinue
        }
        
        if (-not $pipCommand) {
            Write-Error "pip is not available. Please install Python first."
            return $false
        }
        
        # Install requirements
        $installProcess = Start-Process -FilePath $pipCommand.Source -ArgumentList @("install", "-r", $RequirementsPath, "--user") -Wait -PassThru -NoNewWindow
        
        if ($installProcess.ExitCode -eq 0) {
            Write-Success "Python dependencies installed successfully"
            return $true
        } else {
            Write-Error "Failed to install Python dependencies"
            return $false
        }
    } catch {
        Write-Error "Error installing Python dependencies: $($_.Exception.Message)"
        return $false
    }
}

# Install Xray binary
function Install-Xray {
    param([string]$InstallDirectory)
    
    if ($SkipXray) {
        Write-Info "Skipping Xray installation as requested"
        return $true
    }
    
    Write-Info "Installing Xray..."
    
    try {
        # Get latest Xray version
        $apiUrl = "https://api.github.com/repos/XTLS/Xray-core/releases/latest"
        $releaseInfo = Invoke-RestMethod -Uri $apiUrl -ErrorAction Stop
        $version = $releaseInfo.tag_name
        
        # Find Windows x64 asset
        $asset = $releaseInfo.assets | Where-Object { $_.name -like "*windows-64.zip" }
        if (-not $asset) {
            Write-Error "Could not find Windows x64 release asset"
            return $false
        }
        
        # Download Xray
        $xrayZipPath = Join-Path $InstallDirectory "xray-windows-64.zip"
        $downloadSuccess = Download-File -Url $asset.browser_download_url -OutputPath $xrayZipPath -Description "Downloading Xray $version"
        
        if (-not $downloadSuccess) {
            return $false
        }
        
        # Extract Xray
        $xrayDir = Join-Path $InstallDirectory "xray"
        New-Item -ItemType Directory -Path $xrayDir -Force | Out-Null
        
        $extractSuccess = Expand-Archive -Path $xrayZipPath -DestinationPath $xrayDir
        if (-not $extractSuccess) {
            return $false
        }
        
        # Clean up zip file
        Remove-Item $xrayZipPath -Force -ErrorAction SilentlyContinue
        
        # Make xray executable
        $xrayExe = Join-Path $xrayDir "xray.exe"
        if (Test-Path $xrayExe) {
            Write-Success "Xray installed successfully"
            return $true
        } else {
            Write-Error "Xray executable not found after extraction"
            return $false
        }
        
    } catch {
        Write-Error "Failed to install Xray: $($_.Exception.Message)"
        return $false
    }
}

# Create application shortcuts
function New-ApplicationShortcuts {
    param([string]$InstallDirectory)
    
    Write-Info "Creating application shortcuts..."
    
    try {
        $shell = New-Object -ComObject WScript.Shell
        
        # Desktop shortcut
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktopPath "StealthFlow.lnk"
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "python"
        $shortcut.Arguments = "`"$InstallDirectory\stealthflow_gui.py`""
        $shortcut.WorkingDirectory = $InstallDirectory
        $shortcut.Description = "StealthFlow VPN Client"
        $shortcut.Save()
        
        # Start Menu shortcut
        $startMenuPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
        $startMenuShortcut = Join-Path $startMenuPath "StealthFlow.lnk"
        $startShortcut = $shell.CreateShortcut($startMenuShortcut)
        $startShortcut.TargetPath = "python"
        $startShortcut.Arguments = "`"$InstallDirectory\stealthflow_gui.py`""
        $startShortcut.WorkingDirectory = $InstallDirectory
        $startShortcut.Description = "StealthFlow VPN Client"
        $startShortcut.Save()
        
        Write-Success "Shortcuts created successfully"
        return $true
    } catch {
        Write-Warning "Failed to create shortcuts: $($_.Exception.Message)"
        return $false
    }
}

# Create batch launcher
function New-BatchLauncher {
    param([string]$InstallDirectory)
    
    Write-Info "Creating batch launcher..."
    
    $batchContent = @"
@echo off
cd /d "$InstallDirectory"
python stealthflow_gui.py
pause
"@
    
    $batchPath = Join-Path $InstallDirectory "StealthFlow.bat"
    
    try {
        Set-Content -Path $batchPath -Value $batchContent -Encoding UTF8
        Write-Success "Batch launcher created at $batchPath"
        return $true
    } catch {
        Write-Error "Failed to create batch launcher: $($_.Exception.Message)"
        return $false
    }
}

# Verify installation
function Test-Installation {
    param([string]$InstallDirectory)
    
    Write-Info "Verifying installation..."
    
    $success = $true
    
    # Check required files
    $requiredFiles = @(
        "stealthflow_client.py",
        "stealthflow_gui.py",
        "profile_manager.py",
        "requirements.txt"
    )
    
    foreach ($file in $requiredFiles) {
        $filePath = Join-Path $InstallDirectory $file
        if (Test-Path $filePath) {
            Write-Info "[OK] $file found"
        } else {
            Write-Error "[FAIL] $file missing"
            $success = $false
        }
    }
    
    # Test Python environment
    try {
        $pythonTest = python -c "import sys; print('Python', sys.version)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Info "[OK] Python environment working"
        } else {
            Write-Error "[FAIL] Python environment not working"
            $success = $false
        }
    } catch {
        Write-Error "[FAIL] Python test failed: $($_.Exception.Message)"
        $success = $false
    }
    
    # Test Xray if installed
    if (-not $SkipXray) {
        $xrayPath = Join-Path $InstallDirectory "xray\xray.exe"
        if (Test-Path $xrayPath) {
            Write-Info "[OK] Xray available"
        } else {
            Write-Warning "[WARN] Xray not working"
            $success = $false
        }
    }
    
    if ($success) {
        Write-Success "[SUCCESS] All tests passed successfully"
    } else {
        Write-Warning "[WARNING] Some tests failed"
    }
    
    return $success
}

# Main installation function
function Install-StealthFlowClient {
    Write-Info "Starting StealthFlow Client installation..."
    Write-Info "Installation directory: $InstallPath"
    
    # Check system requirements
    if (-not (Test-SystemRequirements)) {
        Write-Error "System requirements not met. Installation aborted."
        exit 1
    }
    
    # Check if already installed
    if ((Test-Path $InstallPath) -and -not $Force) {
        Write-Warning "StealthFlow is already installed at $InstallPath"
        Write-Info "Use -Force to reinstall"
        exit 1
    }
    
    # Create installation directory
    try {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
        Write-Info "Created installation directory: $InstallPath"
    } catch {
        Write-Error "Failed to create installation directory: $($_.Exception.Message)"
        exit 1
    }
    
    # Download client files
    Write-Info "Downloading StealthFlow client files..."
    
    $baseUrl = "https://raw.githubusercontent.com/stealthflow/stealthflow/main/client"
    $files = @{
        "stealthflow_client.py" = "$baseUrl/core/stealthflow_client.py"
        "stealthflow_gui.py" = "$baseUrl/ui/stealthflow_gui.py"
        "profile_manager.py" = "$baseUrl/profiles/profile_manager.py"
        "requirements.txt" = "https://raw.githubusercontent.com/stealthflow/stealthflow/main/requirements.txt"
    }
    
    $downloadSuccess = $true
    foreach ($file in $files.GetEnumerator()) {
        $filePath = Join-Path $InstallPath $file.Key
        if (-not (Download-File -Url $file.Value -OutputPath $filePath -Description "Downloading $($file.Key)")) {
            $downloadSuccess = $false
            break
        }
    }
    
    if (-not $downloadSuccess) {
        Write-Error "Failed to download required files. Installation aborted."
        exit 1
    }
    
    # Install Python dependencies
    $requirementsPath = Join-Path $InstallPath "requirements.txt"
    if (-not (Install-PythonDependencies -RequirementsPath $requirementsPath)) {
        Write-Warning "Failed to install Python dependencies. You may need to install them manually."
    }
    
    # Install Xray
    if (-not (Install-Xray -InstallDirectory $InstallPath)) {
        Write-Warning "Failed to install Xray. You can install it manually later."
    }
    
    # Create shortcuts and launchers
    New-ApplicationShortcuts -InstallDirectory $InstallPath | Out-Null
    New-BatchLauncher -InstallDirectory $InstallPath | Out-Null
    
    # Verify installation
    $verificationSuccess = Test-Installation -InstallDirectory $InstallPath
    
    if ($verificationSuccess) {
        Write-Success "[SUCCESS] StealthFlow client installed successfully!"
        Write-Info ""
        Write-Info "Installation completed at: $InstallPath"
        Write-Info "You can now run StealthFlow using:"
        Write-Info "  - Desktop shortcut"
        Write-Info "  - Start menu shortcut"
        Write-Info "  - Batch file: $InstallPath\StealthFlow.bat"
        Write-Info "  - Command line: python `"$InstallPath\stealthflow_gui.py`""
    } else {
        Write-Error "Installation completed with warnings. Please check the output above."
        exit 1
    }
}

# Main execution
try {
    Install-StealthFlowClient
} catch {
    Write-Error "Installation failed with error: $($_.Exception.Message)"
    Write-Error "Stack trace: $($_.Exception.StackTrace)"
    exit 1
}
