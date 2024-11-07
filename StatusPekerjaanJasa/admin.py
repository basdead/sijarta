from django.contrib import admin
from .models import JobStatus

@admin.register(JobStatus)
class JobStatusAdmin(admin.ModelAdmin):
    list_display = ('job', 'status', 'updated_at')
    list_filter = ('status',)
    search_fields = ('job__id_job', 'job__category__name')
