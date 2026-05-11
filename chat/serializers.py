from rest_framework import serializers

from .models import Formdata

class Formserializers(serializers.ModelSerializer):
    class Meta:
        model=Formdata
        fields='__all__'
