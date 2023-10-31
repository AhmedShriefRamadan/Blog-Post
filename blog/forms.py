from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, UserChangeForm
from django.contrib.postgres.forms import SimpleArrayField

from .models import Comment,Category,CompanyProfile,UserProfile

class unUniqueCharField (forms.CharField):
    def validate(self, value):
        pass

class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False,
                            widget=forms.Textarea)
    

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name','email','body']

        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.TextInput(attrs={'class':'form-control'}),
            'body': forms.Textarea(attrs={'class':'form-control'}),
        }

class SearchForm(forms.Form):
    query = forms.CharField(label='',widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Search'}))


class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first = unUniqueCharField(max_length=50)
    last = unUniqueCharField(max_length=50)

    class Meta:
        model = User
        fields = ['first', 'last', 'username',  'email', 'password1',
                'password2', 'is_staff', 'is_superuser']


class AddCategory(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name','image')
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class':'form-control'})
        }


class CompanyRegistration (forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ('company_name','description','contact1','contact2')
        labels = {
            'contact1':'Phone Contact',
            'contact2':'Other Phone Contact',
        }


class EditUserProfile(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('image','badge','link1','link2')
        labels = {
            'link1': 'Social Link',
            'link2': 'Other Social Link',
        }


class ChangeForm (forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))