# SharePoint Uploader CLI - Production Deployment Script

# This script automates the setup of the SharePoint Uploader CLI in a production environment.
# It creates a virtual environment, installs dependencies, and prepares the configuration file.

# 1. Create a Python virtual environment
Write-Host "Creating Python virtual environment..."
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to create virtual environment. Please ensure Python 3.8+ is installed and in your PATH."
    exit 1
}

# 2. Activate the virtual environment
Write-Host "Activating virtual environment..."
# Note: Activation is for the current script session. 
# The user will need to activate it manually for subsequent sessions.
./venv/Scripts/Activate.ps1

# 3. Install dependencies
Write-Host "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install dependencies. Please check requirements.txt and your internet connection."
    exit 1
}

# 4. Create .env file from template
Write-Host "Creating .env file from env_template.txt..."
if (Test-Path .env) {
    Write-Host "Warning: .env file already exists. Skipping creation."
} else {
    Copy-Item env_template.txt .env
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create .env file."
        exit 1
    }
}

Write-Host "--------------------------------------------------"
Write-Host "✅ Deployment setup complete!"
Write-Host "Next steps:"
Write-Host "1. IMPORTANT: Edit the .env file and fill in your actual production credentials."
Write-Host "2. Activate the virtual environment in your terminal: .\venv\Scripts\Activate.ps1"
Write-Host "3. Run the application: python main.py --help"
Write-Host "--------------------------------------------------"