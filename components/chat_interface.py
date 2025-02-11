import streamlit as st

def render_chat_interface():
    # Initialize chat history in session state if it doesn't exist
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Create a form to capture the user's natural language query, then update session state
    with st.form(key="chat_form", clear_on_submit=True):
        chat_input = st.text_input("Ask a question about the area:")
        submit = st.form_submit_button("Send")
        if submit and chat_input:
            # Append the user's message to the chat history
            st.session_state["chat_history"].append(f"You: {chat_input}")

            # Process the NL query using the NL-to-SQL functionality
            from services.nl_query import process_nl_query

            # Optionally, obtain your OpenAI API key from session_state (if set from elsewhere)
            provided_api_key = st.session_state.get("openai_api_key", None)

            # Connect to your PostgreSQL database (ensure your connection is configured)
            conn = st.connection("postgresql", type="sql")

            with st.spinner("Processing your query..."):
                try:
                    summary = process_nl_query(chat_input, conn, provided_api_key=provided_api_key)
                except Exception as e:
                    summary = f"Error processing query: {e}"

            # Append the summary (or error) to the chat history
            st.session_state["chat_history"].append(f"System: {summary}")

    # Display the updated chat history after the form
    for message in st.session_state["chat_history"]:
        st.write(message) 