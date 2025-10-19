import os
import pickle
import chromadb
from langchain.document_loaders import PyPDFLoader
import ollama

SAVED_FOLDER = "saved"

def doc_loader(path):
    if path.endswith('.pdf'):
        loader = PyPDFLoader(path)
        data = loader.load()
        content_list = [page.page_content for page in data]
        return content_list
    else:
        raise ValueError("Unsupported file format. Currently, only PDF is supported.")

def vector_creator(content, save_name=None):
    client = chromadb.Client()
    collection = client.create_collection(name="docs")

    # Store each document in a vector embedding database
    embeddings_data = []
    for i, d in enumerate(content):
        response = ollama.embeddings(model="mxbai-embed-large", prompt=d)
        embedding = response["embedding"]
        collection.add(
            ids=[str(i)],
            embeddings=[embedding],
            documents=[d]
        )
        embeddings_data.append({"id": str(i), "embedding": embedding, "document": d})

    # Save collection data (only the embeddings and documents, not the entire object)
    if save_name:
        if not os.path.exists(SAVED_FOLDER):
            os.makedirs(SAVED_FOLDER)
        save_path = os.path.join(SAVED_FOLDER, f"{save_name}.pkl")
        with open(save_path, "wb") as f:
            pickle.dump(embeddings_data, f)

    return collection

def load_saved_embedding(file_name):
    file_path = os.path.join(SAVED_FOLDER, file_name)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            embeddings_data = pickle.load(f)  # Load the saved data

        # Recreate the collection using the loaded data
        client = chromadb.Client()
        collection = client.create_collection(name="docs")
        for item in embeddings_data:
            collection.add(
                ids=[item["id"]],
                embeddings=[item["embedding"]],
                documents=[item["document"]]
            )
        return collection  # Return the recreated collection
    else:
        raise FileNotFoundError(f"Embedding file {file_name} not found.")


def chat(collection, query):
    prompt = query
    response = ollama.embeddings(
        prompt=prompt,
        model="mxbai-embed-large"
    )

    results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=1
    )

    data = results['documents'][0][0]
    output = ollama.generate(
        model="llama3.1:8b",
        prompt=f"Your work is to answer the user query: {prompt} using this data: {data}. give short answers."
    )

    return output['response']
