Project Specification

# Law-Law-Land

 ## 1\. Prototype Summary

 Build a document management and question-answering system that can efficiently ingest legal documents and provide accurate, source-backed answers to questions about them.

 The system will be a web application called **Law-Law-Land**, focused on the **Constitution of India** and **Supreme Court of India judgments**.

 ### Sample Queries

 - Who were the key framers of the Constitution?
- Explain Article 19 as if I were five years old.
- Show me all judgments from 2022 by Justice Chandrachud.
- Summarize the latest judgment on the appointment of the Chief Election Commissioner (CEC).

 These queries can be answered using **RAG, SQL queries, or other suitable retrieval mechanisms**, depending on the nature of the question.

 For structured queries, SQL should be generated dynamically by the LLM rather than relying on hard-coded queries. The system must include safeguards to ensure that generated SQL can **only perform read operations** and cannot modify the database.

---

 ## 2\. Data Sources

 ### Supreme Court Judgments

 **Primary source:**

 [Indian Supreme Court Judgments — Dataset](<https://github.com/vanga/indian-supreme-court-judgments/blob/main/opendata/docs/dataset.md>)

 Other reliable sources may also be considered.

 ### Constitution of India

 **Primary source:**

 NCERT book and document published by Legislative Department (GOI) 
 Other reliable sources may also be considered.

---

 ## 3\. Key Tasks

 ### 3.1 Data Ingestion Pipeline

 Build a pipeline to ingest documents and store their content in a vector database, SQL database, or another suitable storage system.

 The pipeline should:

 - Support web scraping and/or document/file processing using Python libraries.
- Clean and normalize extracted data.
- Detect and handle duplicate documents.
- Preserve important document metadata.
- Store the original source URL/link with each document so that answers can be referenced back to the source.
- Support future addition of new documents and data sources.

 ### 3.2 Question-Answering Agent

 Build an agent that can answer user queries using the stored data.

 The agent should be capable of selecting the appropriate retrieval mechanism, such as:

 - **Vector search / RAG** for unstructured questions.
- **SQL** for structured queries and filtering.
- **Other retrieval methods** where appropriate.

 **Security requirement:** The agent must not be able to modify, delete, or otherwise change the database state. Generated SQL must be restricted to safe, read-only operations.

 ### 3.3 Evaluation

 Build a **golden evaluation dataset** containing representative questions and expected answers/references.

 The evaluation should measure factors such as:

 - Answer correctness.
- Retrieval accuracy.
- Source/reference accuracy.
- Completeness.
- Hallucination / unsupported claims.

 The system should meet defined evaluation criteria before being considered production-ready.

 ### 3.4 Application

 Build a simple web application with:

- User authentication.
- Document/file upload.
- Query interface.
- Display of answers with source references.
- Basic document/query history where appropriate.
- Authentication and user management.
- Document ingestion and processing.
- Document/query retrieval.
- Question answering.
- Evaluation and monitoring where required.


 ## 4\. Core Requirements

 The prototype should prioritize:

 1. **Accurate, source-backed answers.**
2. **Reliable document ingestion and deduplication.**
3. **Traceability of answers to original sources.**
4. **Safe, read-only database access for LLM-generated SQL.**
5. **Strong evaluation using a golden dataset.**
6. **A simple and maintainable web architecture.**
