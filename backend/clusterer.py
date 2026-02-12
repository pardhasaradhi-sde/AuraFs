import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
import os
import re
import time
import threading
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Groq API setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
_groq_rate_limited = False
_groq_rate_limit_until = 0
_groq_lock = threading.Lock()

# Name cache
_name_cache = {}
_CACHE_MAX = 200

# Comprehensive category mapping with keywords — covers all major domains
CATEGORY_MAP = {
    # ── Finance & Accounting ──
    "Financial Documents": [
        "revenue", "profit", "loss", "balance sheet", "income statement",
        "cash flow", "expense", "budget", "financial", "accounting",
        "audit", "tax", "fiscal", "earnings", "asset", "liability",
        "equity", "ledger", "invoice", "payroll", "dividend",
        "depreciation", "amortization", "reconciliation", "accounts receivable",
        "accounts payable", "general ledger", "cost of goods", "gross margin"
    ],
    "Investment Documents": [
        "investment", "portfolio", "stock", "bond", "mutual fund", "etf",
        "dividend", "yield", "return", "risk", "diversification", "allocation",
        "hedge fund", "private equity", "securities", "derivatives", "options",
        "futures", "commodities", "forex", "cryptocurrency", "ipo",
        "prospectus", "shareholder", "market cap", "blue chip", "index fund"
    ],
    "Banking Documents": [
        "bank", "deposit", "withdrawal", "savings", "checking", "loan",
        "credit", "debit", "interest rate", "mortgage", "refinance",
        "overdraft", "wire transfer", "ach", "swift", "statement",
        "balance", "routing number", "escrow", "underwriting"
    ],
    "Insurance Documents": [
        "insurance", "policy", "premium", "deductible", "claim", "coverage",
        "underwriter", "actuary", "beneficiary", "annuity", "indemnity",
        "liability insurance", "life insurance", "health insurance",
        "auto insurance", "homeowner insurance", "reinsurance", "rider"
    ],
    "Tax Documents": [
        "tax return", "w2", "1099", "tax deduction", "taxable income",
        "irs", "withholding", "capital gains", "tax bracket", "filing",
        "tax credit", "estimated tax", "self employment tax", "sales tax",
        "property tax", "estate tax", "tax exempt", "tax audit"
    ],

    # ── Business & Strategy ──
    "Startup Documents": [
        "startup", "pitch", "venture", "funding", "investor", "seed",
        "series a", "series b", "valuation", "cap table", "equity stake",
        "term sheet", "convertible note", "runway", "burn rate", "mvp",
        "product market fit", "traction", "growth hacking", "unicorn",
        "incubator", "accelerator", "angel investor", "bootstrapping"
    ],
    "Business Strategy": [
        "strategy", "planning", "roadmap", "objective", "kpi", "metric",
        "competitive analysis", "market research", "swot", "business model",
        "go to market", "positioning", "differentiation", "value proposition",
        "stakeholder", "milestone", "deliverable", "business plan",
        "mission statement", "vision statement", "okr", "balanced scorecard"
    ],
    "Marketing": [
        "marketing", "branding", "advertising", "campaign", "social media",
        "content marketing", "seo", "sem", "email marketing", "analytics",
        "conversion", "lead generation", "customer acquisition", "retention",
        "engagement", "reach", "impression", "click through rate",
        "influencer", "affiliate marketing", "remarketing", "copywriting",
        "brand awareness", "market segmentation", "target audience"
    ],
    "Sales Documents": [
        "sales", "quota", "pipeline", "crm", "deal", "proposal",
        "prospect", "lead", "close", "upsell", "cross sell", "commission",
        "territory", "account management", "sales forecast", "cold call",
        "demo", "price quote", "rfp", "rfq", "tender", "bid"
    ],
    "E-commerce": [
        "ecommerce", "online store", "shopping cart", "checkout", "payment gateway",
        "product listing", "inventory", "sku", "fulfillment", "shipping",
        "dropshipping", "marketplace", "shopify", "woocommerce", "amazon",
        "customer review", "return policy", "order tracking"
    ],
    "Supply Chain and Logistics": [
        "supply chain", "logistics", "warehouse", "inventory management",
        "procurement", "vendor", "supplier", "distribution", "freight",
        "shipping", "tracking", "barcode", "last mile", "cold chain",
        "just in time", "lean manufacturing", "bill of lading", "customs"
    ],

    # ── Legal ──
    "Legal Documents": [
        "contract", "agreement", "legal", "compliance", "regulation",
        "terms", "conditions", "liability", "clause", "amendment",
        "litigation", "lawsuit", "settlement", "attorney", "counsel",
        "jurisdiction", "statute", "ordinance", "intellectual property",
        "patent", "trademark", "copyright", "nda", "confidentiality",
        "arbitration", "mediation", "injunction", "deposition", "affidavit"
    ],
    "Agreements": [
        "agreement", "memorandum", "understanding", "partnership",
        "collaboration", "joint venture", "service level agreement",
        "master service agreement", "statement of work", "addendum",
        "licensing agreement", "franchise agreement", "non compete",
        "non solicitation", "distribution agreement"
    ],
    "Regulatory and Compliance": [
        "compliance", "regulatory", "gdpr", "hipaa", "sox", "pci",
        "ferpa", "ccpa", "data protection", "privacy policy", "consent",
        "breach notification", "audit trail", "whistleblower",
        "anti money laundering", "know your customer", "sanctions"
    ],

    # ── Healthcare & Medicine ──
    "Medical Records": [
        "patient", "diagnosis", "treatment", "prescription", "medical",
        "clinical", "hospital", "doctor", "physician", "nurse",
        "surgery", "therapy", "medication", "symptom", "disease",
        "condition", "health record", "radiology", "laboratory", "pathology",
        "ehr", "emr", "icd", "cpt", "referral", "discharge summary"
    ],
    "Health Research": [
        "epidemiology", "clinical trial", "vaccine", "drug", "pharmaceutical",
        "immunology", "oncology", "cardiology", "neurology", "public health",
        "biomedical", "genomics", "proteomics", "medical research",
        "randomized controlled trial", "placebo", "cohort study", "meta analysis"
    ],
    "Mental Health": [
        "psychology", "psychiatry", "therapy", "counseling", "mental health",
        "anxiety", "depression", "ptsd", "cognitive behavioral", "mindfulness",
        "psychotherapy", "bipolar", "schizophrenia", "adhd", "autism",
        "behavioral health", "substance abuse", "addiction", "rehabilitation"
    ],
    "Dental Records": [
        "dental", "dentist", "orthodontics", "periodontal", "cavity",
        "filling", "crown", "root canal", "extraction", "implant",
        "braces", "oral hygiene", "gingivitis", "fluoride", "dental x ray"
    ],
    "Veterinary Documents": [
        "veterinary", "animal", "pet", "vaccination", "spay", "neuter",
        "kennel", "livestock", "equine", "canine", "feline",
        "animal health", "rabies", "heartworm", "microchip", "breeder"
    ],
    "Pharmacy Documents": [
        "pharmacy", "pharmacist", "dispensing", "formulary", "dosage",
        "side effects", "drug interaction", "generic", "brand name",
        "controlled substance", "compounding", "over the counter"
    ],

    # ── Science & Research ──
    "Physics Research": [
        "physics", "quantum", "particle", "mechanics", "force", "velocity",
        "acceleration", "energy", "momentum", "thermodynamics", "entropy",
        "electromagnetic", "relativity", "newtonian", "gravitational",
        "wave function", "schrodinger", "quantum mechanics", "field theory",
        "cosmology", "astrophysics", "nuclear physics", "optics", "photon",
        "higgs boson", "standard model", "string theory", "dark matter"
    ],
    "Biology Research": [
        "biology", "cell", "dna", "rna", "gene", "protein", "organism",
        "evolution", "natural selection", "ecology", "ecosystem", "species",
        "mitosis", "meiosis", "chromosome", "genetics", "heredity",
        "mutation", "adaptation", "taxonomy", "anatomy", "physiology",
        "molecular biology", "biochemistry", "microbiology", "botany", "zoology",
        "crispr", "gene editing", "cloning", "stem cell", "bioinformatics"
    ],
    "Chemistry Research": [
        "chemistry", "molecule", "atom", "element", "compound", "reaction",
        "chemical", "organic chemistry", "inorganic chemistry", "physical chemistry",
        "biochemistry", "analytical chemistry", "synthesis", "catalyst",
        "polymer", "periodic table", "bond", "ion", "acid", "base",
        "ph", "titration", "spectroscopy", "chromatography", "electrochemistry"
    ],
    "Mathematics": [
        "mathematics", "algebra", "calculus", "geometry", "trigonometry",
        "linear algebra", "differential equation", "integral", "derivative",
        "probability", "statistics", "theorem", "proof", "conjecture",
        "topology", "number theory", "combinatorics", "graph theory",
        "matrix", "vector", "eigenvalue", "fourier", "laplace"
    ],
    "Astronomy and Space": [
        "astronomy", "telescope", "planet", "star", "galaxy", "nebula",
        "solar system", "orbit", "satellite", "space exploration", "nasa",
        "esa", "rocket", "spacecraft", "mars", "moon", "asteroid",
        "black hole", "supernova", "exoplanet", "hubble", "james webb"
    ],
    "Earth Science and Geology": [
        "geology", "rock", "mineral", "fossil", "tectonic", "earthquake",
        "volcano", "sedimentary", "metamorphic", "igneous", "stratigraphy",
        "geomorphology", "paleontology", "seismology", "continental drift",
        "plate tectonics", "erosion", "weathering", "geological survey"
    ],
    "Environmental Science": [
        "environment", "climate change", "global warming", "carbon emission",
        "sustainability", "renewable energy", "pollution", "biodiversity",
        "conservation", "deforestation", "ozone", "greenhouse gas",
        "ecosystem restoration", "recycling", "waste management",
        "carbon footprint", "environmental impact", "clean energy", "solar power",
        "wind energy", "hydroelectric", "geothermal"
    ],
    "Oceanography and Marine Science": [
        "ocean", "marine", "coral reef", "deep sea", "tidal", "current",
        "salinity", "plankton", "marine biology", "oceanography",
        "submarine", "continental shelf", "sea level", "tsunami",
        "aquaculture", "fisheries", "mangrove", "estuary"
    ],
    "Meteorology and Weather": [
        "weather", "forecast", "temperature", "precipitation", "humidity",
        "barometer", "wind speed", "hurricane", "tornado", "cyclone",
        "meteorology", "climate", "drought", "flood", "monsoon",
        "el nino", "la nina", "jet stream", "radar", "satellite imagery"
    ],
    "General Scientific Research": [
        "research", "experiment", "hypothesis", "methodology", "results",
        "conclusion", "abstract", "introduction", "literature review",
        "discussion", "peer review", "publication", "journal", "citation",
        "scientific method", "observation", "measurement", "analysis"
    ],

    # ── Technology & Engineering ──
    "Software Engineering": [
        "code", "programming", "software", "development", "api", "framework",
        "library", "architecture", "design pattern", "algorithm", "debugging",
        "testing", "deployment", "devops", "continuous integration", "version control",
        "git", "docker", "kubernetes", "microservices", "backend", "frontend",
        "agile development", "sprint", "pull request", "code review", "refactoring"
    ],
    "AI Research": [
        "artificial intelligence", "machine learning", "deep learning", "neural network",
        "transformer", "lstm", "cnn", "gan", "reinforcement learning", "nlp",
        "computer vision", "model training", "dataset", "feature engineering",
        "optimization", "gradient descent", "backpropagation", "overfitting",
        "regularization", "attention mechanism", "embedding", "llm",
        "generative ai", "diffusion model", "fine tuning", "prompt engineering"
    ],
    "Data Science": [
        "data analysis", "statistics", "regression", "classification", "clustering",
        "visualization", "pandas", "numpy", "matplotlib", "jupyter",
        "exploratory data analysis", "feature selection", "dimensionality reduction",
        "time series", "forecasting", "hypothesis testing", "correlation",
        "data pipeline", "data warehouse", "etl", "data lake"
    ],
    "Cybersecurity": [
        "security", "encryption", "authentication", "authorization", "vulnerability",
        "penetration testing", "firewall", "malware", "phishing", "ransomware",
        "cryptography", "ssl", "tls", "vpn", "intrusion detection",
        "threat", "exploit", "patch", "compliance", "zero trust",
        "soc", "siem", "incident response", "forensics"
    ],
    "Web Development": [
        "html", "css", "javascript", "react", "angular", "vue",
        "typescript", "webpack", "responsive design", "dom", "ajax",
        "rest api", "graphql", "web application", "spa", "pwa",
        "tailwind", "bootstrap", "next js", "node js", "express"
    ],
    "Mobile Development": [
        "android", "ios", "swift", "kotlin", "flutter", "react native",
        "mobile app", "xcode", "gradle", "app store", "play store",
        "push notification", "geolocation", "responsive", "touch",
        "cordova", "xamarin", "mobile ui", "mobile testing"
    ],
    "Cloud Computing": [
        "cloud", "aws", "azure", "gcp", "serverless", "lambda",
        "ec2", "s3", "iaas", "paas", "saas", "load balancer",
        "auto scaling", "cloud formation", "terraform", "ansible",
        "container", "virtual machine", "cdn", "cloud migration"
    ],
    "Database Administration": [
        "database", "sql", "nosql", "mongodb", "postgresql", "mysql",
        "redis", "elasticsearch", "schema", "query", "index", "table",
        "join", "normalization", "replication", "sharding", "backup",
        "migration", "stored procedure", "transaction", "acid"
    ],
    "Networking and IT Infrastructure": [
        "network", "router", "switch", "tcp", "udp", "dns", "dhcp",
        "ip address", "subnet", "bandwidth", "latency", "firewall",
        "proxy", "nat", "vlan", "mpls", "bgp", "ospf",
        "active directory", "ldap", "server", "rack", "data center"
    ],
    "Game Development": [
        "game", "unity", "unreal engine", "godot", "sprite", "shader",
        "physics engine", "collision detection", "game loop", "rendering",
        "texture", "mesh", "animation", "pathfinding", "level design",
        "game design", "multiplayer", "fps", "rpg", "procedural generation"
    ],
    "Robotics": [
        "robot", "robotics", "actuator", "sensor", "servo", "lidar",
        "autonomous", "kinematics", "path planning", "ros",
        "manipulator", "end effector", "computer vision", "slam",
        "inverse kinematics", "pid controller", "humanoid", "drone"
    ],
    "IoT and Embedded Systems": [
        "iot", "internet of things", "embedded", "arduino", "raspberry pi",
        "microcontroller", "firmware", "sensor", "mqtt", "zigbee",
        "bluetooth", "wifi", "edge computing", "wearable", "smart home",
        "plc", "scada", "rtos", "gpio", "i2c", "spi"
    ],
    "Blockchain and Cryptocurrency": [
        "blockchain", "bitcoin", "ethereum", "smart contract", "solidity",
        "token", "nft", "defi", "mining", "consensus", "proof of work",
        "proof of stake", "wallet", "decentralized", "dao", "web3",
        "dapp", "gas fee", "ledger", "hash"
    ],
    "DevOps and CI/CD": [
        "devops", "ci cd", "jenkins", "github actions", "gitlab ci",
        "pipeline", "build", "release", "deployment", "monitoring",
        "grafana", "prometheus", "elk", "log aggregation", "artifact",
        "helm", "argocd", "infrastructure as code", "site reliability"
    ],

    # ── Engineering (Non-Software) ──
    "Mechanical Engineering": [
        "mechanical", "cad", "solidworks", "autocad", "tolerance",
        "manufacturing", "cnc", "lathe", "milling", "welding",
        "thermodynamics", "fluid dynamics", "stress analysis", "fatigue",
        "gearbox", "bearing", "shaft", "turbine", "engine", "pump"
    ],
    "Electrical Engineering": [
        "electrical", "circuit", "voltage", "current", "resistance",
        "capacitor", "inductor", "transistor", "diode", "pcb",
        "power supply", "amplifier", "oscillator", "signal processing",
        "control system", "plc", "motor", "generator", "transformer"
    ],
    "Civil Engineering": [
        "civil engineering", "structural", "concrete", "steel", "bridge",
        "foundation", "geotechnical", "surveying", "hydrology", "drainage",
        "road design", "highway", "dam", "reinforcement", "load bearing",
        "building code", "seismic design", "soil mechanics"
    ],
    "Chemical Engineering": [
        "chemical engineering", "process design", "reactor", "distillation",
        "heat exchanger", "mass transfer", "fluid flow", "piping",
        "process control", "batch process", "continuous process",
        "petrochemical", "refinery", "separation", "crystallization"
    ],
    "Aerospace Engineering": [
        "aerospace", "aerodynamics", "propulsion", "avionics", "airframe",
        "thrust", "drag", "lift", "mach number", "wind tunnel",
        "flight control", "navigation", "orbit", "payload", "reentry",
        "composite material", "jet engine", "turbofan", "fuselage"
    ],

    # ── Architecture & Design ──
    "Architecture and Building": [
        "architecture", "blueprint", "floor plan", "elevation", "facade",
        "building design", "interior design", "landscape", "zoning",
        "building permit", "renovation", "construction", "architect",
        "structural plan", "site plan", "bim", "revit", "urban planning"
    ],
    "UX UI Design": [
        "ux", "ui", "user experience", "user interface", "wireframe",
        "prototype", "mockup", "figma", "sketch", "adobe xd",
        "usability testing", "persona", "user journey", "information architecture",
        "interaction design", "accessibility", "responsive design", "design system"
    ],
    "Graphic Design": [
        "graphic design", "photoshop", "illustrator", "indesign", "canva",
        "typography", "color theory", "layout", "composition", "logo",
        "brand identity", "vector", "raster", "print design", "poster",
        "brochure", "flyer", "infographic", "visual identity"
    ],

    # ── Education & Academia ──
    "Academic Papers": [
        "thesis", "dissertation", "paper", "publication", "journal",
        "conference", "proceedings", "abstract", "citation", "bibliography",
        "scholarly", "peer review", "academic", "university", "professor",
        "impact factor", "doi", "arxiv", "preprint"
    ],
    "Course Materials": [
        "lecture", "course", "syllabus", "curriculum", "assignment",
        "homework", "exam", "quiz", "grade", "semester", "tutorial",
        "textbook", "slides", "notes", "study guide", "learning objective",
        "lesson plan", "module", "rubric", "assessment"
    ],
    "Training Materials": [
        "training", "workshop", "certification", "onboarding", "e learning",
        "webinar", "tutorial", "skill development", "competency",
        "professional development", "continuing education", "accreditation",
        "learning management system", "lms", "scorm"
    ],

    # ── Human Resources & Operations ──
    "Human Resources": [
        "hr", "employee", "recruitment", "hiring", "onboarding", "training",
        "performance review", "compensation", "benefits", "payroll",
        "termination", "resignation", "job description", "interview",
        "talent management", "workforce", "organizational culture",
        "diversity", "inclusion", "employee engagement", "retention"
    ],
    "Project Management": [
        "project", "task", "timeline", "deadline", "gantt", "agile",
        "scrum", "sprint", "kanban", "backlog", "standup", "retrospective",
        "stakeholder", "resource allocation", "risk management", "scope",
        "deliverable", "milestone", "jira", "asana", "trello",
        "work breakdown structure", "critical path", "earned value"
    ],
    "Meeting Notes": [
        "meeting", "minutes", "agenda", "discussion", "action item",
        "attendee", "summary", "notes", "follow up", "decision",
        "brainstorming", "workshop", "session", "conference call",
        "standup notes", "retrospective notes", "all hands"
    ],
    "Customer Support": [
        "support", "ticket", "helpdesk", "customer service", "issue",
        "resolution", "escalation", "sla", "knowledge base", "faq",
        "chat support", "phone support", "email support", "zendesk",
        "freshdesk", "customer satisfaction", "csat", "nps"
    ],

    # ── Real Estate & Property ──
    "Real Estate": [
        "property", "real estate", "lease", "rent", "mortgage", "deed",
        "title", "appraisal", "valuation", "zoning", "commercial property",
        "residential property", "listing", "broker", "agent", "escrow",
        "closing", "inspection", "landlord", "tenant",
        "condominium", "townhouse", "foreclosure", "mls"
    ],
    "Construction Documents": [
        "construction", "contractor", "subcontractor", "building permit",
        "inspection", "blueprint", "estimate", "bid", "change order",
        "punch list", "certificate of occupancy", "general contractor",
        "safety plan", "osha", "scaffolding", "excavation", "grading"
    ],

    # ── Government & Public Sector ──
    "Government Documents": [
        "government", "policy", "legislation", "regulation", "federal",
        "state", "municipal", "public sector", "administration", "ministry",
        "department", "agency", "bureaucracy", "civil service", "public policy",
        "governance", "constitution", "parliament", "congress",
        "executive order", "proclamation", "ordinance", "statute"
    ],
    "Military and Defense": [
        "military", "defense", "army", "navy", "air force", "marine",
        "intelligence", "classified", "security clearance", "deployment",
        "battalion", "regiment", "operations", "strategy", "logistics",
        "reconnaissance", "surveillance", "weapons system", "nato"
    ],

    # ── Personal & Lifestyle ──
    "Personal Documents": [
        "personal", "diary", "journal", "letter", "correspondence",
        "resume", "cv", "cover letter", "recommendation", "reference",
        "passport", "birth certificate", "marriage certificate", "will",
        "insurance", "warranty", "social security", "drivers license"
    ],
    "Travel and Tourism": [
        "travel", "itinerary", "flight", "hotel", "booking", "reservation",
        "passport", "visa", "tourism", "destination", "vacation",
        "cruise", "airbnb", "backpacking", "travel insurance",
        "customs", "immigration", "currency exchange", "sightseeing"
    ],
    "Food and Recipes": [
        "recipe", "cooking", "ingredient", "meal", "cuisine", "baking",
        "nutrition", "calorie", "diet", "menu", "restaurant",
        "food safety", "allergen", "vegan", "vegetarian", "gluten free",
        "food preparation", "kitchen", "chef", "culinary"
    ],
    "Health and Fitness": [
        "fitness", "exercise", "workout", "gym", "weight loss", "nutrition",
        "diet plan", "cardio", "strength training", "yoga", "pilates",
        "marathon", "running", "bodybuilding", "personal trainer",
        "bmi", "calories", "macros", "stretching", "recovery"
    ],
    "Sports": [
        "sports", "football", "basketball", "soccer", "baseball", "tennis",
        "cricket", "golf", "swimming", "athletics", "olympics",
        "tournament", "championship", "league", "playoff", "score",
        "coach", "referee", "stadium", "athlete", "team"
    ],
    "Fashion and Textile": [
        "fashion", "clothing", "apparel", "textile", "fabric", "designer",
        "collection", "runway", "trend", "pattern", "sewing",
        "garment", "boutique", "sustainable fashion", "accessories",
        "couture", "ready to wear", "fashion week"
    ],

    # ── Creative & Media ──
    "Creative Writing": [
        "story", "novel", "fiction", "poetry", "narrative", "character",
        "plot", "dialogue", "theme", "setting", "prose", "verse",
        "chapter", "manuscript", "draft", "creative", "literary",
        "short story", "memoir", "screenplay", "playwriting"
    ],
    "News Articles": [
        "news", "article", "press release", "journalism", "reporter",
        "headline", "breaking news", "editorial", "opinion", "interview",
        "coverage", "media", "newspaper", "magazine", "broadcast",
        "wire service", "syndication", "byline", "dateline"
    ],
    "Music and Audio": [
        "music", "song", "melody", "harmony", "rhythm", "chord",
        "composition", "orchestra", "band", "album", "track",
        "recording", "mixing", "mastering", "producer", "lyrics",
        "tempo", "key", "scale", "genre", "concert", "playlist"
    ],
    "Photography": [
        "photography", "camera", "lens", "exposure", "aperture", "shutter",
        "iso", "raw", "lightroom", "photoshop", "composition",
        "portrait", "landscape", "macro", "flash", "tripod",
        "resolution", "megapixel", "focal length", "white balance"
    ],
    "Film and Video": [
        "film", "video", "cinema", "director", "screenplay", "script",
        "editing", "cinematography", "production", "post production",
        "documentary", "animation", "vfx", "storyboard", "shot list",
        "premiere pro", "final cut", "davinci resolve", "color grading"
    ],

    # ── Social Sciences & Humanities ──
    "History": [
        "history", "historical", "ancient", "medieval", "renaissance",
        "revolution", "civilization", "empire", "dynasty", "war",
        "archaeology", "artifact", "primary source", "chronicle",
        "era", "century", "colonialism", "independence", "treaty"
    ],
    "Philosophy": [
        "philosophy", "ethics", "metaphysics", "epistemology", "logic",
        "existentialism", "utilitarianism", "phenomenology", "ontology",
        "morality", "virtue", "consciousness", "free will", "determinism",
        "socrates", "plato", "aristotle", "kant", "nietzsche"
    ],
    "Psychology": [
        "psychology", "behavior", "cognition", "perception", "motivation",
        "emotion", "personality", "social psychology", "developmental",
        "neuroscience", "cognitive bias", "memory", "attention",
        "conditioning", "reinforcement", "psychoanalysis", "experiment"
    ],
    "Sociology": [
        "sociology", "society", "social structure", "culture", "institution",
        "stratification", "inequality", "class", "race", "gender",
        "urbanization", "globalization", "social movement", "community",
        "deviance", "norm", "socialization", "demography"
    ],
    "Economics": [
        "economics", "gdp", "inflation", "unemployment", "monetary policy",
        "fiscal policy", "supply demand", "microeconomics", "macroeconomics",
        "trade", "tariff", "recession", "economic growth", "interest rate",
        "federal reserve", "central bank", "consumer price index"
    ],
    "Political Science": [
        "political", "politics", "democracy", "election", "voter",
        "campaign", "party", "ideology", "liberalism", "conservatism",
        "geopolitics", "diplomacy", "foreign policy", "international relations",
        "sovereignty", "republic", "authoritarian", "constitution"
    ],
    "Linguistics": [
        "linguistics", "language", "grammar", "syntax", "semantics",
        "phonetics", "phonology", "morphology", "pragmatics", "dialect",
        "translation", "bilingual", "etymology", "lexicon", "corpus",
        "sociolinguistics", "psycholinguistics", "computational linguistics"
    ],
    "Anthropology": [
        "anthropology", "culture", "ethnography", "fieldwork", "tribe",
        "kinship", "ritual", "artifact", "indigenous", "folklore",
        "cultural anthropology", "biological anthropology", "archaeology",
        "ethnology", "cross cultural", "human evolution"
    ],
    "Religious Studies": [
        "religion", "theology", "spiritual", "faith", "scripture",
        "worship", "prayer", "church", "mosque", "temple", "synagogue",
        "bible", "quran", "torah", "buddhism", "hinduism", "islam",
        "christianity", "judaism", "meditation", "pilgrimage"
    ],
    "Geography": [
        "geography", "map", "cartography", "gis", "topography",
        "latitude", "longitude", "continent", "country", "region",
        "urban", "rural", "population", "migration", "land use",
        "remote sensing", "spatial analysis", "terrain", "elevation"
    ],

    # ── Agriculture & Environment ──
    "Agriculture": [
        "agriculture", "farming", "crop", "harvest", "irrigation",
        "fertilizer", "pesticide", "soil", "livestock", "dairy",
        "organic farming", "sustainable agriculture", "agronomy",
        "horticulture", "aquaculture", "seed", "yield", "plantation",
        "greenhouse", "hydroponics", "agroforestry"
    ],

    # ── Transportation & Automotive ──
    "Automotive": [
        "automotive", "vehicle", "car", "engine", "transmission",
        "brake", "suspension", "emission", "fuel", "electric vehicle",
        "hybrid", "battery", "horsepower", "torque", "odometer",
        "maintenance", "recall", "warranty", "dealership", "vin"
    ],
    "Aviation": [
        "aviation", "aircraft", "pilot", "flight", "airport", "runway",
        "air traffic control", "faa", "cockpit", "altitude", "airspace",
        "maintenance log", "flight plan", "navigation", "turbulence",
        "landing gear", "fuselage", "wing", "hangar"
    ],
    "Maritime": [
        "maritime", "ship", "vessel", "port", "harbor", "cargo",
        "container", "navigation", "maritime law", "admiralty",
        "coast guard", "shipping lane", "tonnage", "dry dock",
        "anchor", "ballast", "buoy", "lighthouse"
    ],

    # ── Energy & Utilities ──
    "Energy": [
        "energy", "power plant", "electricity", "grid", "renewable",
        "solar panel", "wind turbine", "hydropower", "nuclear energy",
        "fossil fuel", "natural gas", "coal", "petroleum", "oil",
        "energy efficiency", "smart grid", "battery storage",
        "kilowatt", "megawatt", "utility", "transmission line"
    ],

    # ── Nonprofit & Social ──
    "Nonprofit Documents": [
        "nonprofit", "charity", "donation", "grant", "fundraising",
        "volunteer", "mission", "501c3", "foundation", "endowment",
        "philanthropy", "beneficiary", "outreach", "community service",
        "social impact", "annual report", "tax exempt", "board of directors"
    ],

    # ── Communications & PR ──
    "Public Relations": [
        "public relations", "pr", "press release", "media relations",
        "spokesperson", "press conference", "crisis communication",
        "reputation management", "media kit", "press coverage",
        "brand image", "corporate communication", "stakeholder communication"
    ],
    "Corporate Communications": [
        "memo", "internal communication", "newsletter", "announcement",
        "company update", "town hall", "all hands", "intranet",
        "employee communication", "organizational update", "bulletin",
        "circular", "notice", "policy update"
    ],

    # ── Technical Writing & Documentation ──
    "Technical Manuals": [
        "manual", "guide", "documentation", "specification", "instruction",
        "user guide", "reference", "handbook", "procedure", "standard",
        "protocol", "operation", "maintenance", "troubleshooting", "installation",
        "api documentation", "release notes", "changelog", "readme"
    ],
    "Research Proposals": [
        "proposal", "grant proposal", "research plan", "funding request",
        "budget justification", "specific aims", "methodology",
        "literature review", "timeline", "expected outcomes",
        "principal investigator", "co investigator", "nsf", "nih"
    ],
    "Reports": [
        "report", "quarterly report", "annual report", "status report",
        "progress report", "incident report", "audit report", "feasibility study",
        "white paper", "case study", "benchmark", "executive summary",
        "findings", "recommendation", "analysis report"
    ],
    "Presentations": [
        "presentation", "slide", "powerpoint", "keynote", "pitch deck",
        "slide deck", "talking points", "visual aid", "speaker notes",
        "conference presentation", "webinar", "demo", "showcase"
    ],

    # ── Miscellaneous / General ──
    "General Documents": [
        "document", "file", "note", "record", "log", "form",
        "template", "checklist", "worksheet", "spreadsheet", "catalog",
        "directory", "index", "inventory", "register", "manifest"
    ]
}


def find_optimal_clusters(embeddings, max_k=8):
    """Find optimal number of clusters using silhouette score."""
    n_samples = len(embeddings)
    if n_samples < 2:
        return 1
    
    max_k = min(max_k, n_samples - 1)
    if max_k < 2:
        return 1
    
    best_score = -1
    best_k = 2
    
    for k in range(2, max_k + 1):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            
            if score > best_score:
                best_score = score
                best_k = k
        except Exception as e:
            print(f"Error computing silhouette for k={k}: {e}")
            continue
    
    return best_k


def cluster_embeddings(embeddings, n_clusters=None, n_neighbors=None):
    """
    Cluster embeddings using KMeans.
    
    Args:
        embeddings: Array of embeddings
        n_clusters: Number of clusters (auto-detect if None)
        n_neighbors: Unused (for API compatibility)
    
    Returns:
        Tuple of (cluster labels, cluster centers)
    """
    if len(embeddings) < 2:
        return np.array([0]), np.array([embeddings[0]])
    
    if n_clusters is None:
        n_clusters = find_optimal_clusters(embeddings)
    
    n_clusters = min(n_clusters, len(embeddings))
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    
    return labels, kmeans.cluster_centers_


def name_all_clusters(cluster_data):
    """
    Name all clusters using fallback strategy:
    1. Check cache
    2. Try Groq API
    3. Try keyword matching
    4. Try TF-IDF
    5. Fallback to filename patterns
    """
    named_clusters = {}
    uncached_data = {}
    
    # Check cache first
    for cluster_id, data in cluster_data.items():
        cache_key = _cache_key(data["texts"])
        cached_name = _get_cached_name(cache_key)
        if cached_name:
            named_clusters[cluster_id] = cached_name
        else:
            uncached_data[cluster_id] = data
    
    if not uncached_data:
        return named_clusters
    
    # Try Groq API if not rate limited
    if not _is_rate_limited():
        groq_names = _name_clusters_groq(uncached_data)
        if groq_names:
            for cluster_id, name in groq_names.items():
                named_clusters[cluster_id] = name
                cache_key = _cache_key(uncached_data[cluster_id]["texts"])
                _set_cached_name(cache_key, name)
                uncached_data.pop(cluster_id, None)
    
    if not uncached_data:
        return named_clusters
    
    # Try keyword matching
    for cluster_id, data in list(uncached_data.items()):
        keyword_name = _name_cluster_by_keywords(data["texts"], data["file_names"])
        if keyword_name:
            named_clusters[cluster_id] = keyword_name
            cache_key = _cache_key(data["texts"])
            _set_cached_name(cache_key, keyword_name)
            uncached_data.pop(cluster_id, None)
    
    if not uncached_data:
        return named_clusters
    
    # Try TF-IDF
    tfidf_names = _name_clusters_tfidf(uncached_data)
    for cluster_id, name in tfidf_names.items():
        named_clusters[cluster_id] = name
        cache_key = _cache_key(uncached_data[cluster_id]["texts"])
        _set_cached_name(cache_key, name)
    
    return named_clusters


def _name_cluster_by_keywords(texts, file_names):
    """
    Name cluster by matching keywords from CATEGORY_MAP.
    Uses word-boundary regex matching to avoid substring matches.
    Requires score >= 5 and at least 2 keyword matches.
    """
    combined_text = " ".join(texts).lower()
    combined_files = " ".join(file_names).lower()
    
    category_scores = {}
    category_match_counts = {}
    
    for category, keywords in CATEGORY_MAP.items():
        score = 0
        match_count = 0
        
        for keyword in keywords:
            # Use word boundaries to prevent substring matches
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            
            text_matches = len(re.findall(pattern, combined_text))
            file_matches = len(re.findall(pattern, combined_files))
            
            if text_matches > 0 or file_matches > 0:
                match_count += 1
                # Filename matches are strong signals — weight them 3x
                score += text_matches + file_matches * 3
        
        if match_count >= 1 and score >= 2:
            category_scores[category] = score
            category_match_counts[category] = match_count
    
    if not category_scores:
        return None
    
    # Return category with highest score
    best_category = max(category_scores.items(), key=lambda x: (x[1], category_match_counts[x[0]]))
    return best_category[0]


def get_subcategory_name(texts, file_names, parent_category):
    """
    Get subcategory name within a parent category using word-boundary matching.
    """
    if parent_category not in CATEGORY_MAP:
        return None
    
    combined_text = " ".join(texts).lower()
    combined_files = " ".join(file_names).lower()
    
    keyword_scores = {}
    parent_keywords = CATEGORY_MAP[parent_category]
    
    for keyword in parent_keywords:
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        
        text_matches = len(re.findall(pattern, combined_text))
        file_matches = len(re.findall(pattern, combined_files))
        
        total_matches = text_matches + file_matches
        if total_matches > 0:
            keyword_scores[keyword] = total_matches
    
    if not keyword_scores:
        return None
    
    # Return top keyword as subcategory
    best_keyword = max(keyword_scores.items(), key=lambda x: x[1])
    return best_keyword[0].title()


def name_sub_clusters_by_keywords(sub_cluster_data, parent_category):
    """Name sub-clusters using keyword matching within parent category."""
    named_subclusters = {}
    
    for sub_id, data in sub_cluster_data.items():
        subcat_name = get_subcategory_name(data["texts"], data["file_names"], parent_category)
        if subcat_name:
            named_subclusters[sub_id] = subcat_name
        else:
            # Fallback to TF-IDF
            tfidf_name = _name_single_cluster_tfidf(data["texts"], data["file_names"])
            named_subclusters[sub_id] = tfidf_name
    
    return named_subclusters


def _name_clusters_groq(cluster_data):
    """Name clusters using Groq API."""
    if not GROQ_API_KEY:
        return {}
    
    try:
        client = _get_groq_client()
        named_clusters = {}
        
        for cluster_id, data in cluster_data.items():
            texts_sample = data["texts"][:3]
            files_sample = data["file_names"][:5]
            
            prompt = f"""Based on these file excerpts and names, suggest a brief category name (2-4 words):

Files: {', '.join(files_sample)}

Content samples:
{chr(10).join([f'- {_smart_truncate(t, 150)}' for t in texts_sample])}

Category name:"""
            
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=30,
                    temperature=0.3,
                    timeout=5
                )
                
                name = response.choices[0].message.content.strip()
                name = re.sub(r'^["\'`]|["\'`]$', '', name)
                name = name.split('\n')[0].strip()
                
                if len(name) > 50:
                    name = name[:50]
                
                if name:
                    named_clusters[cluster_id] = name
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                    _mark_rate_limited()
                    break
                continue
        
        return named_clusters
        
    except Exception as e:
        print(f"Groq API error: {e}")
        return {}


def _name_sub_clusters_groq(sub_cluster_data):
    """Name sub-clusters using Groq API."""
    return _name_clusters_groq(sub_cluster_data)


def _name_clusters_tfidf(cluster_data):
    """Name clusters using TF-IDF analysis."""
    named_clusters = {}
    
    for cluster_id, data in cluster_data.items():
        name = _name_single_cluster_tfidf(data["texts"], data["file_names"])
        named_clusters[cluster_id] = name
    
    return named_clusters


def _name_single_cluster_tfidf(texts, file_names):
    """Name a single cluster using TF-IDF."""
    if not texts:
        return _name_from_filenames(file_names)
    
    try:
        vectorizer = TfidfVectorizer(max_features=10, stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        feature_names = vectorizer.get_feature_names_out()
        avg_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
        
        top_indices = avg_tfidf.argsort()[-3:][::-1]
        top_terms = [feature_names[i] for i in top_indices if avg_tfidf[i] > 0]
        
        if top_terms:
            name = " ".join(top_terms[:2]).title()
            return name if len(name) <= 50 else name[:50]
        
    except Exception as e:
        print(f"TF-IDF naming error: {e}")
    
    return _name_from_filenames(file_names)


def _name_from_filenames(file_names):
    """Generate name from filename patterns."""
    if not file_names:
        return "Mixed Documents"
    
    # Extract common prefixes or patterns
    common_words = {}
    for fname in file_names[:10]:
        fname_clean = re.sub(r'[_\-.]', ' ', os.path.splitext(fname)[0])
        words = [w.lower() for w in fname_clean.split() if len(w) > 3]
        for word in words:
            common_words[word] = common_words.get(word, 0) + 1
    
    if common_words:
        top_words = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:2]
        name = " ".join([w[0].title() for w in top_words])
        return name if name else "Mixed Documents"
    
    return "Mixed Documents"


def sub_cluster_files(file_paths, embeddings, texts, file_names, min_files=4):
    """
    Sub-cluster files within a parent cluster.
    
    Returns:
        dict: { sub_name: [file_indices] } or None
    """
    if len(file_paths) < min_files:
        return None
    
    n_sub = min(3, len(file_paths) // 2)
    if n_sub < 2:
        return None
    
    try:
        sub_labels, _ = cluster_embeddings(embeddings, n_clusters=n_sub)
        
        # Group indices by sub-cluster label
        label_groups = {}
        for i, label in enumerate(sub_labels):
            label = int(label)
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(i)
        
        # Name each sub-cluster using keyword matching
        named_result = {}
        used_names = set()
        for label, indices in label_groups.items():
            sub_texts = [texts[i] for i in indices]
            sub_fnames = [file_names[i] for i in indices]
            
            # Try keyword naming
            name = _name_cluster_by_keywords(sub_texts, sub_fnames)
            if not name:
                name = _name_single_cluster_tfidf(sub_texts, sub_fnames)
            if not name:
                name = _name_from_filenames(sub_fnames)
            
            # Ensure uniqueness
            base_name = name
            counter = 1
            while name in used_names:
                name = f"{base_name} {counter}"
                counter += 1
            used_names.add(name)
            
            named_result[name] = indices
        
        return named_result if len(named_result) >= 2 else None
        
    except Exception as e:
        print(f"Sub-clustering error: {e}")
        return None


def get_3d_positions(embeddings):
    """
    Reduce embeddings to 3D for visualization.
    Uses PCA for n<15, UMAP with init="random" for n>=15.
    Falls back to PCA if UMAP fails.
    """
    n_samples = len(embeddings)
    
    if n_samples < 3:
        # Pad to 3D
        result = np.zeros((n_samples, 3))
        result[:, :embeddings.shape[1]] = embeddings[:, :min(3, embeddings.shape[1])]
        return result
    
    if n_samples < 15:
        # Use PCA for small datasets
        try:
            n_components = min(3, embeddings.shape[1], n_samples)
            pca = PCA(n_components=n_components, random_state=42)
            result = pca.fit_transform(embeddings)
            
            if result.shape[1] < 3:
                padded = np.zeros((n_samples, 3))
                padded[:, :result.shape[1]] = result
                return padded
            
            return result
            
        except Exception as e:
            print(f"PCA error: {e}")
            return np.random.randn(n_samples, 3)
    
    # Use UMAP for larger datasets
    try:
        import umap
        reducer = umap.UMAP(n_components=3, random_state=42, init="random", n_neighbors=min(15, n_samples - 1))
        result = reducer.fit_transform(embeddings)
        return result
        
    except ImportError:
        print("UMAP not available, falling back to PCA")
    except Exception as e:
        print(f"UMAP error: {e}, falling back to PCA")
    
    # Fallback to PCA
    try:
        n_components = min(3, embeddings.shape[1], n_samples)
        pca = PCA(n_components=n_components, random_state=42)
        result = pca.fit_transform(embeddings)
        
        if result.shape[1] < 3:
            padded = np.zeros((n_samples, 3))
            padded[:, :result.shape[1]] = result
            return padded
        
        return result
        
    except Exception as e:
        print(f"PCA fallback error: {e}")
        return np.random.randn(n_samples, 3)


def get_cluster_color(cluster_id):
    """Return a pastel color for a cluster."""
    pastel_colors = [
        "#FFB3BA",  # Pastel Pink
        "#FFDFBA",  # Pastel Peach
        "#FFFFBA",  # Pastel Yellow
        "#BAFFC9",  # Pastel Green
        "#BAE1FF",  # Pastel Blue
        "#D4BAFF",  # Pastel Purple
        "#FFBAF3",  # Pastel Magenta
        "#FFCCCB",  # Light Coral
        "#B5EAD7",  # Mint
        "#C7CEEA",  # Periwinkle
        "#FFDAC1",  # Apricot
        "#E2F0CB",  # Tea Green
        "#F4ACB7",  # Pink
        "#9DD9D2",  # Turquoise
        "#FFF8DC",  # Cornsilk
    ]
    
    return pastel_colors[cluster_id % len(pastel_colors)]


# Helper functions

def _get_groq_client():
    """Get Groq client instance."""
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except ImportError:
        return None


def _is_rate_limited():
    """Check if currently rate limited."""
    global _groq_rate_limited, _groq_rate_limit_until
    
    with _groq_lock:
        if _groq_rate_limited and time.time() < _groq_rate_limit_until:
            return True
        elif _groq_rate_limited:
            _groq_rate_limited = False
            _groq_rate_limit_until = 0
        return False


def _mark_rate_limited(duration=300):
    """Mark as rate limited for specified duration (default 5 minutes)."""
    global _groq_rate_limited, _groq_rate_limit_until
    
    with _groq_lock:
        _groq_rate_limited = True
        _groq_rate_limit_until = time.time() + duration
        print(f"Rate limited. Waiting {duration}s...")


def _cache_key(texts):
    """Generate cache key from texts."""
    if not texts:
        return ""
    
    sample = " ".join(texts[:3])[:200]
    return str(hash(sample))


def _get_cached_name(cache_key):
    """Get cached name if exists."""
    return _name_cache.get(cache_key)


def _set_cached_name(cache_key, name):
    """Set cached name with size limit."""
    global _name_cache
    
    if len(_name_cache) >= _CACHE_MAX:
        # Remove oldest entries (simple FIFO)
        keys_to_remove = list(_name_cache.keys())[:_CACHE_MAX // 4]
        for key in keys_to_remove:
            _name_cache.pop(key, None)
    
    _name_cache[cache_key] = name


def _smart_truncate(text, max_len=150):
    """Truncate text intelligently at word boundary."""
    if len(text) <= max_len:
        return text
    
    truncated = text[:max_len].rsplit(' ', 1)[0]
    return truncated + "..."


def clear_name_cache():
    """Clear the name cache."""
    global _name_cache
    _name_cache = {}
