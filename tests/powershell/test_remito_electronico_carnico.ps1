# Test Script for Remito Electronico Carnico VBS COM object

$vbsPath = Join-Path $PSScriptRoot "..\..\ejemplos\remito_electronico_carnico.vbs"

function Invoke-VBScript {
    param (
        [Parameter(Mandatory=$true)]
        [string]$ScriptPath
    )
    
    $env:PYTHONPATH = "C:\Users\ADMIN\desktop\pyafipws;$env:PYTHONPATH"
    $result = cscript //nologo $ScriptPath 2>&1
    $exitCode = $LASTEXITCODE
    
    return @{
        StdOut = $result -join "`n"
        ExitCode = $exitCode
    }
}

Describe "Remito Electronico Carnico VBS Script Tests" {
    BeforeAll {
        $script:testVbsPath = $vbsPath
    }

    It "Should run without errors" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.ExitCode | Should -Be 0
    }

    It "Should authenticate successfully" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Match "Aut"
    }

    It "Should create WSRemCarne object" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Match "WSRemCarne"
    }

    It "Should connect to the webservice" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Not -Match "Error al conectar"
    }

    It "Should consult last authorized voucher" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Match "comprobante"
    }

    It "Should create a remito" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Match "Remito"
    }

    It "Should add a trip" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Not -Match "Error al agregar viaje"
    }

    It "Should add a vehicle" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Not -Match "Error al agregar vehiculo"
    }

    It "Should add merchandise" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Not -Match "Error al agregar mercaderia"
    }

    It "Should generate remito" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Match "Autorizacion"
    }

    It "Should not have any critical errors" {
        $result = Invoke-VBScript -ScriptPath $script:testVbsPath
        $result.StdOut | Should -Not -Match "Error crítico:"
    }

    AfterAll {
        if (Test-Path "qr.png") {
            Remove-Item "qr.png"
        }
    }
}
