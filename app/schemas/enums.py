from enum import Enum


class QuotationStatus(str, Enum):
    PENDIENTE = "Pendiente"
    CONTACTADO = "Contactado"
    COTIZACION_PRESENTADA = "Cotización Presentada"
    PROPUESTA_CONFIRMADA = "Propuesta Confirmada"
    CANCELADA = "Cancelada"
    RECHAZADA = "Rechazada"


class CandidateStatus(str, Enum):
    POSTULADO = "Postulado"
    VISTO = "Visto"
    CONTACTADO = "Contactado"
    ENTREVISTADO = "Entrevistado"
    NO_APLICA = "No aplica"
    CONTRATADO = "Contratado"


class ResidencyZone(str, Enum):
    CABA = "CABA"
    GBA_NORTE = "GBA Norte"
    GBA_SUR = "GBA Sur"
    GBA_OESTE = "GBA Oeste"