# HassanZindani-ResumeScreening

## Overview

The **resume screening system**, deployed on AWS EC2 using the FastAPI framework, leverages a combination of OpenAI services, cloud storage, and advanced machine learning tools to automate the process of resume evaluation. Users upload resumes in formats such as PDF and DOCX, which are stored in AWS S3 for scalability and backed up in MongoDB for data integrity. Text extraction is performed using OpenAI Vision, efficiently handling both OCR for images and text extraction from PDF and DOCX files. The extracted data is further cleaned and structured using Langchain loaders, ensuring a consistent format, which is subsequently processed by an OpenAI function to produce a structured JSON response that can be easily transformed into a DataFrame for analysis. Once structured, the data undergoes an embedding process using OpenAI's embedding API, which converts textual information into vector representations for efficient storage and retrieval. The embedded vectors are indexed in Pinecone's vector database, enabling rapid search and retrieval capabilities for downstream tasks. When a user queries the system, the search is performed against the embedded vector database, and relevant matches are identified. The OpenAI LLM model is then used to evaluate the relevancy of these matches and generate contextual responses, which are sent back to the user, providing a seamless experience for extracting key insights from resumes. This end-to-end process ensures that the system not only stores resumes efficiently but also processes and retrieves the information in a meaningful manner, providing a robust automated solution for resume screening.


## Application Backend

The backend of the Founder Tribes App is built using **FastAPI**, and the database is managed with **MongoDB**. Follow the instructions below to set up and run the backend on your local machine.

## Running the Backend

### Prerequisites

Ensure you have the following installed:
- Python 3.6+
- MongoDB
- `python3-venv` (for creating a virtual environment)

### Setup Instructions

1. **Clone the Repository**
    ```
    git clone <repository-url>
    cd HassanZindani-ResumeScreenin
    ```

2. **Create and Activate a Virtual Environment**

    If you don't have `python3-venv` installed:
    ```
    sudo apt-get install python3-venv
    ```

    To create a virtual environment:
    ```
    python3 -m venv <virtual-environment-name>
    ```

    To activate the virtual environment:
    ```
    source <virtual-environment-name>/bin/activate
    ```

3. **Install Dependencies**
    ```
    pip install -r requirements.txt

    # For Ubuntu
    apt-get install -y poppler-utils
    apt-get install -y libreoffice
    ```
    **OR**
    ```bash
     chmod +x ./script/dependencies.sh
    ./script/dependencies.sh
    ```

4. **Run the Application**

    You can start the backend server using either of the following methods:
    
    Using `make`:
    ```
    make run
    ```

    Or directly with `uvicorn`:
    ```