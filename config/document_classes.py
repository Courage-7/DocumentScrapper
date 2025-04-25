"""
Configuration for document classes and their search parameters
"""

DOCUMENT_CLASSES = {
    # Company Documents
    "commercial_register": {
        "name": "Commercial Register",
        "category": "company",
        "file_types": [".pdf", ".doc", ".docx"],
        "search_queries": [
            "commercial register document sample filetype:pdf",
            "business registry document filetype:pdf",
            "company register extract sample filetype:pdf",
            "commercial register certificate template filetype:pdf"
        ],
        "keywords": [
            "commercial register", "business registry", "company registration",
            "register extract", "registration number", "commercial court"
        ]
    },
    
    "articles_of_association": {
        "name": "Articles of Association",
        "category": "company",
        "file_types": [".pdf", ".doc", ".docx"],
        "search_queries": [
            "articles of association template filetype:pdf",
            "company articles of association sample filetype:pdf",
            "corporate bylaws sample document filetype:pdf",
            "company constitution document example filetype:pdf"
        ],
        "keywords": [
            "articles of association", "bylaws", "company constitution",
            "corporate governance", "shareholders", "board of directors"
        ]
    },
    
    "incorporation": {
        "name": "Incorporation",
        "category": "company",
        "file_types": [".pdf", ".doc", ".docx"],
        "search_queries": [
            "certificate of incorporation sample filetype:pdf",
            "incorporation document template filetype:pdf",
            "company incorporation certificate filetype:pdf",
            "business incorporation document sample filetype:pdf"
        ],
        "keywords": [
            "certificate of incorporation", "incorporated", "company formation",
            "registration date", "company number", "corporate identity"
        ]
    },
    
    # Individual Documents
    "passport": {
        "name": "Passport",
        "category": "individual",
        "file_types": [".pdf", ".jpg", ".png"],
        "search_queries": [
            "passport sample template filetype:pdf",
            "blank passport document example filetype:jpg",
            "passport specimen filetype:pdf",
            "sample passport document filetype:png"
        ],
        "keywords": [
            "passport", "travel document", "identification", "nationality",
            "date of issue", "date of expiry", "bearer"
        ]
    },
    
    "id": {
        "name": "ID",
        "category": "individual",
        "file_types": [".pdf", ".jpg", ".png"],
        "search_queries": [
            "national ID card sample filetype:pdf",
            "identity card template example filetype:jpg",
            "ID document specimen filetype:pdf",
            "government issued ID sample filetype:png"
        ],
        "keywords": [
            "identity card", "identification", "national ID", "personal number",
            "date of issue", "date of expiry", "government issued"
        ]
    },
    
    "utility_bill": {
        "name": "Utility Bill",
        "category": "individual",
        "file_types": [".pdf", ".doc", ".docx"],
        "search_queries": [
            "utility bill sample template filetype:pdf",
            "electricity bill example document filetype:pdf",
            "water bill sample document filetype:pdf",
            "gas bill template example filetype:pdf"
        ],
        "keywords": [
            "utility bill", "electricity", "water", "gas", "service address",
            "account number", "billing period", "payment due"
        ]
    }
}

def get_document_class(doc_class_id):
    """Get document class configuration by ID"""
    return DOCUMENT_CLASSES.get(doc_class_id.lower().replace(" ", "_"))

def get_all_document_classes():
    """Get all document classes"""
    return DOCUMENT_CLASSES

def get_document_classes_by_category(category):
    """Get document classes by category (company or individual)"""
    return {k: v for k, v in DOCUMENT_CLASSES.items() if v["category"] == category}