from rest_framework import serializers


class DetalleBaseSerializer(serializers.ModelSerializer):
    """Serializer base para detalles de Solicitud y Pedido con validaciones comunes"""

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value
