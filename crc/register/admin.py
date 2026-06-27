from django.contrib import admin

from .models import ComissaoServico, Cong, CongUser, Drive, Grupos, Publicadores, Pioneiros

# Register your models here.
admin.site.register(Cong)
admin.site.register(CongUser)
admin.site.register(Drive)
admin.site.register(Grupos)
admin.site.register(ComissaoServico)
admin.site.register(Publicadores)
admin.site.register(Pioneiros)
