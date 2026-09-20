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