$wsaa = New-Object -ComObject WSAA
echo $wsaa.InstallDir()
$curdir = Get-Location
$cert = Join-Path -Path $curdir -ChildPath "reingart.crt"
$pkey = Join-Path -Path $curdir -ChildPath "reingart.key"
[xml]$ta = $WSAA.Autenticar( "wsfe", $cert , $pkey )
$ta.Save("ta.xml")
describe TestTA { it 'Authentication access ticket ok' { $ta.loginTicketResponse.header.source | Should -Be 'CN=wsaahomo, O=AFIP, C=AR, SERIALNUMBER=CUIT 33693450239' } }
describe TestToken { it 'Token OK' { $WSAA.Token() | Should -Not -BeNullOrEmpty } }
describe TestSign { it 'Sign OK' { $WSAA.Sign() | Should -Not -BeNullOrEmpty } }
