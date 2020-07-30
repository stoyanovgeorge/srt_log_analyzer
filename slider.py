selection = st.selectbox("Select Analysis:", ("", "Dataframe Analysis", "Describe"))
    if selection == "Dataframe Analysis":
        nhead = st.slider("How many rows?", 1, 100, 10)
        st.write(dataframe.head(nhead))
