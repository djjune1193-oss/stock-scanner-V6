from django.db import models

# Create your models here.


from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
