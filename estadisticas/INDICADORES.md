# Catálogo de indicadores — módulo Estadísticas

Define qué mide cada indicador, en qué unidad y de dónde sale el dato.
Si se agrega un indicador nuevo, sumarlo acá con su unidad.

## Unidades de medición

| Unidad | Significado |
|---|---|
| **Postulación** | Un proyecto presentado a una convocatoria del Plan de Fomento (excluye borradores). Una persona con 3 proyectos = 3 postulaciones. |
| **Persona única (presentante)** | Un usuario que presentó al menos una postulación en el resultado filtrado. Cuenta una sola vez aunque tenga varias postulaciones. |
| **Persona registrada** | Una inscripción en el Registro Audiovisual (humana o jurídica). |
| **Solicitud de exención** | Un trámite de exención (excluye borradores). |
| **Inscripción a formación** | Una inscripción a una convocatoria de formación. La misma persona en dos cursos cuenta dos veces. |
| **Contratación / ítem** | Cantidad declarada en la planilla de rendición por categoría. **No** son personas únicas: una misma persona puede aparecer en varias categorías o rendiciones. |
| **Pesos ($)** | Montos de rendiciones, siempre `Decimal`, agregados en base de datos. |

## Plan de Fomento (`/estadisticas/`)

| Indicador | Unidad | Fuente |
|---|---|---|
| Postulaciones | postulaciones | `Postulacion` sin `borrador`, filtros: convocatoria, año de `fecha_envio`, tipo, solo ganadores |
| Presentantes únicos | personas únicas | `user_id` distintos del resultado filtrado |
| Por convocatoria / tipo / género del proyecto / estado | postulaciones | campos de `Postulacion` |
| Género / rango etario / residencia | personas únicas | `PersonaHumana` del presentante; "Sin dato" si no está en el registro |
| **Ganador** | — | estados `seleccionado` y `finalizado` (definido en `views/postulaciones.py::ESTADOS_GANADOR`; `finalizado` = seleccionado que completó rendición) |

## Tasas del Plan de Fomento

Calculadas sobre el resultado filtrado (definidas en `views/postulaciones.py::tasas`):

| Tasa | Definición |
|---|---|
| Admisión | postulaciones que superaron la revisión administrativa (`admitido`, `evaluacion_jurado`, `seleccionado`, `no_seleccionado`, `finalizado`) / total |
| Selección | ganadoras (`seleccionado` + `finalizado`) / total |
| Finalización | `finalizado` / ganadoras |
| Rendición aprobada | rendiciones `APROBADO` de esas postulaciones / ganadoras |

## Impacto económico (misma página)

| Indicador | Unidad | Fuente |
|---|---|---|
| **Monto otorgado** | pesos | `Postulacion.monto_otorgado` de ganadoras (lo carga el staff al seleccionar; el dashboard avisa cuántas ganadoras no lo tienen cargado) |
| **Monto rendido** | pesos | suma de categorías de rendiciones presentadas (`ENVIADO`, `OBSERVADO`, `SUBSANADO`, `APROBADO`) |
| **Monto aprobado** | pesos | ídem, solo rendiciones `APROBADO` |
| **% ejecución** | — | aprobado / otorgado |
| Total rendido y monto por categoría | pesos | `Rendicion` con estado `APROBADO`, `Sum()` por categoría |
| Contrataciones / ítems por categoría | contrataciones/ítems | campos `*_cantidad` de `Rendicion` |
| Filtro de año | — | **año de `fecha_aprobacion` de la rendición** (no el año de envío de la postulación). Se setea al aprobar desde el admin; las históricas se backfillearon con la fecha de última revisión. Con filtro de año, otorgado usa año de envío de la postulación y rendido el año de envío de la rendición. |

## Evolución anual

Las barras comparan años entre sí: respetan los filtros del dashboard
**excepto el de año**. Fomento: postulaciones, ganadoras y monto aprobado
por año. Registro: altas por año. Exenciones: solicitudes por año.
Formación: inscripciones por año.

## Filtros por dashboard

| Dashboard | Filtros |
|---|---|
| Plan de Fomento | convocatoria, año (envío), tipo de proyecto, solo ganadores |
| Registro | localidad, área de desempeño (principal o secundaria) |
| Exenciones | año (solicitud), estado, localidad fiscal |
| Formación | convocatoria, año (inscripción), estado |

Todos los dashboards tienen exportación a Excel que respeta los filtros activos.

## Datos incompletos

- Fomento: presentantes sin datos en el Registro Audiovisual (bajo la tarjeta de presentantes únicos) y ganadoras sin monto otorgado cargado.
- Formación: inscripciones sin género / edad / localidad / vínculo.
- En las tablas, "Sin dato" siempre aparece como fila propia con su cantidad.

Pendiente (etapa 2): separar "contrataciones" de "personas beneficiadas únicas" requiere
cambiar la carga de rendiciones para identificar personas; hoy la planilla solo declara cantidades.

## Registro Audiovisual (`/estadisticas/registro/`)

| Indicador | Unidad | Nota |
|---|---|---|
| Personas humanas / jurídicas / localidades | personas registradas | — |
| Roles predominantes | personas registradas | solo área principal |
| Técnicos disponibles por área | disponibilidad | área principal **y** secundaria: una persona puede estar en dos filas; la suma supera el total de inscriptos a propósito |
| Ubicación territorial | personas registradas | "Otro" se desagrega por el texto libre normalizado (espacios y mayúsculas) |

## Exenciones (`/estadisticas/exenciones/`)

| Indicador | Unidad | Nota |
|---|---|---|
| Solicitudes / por estado / por localidad / tipo de solicitante | solicitudes | filtro de año por `fecha_creacion` |
| Vigentes hoy | solicitudes | `APROBADA` con `fecha_vencimiento >= hoy` |

## Formación (`/estadisticas/formacion/`)

| Indicador | Unidad | Nota |
|---|---|---|
| Inscripciones / por convocatoria / estado / género / edad / localidad / vínculo | inscripciones | filtro por convocatoria |
| Admitidos | inscripciones | estado `admitido` |

## Estructura del código

```
estadisticas/views/
  comun.py          helpers compartidos (conteo, rangos etarios, normalización, Excel)
  postulaciones.py  dashboard Plan de Fomento + exportación
  impacto.py        impacto económico
  registro.py       Registro Audiovisual
  exenciones.py     exenciones
  formacion.py      formación
```
