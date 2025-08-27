from django.contrib import admin
from django.utils.html import format_html
from rag_app.admin_site import admin_site
from .models import PaymentRecord, PaymentRefund


class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_email', 'amount_display', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__email', 'stripe_payment_intent_id', 'description']
    readonly_fields = ['created_at', 'updated_at', 'stripe_payment_intent_id']
    date_hierarchy = 'created_at'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = 'Amount'
    

class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment_id', 'amount', 'reason_short', 'created_at']
    list_filter = ['created_at']
    search_fields = ['payment__user__email', 'stripe_refund_id', 'reason']
    readonly_fields = ['created_at', 'stripe_refund_id']
    date_hierarchy = 'created_at'
    
    def reason_short(self, obj):
        return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Reason'


# Register models with custom admin site
admin_site.register(PaymentRecord, PaymentRecordAdmin)
admin_site.register(PaymentRefund, PaymentRefundAdmin)
