"""
Investigator Agent - Exhaustive Fact Extraction from Legal Documents

This agent performs the initial information retrieval step in the multi-agent pipeline.
It searches the vector store for relevant facts WITHOUT making judgements or inferences.

Key Principle: "Find everything, judge nothing"
"""

from typing import List, Dict
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.retrievers import BM25Retriever, EnsembleRetriever


class InvestigatorAgent:
    """
    The Investigator Agent uses hybrid retrieval (BM25 + Dense Vector) to find
    all relevant facts related to a query.
    
    Example:
        >>> agent = InvestigatorAgent(vectorstore_path="./legal_docs")
        >>> results = agent.search("Find all transfers of Survey No. 2306")
        >>> print(results.facts)  # List of atomic facts with citations
    """
    
    def __init__(self, vectorstore_path: str, model: str = "gemini-1.5-pro"):
        self.vectorstore = FAISS.load_local(vectorstore_path)
        self.model = model
        self._setup_hybrid_retriever()
    
    def _setup_hybrid_retriever(self):
        """
        Combines BM25 (keyword) and Dense Vector (semantic) search.
        
        Hybrid Alpha = 0.7 means:
        - 70% weight to BM25 (exact legal terms)
        - 30% weight to Dense Vector (conceptual understanding)
        """
        dense_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 10})
        bm25_retriever = BM25Retriever.from_documents(self.vectorstore.docstore._dict.values())
        
        self.retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, dense_retriever],
            weights=[0.7, 0.3]
        )
    
    def search(self, query: str) -> Dict:
        """
        Execute hybrid search and return atomic facts.
        
        Args:
            query: Natural language question about legal documents
            
        Returns:
            {
                "facts": List of extracted facts,
                "source_refs": List of [Doc:Page:Line] citations
            }
        """
        docs = self.retriever.get_relevant_documents(query)
        
        facts = []
        for doc in docs:
            facts.append({
                "content": doc.page_content,
                "citation": self._extract_citation(doc.metadata)
            })
        
        return {"facts": facts, "query": query}
    
    def _extract_citation(self, metadata: Dict) -> str:
        """Format citation as [Doc:Page:Line]"""
        return f"[Doc_{metadata.get('doc_id')}:Page_{metadata.get('page')}:Line_{metadata.get('line')}]"
