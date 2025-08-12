# MUFG Risk Mirror Analyzer with RAG

An AI-powered risk assessment platform that uses Retrieval-Augmented Generation (RAG) to provide accurate, fact-based financial and health risk analysis.

## Features

- **Financial Risk Analysis**: Comprehensive assessment of financial health, debt, investments, and retirement planning
- **Health Risk Analysis**: Evaluation of health factors including BMI, lifestyle, and medical history
- **RAG Implementation**: Uses semantic search to retrieve relevant guidelines before generating analysis
- **Interactive Chat**: Follow-up questions with context-aware responses
- **Knowledge Base Management**: Admin endpoints to add and manage domain-specific documents

## RAG Implementation

### How it Works

1. **Document Storage**: Domain-specific guidelines are stored in MongoDB with vector embeddings
2. **Semantic Retrieval**: User queries are encoded and matched against stored documents using cosine similarity
3. **Context Injection**: Retrieved documents are formatted and included in LLM prompts
4. **Factual Responses**: LLM generates responses based on verified guidelines rather than general knowledge

### Knowledge Base Structure

- **Financial Documents**: Emergency fund guidelines, debt-to-income ratios, investment strategies, retirement planning
- **Health Documents**: BMI guidelines, cardiovascular risk factors, exercise recommendations, sleep guidelines
- **Categories**: Each document is categorized for better organization and retrieval

## Installation

1. **Install basic dependencies**:
```bash
pip install -r requirements.txt
```

2. **Optional: Install advanced semantic search** (for better RAG performance):
```bash
pip install sentence-transformers torch transformers
```

3. **Set up environment variables** (create `.env` file):
```env
AI21_API_KEY=your_ai21_api_key
MONGODB_URI=your_mongodb_connection_string
DB_NAME=your_database_name
```

4. **Test the system**:
```bash
python test_rag.py
```

5. **Run the application**:
```bash
python app.py
```

## API Endpoints

### Main Endpoints
- `GET /`: Main application interface
- `POST /analyze`: Submit risk assessment data
- `POST /chat`: Ask follow-up questions
- `GET /history/<user_id>`: Get user's assessment history

### Admin Endpoints
- `POST /admin/add_document`: Add new document to knowledge base
- `GET /admin/documents/<domain>`: Get all documents for a domain

### Adding New Documents

```bash
curl -X POST http://localhost:5000/admin/add_document \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "finance",
    "title": "New Financial Guideline",
    "content": "Detailed guideline content...",
    "category": "investment_risk",
    "tags": ["investment", "risk", "guidelines"]
  }'
```

## RAG Benefits

1. **Reduced Hallucination**: LLM uses verified guidelines instead of making up information
2. **Domain Accuracy**: Responses are based on specific financial and health standards
3. **Consistency**: Same questions get similar answers based on the same knowledge base
4. **Updatability**: Knowledge base can be updated without retraining models
5. **Auditability**: Can trace responses back to specific source documents

## Technical Architecture

```
User Input → Risk Score Calculation → Document Retrieval → LLM with Context → Response
                ↓
            Knowledge Base (MongoDB + Embeddings)
```

### Components

- **KnowledgeBase Class**: Manages document storage, embedding, and retrieval
- **Semantic Search**: Uses 'all-MiniLM-L6-v2' for semantic embeddings (optional)
- **Keyword Search**: Fallback to keyword-based retrieval when semantic search is unavailable
- **Cosine Similarity**: Measures document relevance to user queries
- **MongoDB**: Stores documents and embeddings/keywords

## Customization

### Adding New Domains

1. Add domain-specific documents to the knowledge base
2. Update the risk calculation functions if needed
3. Modify the UI to include new domain options

### Updating Guidelines

Use the admin endpoints to add new documents or update existing ones. The system will automatically create embeddings for new content.

## Performance Considerations

- **Embedding Model**: Uses lightweight 'all-MiniLM-L6-v2' for fast inference (when available)
- **Keyword Fallback**: Automatic fallback to keyword-based search when semantic search fails
- **Top-K Retrieval**: Limits retrieved documents to prevent prompt bloat
- **Caching**: Consider implementing embedding caching for production use
- **Offline Support**: System works without internet connection using keyword-based retrieval

## Security Notes

- Admin endpoints should be protected in production
- Consider rate limiting for API endpoints
- Validate all user inputs before processing
