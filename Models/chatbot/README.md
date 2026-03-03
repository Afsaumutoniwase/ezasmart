# EzaSmart RAG Chatbot

**Model Type:** Hybrid Retrieval-Augmented Generation (RAG) System  
**Author:** Afsa Umutoniwase  
**Project:** EzaSmart Hydroponics Platform  
**Base Model:** [Afsa20/Farmsmart_Growmate](https://huggingface.co/Afsa20/Farmsmart_Growmate) (T5-based)

## Overview

EzaSmart RAG Chatbot answers hydroponics questions using a hybrid approach that combines information retrieval with neural text generation. When you ask a question, the system first searches a curated knowledge base. If it finds a good match (similarity ≥ 0.4), it returns that answer. Otherwise, it generates a new answer using the fine-tuned T5 model.

**Key Features:**
- 1,100+ Q&A pairs from expert sources
- Fast retrieval for common questions (<100ms)
- T5 generation for novel questions
- Source attribution (StackExchange or Wikipedia)

## Files in This Folder

```
chatbot/
├── tfidf_vectorizer.pkl      # Fitted TF-IDF model (~500 KB)
├── tfidf_matrix.pkl          # Sparse matrix of all questions (~1-5 MB)
├── knowledge_base.pkl        # Questions, answers, sources (~500 KB)
├── metadata.json             # System stats and configuration
├── ezasmart_chatbot.ipynb    # Training notebook
└── README.md                 # This file
```

## Data Sources

### 1. StackExchange Gardening & Landscaping (~115 pairs)
- Expert-verified answers
- Practical troubleshooting
- Community-validated knowledge
- Topics: pH/EC management, nutrient solutions, system design

### 2. Wikipedia Hydroponics Articles (~1,000+ pairs)
- Encyclopedic knowledge
- Historical context and techniques
- Scientific principles
- Topics: definitions, systems, crop types, nutrient science

**Note:** All data is from verified public sources. No synthetic/fabricated data is used.

## How It Works

### Retrieval Mode (similarity ≥ 0.4)
1. User question → TF-IDF vectorization
2. Cosine similarity with all knowledge base questions
3. If best match ≥ 0.4 → return stored answer
4. **Advantages:** Fast, accurate, source attribution

### Generative Mode (similarity < 0.4)
1. User question doesn't match knowledge base well
2. T5 model generates new answer
3. Uses beam search (width=4), repetition penalty=2.5
4. **Advantages:** Handles novel questions, compositional reasoning

## Model Specifications

**Retrieval Component:**
- Algorithm: TF-IDF with cosine similarity
- Vocabulary: 5,000 features (unigrams + bigrams)
- Index size: ~1,100 Q&A pairs
- Threshold: 0.4 (empirically optimized)

**Generation Component:**
- Base model: T5 (Text-to-Text Transfer Transformer)
- Parameters: ~60M (T5-small variant)
- Fine-tuning: Hydroponics domain
- Precision: FP16 (GPU) / FP32 (CPU)
- Context window: 512 tokens input, 150 tokens output

## Usage

### In Flask App (Production)

```python
from chatbot import get_chatbot

# Get singleton instance
chatbot = get_chatbot()

# Ask question
response = chatbot.chat("What is the ideal pH for lettuce?")
print(response)
```

**API Endpoint:** `/api/chat` (POST)
```javascript
fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: 'How do I prevent algae?'})
})
```

### Manual Loading

```python
import pickle
from pathlib import Path

rag_dir = Path("Models/chatbot")

# Load components
with open(rag_dir / "tfidf_vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

with open(rag_dir / "tfidf_matrix.pkl", "rb") as f:
    tfidf_matrix = pickle.load(f)

with open(rag_dir / "knowledge_base.pkl", "rb") as f:
    kb = pickle.load(f)
    questions = kb['questions']
    answers = kb['answers']
    sources = kb['sources']
```

## Training

Run `ezasmart_chatbot.ipynb` to rebuild the system:

1. **Setup:** Install dependencies, detect environment (Colab/local)
2. **Load Model:** Download T5 from HuggingFace
3. **Load Data:** StackExchange + Wikipedia JSON files
4. **Combine:** Merge datasets with source tags
5. **Clean:** Remove duplicates, filter low-quality pairs
6. **Build RAG:** Create TF-IDF index, define hybrid logic
7. **Test:** Sample questions across different topics
8. **Save:** Pickle all components for production

**Expected output:** ~1,100 cleaned Q&A pairs ready for deployment

## Performance

**Retrieval Mode:**
- Latency: <100ms
- Accuracy: 85-95% for in-domain queries
- Source: Expert-verified or encyclopedic

**Generative Mode:**
- Latency: 200-500ms (GPU), 1-2s (CPU)
- Accuracy: Moderate (model-generated)
- Handles out-of-domain queries gracefully

**System Requirements:**
- RAM: 1-2 GB (TF-IDF + T5 model)
- Storage: ~500 MB (models + data)
- CPU: 1-2 cores (no GPU required, but faster with GPU)

## Integration with EzaSmart

The chatbot is integrated into the main Flask application at the root level:

**File structure:**
```
FarmSmart/
├── app.py                    # Flask application
├── chatbot.py                # RAG chatbot class (singleton)
├── Models/
│   └── chatbot/              # This folder (trained system)
└── static/js/chatbot.js      # Frontend UI
```

**Backend (`app.py`):**
```python
@app.route('/api/chat', methods=['POST'])
def chat():
    from chatbot import get_chatbot
    message = request.get_json().get('message')
    chatbot = get_chatbot()
    response = chatbot.chat(message)
    return jsonify({'response': response})
```

**Frontend (`chatbot.js`):**
- Chatbot icon in bottom-right corner
- Opens panel with chat interface
- Sends messages to `/api/chat`
- Displays responses with smooth animations

## Limitations

**What it handles well:**
- pH and EC management
- Nutrient solution formulation
- Common crop questions (lettuce, tomatoes, peppers)
- System types (DWC, NFT, ebb & flow)
- Troubleshooting (algae, tip burn, root rot)

**What it struggles with:**
- Questions outside hydroponics domain
- Very specific regional/niche topics
- Multi-turn conversations (no context memory)
- Non-English languages
- Real-time sensor data interpretation (use AI Nutrient Analysis model for that)

## Intended Use

**Primary users:**
- Small-scale hydroponic farmers in Africa
- Urban farmers using affordable systems
- Agricultural extension workers
- Students learning about hydroponics

**Use cases:**
- Quick reference for pH/EC ranges
- Troubleshooting plant problems
- Learning about different hydroponic systems
- Understanding nutrient management

**Not intended for:**
- Medical or pharmaceutical advice
- Soil-based agriculture
- Commercial automation without human oversight
- Legal or financial decisions

## Dependencies

**Production (required):**
```
transformers>=4.30.0
torch>=2.0.0
accelerate>=0.20.0
scikit-learn==1.3.2
numpy==1.24.3
joblib==1.3.2
```

**Training only (not needed in production):**
```
pandas
matplotlib
seaborn
```

See root `requirements.txt` for complete list.
