from django import forms
from .models import JobCategory, JobSubcategory

class FilterPesananForm(forms.Form):
    kategori_jasa = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(),
        empty_label="Pilih Kategori",
        widget=forms.Select(attrs={'onchange': 'this.form.submit();'})
    )
    subkategori_jasa = forms.ModelChoiceField(
        queryset=JobSubcategory.objects.none(),  # Kosongkan dulu
        empty_label="Pilih Subkategori",
        widget=forms.Select()
    )

    class Meta:
        fields = ['kategori_jasa', 'subkategori_jasa']
