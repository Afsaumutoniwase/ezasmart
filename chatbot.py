"""
EzaSmart RAG Chatbot - Retrieval-Augmented Generation for Hydroponics
Loads the trained RAG system and provides chat interface.
"""
import os
import pickle
import json
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

class EzaSmartChatbot:
    def __init__(self):
        self.rag_dir = Path(__file__).parent / "Models" / "chatbot"
        self.vectorizer = None
        self.tfidf_matrix = None
        self.questions = None
        self.answers = None
        self.sources = None
        self.metadata = None
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.threshold = 0.4
        self.model_loaded = False
        self._load_system()
    
    def _load_system(self):
        """Load the RAG system components with fallback support."""
        try:
            print("Loading EzaSmart RAG Chatbot...")
            
            # Load TF-IDF vectorizer
            print("  • Loading TF-IDF vectorizer...")
            with open(self.rag_dir / "tfidf_vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)
            
            # Load TF-IDF matrix
            print("  • Loading TF-IDF matrix...")
            with open(self.rag_dir / "tfidf_matrix.pkl", "rb") as f:
                self.tfidf_matrix = pickle.load(f)
            
            # Load knowledge base
            print("  • Loading knowledge base...")
            with open(self.rag_dir / "knowledge_base.pkl", "rb") as f:
                kb = pickle.load(f)
                self.questions = kb['questions']
                self.answers = kb['answers']
                self.sources = kb['sources']
            
            # Load metadata
            print("  • Loading metadata...")
            with open(self.rag_dir / "metadata.json", "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            
            print(f"✓ Knowledge base loaded: {self.metadata['total_pairs']} Q&A pairs")
            
            # Try to load T5 model (optional - fallback to retrieval-only if fails)
            try:
                print("  • Loading T5 model (this may take a minute on first load)...")
                model_name = self.metadata.get('model_name', 'Afsa20/Farmsmart_Growmate')
                
                self.tokenizer = T5Tokenizer.from_pretrained(model_name)
                print("    ✓ Tokenizer loaded")
                
                self.model = T5ForConditionalGeneration.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if self.device.type == 'cuda' else torch.float32,
                    device_map="auto" if self.device.type == 'cuda' else None
                )
                print("    ✓ Model weights loaded")
                
                if self.device.type == 'cpu':
                    self.model = self.model.to(self.device)
                
                self.model.eval()
                self.model_loaded = True
                print(f"✓ T5 model ready on {self.device}")
                
            except RuntimeError as re:
                if "out of memory" in str(re).lower():
                    print(f"⚠ T5 Model load failed: OUT OF MEMORY")
                    print(f"  Available CUDA memory is insufficient. Using retrieval-only mode.")
                else:
                    print(f"⚠ T5 Model load failed: {re}")
                print("⚠ Running in retrieval-only mode (knowledge base answers only)")
                self.model_loaded = False
                
            except Exception as model_error:
                print(f"⚠ T5 Model load failed: {model_error}")
                print("⚠ Running in retrieval-only mode (knowledge base answers only)")
                self.model_loaded = False
            
            print("✓ EzaSmart Chatbot ready!")
            
        except Exception as e:
            print(f"✗ Critical error loading RAG system: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _retrieve_answers(self, query, top_k=3):
        """Retrieve similar Q&A pairs from knowledge base."""
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'score': float(similarities[idx]),
                'question': self.questions[idx],
                'answer': self.answers[idx],
                'source': self.sources[idx]
            })
        return results
    
    def _generate_answer(self, question, max_length=150):
        """Generate answer using T5 model."""
        input_text = f"Answer this hydroponic farming question: {question}"
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                min_length=15,
                num_beams=4,
                early_stopping=True,
                repetition_penalty=2.5,
                no_repeat_ngram_size=3,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def chat(self, question):
        """
        Main chat interface - hybrid RAG approach.
        Returns answer using retrieval if confidence is high, otherwise generates.
        Falls back to retrieval-only if T5 model not loaded.
        """
        if not question or not question.strip():
            return "Please ask a question about hydroponics!"
        
        # Retrieve similar Q&A pairs
        results = self._retrieve_answers(question, top_k=3)
        
        # Check if best match is above threshold
        if results and results[0]['score'] >= self.threshold:
            best = results[0]
            return best['answer']
        elif self.model_loaded:
            # Generate new answer with T5 if model is available
            try:
                return self._generate_answer(question)
            except Exception as e:
                print(f"Generation error: {e}")
                # Fallback to best retrieval result
                if results and results[0]['score'] > 0.2:
                    return results[0]['answer']
                else:
                    return "I don't have enough information to answer that question. Try asking about pH, EC, nutrients, or specific crops."
        else:
            # Model not loaded - use best retrieval result with disclaimer
            if results and results[0]['score'] > 0.2:
                return results[0]['answer']
            else:
                return "I don't have enough information to answer that specific question. Please try asking about:\n• pH and EC management\n• Nutrient solutions\n• Specific crops (lettuce, tomatoes, peppers)\n• System setup and troubleshooting"

# Singleton instance
_chatbot_instance = None

def get_chatbot():
    """Get or create chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = EzaSmartChatbot()
    return _chatbot_instance
