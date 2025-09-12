import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# LangChain imports for RAG
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    CSVLoader,
    UnstructuredWordDocumentLoader
)
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

class SAP_RAG:
    """RAG system for SAP company knowledge base"""
    
    def __init__(self, knowledge_base_path: str = "knowledge_base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vectorstore = None
        self.retriever = None
        self.documents = []
        
    def load_documents(self) -> List[Document]:
        """Load documents from the knowledge base directory"""
        documents = []
        
        if not self.knowledge_base_path.exists():
            print(f"Knowledge base path {self.knowledge_base_path} does not exist. Creating directory...")
            self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
            return documents
        
        # Define file loaders for different formats
        loaders_config = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.csv': CSVLoader,
            '.docx': UnstructuredWordDocumentLoader,
            '.doc': UnstructuredWordDocumentLoader
        }
        
        # Load all supported files from knowledge base
        for file_path in self.knowledge_base_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in loaders_config:
                try:
                    loader_class = loaders_config[file_path.suffix.lower()]
                    if file_path.suffix.lower() == '.csv':
                        loader = loader_class(str(file_path), encoding='utf-8')
                    else:
                        loader = loader_class(str(file_path))
                    
                    docs = loader.load()
                    
                    # Add metadata to documents
                    for doc in docs:
                        doc.metadata.update({
                            'source': str(file_path),
                            'filename': file_path.name,
                            'file_type': file_path.suffix.lower()
                        })
                    
                    documents.extend(docs)
                    print(f"Loaded {len(docs)} documents from {file_path.name}")
                    
                except Exception as e:
                    print(f"Error loading {file_path}: {str(e)}")
        
        return documents
    
    def create_sample_documents(self):
        """Create sample SAP knowledge base documents if none exist"""
        sample_docs = [
            {
                "filename": "sap_overview.txt",
                "content": """SAP Company Overview
                
SAP SE is a German multinational software corporation that makes enterprise software to manage business operations and customer relations. SAP is headquartered in Walldorf, Baden-Württemberg, Germany with regional offices in 180 countries.

Founded: 1972
Founders: Dietmar Hopp, Claus Wellenreuther, Hasso Plattner, Klaus Tschira, Hasso Plattner
Employees: Over 100,000 worldwide
Revenue: €27.84 billion (2022)

Main Products:
- SAP S/4HANA: Next-generation ERP suite
- SAP SuccessFactors: Human capital management
- SAP Ariba: Procurement and supply chain
- SAP Concur: Travel and expense management
- SAP Analytics Cloud: Business intelligence and analytics
"""
            },
            {
                "filename": "hr_policies.txt", 
                "content": """SAP HR Policies and Guidelines

WORKING HOURS
- Standard working week: 37.5 hours
- Core hours: 10:00-15:00 (must be present)
- Flexible start: 8:00-10:00
- Flexible finish: 16:00-18:30

ANNUAL LEAVE
- 25 days annual leave plus public holidays
- Additional day after 5 years service
- Holiday requests via HR portal, minimum 2 weeks notice
- Carry over maximum 5 days to next year

SICK LEAVE
- Notify manager and HR within 24 hours
- Medical certificate required for 3+ days absence
- Full pay for first 6 months, then statutory sick pay

REMOTE WORKING
- Hybrid working supported
- Up to 3 days per week remote work
- Requires manager approval
- Home office setup allowance available

BENEFITS
- Private health insurance
- Company pension scheme (5% employer contribution)
- Life insurance (4x annual salary)
- Employee share purchase plan
- Cycle to work scheme
- Gym membership discount
"""
            },
            {
                "filename": "it_support.txt",
                "content": """SAP IT Support Guide

GETTING HELP
- IT Helpdesk: Extension 2200
- Email: it-support@sap.com
- Self-service portal: itportal.sap.com
- Emergency support: 24/7 for critical issues

PASSWORD MANAGEMENT
- Passwords expire every 90 days
- Minimum 8 characters, mixed case, numbers, symbols
- Reset via self-service portal or call helpdesk
- Account lockout after 5 failed attempts

NETWORK ACCESS
- Corporate WiFi: SAP-Corporate (domain credentials)
- Guest WiFi: SAP-Guest (daily password from reception)
- VPN: Automatic on company devices, manual setup for personal devices

SOFTWARE INSTALLATION
- Standard software pre-approved and available via software center
- Custom software requires business justification
- No personal software on company devices
- License compliance mandatory

LAPTOP AND EQUIPMENT
- Standard laptop refresh every 4 years
- Damage/theft must be reported immediately
- Home working equipment available on request
- Return all equipment on last day of employment
"""
            }
        ]
        
        # Create knowledge base directory and sample files
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        
        for doc_info in sample_docs:
            file_path = self.knowledge_base_path / doc_info["filename"]
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(doc_info["content"])
                print(f"Created sample document: {doc_info['filename']}")
    
    def initialize_vectorstore(self):
        """Initialize the vector store with documents"""
        # Create sample documents if knowledge base is empty
        if not any(self.knowledge_base_path.iterdir()):
            print("Knowledge base is empty. Creating sample documents...")
            self.create_sample_documents()
        
        # Load all documents
        print("Loading documents...")
        self.documents = self.load_documents()
        
        if not self.documents:
            print("No documents found in knowledge base!")
            return
        
        # Split documents into chunks
        print("Splitting documents into chunks...")
        texts = self.text_splitter.split_documents(self.documents)
        print(f"Created {len(texts)} text chunks")
        
        # Create vector store
        print("Creating vector store...")
        self.vectorstore = FAISS.from_documents(texts, self.embeddings)
        
        # Create ensemble retriever (combining dense and sparse retrieval)
        vector_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        
        bm25_retriever = BM25Retriever.from_documents(texts)
        bm25_retriever.k = 4
        
        self.retriever = EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=[0.7, 0.3]
        )
        
        print("RAG system initialized successfully!")
    
    def search(self, query: str, k: int = 4) -> List[Document]:
        """Search for relevant documents"""
        if not self.retriever:
            print("RAG system not initialized. Call initialize_vectorstore() first.")
            return []
        
        try:
            results = self.retriever.get_relevant_documents(query)
            return results[:k]
        except Exception as e:
            print(f"Error during search: {str(e)}")
            return []
    
    def get_context(self, query: str, max_chars: int = 2000) -> str:
        """Get formatted context for a query"""
        documents = self.search(query)
        
        if not documents:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        total_chars = 0
        
        for doc in documents:
            content = doc.page_content.strip()
            source = doc.metadata.get('filename', 'Unknown source')
            
            part = f"Source: {source}\n{content}\n"
            
            if total_chars + len(part) > max_chars:
                break
            
            context_parts.append(part)
            total_chars += len(part)
        
        return "\n---\n".join(context_parts)

# Global RAG instance
_rag_instance = None

def get_rag_instance() -> SAP_RAG:
    """Get or create the global RAG instance"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = SAP_RAG()
        _rag_instance.initialize_vectorstore()
    return _rag_instance

def rag_search(query: str) -> str:
    """Main function to search the RAG system"""
    rag = get_rag_instance()
    return rag.get_context(query)