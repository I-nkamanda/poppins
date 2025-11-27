# RAG Update Log

**Date**: 2025-11-24
**Status**: ✅ Completed

## 📝 Summary
RAG vector database has been successfully upgraded to v1.5 with **Semantic Chunking**. This major update improved retrieval accuracy by 5% on average, with up to 12.7% improvement on specific queries.

## 🎉 Version 1.5 - Semantic Chunking Implementation

### Implemented Changes
The following changes have been implemented and deployed:

1.  **Semantic Chunking (`SemanticChunker`)**:
    - Replaced fixed-size chunking with meaning-based chunking
    - Uses `langchain-experimental` package
    - Automatically splits documents at semantic boundaries
    - Improves context preservation and retrieval accuracy

2.  **Enhanced Metadata Extraction**:
    - Automatically extracts section headers from documents
    - Stores section information in chunk metadata
    - Improves context understanding during retrieval

3.  **Checkpointing System**:
    - Saves progress after each PDF file processing
    - Prevents data loss during long-running generation
    - Allows resuming from interruptions

4.  **Rate Limiting Improvements**:
    - `RateLimitedEmbeddings` wrapper class
    - Global rate limiting for all embedding API calls
    - Prevents API quota exhaustion

## 📊 Performance Comparison Results

**Three versions compared**:
- **Legacy (v1.0)**: Simple fixed-size chunking
- **Filtered (v1.4)**: Page filtering + text cleaning
- **Semantic (v1.5)**: Semantic chunking + metadata

**Key Findings**:
- Average 5% improvement in similarity scores
- Up to 12.7% improvement on specific queries (e.g., "overfitting prevention")
- Better semantic understanding of user queries
- Section metadata improves context interpretation

**Example (Query: "딥러닝에서 과적합을 방지하는 방법")**:
- Legacy/Filtered: Found English documents with generic overfitting explanations (score: 0.5362)
- Semantic: Found Korean document directly explaining "초과학습(Overfitting)" (score: 0.4679, 12.7% better!)

## ✅ Deployment Status

1. **Vector DB Generated**:
   - Location: `RAG vector generator/vector_db/python_textbook_gemini_db_semantic`
   - Total: 38 PDF files, 1090 chunks
   - Generation time: ~4 hours (2025-11-24)

2. **Application Updated**:
   - `main.py` now uses semantic vector DB by default
   - Backward compatible with environment variable override

3. **Documentation Updated**:
   - `CHANGELOG.md`: v1.5.0 entry added
   - `README.md`: References semantic chunking
   - Comparison analysis report created

## 🔍 Version History

### [1.5.0] - 2025-11-24 ✅
- Semantic Chunking implementation
- 3-way performance comparison
- Checkpointing system
- **Status**: Deployed

### [1.4.0] - 2025-11-23 ✅  
- Page filtering (목차, 색인, 저작권 페이지 제외)
- Text cleaning (헤더/푸터 제거, 공백 정리)
- Rate limiting and batch processing
- **Status**: Deployed (now superseded by v1.5)

### [1.0.0] - Initial Version
- Simple fixed-size chunking
- **Status**: Archived as legacy

## 🚀 Future Improvements

Planned enhancements for v1.6+:

1. **Query Rewriting**:
   - LLM-based query expansion
   - Improves search recall
   - Estimated 5-10% improvement

2. **Reranking**:
   - Two-stage retrieval (Vector Search + Cross-encoder)
   - Top-20 candidates → Top-3 refined results
   - Estimated 10-15% improvement
   - Options: Cohere API (recommended) or local bge-reranker

3. **Hybrid Search**:
   - Combine vector search with BM25 keyword search
   - Better handling of technical terms and proper nouns

## 📂 Backup Info
- Previous versions backed up at: `vector_db/.vector_db-oldver/`
  - `python_textbook_gemini_db_legacy` (v1.0)
  - `python_textbook_gemini_db_filtered` (v1.4)
- Semantic DB (v1.5) at: `RAG vector generator/vector_db/python_textbook_gemini_db_semantic`

---

**For detailed comparison analysis**, see: `rag_comparison_analysis.md`
