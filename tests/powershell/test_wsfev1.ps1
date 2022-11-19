BeforeAll {
    $wsfev1 = New-Object -ComObject WSFEv1
    echo $wsfev1.Version()
    echo $wsfev1.InstallDir()
    $wsfev1.Conectar()
    $wsfev1.Cuit = "20267565393"
    $ta = Get-Content ta.xml
    $wsfev1.SetTicketAcceso([string]$ta)
    $tipo_cbte = 6
    $punto_vta = 4002
    [int]$ult = $wsfev1.CompUltimoAutorizado($tipo_cbte, $punto_vta)
    $fecha_cbte = (Get-Date).tostring("yyyyMMdd")
    [int]$cbte_num = [int]$ult + 1
    $ok = $wsfev1.CrearFactura(1, 80, 33693450239, $tipo_cbte, $punto_vta, `
                              $cbte_num, $cbte_num, 121, 0, 100, `
                              21, 0, 0, $fecha_cbte, "", "", "", `
                              "PES", "1")
    $ok = $wsfev1.AgregarIva(5, 100, 21)
    $CAE = $wsfev1.CAESolicitar()
  }
  describe TestUlt { it 'Last invoice number ok' { [int]$wsfev1.CbteNro() | Should -BeGreaterOrEqual 1 } }
  describe TestInvoiceResult { it 'Invoice result ok' { $wsfev1.Resultado() | Should -Be 'A' } }
  describe TestInvoiceAuthCode { it 'Invoice auth code ok' { $wsfev1.CAE() | Should -Not -BeNullOrEmpty } }
  describe TestInvoiceNoException { it 'No exception' { $wsfev1.Excepcion() | Should -BeNullOrEmpty } }
  describe TestInvoiceNoError { it 'No error' { $wsfev1.ErrMsg() | Should -BeNullOrEmpty } }
  describe TestException { it 'raises exception' { { $wsfev1.ParamGetCotizacion("USD") } | Should -Throw -ErrorId System.Runtime.InteropServices.COMException } }
  describe TestNoException { it 'disabled exception' {
    { $wsfev1.LanzarExcepciones = $false ; $wsfev1.ParamGetCotizacion("USD") } | Should -Not -Throw -ErrorId System.Runtime.InteropServices.COMException
    $wsfev1.Excepcion() | Should -BeLike 'KeyError:*'
    $wsfev1.Traceback() | Should -Not -BeNullOrEmpty
    }
  }
  describe TestError { it 'returns error' { $wsfev1.CompConsultar(1, 1, 1) ; $wsfev1.ErrMsg() | Should -Be "602: No existen datos en nuestros registros para los parametros ingresados." } }
  describe TestDummy { it 'Dummy response ok' { $wsfev1.Dummy() ; $wsfev1.AppServerStatus() | Should -Be 'OK' } }
