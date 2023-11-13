from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Auction


# form for new user registration
class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# form for new auction creation
class CreateAuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['title', 'startingPrice', 'durationDays']
