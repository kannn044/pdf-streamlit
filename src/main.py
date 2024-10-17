import os
import json
import time
import base64
import zipfile
import requests
import sseclient
from io import BytesIO
import streamlit as st
import streamlit.components.v1 as components

BACKEND_URL = "http://127.0.0.1:5000"

# if 'conversation_history' not in st.session_state:
#     st.session_state.conversation_history = []

# # Initialize conversation history in session state (if not already present)
# if 'conversation_history' not in st.session_state:
#     st.session_state.conversation_history = []

# # Ensure the API URL is correctly set
# API_URL = "http://10.1.0.101:8080/api/generate"

# def get_chat_stream():
#     # Prepare the headers and JSON body for the new API
#     headers = {'Content-Type': 'application/json'}
#     data = {
#         "model": "llama3.2",
#         "messages": st.session_state.conversation_history  # Send the multi-turn conversation from session state
#     }

#     # Validate the URL before making a request
#     if not API_URL:
#         st.error("Invalid URL for the API.")
#         return

#     # Send a POST request to the chat API and stream the response
#     try:
#         response = requests.post(API_URL, json=data, headers=headers, stream=True)

#         if response.status_code == 200:
#             # Prepare to store the assistant's full response
#             assistant_response = ""

#             # Create a placeholder for the assistant's response that will be updated
#             response_placeholder = st.empty()

#             # Stream and display the assistant's response with a typing effect
#             for chunk in response.iter_lines():
#                 if chunk:
#                     chunk_data = json.loads(chunk.decode('utf-8'))  # Decode the chunk into JSON
#                     # Extract the 'response' field and append to the assistant's full response
#                     assistant_response += chunk_data.get('response', '')

#                     # Update the placeholder with the assistant's response
#                     response_placeholder.markdown(format_message("assistant", assistant_response), unsafe_allow_html=True)

#                     # Simulate a typing delay between chunks (adjust this time as necessary)
#                     time.sleep(0.05)

#             # After streaming, store the assistant's response in session state
#             st.session_state.conversation_history.append({"role": "assistant", "content": assistant_response})

#         else:
#             st.error(f"Failed to reach API: {response.status_code}")

#     except requests.exceptions.RequestException as e:
#         st.error(f"Error connecting to the API: {e}")

# # Function to format chat messages in HTML/CSS
# def format_message(role, message):
#     if role == "user":
#         return f"""
#         <div style='text-align: right; padding: 10px;'>
#             <div style='display: inline-block; background-color: #DCF8C6; color:black; padding: 10px; border-radius: 10px; max-width: 70%;'>
#                 <strong>User:</strong> {message}
#             </div>
#         </div>
#         """
#     else:
#         return f"""
#         <div style='text-align: left; padding: 10px;'>
#             <div style='display: inline-block; background-color: #E8E8E8; color:black; padding: 10px; border-radius: 10px; max-width: 70%;'>
#                 <strong>Assistant:</strong> {message}
#             </div>
#         </div>
#         """

# st.title("Chat with Ollama (Llama3.2 Model)")
# new_prompt = st.text_input("Enter your next message:")
# if new_prompt:
#     # Add the new user message to the conversation history in session state
#     st.session_state.conversation_history.append({"role": "user", "content": new_prompt})

#     # Display the new user message
#     st.markdown(format_message("user", new_prompt), unsafe_allow_html=True)

#     # Stream the response from the assistant
#     get_chat_stream()

# # Display the conversation so far from session state
# for message in st.session_state.conversation_history:
#     st.markdown(format_message(message['role'], message['content']), unsafe_allow_html=True)

# Add a new prompt to the conversation history
def upload_pdf(pdf_file):
    files = {'file': pdf_file}
    try:
        response = requests.post(f"{BACKEND_URL}/upload", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return {"error": f"Request failed: {e}"}
    except ValueError:
        st.error("Failed to decode JSON from response")
        return {"error": "Failed to decode JSON from response"}

def get_full_pdf_file(filename):
    params = {'filename': filename.replace('.txt', '.pdf')}
    response = requests.get(f"{BACKEND_URL}/get_full_pdf", params=params)

    if response.status_code == 200:
        # st.write(response.content[:100])
        return response.content
    else:
        st.error(f"Failed to fetch full PDF: {response.status_code}")
        return None


def show_pdf_in_expander(filename):
    pdf_data = get_full_pdf_file(filename)

    if pdf_data:
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

        pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="700" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)


def search_query(query, top_k=10):
    params = {'query': query, 'top_k': top_k}
    response = requests.get(f"{BACKEND_URL}/similarity_search", params=params)
    return response.json()


def extract_zip_file(uploaded_zip, extract_to="extracted_files"):
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    zip_file = BytesIO(uploaded_zip.read())

    extracted_files = []

    with zipfile.ZipFile(zip_file, 'r') as z:
        for file_info in z.infolist():
            filename = file_info.filename.encode('utf-8').decode('utf-8')
            extract_path = os.path.join(extract_to, filename)
            if file_info.is_dir():
                os.makedirs(extract_path, exist_ok=True)
            else:
                with z.open(file_info) as source, open(extract_path, "wb") as target:
                    target.write(source.read())
                print(f"Extracted {filename} to {extract_path}")

    print(f"All files extracted to {extract_to}")
    return extracted_files


st.title("PDF Upload and Chat for Information Retrieval")
upload_type = st.radio("Upload Type", options=[
                       "Single PDF", "Multiple PDFs"])

if upload_type == "Single PDF":
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    if uploaded_file is not None:
        response = upload_pdf(uploaded_file)
        if 'error' in response:
            st.error(response['error'])
        else:
            st.success(response['message'])

elif upload_type == "ZIP File":
    uploaded_zip = st.file_uploader(
        "Upload a ZIP file containing PDFs", type="zip")
    if uploaded_zip is not None:
        extract_zip_file(uploaded_zip)

elif upload_type == "Multiple PDFs":
    uploaded_files = st.file_uploader(
        "Upload multiple PDF files", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            response = upload_pdf(uploaded_file)
            if 'error' in response:
                st.error(
                    f"Error processing {uploaded_file.name}: {response['error']}")
            else:
                st.success(f"{uploaded_file.name} processed successfully")

query = st.text_input("Ask a question about the PDF content")

if query:
    results = search_query(query)

    if results.get("results"):
        best_results = {}

        for result in results["results"]:
            filename = result['filename']
            if filename not in best_results or result['score'] > best_results[filename]['score']:
                best_results[filename] = result

        for idx, (filename, result) in enumerate(best_results.items()):
            st.subheader(f"Result {idx + 1}")

            pdfname = filename.replace('.txt', '.pdf')

            if st.button(f"View full document: {pdfname}", key=f"button_{idx}"):
                show_pdf_in_expander(pdfname)
            else:
                st.write(f"**Filename:** {pdfname}")
                st.write(f"**Score:** {result['score']}")
                st.write(f"**Chunk:** {result['chunk'][:500]}...")
    else:
        st.write("No results found.")
