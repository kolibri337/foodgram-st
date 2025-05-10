# recipes/fields.py

from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import imghdr
import uuid


class ImageDataField(serializers.Field):
    """
    Поле для работы с изображениями в формате Base64
    """

    def to_representation(self, value):
        if not value:
            return None
        return value.url

    def to_internal_value(self, data):
        from django.core.files.uploadedfile import UploadedFile

        if isinstance(data, UploadedFile):
            return data

        if isinstance(data, str) and data.startswith('data:image'):
            header, imgstr = data.split(';base64,')
            ext = imghdr.what('', imgstr)
            if ext not in ('png', 'jpg', 'jpeg', 'gif'):
                raise serializers.ValidationError(
                    "Формат изображения не поддерживается")
            data = ContentFile(
                base64.b64decode(imgstr), name=f"{
                    uuid.uuid4()}.{ext}")
            return data

        raise serializers.ValidationError("Некорректный формат изображения")
