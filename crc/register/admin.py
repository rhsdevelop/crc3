from django.contrib import admin

from .models import Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros

# Register your models here.
admin.site.register(Cong)
admin.site.register(CongUser)
admin.site.register(Drive)
admin.site.register(Grupos)
admin.site.register(Publicadores)
admin.site.register(Pioneiros)