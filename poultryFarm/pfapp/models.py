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
    plant_key = models.CharField(max_length=255)
    plant_status = models.IntegerField(max_length=2)
    shiftA = models.TimeField(null=True, blank=True)
    shiftB = models.TimeField(null=True, blank=True)
    shiftC = models.TimeField(null=True, blank=True)
    profile_image = models.CharField(max_length=255, null=True, blank=True)
    plant_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # 👈 ForeignKey to User
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plant'

class Recipemain(models.Model):
    RecipeID = models.IntegerField(primary_key=True)
    plant_id = models.IntegerField()
    
    Bin1SetWt = models.FloatField(null=True, blank=True)
    Bin2SetWt = models.FloatField(null=True, blank=True)
    Bin3SetWt = models.FloatField(null=True, blank=True)
    Bin4SetWt = models.FloatField(null=True, blank=True)
    Bin5SetWt = models.FloatField(null=True, blank=True)
    Bin6SetWt = models.FloatField(null=True, blank=True)
    Bin7SetWt = models.FloatField(null=True, blank=True)
    Bin8SetWt = models.FloatField(null=True, blank=True)
    Bin9SetWt = models.FloatField(null=True, blank=True)
    Bin10SetWt = models.FloatField(null=True, blank=True)
    Bin11SetWt = models.FloatField(null=True, blank=True)
    Bin12SetWt = models.FloatField(null=True, blank=True)
    Bin13SetWt = models.FloatField(null=True, blank=True)
    Bin14SetWt = models.FloatField(null=True, blank=True)
    Bin15SetWt = models.FloatField(null=True, blank=True)
    Bin16SetWt = models.FloatField(null=True, blank=True)
    
    Oil1SetWt = models.FloatField(null=True, blank=True)
    Oil2SetWt = models.FloatField(null=True, blank=True)
    
    MedSetWt = models.FloatField(null=True, blank=True)
    MolassesSetWt = models.FloatField(null=True, blank=True)
    
    Premix1Set = models.FloatField(null=True, blank=True)
    Premix2Set = models.FloatField(null=True, blank=True)
    
    recipename = models.CharField(max_length=255,null=True, blank=True)
    
    Man1SetWt = models.FloatField(null=True, blank=True)
    Man2SetWt = models.FloatField(null=True, blank=True)
    Man3SetWt = models.FloatField(null=True, blank=True)
    Man4SetWt = models.FloatField(null=True, blank=True)
    Man5SetWt = models.FloatField(null=True, blank=True)
    Man6SetWt = models.FloatField(null=True, blank=True)
    Man7SetWt = models.FloatField(null=True, blank=True)
    Man8SetWt = models.FloatField(null=True, blank=True)
    Man9SetWt = models.FloatField(null=True, blank=True)
    Man10SetWt = models.FloatField(null=True, blank=True)
    Man11SetWt = models.FloatField(null=True, blank=True)
    Man12SetWt = models.FloatField(null=True, blank=True)
    Man13SetWt = models.FloatField(null=True, blank=True)
    Man14SetWt = models.FloatField(null=True, blank=True)
    Man15SetWt = models.FloatField(null=True, blank=True)
    Man16SetWt = models.FloatField(null=True, blank=True)
    Man17SetWt = models.FloatField(null=True, blank=True)
    Man18SetWt = models.FloatField(null=True, blank=True)
    Man19SetWt = models.FloatField(null=True, blank=True)
    Man20SetWt = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'recipemain'        
        
        
class BatchData(models.Model):
    BatchID = models.IntegerField(primary_key=True)
    stdate = models.CharField(max_length=255,null=True, blank=True)
    stTime = models.CharField(max_length=255,null=True, blank=True)
    plant_id = models.IntegerField()
    RecipeID = models.IntegerField(null=True, blank=True)
    RecipeName = models.CharField(max_length=255,null=True, blank=True)
    BatchNum = models.IntegerField(null=True, blank=True)
    TotalBatchNum = models.IntegerField(null=True, blank=True)
    endTime = models.CharField(max_length=255,null=True, blank=True)

    # Bins
    Bin1Act = models.FloatField(null=True, blank=True)
    Bin2Act = models.FloatField(null=True, blank=True)
    Bin3Act = models.FloatField(null=True, blank=True)
    Bin4Act = models.FloatField(null=True, blank=True)
    Bin5Act = models.FloatField(null=True, blank=True)
    Bin6Act = models.FloatField(null=True, blank=True)
    Bin7Act = models.FloatField(null=True, blank=True)
    Bin8Act = models.FloatField(null=True, blank=True)
    Bin9Act = models.FloatField(null=True, blank=True)
    Bin10Act = models.FloatField(null=True, blank=True)
    Bin11Act = models.FloatField(null=True, blank=True)
    Bin12Act = models.FloatField(null=True, blank=True)
    Bin13Act = models.FloatField(null=True, blank=True)
    Bin14Act = models.FloatField(null=True, blank=True)
    Bin15Act = models.FloatField(null=True, blank=True)
    Bin16Act = models.FloatField(null=True, blank=True)

    # Manual Weights
    ManWt1 = models.FloatField(null=True, blank=True)
    ManWt2 = models.FloatField(null=True, blank=True)
    ManWt3 = models.FloatField(null=True, blank=True)
    ManWt4 = models.FloatField(null=True, blank=True)
    ManWt5 = models.FloatField(null=True, blank=True)
    ManWt6 = models.FloatField(null=True, blank=True)
    ManWt7 = models.FloatField(null=True, blank=True)
    ManWt8 = models.FloatField(null=True, blank=True)
    ManWt9 = models.FloatField(null=True, blank=True)
    ManWt10 = models.FloatField(null=True, blank=True)
    ManWt11 = models.FloatField(null=True, blank=True)
    ManWt12 = models.FloatField(null=True, blank=True)
    ManWt13 = models.FloatField(null=True, blank=True)
    ManWt14 = models.FloatField(null=True, blank=True)
    ManWt15 = models.FloatField(null=True, blank=True)
    ManWt16 = models.FloatField(null=True, blank=True)

    # Others
    Oil1Act = models.FloatField(null=True, blank=True)
    Oil2Act = models.FloatField(null=True, blank=True)
    MedicineWt = models.FloatField(null=True, blank=True)
    MolassesWt = models.FloatField(null=True, blank=True)

    # Premixes (assuming you have them too)
    PremixWt1 = models.FloatField(null=True, blank=True)
    PremixWt2 = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'batchdata'        
        
class MotorData(models.Model):
    sdate = models.CharField(max_length=255,null=True, blank=True)
    sTime = models.CharField(max_length=255,null=True, blank=True)
    plant_id = models.IntegerField()
    motorID = models.IntegerField(primary_key=True)
    ScrewRPM = models.FloatField(null=True, blank=True)
    hammercurrent = models.FloatField(null=True, blank=True)
    rvfrpm = models.FloatField(null=True, blank=True)
    pelletcurrent = models.FloatField(null=True, blank=True)
    feederRPM = models.FloatField(null=True, blank=True)
    hygenizerRPM = models.FloatField(null=True, blank=True)
    crumblerfeederRPM = models.FloatField(null=True, blank=True)
    molassesRPM = models.FloatField(null=True, blank=True)
    blowerRPM = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'motordata'    
        
class MaterialName(models.Model): 
    MatID = models.IntegerField() 
    plant_id = models.IntegerField()  
    MatName = models.CharField(primary_key=True, max_length=255)    
    class Meta:
        db_table = 'materialname'
        
class BinName(models.Model):
    recipeID = models.IntegerField(primary_key=True)  # Corresponds to the integer type (int)
    plant_id = models.IntegerField()
    bin1 = models.FloatField(max_length=255, blank=True, null=True)  # Corresponds to double type (float)
    bin2 = models.FloatField(max_length=255, blank=True, null=True)
    bin3 = models.FloatField(max_length=255, blank=True, null=True)
    bin4 = models.FloatField(max_length=255, blank=True, null=True)
    bin5 = models.FloatField(max_length=255, blank=True, null=True)
    bin6 = models.FloatField(max_length=255, blank=True, null=True)
    bin7 = models.FloatField(max_length=255, blank=True, null=True)
    bin8 = models.FloatField(max_length=255, blank=True, null=True)
    bin9 = models.FloatField(max_length=255, blank=True, null=True)
    bin10 = models.FloatField(max_length=255, blank=True, null=True)
    bin11 = models.FloatField(max_length=255, blank=True, null=True)
    bin12 = models.FloatField(max_length=255, blank=True, null=True)
    bin13 = models.FloatField(max_length=255, blank=True, null=True)
    bin14 = models.FloatField(max_length=255, blank=True, null=True)
    bin15 = models.FloatField(max_length=255, blank=True, null=True)
    bin16 = models.FloatField(max_length=255, blank=True, null=True)
    
    man1 = models.FloatField(max_length=255, blank=True, null=True)
    man2 = models.FloatField(max_length=255, blank=True, null=True)
    man3 = models.FloatField(max_length=255, blank=True, null=True)
    man4 = models.FloatField(max_length=255, blank=True, null=True)
    man5 = models.FloatField(max_length=255, blank=True, null=True)
    man6 = models.FloatField(max_length=255, blank=True, null=True)
    man7 = models.FloatField(max_length=255, blank=True, null=True)
    man8 = models.FloatField(max_length=255, blank=True, null=True)
    man9 = models.FloatField(max_length=255, blank=True, null=True)
    man10 = models.FloatField(max_length=255, blank=True, null=True)
    man11 = models.FloatField(max_length=255, blank=True, null=True)
    man12 = models.FloatField(max_length=255, blank=True, null=True)
    man13 = models.FloatField(max_length=255, blank=True, null=True)
    man14 = models.FloatField(max_length=255, blank=True, null=True)
    man15 = models.FloatField(max_length=255, blank=True, null=True)
    man16 = models.FloatField(max_length=255, blank=True, null=True)
    man17 = models.FloatField(max_length=255, blank=True, null=True)
    man18 = models.FloatField(max_length=255, blank=True, null=True)
    man19 = models.FloatField(max_length=255, blank=True, null=True)
    man20 = models.FloatField(max_length=255, blank=True, null=True)
    
    oil1 = models.FloatField(max_length=255, blank=True, null=True)
    oil2 = models.FloatField(max_length=255, blank=True, null=True)
    
    medicine = models.FloatField(max_length=255, blank=True, null=True)
    premix1 = models.FloatField(max_length=255, blank=True, null=True)
    premix2 = models.FloatField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'binname'   
        
class BagData(models.Model):
    sdate = models.CharField(max_length=255, blank=True, null=True)   
    bagID = models.IntegerField(primary_key=True) 
    sTime = models.CharField(max_length=255,blank=True, null=True) 
    plant_id = models.IntegerField()
    bagcount = models.IntegerField(blank=True, null=True)
    bagWT = models.FloatField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'bagdata'                       