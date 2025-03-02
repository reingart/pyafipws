# Test script for PyI25 COM object

# Create PyI25 COM object
$PyI25 = New-Object -ComObject PyI25

Describe "PyI25 Tests" {
    # It "Version is not empty" {
    #     $PyI25.Version | Should -Not -BeNullOrEmpty
    # }

    It "Can generate barcode" {
        $barras = "202675653930240016120303473904220110529"
        $barras += $PyI25.DigitoVerificadorModulo10($barras)
        $salida = Join-Path $PWD "barras_test.png"
        $result = $PyI25.GenerarImagen($barras, $salida)
        $result | Should -Be $true
        Test-Path $salida | Should -Be $true
    }

    It "Digito Verificador calculation is correct" {
        $barras = "202675653930240016120303473904220110529"
        $digito = $PyI25.DigitoVerificadorModulo10($barras)
        $digito | Should -Be "9"
    }

    It "Generated barcode file is valid" {
        $salida = Join-Path $PWD "barras_test.png"
        $fileInfo = Get-Item $salida
        $fileInfo.Length | Should -BeGreaterThan 0
    }

    It "Can handle different input for DigitoVerificadorModulo10" {
        $testInput = "123456789"
        $digito = $PyI25.DigitoVerificadorModulo10($testInput)
        $digito | Should -Not -BeNullOrEmpty
    }
}
