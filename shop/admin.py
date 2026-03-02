from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.urls import path
from django.utils import timezone

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import Category, Products, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'subtotal']
    
    def subtotal(self, obj):
        return f"₵{obj.subtotal:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'full_name', 'email', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'full_name', 'email', 'phone']
    readonly_fields = ['order_id', 'paystack_reference', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_id', 'status', 'paystack_reference')
        }),
        ('Customer Info', {
            'fields': ('full_name', 'email', 'phone', 'address')
        }),
        ('Payment', {
            'fields': ('total_amount',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Register your models here.
admin.site.register(Category)


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'product_code', 'category', 'product_price', 'wholesale_price', 'quantity_per_box', 'product_stock', 'wholesale_stock', 'is_new', 'image_thumbnail', 'has_video']
    list_filter = ['category', 'is_new']
    list_select_related = ['category']
    search_fields = ['product_name', 'product_code']
    readonly_fields = ['image_preview', 'video_preview']
    fields = ('category', 'product_name', 'product_code', 'is_new', 'product_price', 'wholesale_price', 'quantity_per_box', 'product_stock', 'wholesale_stock', 'product_image', 'image_preview', 'product_video', 'video_preview')
    change_list_template = 'admin/shop/products/change_list.html'

    # ── Custom URL for PDF download ──────────────────────────
    def get_urls(self):
        custom_urls = [
            path(
                'download-pdf/',
                self.admin_site.admin_view(self.download_products_pdf),
                name='shop_products_download_pdf',
            ),
        ]
        return custom_urls + super().get_urls()

    def download_products_pdf(self, request):
        """Generate a well-structured PDF of all products."""
        response = HttpResponse(content_type='application/pdf')
        now = timezone.localtime(timezone.now()).strftime('%Y-%m-%d_%H%M')
        response['Content-Disposition'] = f'attachment; filename="KONNECT_INC_Products_{now}.pdf"'

        doc = SimpleDocTemplate(
            response,
            pagesize=landscape(A4),
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=20 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        elements = []

        # ── Title ────────────────────────────────────────────
        title_style = ParagraphStyle(
            'PDFTitle',
            parent=styles['Title'],
            fontSize=20,
            spaceAfter=4,
            textColor=colors.HexColor('#002147'),
        )
        elements.append(Paragraph('KONNECT INC – Product Catalogue', title_style))

        subtitle_style = ParagraphStyle(
            'PDFSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            alignment=TA_CENTER,
            spaceAfter=16,
        )
        generated = timezone.localtime(timezone.now()).strftime('%B %d, %Y  %I:%M %p')
        elements.append(Paragraph(f'Generated on {generated}', subtitle_style))
        elements.append(Spacer(1, 6 * mm))

        # ── Styles for table cells ───────────────────────────
        cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10)
        header_style = ParagraphStyle(
            'Header', parent=styles['Normal'], fontSize=8, leading=10,
            textColor=colors.white, fontName='Helvetica-Bold',
        )
        category_style = ParagraphStyle(
            'CatHeader', parent=styles['Heading2'],
            fontSize=12, textColor=colors.HexColor('#002147'),
            spaceBefore=10, spaceAfter=6,
        )

        # ── Build a section per category ─────────────────────
        categories = Category.objects.prefetch_related('products_set').order_by('name')

        for cat in categories:
            products = cat.products_set.all().order_by('product_name')
            if not products.exists():
                continue

            elements.append(Paragraph(f'{cat.name}', category_style))

            # Table header
            header_row = [
                Paragraph('#', header_style),
                Paragraph('Product Name', header_style),
                Paragraph('Code', header_style),
                Paragraph('Retail Price', header_style),
                Paragraph('Wholesale Price', header_style),
                Paragraph('Qty/Box', header_style),
                Paragraph('Box Price', header_style),
                Paragraph('Retail Stock', header_style),
                Paragraph('Wholesale Stock', header_style),
                Paragraph('New?', header_style),
            ]
            data = [header_row]

            for idx, p in enumerate(products, start=1):
                ws_price = p.get_wholesale_price
                data.append([
                    Paragraph(str(idx), cell_style),
                    Paragraph(p.product_name, cell_style),
                    Paragraph(p.product_code or '—', cell_style),
                    Paragraph(f'GHS {p.product_price:,.2f}', cell_style),
                    Paragraph(f'GHS {ws_price:,.2f}', cell_style),
                    Paragraph(str(p.quantity_per_box), cell_style),
                    Paragraph(f'GHS {p.box_price:,.2f}', cell_style),
                    Paragraph(f'{p.product_stock} units', cell_style),
                    Paragraph(f'{p.wholesale_stock} boxes', cell_style),
                    Paragraph('Yes' if p.is_new else '', cell_style),
                ])

            col_widths = [22 * mm, 55 * mm, 25 * mm, 30 * mm, 32 * mm, 20 * mm, 30 * mm, 25 * mm, 30 * mm, 18 * mm]

            table = Table(data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002147')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                # Body rows
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (3, 0), (6, -1), 'RIGHT'),
                ('ALIGN', (7, 0), (8, -1), 'CENTER'),
                ('ALIGN', (9, 0), (9, -1), 'CENTER'),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 8 * mm))

        # ── Summary at the end ───────────────────────────────
        total = Products.objects.count()
        summary_style = ParagraphStyle(
            'Summary', parent=styles['Normal'], fontSize=9,
            textColor=colors.HexColor('#444444'), spaceAfter=4,
        )
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(f'<b>Total products:</b> {total}', summary_style))

        doc.build(elements)
        return response

    def image_preview(self, obj):
        """Large preview shown on the edit form."""
        if obj.product_image:
            url = obj.product_image.url
            return format_html(
                '<img src="{}" style="max-height:300px;max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15)" />',
                url
            )
        return 'No image uploaded yet'
    image_preview.short_description = 'Image Preview'

    def video_preview(self, obj):
        """Video preview shown on the edit form."""
        if obj.product_video:
            url = obj.product_video.url
            return format_html(
                '<video src="{}" controls style="max-height:300px;max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15)"></video>',
                url
            )
        return 'No video uploaded yet'
    video_preview.short_description = 'Video Preview'

    def image_thumbnail(self, obj):
        """Small thumbnail shown in the list view."""
        if obj.product_image:
            url = obj.product_image.url
            return format_html(
                '<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:4px" />',
                url
            )
        return '-'
    image_thumbnail.short_description = 'Image'

    def has_video(self, obj):
        """Show whether product has a video."""
        return bool(obj.product_video)
    has_video.boolean = True
    has_video.short_description = 'Video'

    class Media:
        js = ('admin/js/image_preview.js',)
