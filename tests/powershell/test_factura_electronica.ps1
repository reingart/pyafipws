# Test script for factura_electronica.vbs COM objects

$env:PYTHONPATH += ";$PWD;$PWD\env\lib\site-packages"
$WSAA = New-Object -ComObject WSAA
$WSFEv1 = New-Object -ComObject WSFEv1

function Write-Log {
    param([string]$message)
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $message"
}

function Get-XmlValue {
    param (
        [string]$xml,
        [string]$nodeName
    )
    if ($xml -match "<$nodeName>(.*?)</$nodeName>") {
        return $Matches[1]
    }
    return $null
}

Describe "Factura Electronica Tests" {
    BeforeAll {
        $certFile = Join-Path $PSScriptRoot "..\..\reingart.crt"
        $keyFile = Join-Path $PSScriptRoot "..\..\reingart.key"
        
        Write-Log "Clearing cache..."
        Remove-Item -Path "$env:TEMP\TA*.xml" -ErrorAction SilentlyContinue
        
        $wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
        $service = "wsfe"
        
        Write-Log "Attempting authentication..."
        $authResult = $WSAA.Autenticar($service, $certFile, $keyFile, $wsdl)
        Write-Log "Authentication result: $authResult"
        
        if (-not $authResult) {
            throw "Authentication failed: $($WSAA.Excepcion)"
        }
        Write-Log "Authentication successful"
        
        $token = Get-XmlValue -xml $authResult -nodeName "token"
        $sign = Get-XmlValue -xml $authResult -nodeName "sign"
        
        Write-Log "Setting up WSFEv1..."
        $WSFEv1.Cuit = "20267565393"
        $WSFEv1.Token = $token
        $WSFEv1.Sign = $sign
        $wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
        $ok = $WSFEv1.Conectar("", $wsdl)
        Write-Log "WSFEv1 connection result: $ok"
        if (-not $ok) {
            throw "WSFEv1 connection failed: $($WSFEv1.Excepcion)"
        }
        Write-Log "WSFEv1 setup complete"
    }

    Context "WSAA Tests" {
        It "Has valid Token and Sign" {
            Write-Log "Token: $token"
            Write-Log "Sign: $sign"
            $token | Should -Not -BeNullOrEmpty
            $sign | Should -Not -BeNullOrEmpty
        }
    }

    Context "WSFEv1 Tests" {
        It "Can connect to web service" {
            $WSFEv1.Excepcion | Should -BeNullOrEmpty
        }

        It "Can get last authorized voucher" {
            $tipo_cbte = 1
            $punto_vta = 4002
            $ult = $WSFEv1.CompUltimoAutorizado($tipo_cbte, $punto_vta)
            Write-Log "Last authorized voucher: $ult"
            $ult | Should -Not -BeNullOrEmpty
        }

        It "Can create invoice" {
            $result = $WSFEv1.CrearFactura(1, 80, "33693450239", 1, 4002, ($ult + 1), ($ult + 1), "124.00", "2.00", "100.00", "21.00", "1.00", "0.00", (Get-Date).ToString("yyyyMMdd"), "", "", "", "PES", "1.000")
            Write-Log "Create invoice result: $result"
            Write-Log "WSFEv1 Exception: $($WSFEv1.Excepcion)"
            Write-Log "WSFEv1 ErrMsg: $($WSFEv1.ErrMsg)"
            $result | Should -Be $true
            $WSFEv1.Excepcion | Should -BeNullOrEmpty
        }

        It "Can add associated vouchers" {
            $result = $WSFEv1.AgregarCmpAsoc(1, 4002, $ult)
            Write-Log "Add associated vouchers result: $result"
            $result | Should -Be $true
        }

        It "Can add taxes" {
            $result = $WSFEv1.AgregarTributo(99, "Impuesto Municipal Matanza", "100.00", "1.00", "1.00")
            Write-Log "Add taxes result: $result"
            $result | Should -Be $true
        }

        It "Can add VAT" {
            $result = $WSFEv1.AgregarIva(5, "100.00", "21.00")
            Write-Log "Add VAT result: $result"
            $result | Should -Be $true
        }
    }
}
