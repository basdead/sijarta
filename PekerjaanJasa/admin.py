# from django.contrib import admin
# from .models import JobCategory, Job

# @admin.register(JobCategory)
# class JobCategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description')
#     search_fields = ('name',)

# @admin.register(Job)
# class JobAdmin(admin.ModelAdmin):
#     list_display = ('id_job', 'category', 'subcategory', 'guest', 'status')  # 'room' dihapus
#     list_filter = ('category', 'status')
#     search_fields = ('id_job', 'guest__name', 'category__name')  # Pastikan atribut Guest adalah 'name'
