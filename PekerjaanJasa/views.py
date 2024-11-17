from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from .forms import FilterPesananForm
from .models import Job, JobCategory, JobSubcategory

# Menampilkan daftar pesanan berdasarkan filter kategori dan subkategori
def pekerjaan_jasa(request):
    form = FilterPesananForm(request.GET or None)
    pesanan_jasa = Job.objects.none()  # Defaultnya kosong
    
    if form.is_valid():
        kategori_jasa = form.cleaned_data['kategori_jasa']
        subkategori_jasa = form.cleaned_data['subkategori_jasa']
        
        # Filter pesanan berdasarkan kategori dan subkategori yang dipilih
        pesanan_jasa = Job.objects.filter(
            category=kategori_jasa,
            subcategory=subkategori_jasa,
            status='Mencari Pekerja Terdekat'
        )
    
    return render(request, 'pekerjaanjasa/pekerjaan_jasa.html', {'form': form, 'pesanan_jasa': pesanan_jasa})

# Mengubah status pesanan saat pekerja menekan tombol 'Kerjakan Pesanan'
def kerjakan_pesanan(request, pesanan_id):
    pesanan = Job.objects.get(id_job=pesanan_id)
    
    # Memperbarui status pesanan menjadi 'Menunggu Pekerja Terdekat'
    pesanan.status = 'Menunggu Pekerja Terdekat'
    pesanan.save()
    
    # Arahkan pengguna kembali ke daftar pesanan setelah pesanan dikerjakan
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
