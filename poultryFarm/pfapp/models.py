from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    class DesignationChoices(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MANUFACTURE = 'manufacture', 'Manufacture'
        PLANT_OWNER = 'plant_owner', 'Plant Owner'

    designation = models.CharField(
        max_length=50,
        choices=DesignationChoices.choices,   # 👈 Fix here
        null=True,
        blank=True
    )
    reporting_manager = models.ForeignKey(
        'self',                   
        on_delete=models.SET_NULL,   
        null=True,
        blank=True,
        related_name='team_members'  
    )


    class Meta:
        db_table = 'auth_user'

class Plant(models.Model):
    plant_id = models.CharField(max_length=50, unique=True, editable=False)
    plant_name = models.CharField(max_length=255)
    plant_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # 👈 ForeignKey to User
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plant'

class Recipemain(models.Model):
    RecipeID = models.AutoField(primary_key=True)
    plant_id = models.IntegerField()
    
    Bin1SetWt = models.FloatField()
    Bin2SetWt = models.FloatField()
    Bin3SetWt = models.FloatField()
    Bin4SetWt = models.FloatField()
    Bin5SetWt = models.FloatField()
    Bin6SetWt = models.FloatField()
    Bin7SetWt = models.FloatField()
    Bin8SetWt = models.FloatField()
    Bin9SetWt = models.FloatField()
    Bin10SetWt = models.FloatField()
    Bin11SetWt = models.FloatField()
    Bin12SetWt = models.FloatField()
    Bin13SetWt = models.FloatField()
    Bin14SetWt = models.FloatField()
    Bin15SetWt = models.FloatField()
    Bin16SetWt = models.FloatField()
    
    Oil1SetWt = models.FloatField()
    Oil2SetWt = models.FloatField()
    
    MedSetWt = models.FloatField()
    MolassesSetWt = models.FloatField()
    
    Premix1Set = models.FloatField()
    Premix2Set = models.FloatField()
    
    recipename = models.CharField(max_length=255)
    
    Man1SetWt = models.FloatField()
    Man2SetWt = models.FloatField()
    Man3SetWt = models.FloatField()
    Man4SetWt = models.FloatField()
    Man5SetWt = models.FloatField()
    Man6SetWt = models.FloatField()
    Man7SetWt = models.FloatField()
    Man8SetWt = models.FloatField()
    Man9SetWt = models.FloatField()
    Man10SetWt = models.FloatField()
    Man11SetWt = models.FloatField()
    Man12SetWt = models.FloatField()

    class Meta:
        db_table = 'recipemain'        
        
        
class BatchData(models.Model):
    BatchID = models.IntegerField(primary_key=True)
    stdate = models.CharField(max_length=255)
    stTime = models.CharField(max_length=255)
    plant_id = models.IntegerField()
    RecipeID = models.IntegerField()
    RecipeName = models.CharField(max_length=255)
    BatchNum = models.IntegerField()
    TotalBatchNum = models.IntegerField()
    endTime = models.CharField(max_length=255)

    # Bins
    Bin1Act = models.FloatField()
    Bin2Act = models.FloatField()
    Bin3Act = models.FloatField()
    Bin4Act = models.FloatField()
    Bin5Act = models.FloatField()
    Bin6Act = models.FloatField()
    Bin7Act = models.FloatField()
    Bin8Act = models.FloatField()
    Bin9Act = models.FloatField()
    Bin10Act = models.FloatField()
    Bin11Act = models.FloatField()
    Bin12Act = models.FloatField()
    Bin13Act = models.FloatField()
    Bin14Act = models.FloatField()
    Bin15Act = models.FloatField()
    Bin16Act = models.FloatField()

    # Manual Weights
    ManWt1 = models.FloatField()
    ManWt2 = models.FloatField()
    ManWt3 = models.FloatField()
    ManWt4 = models.FloatField()
    ManWt5 = models.FloatField()
    ManWt6 = models.FloatField()
    ManWt7 = models.FloatField()
    ManWt8 = models.FloatField()
    ManWt9 = models.FloatField()
    ManWt10 = models.FloatField()
    ManWt11 = models.FloatField()
    ManWt12 = models.FloatField()
    ManWt13 = models.FloatField()
    ManWt14 = models.FloatField()
    ManWt15 = models.FloatField()
    ManWt16 = models.FloatField()

    # Others
    Oil1Act = models.FloatField()
    Oil2Act = models.FloatField()
    MedicineWt = models.FloatField()
    MolassesWt = models.FloatField()

    # Premixes (assuming you have them too)
    PremixWt1 = models.FloatField(null=True, blank=True)
    PremixWt2 = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'batchdata'        
        
class MotorData(models.Model):
    sdate = models.CharField(max_length=255)
    sTime = models.CharField(max_length=255)
    plant_id = models.IntegerField(primary_key=True)
    ScrewRPM = models.FloatField()
    hammercurrent = models.FloatField()
    rvfrpm = models.FloatField()
    pelletcurrent = models.FloatField()
    feederRPM = models.FloatField()

    class Meta:
        db_table = 'motordata'        