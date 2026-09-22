# 🧪 TestNexus MCP

TestNexus MCP is an AI-powered QA and automation assistant built using Python, Streamlit, OpenAI, and Model Context Protocol (MCP).

The main goal of this project is to make QA testing and automation tasks easier by connecting multiple tools through a single AI assistant.

## 🚀 Key Features

- Generate test cases
- Generate test scenarios
- Create bug reports
- Generate QA checklists
- Search and retrieve information from documents using RAG
- Search and manage Jira issues
- Read and manage Gmail messages
- Human approval for important actions
- AI agent with MCP tool integration

## 🔧 MCP Servers

TestNexus MCP connects four main servers:

### 🧪 QA Server

Used for QA-related tasks such as:

- Test case generation
- Test scenario generation
- Bug report formatting
- QA checklist generation

### 📚 RAG Server

Used to work with uploaded documents.

It can:

- List available documents
- Search documents
- Retrieve relevant information
- Answer questions based on uploaded documents

The RAG system answers document-related questions using information retrieved from the uploaded documents.

### 📌 Jira Server

Used for Jira operations such as:

- Search issues
- Get issue details
- Create issues
- Update issues
- Add comments
- Transition issues

### ✉️ Gmail Server

Used for Gmail operations such as:

- Search emails
- Read emails
- Create drafts
- Update drafts
- Send emails
- Reply to emails
- Manage labels

## 🏗️ How It Works

```text
User
  ↓
Streamlit UI
  ↓
AI Agent
  ↓
MCP Manager
  ↓
Required MCP Server
  ↓
QA / RAG / Jira / Gmail
  ↓
Result
  ↓
User
The user sends a request through the Streamlit interface.
The AI agent understands the request and selects the required tool.
MCP connects the AI agent with the appropriate server.
The selected server performs the operation and returns the result to the user.
🛠️ Technologies Used
- Python
- Streamlit
- OpenAI
- Model Context Protocol (MCP)
- Retrieval-Augmented Generation (RAG)
- ChromaDB
- Jira API
- Gmail API
- Google OAuth
📁 Project Structure
TestNexus-MCP/
│
├── app.py
├── llm.py
├── mcp_manager.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── config/
│   └── servers.json
│
├── servers/
│   ├── qa_server.py
│   ├── rag_server.py
│   ├── jira_server.py
│   └── gmail_server.py
│
└── sample_docs/
    ├── API_Test_Cases_Correct.pdf
    ├── Selenium_Testing_Guide.pdf
    └── login_testing.pdf
⚙️ Setup
Clone the Repository
git clone https://github.com/rameshguddala19-boop/TestNexus-MCP.git
Move into the Project Directory
cd TestNexus-MCP
Create a Virtual Environment
python -m venv .venv
Activate the Virtual Environment on Windows
.\.venv\Scripts\Activate.ps1
Install Dependencies
pip install -r requirements.txt
Configure the required environment variables and service credentials before running the application.
▶️ Run the Application
Start the Streamlit application:
.\.venv\Scripts\python.exe -m streamlit run app.py
The application will open in the browser.
💡 Example Use Cases
🧪 QA
Generate test cases for the Login feature.
📚 RAG
What is the expected result for wrong credentials?
📌 Jira
Show the latest Jira issues.
✉️ Gmail
List my recent Gmail messages.
🔐 Security
Sensitive credentials are not included in the repository.
The following files are excluded using .gitignore:
credentials.json
token.json
.env
.venv/
chroma_db/
.streamlit/secrets.toml
🎯 Project Goal
The goal of TestNexus MCP is to provide a single AI-powered interface for common QA, document, Jira, and Gmail tasks instead of using each service separately.
👨‍💻 Author
Ramesh Guddala
```