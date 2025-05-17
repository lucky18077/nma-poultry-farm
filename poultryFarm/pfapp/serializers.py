from rest_framework import serializers
from .models import Plant, Recipemain, BatchData, MotorData, MaterialName, BinName, User
 

class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'

class RecipemainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipemain
        fields = '__all__'

class BatchDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchData
        fields = '__all__'

class MotorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotorData
        fields = '__all__'

class MaterialNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialName
        fields = '__all__'

class BinNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = BinName
        fields = '__all__'