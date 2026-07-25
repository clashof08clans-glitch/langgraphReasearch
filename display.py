import streamlit as st
from graph import ReseachState , save_cache,load_cache,generate_query,app,graph,search,check_sufficiency,route,synthesize
import json
st.set_page_config(page_title="RESEARCH AGENT")
st.title("Ask you query")

topic = st.text_input("WHAT U LOOKIN FOR")
 
if st.button("Search 🔍"):
    with st.spinner("Searching..."):
        cached = load_cache(topic)
        if cached :
            st.write(cached)
        else:
            result = app.invoke({"topic":topic,"query":"","results":[],"sufficient":"","answer":"","itr":0})
            save_cache(topic,result["answer"])
            st.write(result["answer"])


try:
    with open("cache.json","r") as file:
        history = json.load(file)

except:
    history = {}

st.sidebar.title("Search History")
if history:
    for past_topic in history:
        if st.sidebar.button(past_topic):
            st.write(history[past_topic])

else:
    st.sidebar.write("No searches yet")