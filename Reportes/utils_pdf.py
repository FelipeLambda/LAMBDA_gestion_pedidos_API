from io import BytesIO
from datetime import datetime
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class FacturaPDFGenerator:

    def __init__(self, pedido):
        self.pedido = pedido
        self.buffer = BytesIO()
        self.pagesize = A4
        self.width, self.height = self.pagesize

    def _crear_encabezado(self):
        styles = getSampleStyleSheet()

        titulo_style = ParagraphStyle(
            'TituloFactura',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#366092'),
            alignment=TA_CENTER,
            spaceAfter=12
        )

        subtitulo_style = ParagraphStyle(
            'Subtitulo',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=20
        )

        elementos = []
        elementos.append(Paragraph('LAMBDA COMMERCE', titulo_style))
        elementos.append(Paragraph('Factura de Compra', subtitulo_style))
        elementos.append(Spacer(1, 0.2*inch))

        return elementos

    def _crear_info_factura(self):
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']

        info_data = [
            ['Número de Orden:', self.pedido.numero_orden],
            ['Fecha de Emisión:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Fecha de Pedido:', self.pedido.fecha_creacion.strftime('%d/%m/%Y')],
        ]

        if self.pedido.tipo_pago == 'DIFERIDO' and self.pedido.fecha_limite_pago:
            info_data.append(['Fecha Límite Pago:', self.pedido.fecha_limite_pago.strftime('%d/%m/%Y')])

        info_data.append(['Tipo de Pago:', self.pedido.get_tipo_pago_display()])

        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        return [info_table, Spacer(1, 0.3*inch)]

    def _crear_info_cliente(self):
        styles = getSampleStyleSheet()

        titulo_cliente = ParagraphStyle(
            'TituloCliente',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=8
        )

        elementos = []
        elementos.append(Paragraph('DATOS DEL CLIENTE', titulo_cliente))

        cliente_data = [
            ['Empresa:', self.pedido.empresa.nombre],
            ['NIT:', self.pedido.empresa.nit],
            ['Solicitante:', self.pedido.solicitante.nombre],
            ['Email:', self.pedido.solicitante.email],
            ['Cargo:', self.pedido.solicitante.cargo],
        ]

        cliente_table = Table(cliente_data, colWidths=[1.5*inch, 4*inch])
        cliente_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elementos.append(cliente_table)
        elementos.append(Spacer(1, 0.3*inch))

        return elementos

    def _crear_tabla_productos(self):
        styles = getSampleStyleSheet()

        titulo_productos = ParagraphStyle(
            'TituloProductos',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=12
        )

        elementos = []
        elementos.append(Paragraph('DETALLE DE PRODUCTOS', titulo_productos))

        headers = ['Producto', 'SKU', 'Cantidad', 'Precio Unit.', 'Subtotal']
        data = [headers]

        for detalle in self.pedido.detalles.filter(estado=True):
            data.append([
                detalle.producto.nombre,
                detalle.producto.sku,
                str(detalle.cantidad),
                f"${detalle.precio_unitario:,.2f}",
                f"${detalle.subtotal:,.2f}"
            ])

        productos_table = Table(data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        productos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))

        elementos.append(productos_table)
        elementos.append(Spacer(1, 0.2*inch))

        return elementos

    def _crear_totales(self):
        total_data = [
            ['TOTAL:', f"${self.pedido.total:,.2f}"]
        ]

        total_table = Table(total_data, colWidths=[5.5*inch, 1.2*inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#366092')),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#366092')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))

        return [total_table, Spacer(1, 0.3*inch)]

    def _crear_pie_pagina(self):
        styles = getSampleStyleSheet()

        nota_style = ParagraphStyle(
            'Nota',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=6
        )

        elementos = []
        elementos.append(Spacer(1, 0.5*inch))

        if self.pedido.observaciones:
            elementos.append(Paragraph(f'<b>Observaciones:</b> {self.pedido.observaciones}', styles['Normal']))
            elementos.append(Spacer(1, 0.2*inch))

        elementos.append(Paragraph('Gracias por su compra', nota_style))
        elementos.append(Paragraph('Lambda Commerce - Sistema de Gestión de Pedidos', nota_style))

        return elementos

    def generar(self, como_respuesta=True):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        story = []

        story.extend(self._crear_encabezado())
        story.extend(self._crear_info_factura())
        story.extend(self._crear_info_cliente())
        story.extend(self._crear_tabla_productos())
        story.extend(self._crear_totales())
        story.extend(self._crear_pie_pagina())

        doc.build(story)

        pdf_bytes = self.buffer.getvalue()
        self.buffer.seek(0)

        if como_respuesta:
            filename = f"Factura_{self.pedido.numero_orden}_{datetime.now().strftime('%Y%m%d')}.pdf"
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            return pdf_bytes


class ReportePDFGenerator:

    def __init__(self, titulo, headers, datos, orientacion='portrait'):
        self.titulo = titulo
        self.headers = headers
        self.datos = datos
        self.buffer = BytesIO()

        if orientacion == 'landscape':
            from reportlab.lib.pagesizes import landscape
            self.pagesize = landscape(A4)
        else:
            self.pagesize = A4

        self.width, self.height = self.pagesize

    def _crear_encabezado(self):
        styles = getSampleStyleSheet()

        titulo_style = ParagraphStyle(
            'TituloReporte',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#366092'),
            alignment=TA_CENTER,
            spaceAfter=8
        )

        subtitulo_style = ParagraphStyle(
            'SubtituloReporte',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=20
        )

        elementos = []
        elementos.append(Paragraph('LAMBDA COMMERCE', titulo_style))
        elementos.append(Paragraph(self.titulo, subtitulo_style))
        elementos.append(Paragraph(f'Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}', subtitulo_style))
        elementos.append(Spacer(1, 0.3*inch))

        return elementos

    def _crear_tabla_datos(self):
        data = [self.headers]
        data.extend(self.datos)

        num_columnas = len(self.headers)
        ancho_disponible = self.width - 1.5*inch
        ancho_columna = ancho_disponible / num_columnas

        col_widths = [ancho_columna] * num_columnas

        tabla = Table(data, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        return [tabla, Spacer(1, 0.3*inch)]

    def _crear_pie_pagina(self):
        styles = getSampleStyleSheet()

        nota_style = ParagraphStyle(
            'NotaReporte',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )

        elementos = []
        elementos.append(Spacer(1, 0.2*inch))
        elementos.append(Paragraph(f'Total de registros: {len(self.datos)}', nota_style))
        elementos.append(Paragraph('Lambda Commerce - Sistema de Gestión de Pedidos', nota_style))

        return elementos

    def generar(self):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        story = []
        story.extend(self._crear_encabezado())
        story.extend(self._crear_tabla_datos())
        story.extend(self._crear_pie_pagina())

        doc.build(story)

        pdf_bytes = self.buffer.getvalue()
        self.buffer.seek(0)

        filename = f"{self.titulo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
