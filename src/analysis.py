"""Funções analíticas puras. Taxas são percentuais, não proporções."""
import math


def missing_events(total, rate):
    """Aproximação de eventos sub-registrados a partir da taxa publicada."""
    if not math.isfinite(total) or total < 0:
        raise ValueError('Total deve ser finito e não negativo')
    if not math.isfinite(rate) or not 0 <= rate <= 100:
        raise ValueError('Taxa deve estar entre 0 e 100')
    return total * rate / 100


def relative_change(before, after):
    if before <= 0:
        return None
    return (after / before - 1) * 100


def scenario(base, reduction, years):
    """Trajetória hipotética composta, nunca uma previsão ou meta oficial."""
    if not math.isfinite(base) or not 0 <= base <= 100:
        raise ValueError('Taxa-base inválida')
    if not math.isfinite(reduction) or not 0 <= reduction <= 100:
        raise ValueError('Redução inválida')
    if not isinstance(years, int) or not 1 <= years <= 10:
        raise ValueError('Horizonte inválido')
    return [base * (1 - reduction / 100) ** i for i in range(years + 1)]
