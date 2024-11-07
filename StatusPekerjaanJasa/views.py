from django.shortcuts import render, get_object_or_404, redirect
from .models import JobStatus

def status_pekerjaan_jasa_view(request):
    job_statuses = JobStatus.objects.filter(job__worker=request.user)
    return render(request, 'status_pekerjaan_jasa.html', {'job_statuses': job_statuses})

def update_status_pekerjaan_view(request, job_id):
    job_status = get_object_or_404(JobStatus, job__id_job=job_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        job_status.status = new_status
        job_status.save()
        return redirect('status_pekerjaan_jasa')
    return render(request, 'update_status_pekerjaan.html', {'job_status': job_status})