import re
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

def validate_user_identifier(value):
    """Проверка корректности имени пользователя"""
    if not isinstance(value, str):
        raise ValidationError('Имя пользователя должно быть строкой')
    
    if len(value) < 3:
        raise ValidationError('Слишком короткое имя пользователя (мин. 3 символа)')
    
    if value.lower() == 'me':
        raise ValidationError('Запрещено использовать "me" как имя пользователя')
    
    if not re.fullmatch(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            'Имя пользователя может содержать только буквы, цифры и @/./+/-/_'
        )

def validate_credential_strength(value):
    """Проверка сложности учетных данных"""
    try:
        validate_password(value)
    except ValidationError as errors:
        raise serializers.ValidationError(
            {'password': list(errors.messages)}
        )
