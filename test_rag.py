# test_rag.py
from rag_engine import load_pdf, chunk_text, create_vector_store, search_documents

text = load_pdf("sample.pdf")
print(f"✓ Read {len(text)} characters from PDF")

chunks = chunk_text(text)
print(f"✓ Created {len(chunks)} chunks")

store = create_vector_store(chunks)
print("✓ Vector store created!")

result = search_documents("explain the main topic", store)
print("\n✓ Retrieved context:")
print(result[:400])