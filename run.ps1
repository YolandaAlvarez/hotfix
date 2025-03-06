# This scripts is meant to automate virtual env preparation, 
# activation and running of main.py

function Start-CountdownAndClearScreen {
    for ($i = 2; $i -gt 0; $i--) {
        # Write-Host "counter: $i"
        Start-Sleep -Seconds 1
    }

    # wait 1 second
    Start-Sleep -Seconds 1

    Clear-Host
}

if (-not (Test-Path -Path ".\.venv")) {
    Write-Output ".venv not found. Creating..."
    Write-Output ""
    python -m venv .venv
    
    .\.venv\Scripts\Activate.ps1
    
    if (Test-Path -Path ".\requirements.txt") {
        Write-Output "Installing requirements.txt... "
        Write-Output ""
        
        # pip install -r .\requirements.txt
        pip install --proxy=http://rb-proxy-de.bosch.com:8080 -r .\requirements.txt
        Write-Output ""
        Write-Output "requirements.txt installed succesfully"
    }
    else {
        Write-Output "requirements.txt not found."
    }
}
else {
    .\.venv\Scripts\Activate.ps1
    Write-Output ".venv activated"
}

# Start-CountdownAndClearScreen
Write-Output "Running main.py ..."
Write-Output ""
python main.py