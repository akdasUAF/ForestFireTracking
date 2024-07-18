from django import forms

class DemoForm(forms.Form):
    SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]
    size = forms.ChoiceField(choices=SIZE_CHOICES, label='Model Size')
    model_type = forms.ChoiceField(choices=[], label='Model Type')
    input_file = forms.FileField(label='Upload Image or Video')
    conf = forms.ChoiceField(choices=[('0.1', '0.1'), ('0.2', '0.2'), ('0.4', '0.4')])

class model_compare_form(forms.Form):
    SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]
    size = forms.ChoiceField(choices=SIZE_CHOICES, label='Model Size')
    input_file = forms.FileField(label='Upload Image or Video')