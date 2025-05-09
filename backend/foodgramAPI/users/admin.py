from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Subscription
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    """Административная панель для модели пользователя"""
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = (
        'email', 
        'username',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'date_joined'
    )
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'avatar')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'is_staff',
                'is_active'
            )
        }),
    )

class SubscriptionAdmin(admin.ModelAdmin):
    """Административная панель для подписок"""
    list_display = (
        'id',
        'subscriber_email',
        'author_email',
        'created_at'
    )
    list_filter = ('created_at',)
    search_fields = (
        'subscriber__email',
        'subscriber__username',
        'author__email',
        'author__username'
    )
    raw_id_fields = ('subscriber', 'author')
    
    def subscriber_email(self, obj):
        return obj.subscriber.email
    subscriber_email.short_description = 'Подписчик'
    
    def author_email(self, obj):
        return obj.author.email
    author_email.short_description = 'Автор'

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
