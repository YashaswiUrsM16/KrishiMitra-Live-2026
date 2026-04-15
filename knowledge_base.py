import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from database import db, AgriculturalKnowledge, Role
from flask import Flask

# Initialize Hugging Face model (Professional Grade & Highly Accurate)
# Model: all-MiniLM-L6-v2 is one of the most popular and optimized for sentence embeddings
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

class AgriVectorStore:
    def __init__(self, index_path="agri_index.faiss"):
        self.index_path = index_path
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = None
        self.knowledge_ids = []
        
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            # Metadata mapping would usually go in a separate file or DB
            print("Loaded existing FAISS index.")
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            print("Created new FAISS index.")

    def add_texts(self, texts, metadata_ids):
        """Encodes texts using Hugging Face model and adds to FAISS."""
        embeddings = model.encode(texts)
        embeddings = np.array(embeddings).astype('float32')
        self.index.add(embeddings)
        self.knowledge_ids.extend(metadata_ids)
        faiss.write_index(self.index, self.index_path)

    def search(self, query, top_k=3):
        """Searches the vector store for most relevant agricultural facts."""
        if self.index.ntotal == 0:
            return []
            
        query_embedding = model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        distances, indices = self.index.search(query_embedding, top_k)
        
        return [self.knowledge_ids[i] for i in indices[0] if i != -1]

def seed_professional_data(app):
    """Seed the database and vector store with highly accurate agricultural data."""
    with app.app_context():
        # Check if basic data already exists
        if AgriculturalKnowledge.query.count() > 0:
            return

        print("Seeding validated agricultural data...")
        facts = [
            {
                "cat": "Soil Suitability",
                "soil": "Red Soil",
                "crop": "Mango",
                "content": "Mangoes are perfectly suited for Red Soil provided the soil is deep and well-drained. Red soils in South India (like Karnataka) are ideal because they offer good aeration for deep mango root systems.",
                "source": "Expert Validation / Agri-University Guidelines"
            },
            {
                "cat": "Soil Suitability",
                "soil": "Red Soil",
                "crop": "Ragi",
                "content": "Ragi (Finger Millet) is the most suitable crop for Red Soils. It is drought-tolerant and performs exceptionally well even in the nutrient-limited conditions typical of red soil regions.",
                "source": "Krishi Vigyan Kendra (KVK) Research"
            },
            {
                "cat": "Soil Suitability",
                "soil": "Alluvial Soil",
                "crop": "Rice",
                "content": "Alluvial soil is rich in nutrients and is excellent for water-intensive crops like Rice.",
                "source": "General Agronomy"
            }
        ]

        texts_to_embed = []
        db_ids = []
        
        for f in facts:
            item = AgriculturalKnowledge(
                category=f['cat'],
                content=f['content'],
                soil_type=f['soil'],
                crop_name=f['crop'],
                source=f['source']
            )
            db.session.add(item)
            db.session.flush() # Get the ID
            texts_to_embed.append(f"{f['soil']} {f['crop']}: {f['content']}")
            db_ids.append(item.id)

        db.session.commit()
        
        # Add to Vector Store
        store = AgriVectorStore()
        store.add_texts(texts_to_embed, db_ids)
        print("Knowledge base initialization complete.")

if __name__ == "__main__":
    # For standalone testing/seeding
    from app import app
    seed_professional_data(app)
