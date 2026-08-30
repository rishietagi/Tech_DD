"""Builds the /meta/enums payload from app.reference.enums (initial_plan.md §6)."""

from enum import Enum

from app.reference import enums as enum_module
from app.schemas.meta import EnumOption

_ENUM_CLASSES: dict[str, type[Enum]] = {
    "dealStage": enum_module.DealStage,
    "processType": enum_module.ProcessType,
    "valueCreationLever": enum_module.ValueCreationLever,
    "investmentType": enum_module.InvestmentType,
    "stake": enum_module.Stake,
    "postCloseIntent": enum_module.PostCloseIntent,
    "holdPeriod": enum_module.HoldPeriod,
    "sector": enum_module.Sector,
    "businessModel": enum_module.BusinessModel,
    "digitalMaturity": enum_module.DigitalMaturity,
    "revenueStage": enum_module.RevenueStage,
    "customerConcentration": enum_module.CustomerConcentration,
    "techIsProduct": enum_module.TechIsProduct,
    "buildVsBuy": enum_module.BuildVsBuy,
    "coreSystem": enum_module.CoreSystem,
    "hostingModel": enum_module.HostingModel,
    "cloudProvider": enum_module.CloudProvider,
    "outsourcingReliance": enum_module.OutsourcingReliance,
    "aiMlDependence": enum_module.AiMlDependence,
    "dataSensitivity": enum_module.DataSensitivity,
    "complianceRegime": enum_module.ComplianceRegime,
    "ddObjective": enum_module.DdObjective,
    "accessLevel": enum_module.AccessLevel,
    "deliverableFormat": enum_module.DeliverableFormat,
    "budgetBand": enum_module.BudgetBand,
    "ddTypePreference": enum_module.DdTypePreference,
    "engagementStatus": enum_module.EngagementStatus,
    "ddType": enum_module.DdType,
}


def build_enums_payload() -> dict[str, list[EnumOption]]:
    return {
        key: [EnumOption(value=member.value, label=member.value) for member in enum_cls]
        for key, enum_cls in _ENUM_CLASSES.items()
    }
