SECTORS_FIELD = "sectors"

# --- licence classes (Regulated Activities Order 2011, Schedule 1) ---
CLASS_1 = "class_1"  # Deposit taking
CLASS_2 = "class_2"  # Investment business
CLASS_3 = "class_3"  # Services to collective investment schemes
CLASS_4 = "class_4"  # Corporate services
CLASS_5 = "class_5"  # Trust services
CLASS_6 = "class_6"  # Crowdfunding platforms
CLASS_7 = "class_7"  # Management or administration services
CLASS_8 = "class_8"  # Money transmission services
CLASS_9 = "class_9"  # Credit unions

LICENCE_CLASSES: tuple[str, ...] = (
    CLASS_1,
    CLASS_2,
    CLASS_3,
    CLASS_4,
    CLASS_5,
    CLASS_6,
    CLASS_7,
    CLASS_8,
    CLASS_9,
)

# --- designated businesses (DBROA 2015, Schedule 1 Part 1, items 1-13) ---
LEGAL_PROFESSIONAL = "legal_professional"
EXTERNAL_ACCOUNTANT = "external_accountant"
TAX_ADVISER = "tax_adviser"
PAYROLL_AGENT = "payroll_agent"
LENDER = "lender"
FINANCIAL_LEASING = "financial_leasing"
FINANCIAL_GUARANTEES = "financial_guarantees"
ESTATE_AGENT = "estate_agent"
HIGH_VALUE_DEALER = "high_value_dealer"
SAFE_CUSTODY = "safe_custody"
VASP = "vasp"
MONEY_ADMINISTRATION = "money_administration"

DESIGNATED_BUSINESSES: tuple[str, ...] = (
    LEGAL_PROFESSIONAL,
    EXTERNAL_ACCOUNTANT,
    TAX_ADVISER,
    PAYROLL_AGENT,
    LENDER,
    FINANCIAL_LEASING,
    FINANCIAL_GUARANTEES,
    ESTATE_AGENT,
    HIGH_VALUE_DEALER,
    SAFE_CUSTODY,
    VASP,
    MONEY_ADMINISTRATION,
)

SECTOR_LABELS: dict[str, str] = {
    # licence classes
    CLASS_1: "Class 1 – Deposit taking",
    CLASS_2: "Class 2 – Investment business",
    CLASS_3: "Class 3 – Services to collective investment schemes",
    CLASS_4: "Class 4 – Corporate services",
    CLASS_5: "Class 5 – Trust services",
    CLASS_6: "Class 6 – Crowdfunding platforms",
    CLASS_7: "Class 7 – Management or administration services",
    CLASS_8: "Class 8 – Money transmission services",
    CLASS_9: "Class 9 – Credit unions",
    # designated businesses
    LEGAL_PROFESSIONAL: "Legal professional",
    EXTERNAL_ACCOUNTANT: "External accountant",
    TAX_ADVISER: "Tax adviser",
    PAYROLL_AGENT: "Payroll agent",
    LENDER: "Lending on behalf of customers",
    FINANCIAL_LEASING: "Financial leasing",
    FINANCIAL_GUARANTEES: "Financial guarantees and commitments",
    ESTATE_AGENT: "Estate agent",
    HIGH_VALUE_DEALER: "High value dealer (cash of €15,000 or more)",
    SAFE_CUSTODY: "Safe custody and secure storage",
    VASP: "Virtual asset service provider",
    MONEY_ADMINISTRATION: "Administering or managing money for others",
}


# --- Sector groupings ---
ALL_SECTORS: tuple[str, ...] = LICENCE_CLASSES + DESIGNATED_BUSINESSES
FSA08_SECTORS: tuple[str, ...] = (
    CLASS_1,
    CLASS_2,
    CLASS_3,
    CLASS_4,
    CLASS_5,
    CLASS_7,
    CLASS_8,
)
NON_BANK: tuple[str, ...] = (CLASS_2, CLASS_3, CLASS_4, CLASS_5, CLASS_8)
TCSP: tuple[str, ...] = (CLASS_4, CLASS_5)

# NOTE: Gaming/Gambling and SNPOs not included for now
