# # Test script for PyQR COM object

# # Create PyQR COM object
# $PyQR = New-Object -ComObject PyQR

# Describe "PyQR Tests" {
#     It "Can create a file" {
#         $archivo = $PyQR.CrearArchivo()
#         $archivo | Should -Not -BeNullOrEmpty
#     }

#     It "Can generate QR image" {
#         $ver = 1
#         $fecha = "2020-10-13"
#         $cuit = 30000000007
#         $pto_vta = 10
#         $tipo_cmp = 1
#         $nro_cmp = 94
#         $importe = 12100
#         $moneda = "DOL"
#         $ctz = 65
#         $tipo_doc_rec = 80
#         $nro_doc_rec = 20000000001
#         $tipo_cod_aut = "E"
#         $cod_aut = 70417054367476

#         $url = $PyQR.GenerarImagen($ver, $fecha, $cuit, $pto_vta, $tipo_cmp, $nro_cmp,
#                                    $importe, $moneda, $ctz, $tipo_doc_rec, $nro_doc_rec,
#                                    $tipo_cod_aut, $cod_aut)
#         $url | Should -Not -BeNullOrEmpty
#         Test-Path $url | Should -Be $true
#     }
# }

$PyQR = New-Object -ComObject PyQR

Describe "PyQR Tests" {
    It "Can create a file" {
        $archivo = $PyQR.CrearArchivo()
        $archivo | Should -Not -BeNullOrEmpty
    }

    It "Can generate QR image URL" {
        $ver = 1
        $fecha = "2020-10-13"
        $cuit = 30000000007
        $pto_vta = 10
        $tipo_cmp = 1
        $nro_cmp = 94
        $importe = 12100
        $moneda = "DOL"
        $ctz = 65
        $tipo_doc_rec = 80
        $nro_doc_rec = 20000000001
        $tipo_cod_aut = "E"
        $cod_aut = 70417054367476

        $url = $PyQR.GenerarImagen($ver, $fecha, $cuit, $pto_vta, $tipo_cmp, $nro_cmp,
                                   $importe, $moneda, $ctz, $tipo_doc_rec, $nro_doc_rec,
                                   $tipo_cod_aut, $cod_aut)
        $url | Should -Not -BeNullOrEmpty
        Write-Host "Generated QR image URL: $url"
        $url | Should -Match '^https://www\.afip\.gob\.ar/fe/qr/\?p='

        # Optionally, check if the URL is accessible
        $response = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing
        $response.StatusCode | Should -Be 200
    }
}
