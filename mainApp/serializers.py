from rest_framework import serializers

class TravelRequestSerializer(serializers.Serializer):
    age = serializers.IntegerField()
    group_type = serializers.CharField()
    group_numbers = serializers.IntegerField()
    budget_usd = serializers.FloatField()
    days = serializers.IntegerField()
    month = serializers.CharField()
    is_disabled = serializers.BooleanField(default=False)
