from pathlib import Path
from operator import itemgetter

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.load import dumps, loads

from ami.config import Config
from ami.ai import Filesystem
from ami.tools.base import SingletonTool


RAG_TEMPLATE = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.

# Question: {{question}}

# Context: {{context}}

# Background info: {background}

# Answer:
"""

class RAG(SingletonTool):
    """ RAG (Retrieval Augmentation Generation)
        - Entire RAG system and pipeline

    """

    def __init__(self, allowed_suffix=[".pdf"]):

        self.allowed_suffix = allowed_suffix

        config = Config()
        self.fs = Filesystem("RAG")

        self._documents_path = self.fs / config['rag']["documents_directory"]
        self._vector_stores_path = self.fs / config['rag']["vector_dbs_directory"]
        self._memory_path = self.fs / config['rag']["memory_directory"]

        self.chunk_size = config['rag']["chunk_size"]
        self.chunk_overlap = config['rag']["chunk_overlap"]

        self._embeddings_function = None
        self._vector_cache = {}

    def __getitem__(self, vectorstore_name: str):

        if not isinstance(vectorstore_name, str):
            raise ValueError(f"RAG vectorstore are index by string! not '{type(vectorstore_name)}'")

        if vectorstore_name in self._vector_cache:
            return self._vector_cache[vectorstore_name]

        if vectorstore_name in self.saved_vectorstores:
            return self.load_vector_store(vectorstore_name)

        raise ValueError(f"RAG vectorstore '{vectorstore_name}' is not cached and cannot be found!")

    def _check_make_directory(self, directory_path: Path) -> None:
        if not directory_path.exists():
            directory_path.mkdir(parents=True, exist_ok=True)
        if not directory_path.is_dir():
            raise NotADirectoryError(f"{directory_path} is not a directory")
        return directory_path

    @property
    def documents_path(self):
        self._check_make_directory(self._documents_path)
        return self._documents_path
    @property
    def vector_stores_path(self):
        self._check_make_directory(self._vector_stores_path)
        return self._vector_stores_path
    @property
    def memory_path(self):
        self._check_make_directory(self._memory_path)
        return self._memory_path

    @property
    def documents(self):
        return [ file for file in self.documents_path.iterdir() if file.suffix in self.allowed_suffix and file.is_file() ]

    @property
    def embeddings(self):
        if self._embeddings_function is None:
            self._embeddings_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        return self._embeddings_function

    @property
    def saved_vectorstores(self):
        return [ vectorstore.name for vectorstore in self.vector_stores_path.iterdir() if vectorstore.is_dir() ]

    def save_vector_store(self, vectorstore, savepath):

        if not isinstance(vectorstore, FAISS):
            raise ValueError("Must be of a FAISS vector database!")

        if not savepath.parent.is_dir():
            raise NotADirectoryError("Parent directory must exist to save!")

        vectorstore.save_local(savepath)

    def index_documents(self, documents: list, chunk_size: int=None, chunk_overlap: int=None):

        if not isinstance(chunk_size, int):
            chunk_size = self.chunk_size
        if not isinstance(chunk_overlap, int):
            chunk_overlap = self.chunk_overlap

        embed_docs = []

        for doc in documents:
            doc = Path(doc)
            if not doc.is_file() or doc.suffix != ".pdf":
                raise ValueError(f"Rag.get_vector_store({doc}) must be an existing pdf file!")
 
            docs = PyPDFLoader(str(doc)).load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            splits = text_splitter.split_documents(docs)

            for split in splits:
                split.metadata['details'] = "Include user generated details here!"

            embed_docs.extend(splits)

        return FAISS.from_documents(embed_docs, self.embeddings)

    def create_vector_store(self, documents: list, name: str):
        
        save_path  = self.vector_stores_path / name
        db = self.index_documents(documents)

        self.save_vector_store(db, save_path)
        return db

    def load_vector_store(self, name: str):
        
        load_path  = self.vector_stores_path / name
        
        if not load_path.is_dir():
            raise FileNotFoundError(f"{load_path} not found!")

        db = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True)
        return db

    @property
    def query_generator_template(self):
        template = """You are an AI language model assistant. Your task is to generate five different versions of the given user question to retrieve relevant documents from a vector 
            database. By generating multiple perspectives on the user question, your goal is to help the user overcome some of the limitations of the distance-based similarity search.
            You want to be extremely general in the response to trigger the vector db maximally. Provide these alternative questions separated by newlines. Original question: {question}"""
        return ChatPromptTemplate.from_template(template)

    def basic_rag(self, query, vectorstore_name, llm, reference_data=""):
        format_docs = lambda docs: "\n\n".join(doc.page_content for doc in docs)

        def get_unique_union(documents: list[list]):
            flattened_docs = [ dumps(doc) for sublist in documents for doc in sublist ]
            unique_docs = list(set(flattened_docs))
            return [ loads(doc) for doc in unique_docs ]

        if not isinstance(reference_data, str):
            raise ValueError(f"RAG.basic_rag -> reference_data must be of type string! Not {type(reference_data)}")

        retriever = self[vectorstore_name].as_retriever()

        generate_queries = (self.query_generator_template | llm | StrOutputParser() | (lambda x: x.split("\n")) )
        retrieval_chain = generate_queries | retriever.map() | get_unique_union
        #docs = retrieval_chain.invoke({"question":query})

        prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE.format(background=reference_data))
        final_rag_chain = ({"context": retrieval_chain, "question": itemgetter("question")}  | prompt | llm | StrOutputParser() )

        return final_rag_chain.invoke({"question":query})
