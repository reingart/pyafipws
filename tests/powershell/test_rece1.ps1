# call webservice to get last invoice number (Invoice type: 1 - Point of Sale: 2):
RECE1.exe /ult 1 2 /json --debug --trace
# convert the output file to json to read the results: 
$json = Get-Content -Path salida.txt | ConvertFrom-Json

describe TestUlt {
    Context {
        it 'returns last invoice number' {
            [int]$json[0].cbt_desde | Should -BeGreaterOrEqual 1
        } 
    }
}
