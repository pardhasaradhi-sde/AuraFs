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

# Comprehensive category mapping with keywords
CATEGORY_MAP = {
    "Financial Documents": [
        "revenue", "profit", "loss", "balance sheet", "income statement", 
        "cash flow", "expense", "budget", "financial", "accounting", 
        "audit", "tax", "fiscal", "earnings", "asset", "liability",
        "equity", "ledger", "invoice", "payroll", "dividend"
    ],
    "Startup Documents": [
        "startup", "pitch", "venture", "funding", "investor", "seed",
        "series a", "series b", "valuation", "cap table", "equity stake",
        "term sheet", "convertible note", "runway", "burn rate", "mvp",
        "product market fit", "traction", "growth hacking", "unicorn"
    ],
    "Business Strategy": [
        "strategy", "planning", "roadmap", "objective", "kpi", "metric",
        "competitive analysis", "market research", "swot", "business model",
        "go to market", "positioning", "differentiation", "value proposition",
        "stakeholder", "milestone", "deliverable"
    ],
    "Investment Documents": [
        "investment", "portfolio", "stock", "bond", "mutual fund", "etf",
        "dividend", "yield", "return", "risk", "diversification", "allocation",
        "hedge fund", "private equity", "securities", "derivatives", "options",
        "futures", "commodities", "forex", "cryptocurrency"
    ],
    "Legal Documents": [
        "contract", "agreement", "legal", "compliance", "regulation",
        "terms", "conditions", "liability", "clause", "amendment",
        "litigation", "lawsuit", "settlement", "attorney", "counsel",
        "jurisdiction", "statute", "ordinance", "intellectual property",
        "patent", "trademark", "copyright", "nda", "confidentiality"
    ],
    "Medical Records": [
        "patient", "diagnosis", "treatment", "prescription", "medical",
        "clinical", "hospital", "doctor", "physician", "nurse",
        "surgery", "therapy", "medication", "symptom", "disease",
        "condition", "health record", "radiology", "laboratory", "pathology"
    ],
    "Health Research": [
        "epidemiology", "clinical trial", "vaccine", "drug", "pharmaceutical",
        "immunology", "oncology", "cardiology", "neurology", "public health",
        "biomedical", "genomics", "proteomics", "medical research"
    ],
    "Software Engineering": [
        "code", "programming", "software", "development", "api", "framework",
        "library", "architecture", "design pattern", "algorithm", "debugging",
        "testing", "deployment", "devops", "continuous integration", "version control",
        "git", "docker", "kubernetes", "microservices", "backend", "frontend"
    ],
    "AI Research": [
        "artificial intelligence", "machine learning", "deep learning", "neural network",
        "transformer", "lstm", "cnn", "gan", "reinforcement learning", "nlp",
        "computer vision", "model training", "dataset", "feature engineering",
        "optimization", "gradient descent", "backpropagation", "overfitting",
        "regularization", "attention mechanism", "embedding", "llm"
    ],
    "Data Science": [
        "data analysis", "statistics", "regression", "classification", "clustering",
        "visualization", "pandas", "numpy", "matplotlib", "jupyter",
        "exploratory data analysis", "feature selection", "dimensionality reduction",
        "time series", "forecasting", "hypothesis testing", "correlation"
    ],
    "Cybersecurity": [
        "security", "encryption", "authentication", "authorization", "vulnerability",
        "penetration testing", "firewall", "malware", "phishing", "ransomware",
        "cryptography", "ssl", "tls", "vpn", "intrusion detection",
        "threat", "exploit", "patch", "compliance", "zero trust"
    ],
    "Physics Research": [
        "physics", "quantum", "particle", "mechanics", "force", "velocity",
        "acceleration", "energy", "momentum", "thermodynamics", "entropy",
        "electromagnetic", "relativity", "newtonian", "gravitational",
        "wave function", "schrodinger", "quantum mechanics", "field theory",
        "cosmology", "astrophysics", "nuclear physics", "optics", "photon"
    ],
    "Biology Research": [
        "biology", "cell", "dna", "rna", "gene", "protein", "organism",
        "evolution", "natural selection", "ecology", "ecosystem", "species",
        "mitosis", "meiosis", "chromosome", "genetics", "heredity",
        "mutation", "adaptation", "taxonomy", "anatomy", "physiology",
        "molecular biology", "biochemistry", "microbiology", "botany", "zoology",
        "crispr", "gene editing", "cloning", "stem cell"
    ],
    "Chemistry Research": [
        "chemistry", "molecule", "atom", "element", "compound", "reaction",
        "chemical", "organic chemistry", "inorganic chemistry", "physical chemistry",
        "biochemistry", "analytical chemistry", "synthesis", "catalyst",
        "polymer", "periodic table", "bond", "ion", "acid", "base",
        "ph", "titration", "spectroscopy", "chromatography", "electrochemistry"
    ],
    "General Scientific Research": [
        "research", "experiment", "hypothesis", "methodology", "results",
        "conclusion", "abstract", "introduction", "literature review",
        "discussion", "peer review", "publication", "journal", "citation",
        "scientific method", "observation", "measurement", "analysis"
    ],
    "Academic Papers": [
        "thesis", "dissertation", "paper", "publication", "journal",
        "conference", "proceedings", "abstract", "citation", "bibliography",
        "scholarly", "peer review", "academic", "university", "professor"
    ],
    "Course Materials": [
        "lecture", "course", "syllabus", "curriculum", "assignment",
        "homework", "exam", "quiz", "grade", "semester", "tutorial",
        "textbook", "slides", "notes", "study guide", "learning objective"
    ],
    "Human Resources": [
        "hr", "employee", "recruitment", "hiring", "onboarding", "training",
        "performance review", "compensation", "benefits", "payroll",
        "termination", "resignation", "job description", "interview",
        "talent management", "workforce", "organizational culture"
    ],
    "Marketing": [
        "marketing", "branding", "advertising", "campaign", "social media",
        "content marketing", "seo", "sem", "email marketing", "analytics",
        "conversion", "lead generation", "customer acquisition", "retention",
        "engagement", "reach", "impression", "click through rate"
    ],
    "Project Management": [
        "project", "task", "timeline", "deadline", "gantt", "agile",
        "scrum", "sprint", "kanban", "backlog", "standup", "retrospective",
        "stakeholder", "resource allocation", "risk management", "scope",
        "deliverable", "milestone", "jira", "asana", "trello"
    ],
    "Real Estate": [
        "property", "real estate", "lease", "rent", "mortgage", "deed",
        "title", "appraisal", "valuation", "zoning", "commercial property",
        "residential property", "listing", "broker", "agent", "escrow",
        "closing", "inspection", "landlord", "tenant"
    ],
    "Government Documents": [
        "government", "policy", "legislation", "regulation", "federal",
        "state", "municipal", "public sector", "administration", "ministry",
        "department", "agency", "bureaucracy", "civil service", "public policy",
        "governance", "constitution", "parliament", "congress"
    ],
    "Personal Documents": [
        "personal", "diary", "journal", "letter", "correspondence",
        "resume", "cv", "cover letter", "recommendation", "reference",
        "passport", "birth certificate", "marriage certificate", "will",
        "insurance", "warranty"
    ],
    "Creative Writing": [
        "story", "novel", "fiction", "poetry", "narrative", "character",
        "plot", "dialogue", "theme", "setting", "prose", "verse",
        "chapter", "manuscript", "draft", "creative", "literary"
    ],
    "News Articles": [
        "news", "article", "press release", "journalism", "reporter",
        "headline", "breaking news", "editorial", "opinion", "interview",
        "coverage", "media", "newspaper", "magazine", "broadcast"
    ],
    "Technical Manuals": [
        "manual", "guide", "documentation", "specification", "instruction",
        "user guide", "reference", "handbook", "procedure", "standard",
        "protocol", "operation", "maintenance", "troubleshooting", "installation"
    ],
    "Meeting Notes": [
        "meeting", "minutes", "agenda", "discussion", "action item",
        "attendee", "summary", "notes", "follow up", "decision",
        "brainstorming", "workshop", "session", "conference call"
    ],
    "Agreements": [
        "agreement", "memorandum", "understanding", "partnership",
        "collaboration", "joint venture", "service level agreement",
        "master service agreement", "statement of work", "addendum"
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
