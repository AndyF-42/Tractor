Start-Process powershell -ArgumentList "-NoExit -Command `"python server.py --dev`""

$labels = @("A", "B", "C", "D")

for ($i = 0; $i -lt $labels.Length; $i++) {
    $label = $labels[$i]
    Start-Process powershell -ArgumentList "-NoExit -Command `"Write-Host '$label'; python client.py $label`""
}