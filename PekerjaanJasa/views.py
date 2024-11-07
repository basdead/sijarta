from django.shortcuts import render, redirect, get_object_or_404
from .models import Job

def pekerjaan_jasa_view(request):
    jobs = Job.objects.filter(status="Mencari Pekerja Terdekat")
    return render(request, 'pekerjaan_jasa.html', {'jobs': jobs})

def ambil_pekerjaan_view(request, job_id):
    job = get_object_or_404(Job, id_job=job_id)
    job.status = "Menunggu Pekerja Terdekat"
    job.save()
    return redirect('pekerjaan_jasa')