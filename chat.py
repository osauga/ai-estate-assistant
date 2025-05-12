import os
import chainlit as cl
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# --------------- CONFIG -----------------

DOCS_PATH = "./docs"  # folder where DOCX and PDF files are stored
OLLAMA_MODEL = "llama3"

# --------------- LOAD DOCUMENTS -----------------

def load_documents():
    loaders = []

    # Load PDF files
    loaders.append(DirectoryLoader(DOCS_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader))

    # Load DOCX files
    loaders.append(DirectoryLoader(DOCS_PATH, glob="**/*.docx", loader_cls=UnstructuredWordDocumentLoader))

    docs = []
    for loader in loaders:
        docs.extend(loader.load())

    return docs

# --------------- VECTOR STORE -----------------

def create_vectorstore(docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    embeddings = OllamaEmbeddings(model=OLLAMA_MODEL)
    vectorstore = FAISS.from_documents(splits, embeddings)

    return vectorstore

# --------------- MAIN CHAIN -----------------

@cl.on_chat_start
async def on_chat_start():
    # Load documents and create vectorstore
    docs = load_documents()
    vectorstore = create_vectorstore(docs)

    # Setup memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Setup chain
    llm = ChatOllama(model=OLLAMA_MODEL)
    chain = ConversationalRetrievalChain.from_llm(
        llm,
        vectorstore.as_retriever(),
        memory=memory
    )

    # Save chain to user session
    cl.user_session.set("chain", chain)

    await cl.Message("Ready! Ask me anything about your documents.").send()

# --------------- HANDLE MESSAGES -----------------

@cl.on_message
async def on_message(message: cl.Message):
    chain = cl.user_session.get("chain")  # retrieve the chain

    # Run the chain with user message
    response = chain.run(message.content)

    # Send response
    await cl.Message(response).send()
