from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile
from admin_site import admin_site

class ProfileInline(admin.StackedInline):
    model = Profile
    fields = ('avatar', 'bio', 'birth_date', 'location', 'website', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    classes = ('collapse',)


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_location', 'is_staff')

    def get_location(self, obj):
        return obj.profile.location if hasattr(obj, 'profile') else '-'
    get_location.short_description = 'Місто'


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'birth_date', 'has_avatar', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'location', 'bio')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Користувач', {
            'fields': ('user',)
        }),
        ('Основна інформація', {
            'fields': ('avatar', 'bio', 'birth_date', 'location', 'website')
        }),
        ('Системна інформація', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_avatar(self, obj):
        return '✓' if obj.avatar else '✗'
    has_avatar.short_description = 'Аватар'


admin_site.register(Profile, ProfileAdmin)
admin_site.register(User, UserAdmin)