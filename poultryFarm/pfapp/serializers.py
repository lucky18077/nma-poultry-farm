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

    def __init__(self, *args, **kwargs):
        super(BatchDataSerializer, self).__init__(*args, **kwargs)
        optional_fields = [
            "Bin1SetWt", "Bin2SetWt", "Bin3SetWt", "Bin4SetWt", "Bin5SetWt",
            "Bin6SetWt", "Bin7SetWt", "Bin8SetWt", "Bin9SetWt", "Bin10SetWt",
            "Bin11SetWt", "Bin12SetWt", "Bin13SetWt", "Bin14SetWt", "Bin15SetWt",
            "Bin16SetWt", "Oil1SetWt", "Oil2SetWt", "MedSetWt", "MolassesSetWt",
            "Premix1Set", "Premix2Set", "recipename", "Man1SetWt", "Man2SetWt",
            "Man3SetWt", "Man4SetWt", "Man5SetWt", "Man6SetWt", "Man7SetWt",
            "Man8SetWt", "Man9SetWt", "Man10SetWt", "Man11SetWt", "Man12SetWt",
            "Man13SetWt", "Man14SetWt", "Man15SetWt", "Man16SetWt", "Man17SetWt",
            "Man18SetWt", "Man19SetWt", "Man20SetWt"
        ]

        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False

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