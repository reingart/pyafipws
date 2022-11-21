describe TestUlt {
    Context "get last invoice - json interchange files" {
        BeforeAll {
            # call webservice to get last invoice number (Invoice type: 1 - Point of Sale: 2):
            RECE1.exe /ult 1 2 /json --debug --trace
            # convert the output file to json to read the results:
            $json = Get-Content -Path salida.txt | ConvertFrom-Json
        }
        it 'returns last invoice number' {
            [int]$json[0].cbt_desde | Should -BeGreaterOrEqual 1
        } 
    }
}

describe TestGetCAE {
    Context "authorize invoice - json interchange files" {
        BeforeAll {
            # call webservice to get last invoice number (Invoice type: 1 - Point of Sale: 2):
            RECE1.exe /prueba /json --debug --trace
            # convert the output file to json to read the results:
            $json = Get-Content -Path salida.txt | ConvertFrom-Json
        }
        it 'Invoice result ok' { $json[0].resultado | Should -Be 'A' }
        it 'Invoice auth code ok' { $json[0].cae | Should -Not -BeNullOrEmpty }
    }
}
