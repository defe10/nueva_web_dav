"""Vistas de estadísticas, separadas por dashboard.

- postulaciones: dashboard del Plan de Fomento y exportación a Excel
- impacto: impacto económico de rendiciones aprobadas
- registro: Registro Audiovisual
- exenciones: exenciones impositivas
- formacion: convocatorias de formación
- comun: helpers compartidos (conteos, rangos etarios, Excel)
"""
from .postulaciones import dashboard, exportar
from .registro import dashboard_registro, exportar_registro
from .exenciones import dashboard_exencion, exportar_exenciones
from .formacion import dashboard_formacion, exportar_formacion

__all__ = [
    "dashboard", "exportar",
    "dashboard_registro", "exportar_registro",
    "dashboard_exencion", "exportar_exenciones",
    "dashboard_formacion", "exportar_formacion",
]
