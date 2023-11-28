from django.db import models

# Create your models here.
class Patient(models.Model):
    id = models.IntegerField(default=0, primary_key=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    birth_date = models.DateField()
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    

    def __str__(self):
        return self.name