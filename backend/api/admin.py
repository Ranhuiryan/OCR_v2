from django.contrib import admin
from .models import OcrDocument
import json
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters.html import HtmlFormatter

@admin.register(OcrDocument)
class OcrDocumentAdmin(admin.ModelAdmin):
    """
    Admin view for OcrDocument to easily inspect and manage documents in the pipeline.
    This interface is ideal for developers and data managers.
    """
    list_display = ('id', 'get_filename', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('original_pdf_path', 'id')
    # --- 核心改动：修正了字段名 ---
    readonly_fields = ('id', 'created_at', 'original_pdf_path', 'mineru_json_path', 
                       'pretty_raw_ocr_json', 'pretty_corrected_label_studio_json')

    fieldsets = (
        (None, {
            'fields': ('id', 'status', 'created_at')
        }),
        ('File Paths (Read-only)', {
            'classes': ('collapse',),
            'fields': ('original_pdf_path', 'mineru_json_path')
        }),
        ('Stored JSON Data (Read-only)', {
            'classes': ('collapse',),
            # --- 核心改动：修正了字段名 ---
            'fields': ('pretty_raw_ocr_json', 'pretty_corrected_label_studio_json'),
        }),
    )

    def get_filename(self, obj):
        if obj.original_pdf_path:
            # Safely handle both Windows and Linux paths
            return os.path.basename(obj.original_pdf_path)
        return "N/A"
    get_filename.short_description = 'Original Filename'

    def _format_json(self, obj_json):
        """Helper to format and colorize JSON for the admin view."""
        if obj_json:
            formatted_json = json.dumps(obj_json, indent=2, ensure_ascii=False)
            formatter = HtmlFormatter(style='colorful')
            style = "<style>" + formatter.get_style_defs() + "</style>"
            highlighted_json = highlight(formatted_json, JsonLexer(), formatter)
            return mark_safe(style + highlighted_json)
        return "No data available."

    def pretty_raw_ocr_json(self, obj):
        return self._format_json(obj.raw_ocr_json)
    pretty_raw_ocr_json.short_description = 'Raw OCR JSON'

    # --- 核心改动：修正了整个方法 ---
    def pretty_corrected_label_studio_json(self, obj):
        return self._format_json(obj.corrected_label_studio_json)
    pretty_corrected_label_studio_json.short_description = 'Corrected Label Studio JSON'
