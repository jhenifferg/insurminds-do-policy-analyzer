"""Conservative, deterministic clause-name normalization."""

import unicodedata

from .models import PolicyExtraction


_COVERAGE_ALIASES = {
    "side a": "SIDE_A", "side b": "SIDE_B", "side c": "SIDE_C",
    "custos de defesa": "DEFENSE_COSTS", "despesas de defesa": "DEFENSE_COSTS",
    "honorarios de defesa": "DEFENSE_COSTS",
    "investigacao regulatoria": "REGULATORY_INVESTIGATION",
    "pre investigacao": "PRE_INVESTIGATION", "epl": "EPL",
    "praticas trabalhistas indevidas": "EPL", "gestao de crise": "CRISIS_MANAGEMENT",
    "responsabilidade ambiental": "ENVIRONMENTAL_LIABILITY",
    "danos ambientais": "ENVIRONMENTAL_LIABILITY",
    "cobertura mundial": "WORLDWIDE_COVERAGE", "run off": "RUN_OFF",
}

_EXCLUSION_ALIASES = {
    "fraude": "FRAUD", "ato doloso": "FRAUD", "ma fe": "FRAUD",
    "ganho ilicito": "ILLICIT_GAIN", "enriquecimento indevido": "ILLICIT_GAIN",
    "dano ambiental": "ENVIRONMENTAL_DAMAGE", "poluicao": "ENVIRONMENTAL_DAMAGE",
    "guerra": "WAR", "terrorismo": "TERRORISM",
    "reclamacoes anteriores": "PRIOR_CLAIMS", "fatos conhecidos": "KNOWN_CIRCUMSTANCES",
    "insured vs insured": "INSURED_VS_INSURED",
}


class ClauseNormalizer:
    """Assign only codes backed by a small, explicit Portuguese alias list."""

    def normalize(self, policy: PolicyExtraction) -> PolicyExtraction:
        for field in (policy.coverages, policy.lmi_sublimits, policy.extensions):
            if field.value:
                for clause in field.value:
                    clause.taxonomy_code = _coverage_code(clause.name)
        if policy.exclusions.value:
            for exclusion in policy.exclusions.value:
                exclusion.category = _exclusion_code(exclusion.name)
        return policy


def _coverage_code(name: str) -> str | None:
    key = _key(name)
    exact = _COVERAGE_ALIASES.get(key)
    if exact:
        return exact
    # Normalize name variants for the core D&O claims-made liability coverage.
    prefixes = (
        "responsabilidade de administradores e diretores",
        "responsabilidade civil de administradores e diretores",
        "cobertura a responsabilidade de administradores e diretores",
        "cobertura a responsabilidade civil de administradores e diretores",
    )
    if any(key.startswith(prefix) for prefix in prefixes):
        return "DNO_ADMINISTRATOR_LIABILITY"
    reimbursement_prefixes = (
        "cobertura b reembolso a sociedade",
        "reembolso a sociedade por valores pagos em nome de administrador",
    )
    if any(key.startswith(prefix) for prefix in reimbursement_prefixes):
        return "CORPORATE_REIMBURSEMENT"
    return None


def _exclusion_code(name: str) -> str | None:
    key = _key(name)
    exact = _EXCLUSION_ALIASES.get(key)
    if exact:
        return exact
    if key.startswith("danos corporais e materiais"):
        return "BODILY_INJURY_PROPERTY_DAMAGE"
    return None


def _key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(value.casefold().replace("-", " ").split())


__all__ = ["ClauseNormalizer"]
