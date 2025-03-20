import streamlit as st
from datetime import datetime

# ==========================
# LÓGICA CONTABLE (Dominio)
# ==========================
class AperturaData:
    """
    Maneja la información contable y las operaciones:
      - Asiento de Apertura
      - Compra en Efectivo
      - Compra a Crédito
      - Compra Combinada
      - Pago de Rentas Pagadas por Anticipado
      - Compra de Papelería
      - Anticipo de Clientes
      - Venta (pago completo del cliente)
      + Libro Diario (registro automático de cada asiento)
      + Tablas de Mayor (un 'T-account' para cada cuenta).
      + Balance de Comprobación (nuevo).
    """
    def __init__(self):
        # Nombre de la empresa
        self.company_name = "Mi Empresa"
        self.apertura_realizada = False
        
        # Tasa de IVA
        self.iva_rate = 0.16
        
        # Cuentas de Activo (fijas, Activo Circulante)
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
        self.anticipo_clientes = []
        
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
    # OPERACIONES
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
        
        # Libro Diario (Código 6)
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
        if not self.apertura_realizada:
            raise ValueError("Debe realizar primero el Asiento de Apertura.")
        
        half_sale = venta / 2.0
        half_iva = half_sale * self.iva_rate
        self.caja += (half_sale + half_iva)
        self.anticipo_clientes.append((f"Anticipo de Clientes - {nombre}", half_sale))
        self.anticipo_clientes.append((f"IVA Trasladado - {nombre}", half_iva))
        self.recalcular_totales()
        
        # Libro Diario (Código 4)
        lineas = [
            ("Caja", half_sale + half_iva, 0.0),
            (f"Anticipo de Clientes - {nombre}", 0.0, half_sale),
            (f"IVA Trasladado - {nombre}", 0.0, half_iva),
        ]
        self.registrar_en_libro_diario(f"Anticipo de Clientes - {nombre}", lineas, "6")



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
    # BALANCE DE COMPROBACIÓN
    # =======================
    def generar_balance_comprobacion(self) -> str:
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
        lines.append("BALANCE DE COMPROBACIÓN".center(60))
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


# ========================
# INTERFAZ EN STREAMLIT
# ========================
def main():
    st.title("Aplicación Contable Básica")
    st.subheader("Empresa: Mi Empresa")
    
    if "apertura_data" not in st.session_state:
        st.session_state["apertura_data"] = AperturaData()
    data = st.session_state["apertura_data"]
    
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
            "Mostrar Balance",
            "Mostrar Libro Diario",
            "Mostrar Tablas de Mayor",
            "Balance de Comprobacion"
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
    elif menu == "Mostrar Balance":
        st.subheader("Balance General")
        st.code(data.generar_tabla_balance())
    elif menu == "Mostrar Libro Diario":
        st.subheader("Libro Diario (Modo Oscuro)")
        st.code(data.generar_libro_diario())
    elif menu == "Mostrar Tablas de Mayor":
        st.subheader("Tablas de Mayor")
        st.code(data.generar_tabla_mayor())
    else:  # Balance de Comprobacion
        st.subheader("Balance de Comprobación")
        st.code(data.generar_balance_comprobacion())


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
