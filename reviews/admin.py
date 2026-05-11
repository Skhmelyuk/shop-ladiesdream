from django.contrib import admin
from .models import Review, ReviewReply
from admin_site import admin_site

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'author', 'rating', 'title_preview', 'created_at', 'is_active', 'helpful_count')
    list_editable = ('is_active',) 
    
    list_filter = ('rating', 'is_active', 'created_at')
    search_fields = ('author__username', 'product__name', 'title', 'content') 
    readonly_fields = ('created_at', 'updated_at', 'helpful_count')
    
    fieldsets = (
        (None, {
            'fields': (('product', 'author'), 'rating', ('is_active', 'helpful_count'))
        }),
        ('Текст відгуку', {
            'fields': ('title', 'content', 'advantages', 'disadvantages')
        }),
        ('Дати', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def title_preview(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_preview.short_description = 'Заголовок'

    @admin.action(description='Активувати вибрані відгуки')
    def activate_reviews(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} відгуків успішно активовано.")

    @admin.action(description='Деактивувати вибрані відгуки')
    def deactivate_reviews(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} відгуків успішно деактивовано.")
    
    actions = [activate_reviews, deactivate_reviews]


admin_site.register(Review, ReviewAdmin)


class ReviewReplyAdmin(admin.ModelAdmin):
    list_display = ('review', 'author', 'created_at', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('author__username', 'review__product__name', 'content')
    readonly_fields = ('created_at', 'updated_at')


admin_site.register(ReviewReply, ReviewReplyAdmin)