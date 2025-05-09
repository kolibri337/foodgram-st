from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """Форма создания пользователя для админки"""
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'username')

class CustomUserChangeForm(UserChangeForm):
    """Форма изменения пользователя для админки"""
    
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = '__all__'