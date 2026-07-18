"""Vistas de estadísticas, separadas por dashboard.

- postulaciones: dashboards del Plan de Fomento y de Cash Rebate (misma
  lógica sobre Postulacion, filtrada por línea) y exportación a Excel
- impacto: impacto económico de rendiciones aprobadas
- registro: Registro Audiovisual
- exenciones: exenciones impositivas
- formacion: convocatorias de formación
- comun: helpers compartidos (conteos, rangos etarios, Excel)
"""
from .postulaciones import (
    dashboard, exportar,
    dashboard_cash_rebate, exportar_cash_rebate,
)
from .registro import dashboard_registro, exportar_registro
from .exenciones import dashboard_exencion, exportar_exenciones
from .formacion import dashboard_formacion, exportar_formacion

__all__ = [
    "dashboard", "exportar",
    "dashboard_cash_rebate", "exportar_cash_rebate",
    "dashboard_registro", "exportar_registro",
    "dashboard_exencion", "exportar_exenciones",
    "dashboard_formacion", "exportar_formacion",
]
