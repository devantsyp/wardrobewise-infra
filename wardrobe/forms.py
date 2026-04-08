from django import forms
from django.core.files.uploadedfile import UploadedFile

from wardrobe.models import CareAnalysis, Garment

INPUT_CLASSES = (
    'w-full px-4 py-3 rounded-lg border border-accent-500 '
    'focus:ring-2 focus:ring-primary-700 focus:border-transparent transition'
)

SELECT_CLASSES = (
    'w-full px-4 py-3 rounded-lg border border-accent-500 '
    'focus:ring-2 focus:ring-primary-700 focus:border-transparent transition'
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
        Only validates newly uploaded files — skips existing ImageFieldFile objects.
        Checks content type (JPG/PNG only) and file size (max 10 MB).
        """
        if isinstance(file, UploadedFile):
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


class CareLabelUploadForm(forms.Form):
    """Minimal form for uploading just the care label photo."""
    care_label_photo = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': FILE_INPUT_CLASSES,
            'accept': 'image/jpeg,image/png',
        })
    )

    def clean_care_label_photo(self):
        file = self.cleaned_data.get('care_label_photo')
        if isinstance(file, UploadedFile):
            allowed_types = ['image/jpeg', 'image/png']
            if file.content_type not in allowed_types:
                raise forms.ValidationError('Only JPG and PNG files are accepted.')
            max_size = 10 * 1024 * 1024  # 10 MB
            if file.size > max_size:
                raise forms.ValidationError('File size must not exceed 10 MB.')
        return file


class CareInstructionsForm(forms.ModelForm):
    class Meta:
        model = CareAnalysis
        fields = ['washing', 'drying', 'ironing', 'bleach', 'is_delicate', 'personal_notes']
        widgets = {
            'washing': forms.TextInput(attrs={
                'class': (
                    'w-full px-4 py-3 rounded-lg border border-accent-500 '
                    'focus:ring-2 focus:ring-primary-700 focus:border-transparent transition'
                ),
                'placeholder': 'e.g., Machine wash cold',
            }),
            'drying': forms.TextInput(attrs={
                'class': (
                    'w-full px-4 py-3 rounded-lg border border-accent-500 '
                    'focus:ring-2 focus:ring-primary-700 focus:border-transparent transition'
                ),
                'placeholder': 'e.g., Tumble dry low',
            }),
            'ironing': forms.TextInput(attrs={
                'class': (
                    'w-full px-4 py-3 rounded-lg border border-accent-500 '
                    'focus:ring-2 focus:ring-primary-700 focus:border-transparent transition'
                ),
                'placeholder': 'e.g., Iron on medium heat',
            }),
            'bleach': forms.TextInput(attrs={
                'class': (
                    'w-full px-4 py-3 rounded-lg border border-accent-500 '
                    'focus:ring-2 focus:ring-primary-700 focus:border-transparent transition'
                ),
                'placeholder': 'e.g., Do not bleach',
            }),
            'is_delicate': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-accent-500 text-primary-700 focus:ring-primary-700',
            }),
            'personal_notes': forms.Textarea(attrs={
                'class': (
                    'w-full px-4 py-3 rounded-lg border border-accent-500 '
                    'focus:ring-2 focus:ring-primary-700 focus:border-transparent transition'
                ),
                'rows': 3,
                'placeholder': 'Your personal care notes...',
            }),
        }
        labels = {
            'is_delicate': 'Delicate item',
            'personal_notes': 'Personal notes',
        }
