import os
import json
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
import logging
from pymongo import MongoClient
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import sentence transformers, with fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not available. Using simple keyword-based retrieval.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class KnowledgeBase:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DB_NAME]
        self.documents_collection = self.db.documents
        self.embeddings_collection = self.db.embeddings
        
        # Initialize embedding model with fallback
        self.embedding_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info("Initializing sentence transformer model...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer model: {e}")
                logger.info("Falling back to keyword-based retrieval")
                self.embedding_model = None
        
        # Initialize with default knowledge base
        self._initialize_default_knowledge()
    
    def _initialize_default_knowledge(self):
        """Initialize the knowledge base with default financial and health documents"""
        
        # Check if documents already exist
        if self.documents_collection.count_documents({}) > 0:
            return
        
        # Financial Risk Assessment Documents
        financial_docs = [
            {
                "domain": "finance",
                "title": "Emergency Fund Guidelines",
                "content": "Emergency funds should cover 3-6 months of living expenses. For high-risk individuals, aim for 6-12 months. Emergency funds should be kept in liquid, low-risk accounts like savings accounts or money market funds. Never invest emergency funds in volatile assets.",
                "category": "liquidity_risk",
                "tags": ["emergency fund", "liquidity", "cash flow", "financial security"]
            },
            {
                "domain": "finance", 
                "title": "Debt-to-Income Ratio Standards",
                "content": "A healthy debt-to-income ratio is below 36%. Ratios above 43% are considered high risk. This includes all debt payments: mortgage, car loans, credit cards, student loans. Lenders typically prefer ratios below 28% for optimal loan terms.",
                "category": "debt_risk",
                "tags": ["debt", "DTI ratio", "credit", "borrowing capacity"]
            },
            {
                "domain": "finance",
                "title": "Investment Risk Tolerance Guidelines",
                "content": "Conservative investors should allocate 60-70% to bonds and 30-40% to stocks. Moderate investors: 50-60% stocks, 40-50% bonds. Aggressive investors: 70-80% stocks, 20-30% bonds. Age-based rule: percentage in bonds should roughly equal your age.",
                "category": "investment_risk",
                "tags": ["investment", "risk tolerance", "asset allocation", "portfolio"]
            },
            {
                "domain": "finance",
                "title": "Retirement Planning Standards",
                "content": "Save 10-15% of income for retirement. The 4% rule: withdraw 4% of portfolio annually in retirement. Aim to replace 70-80% of pre-retirement income. Start saving early - compound interest is crucial. Consider tax-advantaged accounts like 401(k) and IRA.",
                "category": "retirement_risk",
                "tags": ["retirement", "savings", "401k", "IRA", "financial planning"]
            },
            {
                "domain": "finance",
                "title": "Income Stability Assessment",
                "content": "Evaluate income stability by considering: job security, industry trends, skill demand, multiple income sources. High-risk factors: single income source, declining industry, limited skills. Mitigation: skill development, side income, emergency fund, insurance.",
                "category": "income_risk",
                "tags": ["income", "job security", "career", "financial stability"]
            }
        ]
        
        # Health Risk Assessment Documents
        health_docs = [
            {
                "domain": "health",
                "title": "BMI and Health Risk Guidelines",
                "content": "BMI categories: Underweight (<18.5), Normal (18.5-24.9), Overweight (25-29.9), Obese (≥30). Health risks increase with BMI outside normal range. Waist circumference also important: >40 inches (men) or >35 inches (women) indicates higher risk.",
                "category": "metabolic_risk",
                "tags": ["BMI", "weight", "obesity", "metabolic health"]
            },
            {
                "domain": "health",
                "title": "Cardiovascular Risk Factors",
                "content": "Major risk factors: high blood pressure (>130/80), high cholesterol (>200 mg/dL), smoking, diabetes, obesity, physical inactivity, poor diet. Modifiable factors: diet, exercise, smoking, alcohol. Non-modifiable: age, gender, family history.",
                "category": "cardiovascular_risk",
                "tags": ["heart disease", "blood pressure", "cholesterol", "cardiovascular"]
            },
            {
                "domain": "health",
                "title": "Exercise Recommendations",
                "content": "Adults should get 150 minutes moderate exercise or 75 minutes vigorous exercise weekly. Include muscle-strengthening 2+ days/week. Benefits: reduced heart disease, diabetes, cancer risk. Start slowly, gradually increase intensity. Consult doctor before starting new program.",
                "category": "lifestyle_risk",
                "tags": ["exercise", "physical activity", "fitness", "lifestyle"]
            },
            {
                "domain": "health",
                "title": "Sleep and Health Guidelines",
                "content": "Adults need 7-9 hours sleep nightly. Poor sleep linked to: heart disease, diabetes, obesity, depression. Sleep hygiene: consistent schedule, dark/quiet room, avoid screens before bed, limit caffeine. Sleep disorders require medical evaluation.",
                "category": "lifestyle_risk",
                "tags": ["sleep", "rest", "health", "wellness"]
            },
            {
                "domain": "health",
                "title": "Stress Management Guidelines",
                "content": "Chronic stress increases heart disease, diabetes, depression risk. Management techniques: exercise, meditation, deep breathing, time management, social support. Identify stress sources and develop coping strategies. Consider professional help for persistent stress.",
                "category": "lifestyle_risk",
                "tags": ["stress", "mental health", "wellness", "coping"]
            }
        ]
        
        # Add all documents to database
        all_docs = financial_docs + health_docs
        for doc in all_docs:
            doc_id = self.documents_collection.insert_one(doc).inserted_id
            # Create embedding for the document if model is available
            if self.embedding_model:
                try:
                    embedding = self.embedding_model.encode(doc["content"]).tolist()
                    self.embeddings_collection.insert_one({
                        "document_id": doc_id,
                        "embedding": embedding,
                        "domain": doc["domain"],
                        "category": doc["category"]
                    })
                except Exception as e:
                    logger.error(f"Failed to create embedding for document {doc['title']}: {e}")
            else:
                # Store keywords for keyword-based retrieval
                keywords = self._extract_keywords(doc["content"])
                self.embeddings_collection.insert_one({
                    "document_id": doc_id,
                    "keywords": keywords,
                    "domain": doc["domain"],
                    "category": doc["category"]
                })
    
    def add_document(self, domain: str, title: str, content: str, category: str, tags: List[str]):
        """Add a new document to the knowledge base"""
        doc = {
            "domain": domain,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags,
            "created_at": datetime.now()
        }
        
        doc_id = self.documents_collection.insert_one(doc).inserted_id
        
        # Create and store embedding or keywords
        if self.embedding_model:
            try:
                embedding = self.embedding_model.encode(content).tolist()
                self.embeddings_collection.insert_one({
                    "document_id": doc_id,
                    "embedding": embedding,
                    "domain": domain,
                    "category": category
                })
            except Exception as e:
                logger.error(f"Failed to create embedding for new document: {e}")
        else:
            keywords = self._extract_keywords(content)
            self.embeddings_collection.insert_one({
                "document_id": doc_id,
                "keywords": keywords,
                "domain": domain,
                "category": category
            })
        
        return doc_id
    
    def retrieve_relevant_documents(self, query: str, domain: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant documents based on semantic similarity or keyword matching"""
        
        # Get all documents for the domain
        stored_docs = list(self.embeddings_collection.find({"domain": domain}))
        
        if not stored_docs:
            return []
        
        if self.embedding_model:
            # Use semantic similarity
            try:
                query_embedding = self.embedding_model.encode(query).tolist()
                similarities = []
                for emb_doc in stored_docs:
                    if "embedding" in emb_doc:
                        similarity = self._cosine_similarity(query_embedding, emb_doc["embedding"])
                        similarities.append((similarity, emb_doc["document_id"]))
                
                # Sort by similarity and get top_k
                similarities.sort(reverse=True)
                top_doc_ids = [doc_id for _, doc_id in similarities[:top_k]]
            except Exception as e:
                logger.error(f"Semantic search failed: {e}")
                return self._keyword_based_retrieval(query, domain, top_k)
        else:
            # Use keyword-based retrieval
            return self._keyword_based_retrieval(query, domain, top_k)
        
        # Get the actual documents
        documents = list(self.documents_collection.find({"_id": {"$in": top_doc_ids}}))
        return documents
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for keyword-based retrieval"""
        import re
        # Convert to lowercase and remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Split into words and filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'his', 'hers', 'ours', 'theirs'}
        words = [word for word in text.split() if word not in stop_words and len(word) > 2]
        return list(set(words))  # Remove duplicates
    
    def _keyword_based_retrieval(self, query: str, domain: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve documents based on keyword matching"""
        query_keywords = set(self._extract_keywords(query))
        
        # Get all documents for the domain
        stored_docs = list(self.embeddings_collection.find({"domain": domain}))
        
        if not stored_docs:
            return []
        
        # Calculate keyword overlap scores
        scores = []
        for doc in stored_docs:
            if "keywords" in doc:
                doc_keywords = set(doc["keywords"])
                overlap = len(query_keywords.intersection(doc_keywords))
                if overlap > 0:
                    scores.append((overlap, doc["document_id"]))
        
        # Sort by overlap score and get top_k
        scores.sort(reverse=True)
        top_doc_ids = [doc_id for _, doc_id in scores[:top_k]]
        
        # Get the actual documents
        documents = list(self.documents_collection.find({"_id": {"$in": top_doc_ids}}))
        return documents
    
    def get_documents_by_category(self, domain: str, category: str) -> List[Dict[str, Any]]:
        """Get documents by domain and category"""
        return list(self.documents_collection.find({"domain": domain, "category": category}))
    
    def format_documents_for_prompt(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents for inclusion in LLM prompt"""
        if not documents:
            return "No specific guidelines available. Use general best practices."
        
        formatted = "Use the following verified guidelines for your analysis:\n\n"
        for i, doc in enumerate(documents, 1):
            formatted += f"{i}. {doc['title']}:\n{doc['content']}\n\n"
        
        return formatted

# Global knowledge base instance
kb = KnowledgeBase()
