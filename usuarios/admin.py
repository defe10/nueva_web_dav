from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

# ✅ Si ya estaba registrado (por Django u otro admin), lo sacamos
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("es_jurado",)
    list_filter = UserAdmin.list_filter + ("groups",)

    def es_jurado(self, obj):
        return obj.groups.filter(name="jurado").exists()

    es_jurado.boolean = True
    es_jurado.short_description = "jurado"
