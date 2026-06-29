import streamlit as st
from research import get_findings_text,search_web,research, synthesize,load_cache,save_cache

st.set_page_config(page_title="Research Agent")
st.title("Ask your Query")

topic = st.text_input("Ask your query")


if st.button("Search"):
    with st.spinner("Searching..."):
        cached = load_cache(topic)
        if cached:
            st.write(cached)
        else:
            answer = synthesize(topic,research(topic))
            st.write(answer)
            save_cache(topic,answer)
        

