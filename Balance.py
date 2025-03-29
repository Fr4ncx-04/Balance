import streamlit as st
from datetime import datetime

# ==========================
# LÓGICA CONTABLE (Dominio)
# ==========================
class AperturaData:
    """
    Maneja la información contable y las operaciones:
      1. Asiento de Apertura
      2. Compras (Efectivo, Crédito, Combinada)
      3. Pago de Rentas Pagadas por Anticipado
      4. Compra de Papelería
      5. Anticipo de Clientes
      6. Venta
      7. Costo de lo Vendido
      8. Gastos Generales
      9. Anulación de Anticipo de Clientes
      10. Depreciaciones

      + Libro Diario (registro automático de cada asiento)
      + Tablas de Mayor (T-accounts)
      + Balanza de Comprobación
      + Balance General
    """
    def __init__(self):
        # Nombre de la empresa
        self.company_name = "Mi Empresa"
        self.apertura_realizada = False
        
        # Tasa de IVA
        self.iva_rate = 0.16
        
        # Cuentas de Activo (circulante)
        self.caja = 0.0
        self.inventario = 0.0
        self.rentas_anticipadas = 0.0
        
        # Activo No Circulante
        self.activos_no_circulantes = []
        
        # Cuentas de IVA (activo circulante)
        self.iva_acreditable = 0.0
        self.iva_por_acreditar = 0.0
        
        # Pasivo
        self.acreedores = 0.0
        self.documentos_por_pagar = 0.0
        self.anticipo_clientes = []  # Lista de (descripcion, monto)
        
        # Totales y Capital
        self.total_circulante = 0.0
        self.total_no_circulante = 0.0
        self.total_activo = 0.0
        self.total_pasivo = 0.0
        self.capital = 0.0
        
        # Estructura para el Libro Diario (lista de asientos)
        self.libro_diario = []
        
        # Diccionario para el Libro Mayor
        self.ledger_accounts = {}

    # ----------------------------------------------------------------
    # MÉTODOS PARA EL LIBRO DIARIO
    # ----------------------------------------------------------------
    def registrar_en_libro_diario(self, descripcion, lineas, trans_code):
        """
        Agrega un asiento al libro diario y de inmediato lo 'postea' al libro mayor.
        """
        fecha_str = datetime.now().strftime("%d/%m/%Y")
        self.libro_diario.append({
            "fecha": fecha_str,
            "descripcion": descripcion,
            "lines": lineas,
            "code": trans_code
        })
        
        # Postear cada línea de este asiento al libro mayor
        self.post_to_ledger(fecha_str, descripcion, lineas, trans_code)

    def post_to_ledger(self, fecha, descripcion, lineas, trans_code):
        """
        Registra cada movimiento (debe/haber) en la cuenta correspondiente
        dentro de self.ledger_accounts.
        """
        for (cuenta, debe, haber) in lineas:
            if cuenta not in self.ledger_accounts:
                self.ledger_accounts[cuenta] = []
            self.ledger_accounts[cuenta].append({
                "fecha": fecha,
                "descripcion": descripcion,
                "trans_code": trans_code,
                "debe": debe,
                "haber": haber
            })

    def generar_libro_diario(self) -> str:
        """
        Genera un texto con columnas: Fecha | Cuentas | Debe | Haber
        y al final la suma total de los débitos y créditos.
        """
        if not self.libro_diario:
            return "Debes iniciar tu asiento de apertura para ver tu libro diario."

        texto = ""
        texto += f"{'='*60}\n"
        texto += f"{self.company_name.upper()} - LIBRO DIARIO (Modo Oscuro)\n"
        texto += f"{'='*60}\n"
        texto += f"{'Fecha':<12}{'Cuentas':<30}{'Debe':>10}{'Haber':>10}\n"
        texto += f"{'-'*60}\n"

        total_debe = 0.0
        total_haber = 0.0

        for asiento in self.libro_diario:
            fecha = asiento["fecha"]
            desc = asiento["descripcion"]
            code = asiento["code"]
            lines = asiento["lines"]
            
            # Encabezado del asiento
            texto += f"{fecha:<12}{desc} (Código {code})\n"
            
            # Detalle de cada línea
            for (cuenta, debe, haber) in lines:
                texto += (f"{'':<12}"  
                          f"{cuenta:<30}"
                          f"{debe:>10,.2f}"
                          f"{haber:>10,.2f}\n")
                total_debe += debe
                total_haber += haber
            texto += "\n"
        
        # Suma total Debe/Haber
        texto += f"{'-'*60}\n"
        texto += (f"{'':<12}{'SUMA TOTAL':<30}"
                  f"{total_debe:>10,.2f}"
                  f"{total_haber:>10,.2f}\n")

        return texto

    # ----------------------------------------------------------------
    # CÁLCULOS DE TOTALES
    # ----------------------------------------------------------------
    def recalcular_totales(self):
        total_activo_circulante = (
            self.caja 
            + self.inventario 
            + self.rentas_anticipadas 
            + self.iva_acreditable 
            + self.iva_por_acreditar
        )
        self.total_circulante = total_activo_circulante
        self.total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        self.total_activo = total_activo_circulante + self.total_no_circulante
        
        anticipo_total = sum(monto for _, monto in self.anticipo_clientes)
        self.total_pasivo = self.acreedores + self.documentos_por_pagar + anticipo_total

    def calcular_asiento_apertura(self):
        total_activo_circulante = self.caja
        total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        self.total_activo = total_activo_circulante + total_no_circulante
        self.capital = self.total_activo
        self.total_pasivo = 0.0
        self.apertura_realizada = True
        
        # REGISTRAR EN LIBRO DIARIO (Código A)
        lineas = []
        if self.caja > 0:
            lineas.append(("Caja", self.caja, 0.0))
        for (nombre, valor) in self.activos_no_circulantes:
            lineas.append((nombre, valor, 0.0))
        lineas.append(("Capital (Apertura)", 0.0, self.total_activo))
        
        self.registrar_en_libro_diario("Asiento de Apertura", lineas, "A")
        
        self.recalcular_totales()

    # ----------------------------------------------------------------
    # OPERACIONES (1a PARTE)
    # ----------------------------------------------------------------
    def compra_en_efectivo(self, nombre: str, valor: float):
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        iva = valor * self.iva_rate
        self.inventario += valor
        self.iva_acreditable += iva
        self.caja -= (valor + iva)
        self.recalcular_totales()
        
        # Libro Diario (Código 1)
        lineas = [
            ("Inventario", valor, 0.0),
            ("IVA Acreditable", iva, 0.0),
            ("Caja", 0.0, valor + iva)
        ]
        self.registrar_en_libro_diario(f"Compra en Efectivo - {nombre}", lineas, "1")

    def compra_a_credito(self, nombre: str, valor: float):
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        iva = valor * self.iva_rate
        self.activos_no_circulantes.append((nombre, valor))
        self.iva_por_acreditar += iva
        self.acreedores += (valor + iva)
        self.recalcular_totales()
        
        # Libro Diario (Código 2)
        lineas = [
            (nombre, valor, 0.0),
            ("IVA por Acreditar", iva, 0.0),
            ("Acreedores", 0.0, valor + iva)
        ]
        self.registrar_en_libro_diario(f"Compra a Crédito - {nombre}", lineas, "2")

    def compra_combinada(self, nombre: str, valor: float):
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        iva_total = valor * self.iva_rate
        mitad_valor = valor / 2.0
        mitad_iva = iva_total / 2.0
        self.activos_no_circulantes.append((nombre, valor))
        
        # Efectivo
        self.caja -= (mitad_valor + mitad_iva)
        self.iva_acreditable += mitad_iva
        # Crédito
        self.documentos_por_pagar += (mitad_valor + mitad_iva)
        self.iva_por_acreditar += mitad_iva
        self.recalcular_totales()
        
        # Libro Diario (Código 3)
        lineas = [
            (nombre, valor, 0.0),
            ("IVA Acreditable", mitad_iva, 0.0),
            ("IVA por Acreditar", mitad_iva, 0.0),
            ("Caja", 0.0, (mitad_valor + mitad_iva)),
            ("Documentos por Pagar", 0.0, (mitad_valor + mitad_iva))
        ]
        self.registrar_en_libro_diario(f"Compra Combinada - {nombre}", lineas, "3")

    def pago_rentas_op(self, nombre: str, valor: float):
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        iva_renta = valor * self.iva_rate
        self.rentas_anticipadas += valor
        self.iva_acreditable += iva_renta
        self.caja -= (valor + iva_renta)
        self.recalcular_totales()
        
        # Libro Diario (Código 4)
        lineas = [
            ("Rentas Pagadas Anticipado", valor, 0.0),
            ("IVA Acreditable", iva_renta, 0.0),
            ("Caja", 0.0, valor + iva_renta)
        ]
        self.registrar_en_libro_diario(f"Pago Rentas - {nombre}", lineas, "4")

    def compra_papeleria_op(self, nombre: str, valor: float):
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        iva = valor * self.iva_rate
        self.activos_no_circulantes.append((f"Papelería - {nombre}", valor))
        self.iva_acreditable += iva
        self.caja -= (valor + iva)
        self.recalcular_totales()
        
        # Libro Diario (Código 5)
        lineas = [
            (f"Papelería - {nombre}", valor, 0.0),
            ("IVA Acreditable", iva, 0.0),
            ("Caja", 0.0, valor + iva)
        ]
        self.registrar_en_libro_diario(f"Compra Papelería - {nombre}", lineas, "5")
        
    def anticipo_clientes_op(self, nombre: str, venta: float):
        """
        Registra un anticipo de un cliente por la mitad del valor 'venta'.
        """
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        half_sale = venta / 2.0
        half_iva = half_sale * self.iva_rate
        self.caja += (half_sale + half_iva)
        # Guardamos dos renglones en la lista anticipo_clientes, uno para el anticipo y otro para el IVA
        self.anticipo_clientes.append((f"Anticipo de Clientes - {nombre}", half_sale))
        self.anticipo_clientes.append((f"IVA Trasladado - {nombre}", half_iva))
        self.recalcular_totales()
        
        # Libro Diario (Código 6)
        lineas = [
            ("Caja", half_sale + half_iva, 0.0),
            (f"Anticipo de Clientes - {nombre}", 0.0, half_sale),
            (f"IVA Trasladado - {nombre}", 0.0, half_iva),
        ]
        self.registrar_en_libro_diario(f"Anticipo de Clientes - {nombre}", lineas, "6")

    # ----------------------------------------------------------------
    # OPERACIONES (2a PARTE) 
    #   - Venta
    #   - Costo de lo Vendido
    #   - Gastos Generales
    #   - Anular Anticipo de Cliente
    #   - Depreciaciones
    # ----------------------------------------------------------------
    def registrar_venta(self, descripcion: str, monto: float):
        """
        Registra una venta (cobro completo en efectivo, por ejemplo).
        Se incrementa la caja y se reconoce 'Ventas' y 'IVA Trasladado'.
        """
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        iva_venta = monto * self.iva_rate
        self.caja += (monto + iva_venta)
        self.recalcular_totales()
        
        lineas = [
            ("Caja", monto + iva_venta, 0.0),
            ("Ventas", 0.0, monto),
            ("IVA Trasladado", 0.0, iva_venta)
        ]
        self.registrar_en_libro_diario(f"Venta - {descripcion}", lineas, "V")

    def registrar_costo_vendido(self, descripcion: str, costo: float):
        """
        Descarga el inventario y reconoce el Costo de lo Vendido.
        """
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        if costo > self.inventario:
            raise ValueError("No hay suficiente inventario para ese costo.")
        
        self.inventario -= costo
        self.recalcular_totales()
        
        lineas = [
            ("Costo de lo Vendido", costo, 0.0),
            ("Inventario", 0.0, costo)
        ]
        self.registrar_en_libro_diario(f"Costo de lo Vendido - {descripcion}", lineas, "CV")

    def registrar_gastos_generales(self, descripcion: str, monto: float):
        """
        Registra gastos generales (por ejemplo, pago de renta, servicios, etc.)
        sin anticipo. Se descuenta de caja.
        """
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        # Si hay IVA en el gasto, puedes dividir. Aquí lo hacemos sin IVA para simplificar.
        self.caja -= monto
        self.recalcular_totales()
        
        lineas = [
            ("Gastos Generales", monto, 0.0),
            ("Caja", 0.0, monto)
        ]
        self.registrar_en_libro_diario(f"Gastos Generales - {descripcion}", lineas, "G")

    def anular_anticipo_cliente(self, descripcion: str, monto: float):
        """
        Cuando recibes la otra parte de la venta (o quieres 'liberar' ese anticipo),
        lo conviertes en 'Ventas' y quitas el 'Anticipo de Clientes'.
        """
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        # Suponiendo que el anticipo fue la mitad, ahora registramos la otra mitad
        iva_venta = monto * self.iva_rate
        self.caja += (monto + iva_venta)
        self.recalcular_totales()

        # Debitar Anticipo, acreditar Ventas e IVA Trasladado
        lineas = [
            ("Caja", monto + iva_venta, 0.0),
            ("Anticipo de Clientes", monto, 0.0),     # Quitamos el anticipo
            ("IVA Trasladado", 0.0, iva_venta),
            ("Ventas", 0.0, monto)
        ]
        self.registrar_en_libro_diario(f"Anular anticipo - {descripcion}", lineas, "AA")
    
    def registrar_depreciacion(self, descripcion: str, dict_depreciaciones: dict):
        """
        dict_depreciaciones: un diccionario con las cuentas de Dep. Acum. y sus montos.
        Por ejemplo:
        {
          "Dep. Acum. De Departamento": 1000.0,
          "Dep. Acum. De Eq. Y Tecnologia": 2000.0,
          ...
        }
        Se registra la depreciación como un gasto (p.e. 'Gastos Generales' o 'Depreciación')
        y se abona a las cuentas de Dep. Acumulada correspondientes.
        """
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")

        total_dep = sum(dict_depreciaciones.values())
        # Cargo a Gastos Generales (o podrías usar otra cuenta "Gasto x Depreciación")
        lineas = [("Gastos Generales", total_dep, 0.0)]
        
        # Abono a cada Dep. Acumulada
        for cuenta_dep, valor in dict_depreciaciones.items():
            lineas.append((cuenta_dep, 0.0, valor))
        
        self.registrar_en_libro_diario(f"Depreciaciones - {descripcion}", lineas, "DEP")
        self.recalcular_totales()

    # --------------------------------------
    # MÉTODO PARA GENERAR EL BALANCE
    # --------------------------------------
    def generar_tabla_balance(self) -> str:
        anticipo_total = sum(monto for _, monto in self.anticipo_clientes)
        total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        
        tabla = f"{'ACTIVO':<45}{'PASIVO':<35}{'CAPITAL':<20}\n"
        tabla += "=" * 100 + "\n"
        
        # Activo Circulante
        tabla += "Activo Circulante:\n"
        tabla += f"  Caja: ${self.caja:,.2f}\n"
        if self.inventario:
            tabla += f"  Inventario: ${self.inventario:,.2f}\n"
        if self.iva_acreditable:
            tabla += f"  IVA Acreditable: ${self.iva_acreditable:,.2f}\n"
        if self.iva_por_acreditar:
            tabla += f"  IVA por Acreditar: ${self.iva_por_acreditar:,.2f}\n"
        if self.rentas_anticipadas:
            tabla += f"  Rentas Pagadas Anticipado: ${self.rentas_anticipadas:,.2f}\n"
        tabla += f"  Total Activo Circulante: ${self.total_circulante:,.2f}\n"
        
        # Activo No Circulante
        tabla += "\nActivo No Circulante:\n"
        if self.activos_no_circulantes:
            for nombre, valor in self.activos_no_circulantes:
                tabla += f"  {nombre}: ${valor:,.2f}\n"
        else:
            tabla += "  (Sin activos no circulantes)\n"
        tabla += f"  Total Activo No Circulante: ${total_no_circulante:,.2f}\n"
        
        # Pasivo
        tabla += "\nPASIVO:\n"
        tabla += f"  Acreedores: ${self.acreedores:,.2f}\n"
        tabla += f"  Documentos por Pagar: ${self.documentos_por_pagar:,.2f}\n"
        if self.anticipo_clientes:
            for nombre, monto in self.anticipo_clientes:
                tabla += f"  {nombre}: ${monto:,.2f}\n"
        tabla += "\n"
        
        # Totales y Capital
        tabla += "=" * 100 + "\n"
        tabla += f"Total Activo: ${self.total_activo:,.2f}\n"
        tabla += f"Total Pasivo: ${self.total_pasivo:,.2f}\n"
        tabla += f"Capital: ${self.capital:,.2f}\n"
        tabla += f"Total Pasivo + Capital: ${self.total_pasivo + self.capital:,.2f}\n"
        
        return tabla

    def generar_tabla_mayor(self) -> str:
        """
        Genera el reporte de cada cuenta en formato de 'T' (o tabla),
        mostrando fecha, código del asiento, descripción, Debe, Haber
        y el saldo final de cada cuenta.
        """
        if not self.ledger_accounts:
            return "No hay movimientos en las cuentas del Mayor. (Realiza primero el Asiento de Apertura)"
        
        texto = ""
        for cuenta, movimientos in self.ledger_accounts.items():
            texto += f"\nCUENTA: {cuenta}\n"
            texto += "Fecha       Cód  Descripción               Debe        Haber\n"
            texto += "-" * 66 + "\n"
            total_debe = 0.0
            total_haber = 0.0
            for mov in movimientos:
                fecha = mov["fecha"]
                code = mov["trans_code"]
                desc = mov["descripcion"]
                debe = mov["debe"]
                haber = mov["haber"]
                texto += (f"{fecha:<11} {code:<3} "
                          f"{desc[:20]:<20} "
                          f"{debe:>10.2f} "
                          f"{haber:>10.2f}\n")
                total_debe += debe
                total_haber += haber
            saldo = total_debe - total_haber
            texto += "-" * 66 + "\n"
            texto += (f"{'':<15}{'TOTAL':<20}"
                      f"{total_debe:>10.2f} "
                      f"{total_haber:>10.2f}   "
                      f"SALDO: {saldo:>.2f}\n\n")
        return texto

    # =======================
    # BALANZA DE COMPROBACIÓN
    # =======================
    def generar_balanza_comprobacion(self) -> str:
        """
        Genera la Balanza de Comprobación con cuatro columnas:
        - Debe total
        - Haber total
        - Debe (diferencia)
        - Haber (diferencia)
        para cada cuenta. 
        """
        if not self.ledger_accounts:
            return "No hay movimientos en las cuentas del Mayor. (Realiza primero el Asiento de Apertura)"

        lines = []
        lines.append("BALANZA DE COMPROBACIÓN".center(60))
        lines.append("")
        header = f"{'Cuenta':<30}{'Debe':>12}{'Haber':>12}{'Debe':>12}{'Haber':>12}"
        lines.append(header)
        lines.append("-" * len(header))

        sum_debe1 = 0.0
        sum_haber1 = 0.0
        sum_debe2 = 0.0
        sum_haber2 = 0.0

        # Recorremos cada cuenta para sumar
        for cuenta, movimientos in self.ledger_accounts.items():
            total_debe = sum(m["debe"] for m in movimientos)
            total_haber = sum(m["haber"] for m in movimientos)
            
            # Cálculo de la diferencia
            if total_debe > total_haber:
                diff_debe = total_debe - total_haber
                diff_haber = 0.0
            else:
                diff_debe = 0.0
                diff_haber = total_haber - total_debe
            
            sum_debe1 += total_debe
            sum_haber1 += total_haber
            sum_debe2 += diff_debe
            sum_haber2 += diff_haber

            line = (f"{cuenta:<30}"
                    f"{total_debe:>12,.2f}"
                    f"{total_haber:>12,.2f}"
                    f"{diff_debe:>12,.2f}"
                    f"{diff_haber:>12,.2f}")
            lines.append(line)

        lines.append("-" * len(header))
        total_line = (f"{'Totales':<30}"
                      f"{sum_debe1:>12,.2f}"
                      f"{sum_haber1:>12,.2f}"
                      f"{sum_debe2:>12,.2f}"
                      f"{sum_haber2:>12,.2f}")
        lines.append(total_line)

        return "\n".join(lines)

    # ===============================
    # Balance General
    # ===============================
    def generar_balance_general(self) -> str:
        """
        Suma Ventas, Costo de lo Vendido y Gastos Generales
        para calcular la Utilidad del periodo.
        """
        if not self.ledger_accounts:
            return "No hay datos para generar Balance General."

        total_ventas = 0.0
        total_costo = 0.0
        total_gastos = 0.0

        for cuenta, movimientos in self.ledger_accounts.items():
            # Suma de 'Ventas' (generalmente en el Haber)
            if "Ventas" in cuenta:
                total_ventas += sum(m["haber"] for m in movimientos)
            # Suma de 'Costo de lo Vendido' (generalmente en el Debe)
            if "Costo de lo Vendido" in cuenta:
                total_costo += sum(m["haber"] for m in movimientos)
            # Suma de 'Gastos Generales' (generalmente en el Debe)
            if "Gastos Generales" in cuenta:
                total_gastos += sum(m["debe"] for m in movimientos)

        utilidad_bruta = total_ventas - total_costo
        utilidad_neta = utilidad_bruta - total_gastos

        texto = "Balance General\n"
        texto += f"Ventas: ${total_ventas:,.2f}\n"
        texto += f"Costo de lo Vendido: ${total_costo:,.2f}\n"
        texto += f"Utilidad Bruta: ${utilidad_bruta:,.2f}\n"
        texto += f"Gastos Generales: ${total_gastos:,.2f}\n"
        texto += f"Utilidad del Periodo: ${utilidad_neta:,.2f}\n"
        return texto

    # ==========================================
    # ESTADO DE CAMBIOS EN EL CAPITAL CONTABLE
    # ==========================================
    def generar_estado_flujos_efectivo(self) -> str:
        # Calcular valores necesarios
        utilidad_ejercicio = self.calcular_utilidad()
        depreciacion_total = sum(sum(m['haber'] for m in movs) 
                            for cuenta, movs in self.ledger_accounts.items() 
                            if "Dep. Acum." in cuenta)
        
        # Calcular cambios en cuentas de operación
        cambio_clientes = sum(m['debe'] - m['haber'] 
                          for cuenta in self.ledger_accounts 
                          if "Clientes" in cuenta 
                          for m in self.ledger_accounts[cuenta])
        
        cambio_inventario = sum(m['debe'] - m['haber'] 
                            for m in self.ledger_accounts.get("Inventario", []))
        
        cambio_iva_acreditable = sum(m['debe'] - m['haber'] 
                                  for m in self.ledger_accounts.get("IVA Acreditable", []))
        
        cambio_iva_por_acreditar = sum(m['debe'] - m['haber'] 
                                    for m in self.ledger_accounts.get("IVA por Acreditar", []))
        
        cambio_proveedores = sum(m['haber'] - m['debe'] 
                           for m in self.ledger_accounts.get("Acreedores", []))
        
        # Calculos de impuestos
        isr = utilidad_ejercicio * 0.30
        ptu = utilidad_ejercicio * 0.10
        utilidad_despues_impuestos = utilidad_ejercicio - isr - ptu
        
        # Efectivo inicial/final
        caja_inicial = next((m['debe'] for m in self.ledger_accounts.get("Caja", []) 
                           if m['trans_code'] == "A"), 0.0)
        caja_final = self.caja
        
        texto = """
ESTADOS DE FLUJOS DE EFECTIVO                                
METODO INDIRECTO                                
    Actividades en Operación                            
                                
Sumar   Clientes             ${:>15,.2f}                    
Sumar   Almacén              ${:>15,.2f}                    
Sumar   IVA Acreditado       ${:>15,.2f}                    
Sumar   IVA por acreditar    ${:>15,.2f}    ${:>15,.2f}                
Restar  IVA Trasladado       ${:>15,.2f}                    
Restar  IVA por trasladar    ${:>15,.2f}                    
Restar  Proveedores          ${:>15,.2f}            
Restar  Provisiones de ISR   ${:>15,.2f}    30%    ${:>15,.2f}    ${:>15,.2f} 
Restar  Provision de PTU     ${:>15,.2f}    10%    ${:>15,.2f}    
Restar  Utilidad ejercicio   ${:>15,.2f}    ${:>15,.2f}                
                                
    Flujos netos del efectivo de actividades en operación    ${:>15,.2f}                
                                
                                
    Actividades de Inversion                            
                                
    Departamento               ${:>15,.2f}                    
    Equipo de computo y tecnologias ${:>15,.2f}                    
    Software                   ${:>15,.2f}                    
    Muebles y Enseres          ${:>15,.2f}                    
    Equipo de iluminacion      ${:>15,.2f}                    
                                
    Flujos netos del efectivo de inversion    ${:>15,.2f}                
                                
    Capital social             ${:>15,.2f}                    
    Acreedores diversos        ${:>15,.2f}                    
                                
    Flujos netos de efectivo de actividades de financiamiento    ${:>15,.2f}                
                                
    Incremento Neto de efectivo y equivalentes de efectivo                                
                                
    Efectivo al Final del periodo                                
    Caja               ${:>15,.2f}                    
    Efectivo al Principio del periodo                                
    Caja               ${:>15,.2f}                    
                                
    Efectivo al Principio del periodo                                
    Bancos                              
    Efectivo al Final del periodo       ${:>15,.2f}    ${:>15,.2f}    ${:>15,.2f}            
    Bancos                              
    Efectivo al final del periodo               ${:>15,.2f}                
                                
                                
METODO DIRECTO                                
Utlidad del ejercicio               ${:>15,.2f}                
Cargos a resultados que no implican utilizacion de efectivo                                
ISR                 ${:>15,.2f}                    
PTU                 ${:>15,.2f}                    
Acreedores          ${:>15,.2f}    ${:>15,.2f}                
Depreciaciones      ${:>15,.2f}                
Efectivo generado en la operación       ${:>15,.2f}                
Financiamiento y otras fuentes       ${:>15,.2f}                
Proveedores                 ${:>15,.2f}                
Suma de las fuentes de efectivo       ${:>15,.2f}                
    APLICACIÓN DE EFECTIVO                            
Almacén                 ${:>15,.2f}                
Clientes                ${:>15,.2f}                
IVA acreditable         ${:>15,.2f}                
IVA por acreditar       ${:>15,.2f}                
IVA trasladado          ${:>15,.2f}                
IVA por trasladar       ${:>15,.2f}    ${:>15,.2f}            
Activos no circulantes      ${:>15,.2f}                
Disminucion neta del efectivo      ${:>15,.2f}                
Saldo inicial de caja       ${:>15,.2f}                
Saldo final de caja                            
""".format(
    # Método Indirecto
    cambio_clientes,
    cambio_inventario,
    cambio_iva_acreditable,
    cambio_iva_por_acreditar,
    cambio_clientes + cambio_inventario + cambio_iva_acreditable + cambio_iva_por_acreditar,
    sum(m['haber'] for m in self.ledger_accounts.get("IVA Trasladado", [])),
    sum(m['haber'] for m in self.ledger_accounts.get("IVA por Trasladar", [])),
    cambio_proveedores,
    isr, isr, utilidad_despues_impuestos,
    ptu, ptu,
    utilidad_ejercicio,
    utilidad_ejercicio + depreciacion_total + cambio_proveedores - isr - ptu,
    # Actividades de Inversion
    sum(v for n, v in self.activos_no_circulantes if "Departamento" in n),
    sum(v for n, v in self.activos_no_circulantes if "Equipo de computo" in n),
    sum(v for n, v in self.activos_no_circulantes if "Software" in n),
    sum(v for n, v in self.activos_no_circulantes if "Muebles" in n),
    sum(v for n, v in self.activos_no_circulantes if "iluminacion" in n),
    sum(v for n, v in self.activos_no_circulantes),
    # Financiamiento
    -self.capital,
    -self.acreedores,
    -self.capital - self.acreedores,
    # Efectivo
    caja_final,
    caja_inicial,
    caja_inicial - caja_final, 0.0, caja_inicial - caja_final,
    caja_final - caja_inicial,
    # Método Directo
    utilidad_ejercicio,
    isr,
    ptu,
    cambio_proveedores, isr + ptu + cambio_proveedores,
    depreciacion_total,
    utilidad_ejercicio + isr + ptu + cambio_proveedores + depreciacion_total,
    0.0,
    0.0,
    utilidad_ejercicio + isr + ptu + cambio_proveedores + depreciacion_total,
    # Aplicación de Efectivo
    self.inventario,
    cambio_clientes,
    self.iva_acreditable,
    self.iva_por_acreditar,
    sum(m['haber'] for m in self.ledger_accounts.get("IVA Trasladado", [])),
    sum(m['haber'] for m in self.ledger_accounts.get("IVA por Trasladar", [])),
    self.inventario + cambio_clientes + self.iva_acreditable + self.iva_por_acreditar,
    sum(v for _, v in self.activos_no_circulantes),
    caja_inicial - caja_final,
    caja_inicial,
)

        return texto


# ========================
# INTERFAZ EN STREAMLIT
# ========================
def main():
    st.title("Aplicación Contable Básica")
    st.subheader("Empresa: Gameverse")
    
    if "apertura_data" not in st.session_state:
        st.session_state["apertura_data"] = AperturaData()
    data = st.session_state["apertura_data"]
    
    # Agregamos en el menú las operaciones de la 2a parte
    menu = st.sidebar.radio(
        "Seleccione una operación:",
        (
            "Asiento de Apertura",
            "Compra en Efectivo",
            "Compra a Crédito",
            "Compra Combinada",
            "Pago de Rentas Pagadas por Anticipado",
            "Compra de Papelería",
            "Anticipo de Clientes",
            "Venta",
            "Costo de lo Vendido",
            "Gastos Generales",
            "Anular Anticipo de Cliente",
            "Registrar Depreciaciones",
            "Mostrar Balance",
            "Mostrar Libro Diario",
            "Mostrar Tablas de Mayor",
            "Balanza de Comprobacion",
            "Mostrar Balance General",
            "Mostrar Estado de flujos"
        )
    )
    
    if menu == "Asiento de Apertura":
        mostrar_asiento_apertura(data)
    elif menu == "Compra en Efectivo":
        mostrar_compra_efectivo(data)
    elif menu == "Compra a Crédito":
        mostrar_compra_credito(data)
    elif menu == "Compra Combinada":
        mostrar_compra_combinada(data)
    elif menu == "Pago de Rentas Pagadas por Anticipado":
        mostrar_pago_rentas(data)
    elif menu == "Compra de Papelería":
        mostrar_compra_papeleria(data)
    elif menu == "Anticipo de Clientes":
        mostrar_anticipo_clientes(data)
    elif menu == "Venta":
        mostrar_venta(data)
    elif menu == "Costo de lo Vendido":
        mostrar_costo_vendido(data)
    elif menu == "Gastos Generales":
        mostrar_gastos_generales(data)
    elif menu == "Anular Anticipo de Cliente":
        mostrar_anular_anticipo(data)
    elif menu == "Registrar Depreciaciones":
        mostrar_depreciaciones(data)
    elif menu == "Mostrar Balance":
        st.subheader("Balance General")
        st.code(data.generar_tabla_balance())
    elif menu == "Mostrar Libro Diario":
        st.subheader("Libro Diario (Modo Oscuro)")
        st.code(data.generar_libro_diario())
    elif menu == "Mostrar Tablas de Mayor":
        st.subheader("Tablas de Mayor")
        st.code(data.generar_tabla_mayor())
    elif menu == "Balanza de Comprobacion":
        st.subheader("Balance de Comprobación")
        st.code(data.generar_balanza_comprobacion())
    elif menu == "Mostrar Balance General":
        st.subheader("Balance General")
        st.code(data.generar_balance_general())
    else:  # "Mostrar Estado de flujos"
        st.subheader("Estado de Flujos de Efectivo")
        st.code(data.generar_estado_flujos_efectivo())


# ============================
# FUNCIONES DE INTERFAZ (2a parte)
# ============================
def mostrar_venta(data: AperturaData):
    st.subheader("Registrar Venta")
    descripcion = st.text_input("Descripción de la Venta")
    monto = st.number_input("Monto de la Venta", min_value=0.0, step=1000.0)
    if st.button("Registrar Venta"):
        try:
            data.registrar_venta(descripcion, monto)
            st.success(f"Venta '{descripcion}' por ${monto:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))

def mostrar_costo_vendido(data: AperturaData):
    st.subheader("Registrar Costo de lo Vendido")
    descripcion = st.text_input("Descripción del Costo")
    costo = st.number_input("Costo de lo Vendido", min_value=0.0, step=1000.0)
    if st.button("Registrar Costo"):
        try:
            data.registrar_costo_vendido(descripcion, costo)
            st.success(f"Costo de lo Vendido '{descripcion}' por ${costo:,.2f} registrado.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))

def mostrar_gastos_generales(data: AperturaData):
    st.subheader("Registrar Gastos Generales")
    descripcion = st.text_input("Descripción del Gasto")
    monto = st.number_input("Monto del Gasto", min_value=0.0, step=1000.0)
    if st.button("Registrar Gasto General"):
        try:
            data.registrar_gastos_generales(descripcion, monto)
            st.success(f"Gasto '{descripcion}' por ${monto:,.2f} registrado.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))

def mostrar_anular_anticipo(data: AperturaData):
    st.subheader("Anular Anticipo de Cliente (Recibir la otra parte)")
    descripcion = st.text_input("Descripción de la Operación")
    monto = st.number_input("Monto de la Venta/Anticipo", min_value=0.0, step=1000.0)
    if st.button("Anular Anticipo"):
        try:
            data.anular_anticipo_cliente(descripcion, monto)
            st.success(f"Anticipo anulado por ${monto:,.2f}.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))

def mostrar_depreciaciones(data: AperturaData):
    st.subheader("Registrar Depreciaciones")
    st.write("Ingrese las depreciaciones de cada cuenta (Dejar en 0 si no aplica).")
    dep_departamento = st.number_input("Dep. Acum. De Departamento", min_value=0.0, step=1000.0)
    dep_tec = st.number_input("Dep. Acum. De Eq. Y Tecnologia", min_value=0.0, step=1000.0)
    dep_software = st.number_input("Dep. Acum. De Software para desarrollo", min_value=0.0, step=100.0)
    dep_muebles = st.number_input("Dep. Acum. De Muebles", min_value=0.0, step=1000.0)
    dep_ilum = st.number_input("Dep. Acum. De Eq. De Iluminacion", min_value=0.0, step=1000.0)
    descripcion = st.text_input("Descripción (Ejem: Depreciación Mensual)")

    if st.button("Registrar Depreciación"):
        try:
            dict_deps = {}
            if dep_departamento > 0:
                dict_deps["Dep. Acum. De Departamento"] = dep_departamento
            if dep_tec > 0:
                dict_deps["Dep. Acum. De Eq. Y Tecnologia"] = dep_tec
            if dep_software > 0:
                dict_deps["Dep. Acum. De Software para desarrollo"] = dep_software
            if dep_muebles > 0:
                dict_deps["Dep. Acum. De Muebles"] = dep_muebles
            if dep_ilum > 0:
                dict_deps["Dep. Acum. De Eq. De Iluminacion"] = dep_ilum
            
            if dict_deps:
                data.registrar_depreciacion(descripcion, dict_deps)
                st.success("Depreciaciones registradas correctamente.")
                st.code(data.generar_tabla_balance())
            else:
                st.info("No se ingresaron importes de depreciación.")
        except ValueError as e:
            st.warning(str(e))

# ========================
# FUNCIONES DE INTERFAZ (1a parte)
# ========================
def mostrar_asiento_apertura(data: AperturaData):
    st.subheader("Asiento de Apertura")
    if data.apertura_realizada:
        st.info("El asiento de apertura ya fue realizado.")
        st.code(data.generar_tabla_balance())
        return

    nuevo_monto = st.number_input("Ingrese el monto inicial de Caja (Activo Circulante):", 
                                  min_value=0.0, step=1000.0)
    if st.button("Actualizar Caja"):
        data.caja = nuevo_monto
        st.success("Monto de Caja actualizado.")

    st.write("### Agregar Activos No Circulantes (Compras Iniciales)")
    nombre_activo = st.text_input("Nombre del Activo No Circulante")
    valor_activo = st.number_input("Valor del Activo No Circulante", 
                                   min_value=0.0, step=1000.0, key="activo_inicial")
    if st.button("Agregar Activo No Circulante"):
        if nombre_activo.strip():
            data.activos_no_circulantes.append((nombre_activo, valor_activo))
            st.success(f"Activo '{nombre_activo}' agregado.")
        else:
            st.warning("Ingrese un nombre válido.")
    
    if data.activos_no_circulantes:
        st.write("**Activos No Circulantes Ingresados:**")
        for idx, (n, v) in enumerate(data.activos_no_circulantes, start=1):
            st.write(f"{idx}. {n}: ${v:,.2f}")
    
    if st.button("Finalizar Asiento de Apertura"):
        data.calcular_asiento_apertura()
        st.success("Asiento de Apertura finalizado.")
        st.code(data.generar_tabla_balance())


def mostrar_compra_efectivo(data: AperturaData):
    st.subheader("Compra en Efectivo")
    nombre = st.text_input("Nombre de la Compra en Efectivo")
    valor = st.number_input("Valor de la Compra", min_value=0.0, step=1000.0)
    if st.button("Agregar Compra en Efectivo"):
        try:
            data.compra_en_efectivo(nombre, valor)
            st.success(f"Compra '{nombre}' por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))

def mostrar_compra_credito(data: AperturaData):
    st.subheader("Compra a Crédito")
    nombre = st.text_input("Nombre de la Compra a Crédito")
    valor = st.number_input("Valor de la Compra a Crédito", min_value=0.0, step=1000.0)
    if st.button("Agregar Compra a Crédito"):
        try:
            data.compra_a_credito(nombre, valor)
            st.success(f"Compra a crédito '{nombre}' por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))

def mostrar_compra_combinada(data: AperturaData):
    st.subheader("Compra Combinada")
    nombre = st.text_input("Nombre de la Compra Combinada")
    valor = st.number_input("Valor de la Compra Combinada", min_value=0.0, step=1000.0)
    if st.button("Agregar Compra Combinada"):
        try:
            data.compra_combinada(nombre, valor)
            st.success(f"Compra combinada '{nombre}' por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))

def mostrar_anticipo_clientes(data: AperturaData):
    st.subheader("Anticipo de Clientes")
    nombre = st.text_input("Nombre de la Venta")
    venta = st.number_input("Monto de la Venta", min_value=0.0, step=1000.0)
    if st.button("Registrar Anticipo de Clientes"):
        try:
            data.anticipo_clientes_op(nombre, venta)
            st.success(f"Anticipo de clientes '{nombre}' con venta de ${venta:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))

def mostrar_compra_papeleria(data: AperturaData):
    st.subheader("Compra de Papelería")
    nombre = st.text_input("Nombre de la Compra de Papelería")
    valor = st.number_input("Valor de la Compra de Papelería", min_value=0.0, step=1000.0)
    if st.button("Registrar Compra de Papelería"):
        try:
            data.compra_papeleria_op(nombre, valor)
            st.success(f"Compra de papelería '{nombre}' por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))
            
def mostrar_pago_rentas(data: AperturaData):
    st.subheader("Pago de Rentas Pagadas por Anticipado")
    nombre = st.text_input("Descripción del Pago de Rentas")
    valor = st.number_input("Valor del Pago de Rentas", min_value=0.0, step=1000.0)
    if st.button("Registrar Pago de Rentas"):
        try:
            data.pago_rentas_op(nombre, valor)
            st.success(f"Pago de rentas '{nombre}' por ${valor:,.2f} registrado.")
            st.code(data.generar_tabla_balance())
        except ValueError as e:
            st.warning(str(e))


if __name__ == "__main__":
    main()
