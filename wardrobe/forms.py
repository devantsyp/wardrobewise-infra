from django import forms

from wardrobe.models import Garment

INPUT_CLASSES = (
    'w-full px-4 py-3 rounded-lg border border-gray-300 '
    'focus:ring-2 focus:ring-dark-teal-500 focus:border-transparent transition'
)

SELECT_CLASSES = (
    'w-full px-4 py-3 rounded-lg border border-gray-300 '
    'focus:ring-2 focus:ring-dark-teal-500 focus:border-transparent transition'
)

FILE_INPUT_CLASSES = 'hidden'


class GarmentForm(forms.ModelForm):
    class Meta:
        model = Garment
        fields = [
            'name',
            'category',
            'color',
            'fabric',
            'notes',
            'garment_photo',
            'care_label_photo',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'e.g., Blue Oxford Shirt',
            }),
            'category': forms.Select(attrs={
                'class': SELECT_CLASSES,
            }),
            'color': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'e.g., Navy blue',
            }),
            'fabric': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'e.g., 100% cotton',
            }),
            'notes': forms.Textarea(attrs={
                'class': INPUT_CLASSES,
                'rows': 3,
                'placeholder': 'Any special care notes...',
            }),
            'garment_photo': forms.ClearableFileInput(attrs={
                'class': FILE_INPUT_CLASSES,
                'accept': 'image/jpeg,image/png',
            }),
            'care_label_photo': forms.ClearableFileInput(attrs={
                'class': FILE_INPUT_CLASSES,
                'accept': 'image/jpeg,image/png',
            }),
        }

    def _validate_image(self, file, field_name):
        """
        Shared validation for image uploads.
        Checks content type (JPG/PNG only) and file size (max 10 MB).
        """
        if file:
            allowed_types = ['image/jpeg', 'image/png']
            if file.content_type not in allowed_types:
                raise forms.ValidationError('Only JPG and PNG files are accepted.')
            max_size = 10 * 1024 * 1024  # 10 MB
            if file.size > max_size:
                raise forms.ValidationError('File size must not exceed 10 MB.')
        return file

    def clean_garment_photo(self):
        file = self.cleaned_data.get('garment_photo')
        return self._validate_image(file, 'garment_photo')

    def clean_care_label_photo(self):
        file = self.cleaned_data.get('care_label_photo')
        return self._validate_image(file, 'care_label_photo')
