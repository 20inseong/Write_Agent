from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.contrib.auth.models import User
from .models import BetaCode

class CustomUserCreationForm(UserCreationForm):
    beta_code = forms.CharField(
        max_length=50, 
        required=True, 
        label='베타 추천 코드',
        widget=forms.TextInput(attrs={'placeholder': '발급받은 코드를 입력하세요'})
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        labels = {
            'username': '아이디',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 mt-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200',
            })
            
    # 코드가 존재하는지, 이미 사용됐는지 확실하게 검증하고 튕겨내는 로직
    def clean_beta_code(self):
        code_str = self.cleaned_data.get('beta_code')
        try:
            beta_obj = BetaCode.objects.get(code=code_str)
            if beta_obj.is_used:
                raise forms.ValidationError("이미 사용된 추천 코드입니다.")
            return beta_obj  # 통과하면 뷰(View)에서 바로 처리하기 편하도록 텍스트가 아닌 객체 자체를 넘겨줌
        except BetaCode.DoesNotExist:
            raise forms.ValidationError("존재하지 않거나 잘못된 추천 코드입니다.")


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 mt-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors duration-200',
            })