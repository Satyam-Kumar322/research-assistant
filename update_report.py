import sys

with open('project_report.tex', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    (
        r'''The project was completed under the guidance of \textbf{Prof. [Guide Name]}, \textbf{[Guide Institution]}. The work includes secure user authentication, JWT login, MongoDB Atlas database integration, PDF/DOCX/TXT document upload, text extraction, text cleaning, chunk generation, embedding generation, retrieval mechanism, prompt building, local LLM integration, AI chatbot functionality, GitHub version control, and Render deployment.''',
        r'''The project was completed under the guidance of \textbf{Prof. [Guide Name]}, \textbf{[Guide Institution]}. The work includes secure user authentication, JWT login via FastAPI, SQLite and MongoDB Atlas database integration, PDF/DOCX/TXT document upload, text extraction, text cleaning, chunk generation, semantic embedding generation using sentence-transformers, FAISS vector search retrieval mechanism, prompt building, local LLM integration, AI chatbot functionality, GitHub version control, and deployment.'''
    ),
    (
        r'''This project helped me understand how a real-world application is built from frontend to backend. I learned about HTML, CSS, JavaScript, Node.js, Express.js, MongoDB Atlas, JWT, file upload, text extraction, RAG workflow, Ollama/local LLM integration, GitHub version control, and Render deployment.''',
        r'''This project helped me understand how a real-world application is built from frontend to backend. I learned about HTML, CSS, JavaScript, Python, FastAPI, SQLite, MongoDB Atlas, FAISS, JWT, file upload, text extraction, RAG workflow, Ollama/local LLM integration, GitHub version control, and deployment.'''
    ),
    (
        r'''The project uses HTML, CSS, JavaScript, Node.js, Express.js, MongoDB Atlas, JWT, Multer, document parsing tools, GitHub, Render, and Ollama/local LLM support. The system is designed to help users securely manage documents and interact with their content through a RAG-based chatbot. This report explains the complete system design, implementation, database structure, MongoDB Atlas section, APIs, screenshots, testing, results, limitations, and future scope.''',
        r'''The project uses HTML, CSS, JavaScript, Python, FastAPI, SQLite, MongoDB Atlas, FAISS, JWT, document parsing tools (PyMuPDF, python-docx), GitHub, and Ollama/local LLM support. The system is designed to help users securely manage documents and interact with their content through a RAG-based chatbot. This report explains the complete system design, implementation, database structure, database integration, APIs, screenshots, testing, results, limitations, and future scope.'''
    ),
    (
        r'''\item Implemented backend APIs using Node.js and Express.js.''',
        r'''\item Implemented backend APIs using Python and FastAPI.'''
    ),
    (
        r'''\item Connected the system with MongoDB Atlas.''',
        r'''\item Connected the system with SQLite and MongoDB Atlas.'''
    ),
    (
        r'''\section{MongoDB in Full-Stack Applications}
MongoDB is a NoSQL database used to store flexible JSON-like documents. It is useful for full-stack applications because schemas can evolve easily. MongoDB Atlas provides a cloud-hosted database that can be accessed by deployed backend services.''',
        r'''\section{Databases in Full-Stack Applications}
The project utilizes both relational and NoSQL databases. SQLite is used via SQLAlchemy for structured relational data such as users and workspaces, providing reliability and integrity. MongoDB Atlas is used as a NoSQL document database to store flexible text and metadata for uploaded documents and processed chunks.'''
    ),
    (
        r'''\begin{itemize}
    \item Visual Studio Code.
    \item Node.js and npm.
    \item MongoDB Atlas account.
    \item Git and GitHub.
    \item Render account.
    \item Ollama for local LLM.
    \item Overleaf for report preparation.
\end{itemize}''',
        r'''\begin{itemize}
    \item Visual Studio Code.
    \item Python 3.
    \item SQLite and MongoDB Atlas account.
    \item Git and GitHub.
    \item Ollama for local LLM.
    \item Overleaf for report preparation.
\end{itemize}'''
    ),
    (
        r'''\begin{tabular}{|l|p{10cm}|}
\hline
\textbf{Technology} & \textbf{Use in Project} \\ \hline
HTML & Used to create the structure of homepage, login, registration, and dashboard pages. \\ \hline
CSS & Used for styling, layout, colors, cards, modals, dashboard design, and responsive UI. \\ \hline
JavaScript & Used for frontend logic, API calls, local storage, chatbox interaction, and dynamic sections. \\ \hline
Node.js & Used as the backend runtime environment. \\ \hline
Express.js & Used to create REST APIs and route handling. \\ \hline
MongoDB Atlas & Used as the cloud database for users, documents, and chunks. \\ \hline
Mongoose & Used to define schemas and interact with MongoDB. \\ \hline
JWT & Used for secure token-based authentication. \\ \hline
Multer & Used for file upload handling. \\ \hline
pdf-parse / parser tools & Used for extracting text from uploaded PDF files. \\ \hline
Ollama & Used to run local LLM models for AI chat responses. \\ \hline
GitHub & Used for version control and repository management. \\ \hline
Render & Used for backend deployment. \\ \hline
\end{tabular}''',
        r'''\begin{tabular}{|l|p{10cm}|}
\hline
\textbf{Technology} & \textbf{Use in Project} \\ \hline
HTML & Used to create the structure of homepage, login, registration, and dashboard pages. \\ \hline
CSS & Used for styling, layout, colors, cards, modals, dashboard design, and responsive UI. \\ \hline
JavaScript & Used for frontend logic, API calls, local storage, chatbox interaction, and dynamic sections. \\ \hline
Python & Core programming language for the backend. \\ \hline
FastAPI & High-performance framework to create REST APIs and route handling. \\ \hline
SQLite \& MongoDB & Used as the primary relational database (SQLite) and NoSQL datastore (MongoDB). \\ \hline
SQLAlchemy & Used as the ORM to define schemas and interact with SQLite. \\ \hline
FAISS & Used as the high-speed vector database for similarity search. \\ \hline
JWT (python-jose) & Used for secure token-based authentication. \\ \hline
PyMuPDF & Used for extracting text from uploaded PDF files. \\ \hline
Ollama & Used to run local LLM models for AI chat responses. \\ \hline
GitHub & Used for version control and repository management. \\ \hline
\end{tabular}'''
    ),
    (
        r'''The selected technologies are widely used in full-stack development. Node.js and Express.js are suitable for building APIs. MongoDB Atlas provides cloud database support. JWT provides secure authentication. JavaScript allows frontend and backend development using the same language. Ollama enables local AI experimentation.''',
        r'''The selected technologies are widely used in full-stack development. Python and FastAPI are suitable for building highly performant AI-integrated APIs. SQLite and MongoDB Atlas provide robust structured and unstructured database support respectively. FAISS is highly optimized for fast similarity search. JWT provides secure authentication. Ollama enables local AI experimentation.'''
    ),
    (
        r'''User Interface $\rightarrow$ Frontend JavaScript $\rightarrow$ REST API Request $\rightarrow$ Express Backend $\rightarrow$ MongoDB Atlas $\rightarrow$ Document Processing Pipeline $\rightarrow$ RAG Retriever $\rightarrow$ Ollama Local LLM $\rightarrow$ AI Response''',
        r'''User Interface $\rightarrow$ Frontend JavaScript $\rightarrow$ REST API Request $\rightarrow$ FastAPI Backend $\rightarrow$ SQLite \& MongoDB $\rightarrow$ Document Processing Pipeline $\rightarrow$ FAISS Retriever $\rightarrow$ Ollama Local LLM $\rightarrow$ AI Response'''
    ),
    (
        r'''\begin{itemize}
    \item \textbf{Backend:} Express server, authentication routes, upload routes, chat routes, middleware, and utility functions.
    \item \textbf{Database:} MongoDB Atlas stores users, documents, and chunks.
    \item \textbf{AI Layer:} Retriever, prompt builder, and local LLM.
\end{itemize}''',
        r'''\begin{itemize}
    \item \textbf{Backend:} FastAPI server, authentication routes, workspace routes, chat routes, middleware, and utility functions.
    \item \textbf{Database:} SQLite stores relational user and workspace data; MongoDB Atlas stores raw text and processed chunks. FAISS indexes embeddings.
    \item \textbf{AI Layer:} Retriever, prompt builder, and local LLM.
\end{itemize}'''
    ),
    (
        r'''\chapter{Backend Design}
\section{Server Setup}
The backend is created using Node.js and Express.js. It uses middleware for CORS, JSON parsing, and static file serving.

\section{Route Structure}
\begin{itemize}
    \item \textbf{authRoutes.js:} Handles registration and login.
    \item \textbf{uploadRoutes.js:} Handles document upload, metadata, processing, and delete operations.
    \item \textbf{chatRoutes.js:} Handles AI question answering.
\end{itemize}

\section{Utility Functions}
The project uses multiple utility files:
\begin{itemize}
    \item textCleaner.js
    \item chunkEngine.js
    \item embeddingEngine.js
    \item retriever.js
    \item promptBuilder.js
\end{itemize}

\section{Environment Variables}
Important values such as MongoDB URI, JWT secret, and API keys should be stored in the .env file. This file must not be pushed to GitHub.''',
        r'''\chapter{Backend Design}
\section{Server Setup}
The backend is created using Python and FastAPI. It uses middleware for CORS, request parsing, and static file serving.

\section{Route Structure}
\begin{itemize}
    \item \textbf{routers/auth.py:} Handles registration and login.
    \item \textbf{routers/workspace.py:} Handles workspace and project creation.
    \item \textbf{routers/documents.py:} Handles document upload, metadata, and delete operations.
    \item \textbf{routers/rag.py:} Handles AI question answering and indexing.
\end{itemize}

\section{Utility Functions}
The project uses multiple utility files:
\begin{itemize}
    \item text_cleaning.py
    \item chunking_engine.py
    \item embedding_engine.py
    \item retrieval_engine.py
    \item prompt_builder.py
\end{itemize}

\section{Environment Variables}
Important values such as DATABASE_URL, MONGODB_URL, JWT secret, and API keys should be stored in the .env file. This file must not be pushed to GitHub.'''
    ),
    (
        r'''When the user registers, the frontend sends the user details to the backend. The backend checks the data and stores the user in MongoDB.''',
        r'''When the user registers, the frontend sends the user details to the backend. The backend checks the data, hashes the password using bcrypt, and stores the user in the SQLite database via SQLAlchemy.'''
    ),
    (
        r'''\chapter{MongoDB Atlas Integration}
\section{Introduction to MongoDB Atlas}
MongoDB Atlas is a cloud-hosted database platform. It allows developers to create and manage MongoDB clusters without installing a database locally. In this project, MongoDB Atlas is used to store user accounts, uploaded document metadata, extracted text information, and processed chunks.

\section{Why MongoDB Atlas is Used}
MongoDB Atlas is selected because it is easy to connect with Node.js applications and provides cloud access. It supports flexible schemas, which is useful because the project stores different types of data such as user details, documents, chunks, embeddings, metadata, and quality reports.

\section{Database Collections}
The project mainly uses the following collections:
\begin{itemize}
    \item \textbf{Users Collection:} Stores registered user information.
    \item \textbf{Documents Collection:} Stores uploaded file metadata.
    \item \textbf{Chunks Collection:} Stores processed chunks and embeddings.
\end{itemize}''',
        r'''\chapter{Database Integration (SQLite \& MongoDB)}
\section{Introduction to Database Setup}
This project adopts a hybrid database approach. SQLite is used as the primary relational database to manage users, sessions, workspaces, and document metadata. MongoDB Atlas, a cloud-hosted NoSQL platform, is used to store large volumes of unstructured data such as raw extracted text, clean text, and document chunks.

\section{Why a Hybrid Approach is Used}
SQLite with SQLAlchemy provides ACID compliance and structured relationships, ideal for authentication and workspace management in a FastAPI application. MongoDB Atlas provides flexible schemas for variable-length text data, reducing the burden on the relational database.

\section{Database Tables and Collections}
The project uses the following tables (SQLite) and collections (MongoDB):
\begin{itemize}
    \item \textbf{Users Table (SQLite):} Stores registered user information and password hashes.
    \item \textbf{Workspaces Table (SQLite):} Stores user project workspaces.
    \item \textbf{Documents Table (SQLite):} Stores uploaded file metadata.
    \item \textbf{Chunks Collection (MongoDB):} Stores processed text chunks and embeddings.
    \item \textbf{FAISS Index (Local):} Stores vector embeddings for fast similarity search.
\end{itemize}'''
    ),
    (
        r'''The backend connects to MongoDB Atlas using a connection string. This connection string is stored in the .env file. When the server starts, the connection function connects the Express backend to MongoDB Atlas.''',
        r'''The backend connects to MongoDB Atlas using Motor (AsyncIOMotorClient) and to SQLite using SQLAlchemy. Connection strings are stored in the .env file. When the server starts, startup events test the MongoDB Atlas connection.'''
    ),
    (
        r'''\section{MongoDB Benefits in This Project}
\begin{itemize}
    \item Stores user authentication data.
    \item Stores uploaded document metadata.
    \item Stores chunked text.
    \item Supports flexible schema structure.
    \item Works with deployed backend on Render.
    \item Easy to monitor and manage collections.
\end{itemize}''',
        r'''\section{Database Benefits in This Project}
\begin{itemize}
    \item SQLite ensures relational integrity for auth and workspaces.
    \item MongoDB effortlessly stores large chunks of unstructured text.
    \item FAISS enables lightning-fast semantic search.
    \item Works with deployed backends.
    \item Scalable structure for future expansions.
\end{itemize}'''
    ),
    (
        r'''The document upload module allows users to upload PDF, DOCX, and TXT files. The frontend sends the file using FormData, and the backend receives it using Multer.''',
        r'''The document upload module allows users to upload PDF, DOCX, and TXT files. The frontend sends the file using FormData, and the FastAPI backend processes it securely using Python's multipart capabilities.'''
    ),
    (
        r'''\section{Chunking}
Chunking divides long text into smaller pieces. A large document cannot be passed completely to the AI model, so smaller chunks are created.''',
        r'''\section{Chunking}
Chunking divides long text into smaller pieces using intelligent recursive text splitting. A large document cannot be passed completely to the AI model, so smaller chunks are created while respecting semantic boundaries.'''
    ),
    (
        r'''\section{Embedding Generation}
Embedding converts text into numerical vectors. These vectors represent the meaning of the text in a numerical form.''',
        r'''\section{Embedding Generation and FAISS}
Embedding converts text into numerical vectors using models like sentence-transformers. These vectors are then indexed into a FAISS (Facebook AI Similarity Search) index, optimizing them for rapid and scalable semantic similarity retrieval.'''
    ),
    (
        r'''\chapter{Database Schema}
\section{User Schema}
\begin{lstlisting}[language=JavaScript]
const userSchema = new mongoose.Schema({
    name: String,
    email: String,
    password: String
});
\end{lstlisting}

\section{Document Schema}
\begin{lstlisting}[language=JavaScript]
const documentSchema = new mongoose.Schema({
    fileName: String,
    title: String,
    author: String,
    fileType: String,
    filePath: String,
    fileSize: Number,
    pageCount: Number,
    textLength: Number,
    chunks: [String],
    qualityReport: Object
});
\end{lstlisting}

\section{Chunk Schema}
\begin{lstlisting}[language=JavaScript]
const chunkSchema = new mongoose.Schema({
    documentId: ObjectId,
    fileName: String,
    chunkText: String,
    chunkIndex: Number,
    embedding: [Number]
});
\end{lstlisting}

\section{Schema Explanation}
The User schema stores authentication data. The Document schema stores file metadata and processing information. The Chunk schema stores text chunks and embeddings used by the retriever.''',
        r'''\chapter{Database Schema}
\section{User Schema}
\begin{lstlisting}[language=Python]
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
\end{lstlisting}

\section{Document Schema}
\begin{lstlisting}[language=Python]
class Document(Base):
    __tablename__ = "documents"
    document_id = Column(String(36), primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.workspace_id"))
    title = Column(String(500), nullable=True)
    path = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    file_type = Column(String(20), nullable=True)
\end{lstlisting}

\section{Chunk Schema}
\begin{lstlisting}[language=Python]
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    chunk_id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.document_id"))
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
\end{lstlisting}

\section{Schema Explanation}
The User and Document schemas define relational tables managed by SQLAlchemy for structured data storage. The Chunk schema maintains relationships to documents and holds specific chunk indices. Text and embeddings are additionally managed in FAISS and MongoDB.'''
    ),
    (
        r'''Render is used to deploy the backend. The deployed service runs the Node.js server and connects to MongoDB Atlas.''',
        r'''Render is used to deploy the backend. The deployed service runs the Uvicorn ASGI server hosting the FastAPI application and connects to the respective databases.'''
    ),
    (
        r'''\item MongoDB Atlas connected successfully.''',
        r'''\item SQLite and MongoDB Atlas connected successfully.'''
    )
]

new_content = content
for i, (search, replace) in enumerate(replacements):
    if search not in new_content:
        print(f"Warning: Replacement {i} not found.")
    new_content = new_content.replace(search, replace)
    
if new_content != content:
    with open('project_report.tex', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Updated successfully')
else:
    print('No changes made.')

