import streamlit as st
import pandas as pd
import datetime
# import matplotlib.pyplot as plt
import altair as alt


def is_authenticated(password):
    return password == "admin"

def generate_login_block():
    block1 = st.empty()
    block2 = st.empty()
    return block1, block2

def clean_blocks(blocks):
    for block in blocks:
        block.empty()

def login(blocks):
    blocks[0].markdown("""
            <style>
                input {
                    -webkit-text-security: disc;
                }
            </style>
        """, unsafe_allow_html=True)

    return blocks[1].text_input('Password')

def df_format(dataframe, sender):
    
    if sender:
        # Dropping all Receiver Columns
        dataframe.drop(["pktRecv", "pktRcvLoss", "pktRcvDrop", "pktRcvRetrans", "pktRcvBelated", \
                "byteRecv", "byteRcvLoss", "byteRcvDrop", "mbpsRecvRate", "mbpsMaxBW", \
                "pktRcvFilterExtra", "pktRcvFilterSupply", "pktRcvFilterLoss"], axis = 1, inplace = True)
    else:
        # Dropping all Sender Columns
        dataframe.drop(["pktSent", "pktSndLoss", "pktSndDrop", "pktRetrans", \
                "byteSent", "byteSndDrop", "mbpsSendRate", "mbpsMaxBW", \
                "pktSndFilterExtra"], axis = 1, inplace = True)
    # Originally the Time column contains the elapsed time in milliseconds
    # Converting the milliseconds to timestamp 
    dataframe["Seconds"] = pd.to_datetime(dataframe.Time).astype(int) / 10 ** 3
    # Converting the Time column into datetime and then converting it to timestamp
    dataframe.Time = pd.to_datetime(dataframe.Time, unit = "ms").dt.time
    # Reordering the Dataframe and placing the Seconds column at the beginning instead of the end
    df_cols = list(dataframe.columns.values)
    df_cols.pop(df_cols.index("Seconds"))
    dataframe = dataframe[["Seconds"] + df_cols]
    # Finding out the number of rows and columns     
    num_rows = dataframe.shape[0]
    num_cols = dataframe.shape[1]
    st.write(f"Number of Columns: {num_cols} and Log Entries: {num_rows}")
    # Creating a new Dataframe, where the index is actually the Timestamp from column 1
    # df_plot = df.set_index("Time")
    # st.write(df_plot.head())

def slider(min_val, max_val, def_val, label):
    slider_val = st.slider(label, min_val, max_val, def_val)
    return slider_val

def df_analysis(dataframe):
    rows = slider(0, 50, 5, "Select Number of Rows:")
    st.write(f"First {rows} Rows:")
    st.write(dataframe.head(rows))
    st.write(f"Last {rows} Rows:")
    st.write(dataframe.tail(rows))
    # rows = slider(0, 50, 5, "Select Number of Rows:")

def drop_down_menu(dataframe):
    selection = st.selectbox("Select Analysis:", ("", "Dataframe Analysis", "Describe", "Datatypes", "General Statistics"))
    if st.button("Submit"):
        if selection == "Dataframe Analysis":
            # df_analysis(dataframe)
            nhead = st.slider("How many rows?", 1, 100, 10)
            st.write(nhead)
            st.write(dataframe.head(nhead))
        if selection == "Describe":
            st.write("Describe Selected")

def general_stats(dataframe, sender):
    st.write(f"Log Duration: {dataframe.Time.iloc[-1]}")
    st.write(f"Defined Latency: {dataframe.RCVLATENCYms.iloc[-1]} ms")
    min_rtt = round(dataframe.msRTT.min(), 3)
    max_rtt = round(dataframe.msRTT.max(), 3)
    avg_rtt = round(dataframe.msRTT.mean(), 3)
    st.write(f"Minimal RTT: {min_rtt} ms")
    st.write(f"Maximal RTT: {max_rtt} ms")
    st.write(f"Average RTT: {avg_rtt} ms")
    st.write(f"Jitter: {round((max_rtt - min_rtt), 3)} ms")
    
    if not dataframe[dataframe.pktFlightSize > dataframe.pktFlowWindow].empty:
        st.error("pktFlightSize is lower than the pktFlowWindow!")
        st.markdown("pktFlightSize is the distance between the packet sequence number that was \
            last reported by an ACK message and the sequence number of the latest packet sent \
            (at the moment when the statistics are being read).")
        st.write(dataframe[dataframe.pktFlightSize > dataframe.pktFlowWindow][["pktFlightSize", "pktFlowWindow"]])
    # Checking if the pktFlightSize is higher than the pktCongestionWindow
    if not dataframe[dataframe.pktFlightSize > dataframe.pktCongestionWindow].empty:
        st.error("pktFlightSize is lower than the pktCongestionWindow!")
        st.markdown("pktFlightSize is the distance between the packet sequence number that was \
            last reported by an ACK message and the sequence number of the latest packet sent \
            (at the moment when the statistics are being read).")
        st.markdown("Dynamically limits the maximum number of packets that can be in flight. \
            Congestion control module dynamically changes the value.")
        st.write(dataframe[dataframe.pktFlightSize > dataframe.pktCongestionWindow][["pktFlightSize", "pktCongestionWindow"]])
    st.write("---")
    st.markdown("### Line Bandwidth Stats:")
    st.write(f"Minimal Line Bandwidth: {dataframe.mbpsBandwidth.min()} Mbps")
    st.table(dataframe.nsmallest(10, "mbpsBandwidth")[["Time", "msRTT", "mbpsBandwidth", "pktSndDrop", "pktSndLoss", "pktRetrans", "mbpsSendRate"]])
    if sender:
        # Checking if we have lost sent data packets 
        if dataframe.pktSndLoss.max() > 0:
            st.write("---")
            st.markdown("### Lost Sent Data Packets Stats:")
            st.write(f"Maximal Lost Sent Data Packets: {dataframe.pktSndLoss.max()} packets")
            st.write(f"Total Lost Sent Data Packets: {dataframe.pktSndLoss.sum()} packets")
            st.table(dataframe.nlargest(10, "pktSndLoss")[["Time", "msRTT", "mbpsBandwidth", "pktSndDrop", "pktSndLoss", "pktRetrans", "mbpsSendRate"]])

        else:
            st.write("No Lost Sent Data Packets Detected")
        # Checking if we have dropped sent data packets 
        if dataframe.pktSndDrop.max() > 0:
            st.write("---")
            st.markdown("### Dropped Sent Data Packets Stats:")
            st.write(f"Maximal Dropped Sent Data Packets: {dataframe.pktSndDrop.max()} packets")
            st.write(f"Total Dropped Sent Data Packets: {dataframe.pktSndDrop.sum()} packets")
            st.table(dataframe.nlargest(10, "pktSndDrop")[["Time", "msRTT", "mbpsBandwidth", "pktSndDrop", "pktSndLoss", "pktRetrans", "mbpsSendRate"]])
        else:
            st.write("No Dropped Sent Data Packets Detected")
        # Checking if we have retransmitted sent data packets 
        if dataframe.pktRetrans.max() > 0:
            st.write("---")
            st.markdown("### Retransmitted Data Packets Stats:")
            st.write(f"Maximal Retransmitted Data Packets: {dataframe.pktRetrans.max()} packets")
            st.write(f"Total Retransmitted Data Packets: {dataframe.pktRetrans.sum()} packets")
            st.table(dataframe.nlargest(10, "pktRetrans")[["Time", "msRTT", "mbpsBandwidth", "pktSndDrop", "pktSndLoss", "pktRetrans", "mbpsSendRate"]])
        else:
            st.write("No Retransmitted Data Packets Detected")

def main():
    # st.title("SRT Log Analyzer")
    st.markdown("<h1 style='text-align: center;'>SRT Log Analyzer</h1>", unsafe_allow_html=True)

    ### Excluding Imports ###
    st.markdown("### Upload And Analyse CSV Log File")

    uploaded_file = st.file_uploader("Choose a CSV Log File...", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if df.shape[1] != 30:
            st.warning(f"The uploaded CSV file is not properly formatted SRT Log File.")
            st.warning(f"The uploaded file has only {df.shape[1]} columns instead of 30!")
        else:
            # Dropping the SocketID column, since it is not informative
            df.drop(["SocketID"], axis = 1, inplace = True)
            # Finding if the logs are for SRT receiver or sender
        # Checking if the log file is for sender or receiving device
        sender = df.byteSent.iloc[0] != 0
        # Removing unimportant columns
        df_format(df, sender)

        st.write("Additional Statistics:")

        dframe_analysis = st.checkbox("Dataframe Analysis")
        describe = st.checkbox("Print the statistics for all numeric columns")
        types = st.checkbox("Types of the Columns")
        stats = st.checkbox("Show General Statistics of the Line")
        bw_plot = st.checkbox("Draw a Plot of the Bandwidth")

        if dframe_analysis:
            df_analysis(df)
        if describe:
            st.write(df.describe().T)
        if types:
            st.table(df.dtypes)
        if bw_plot:
            line_chart = alt.Chart(df).mark_line().encode(
            alt.X('Seconds:Q', title='Time, [s]'),
            alt.Y('mbpsBandwidth', title='Bandwidth, [Mbps]')).properties(title='SRT Line Bandwidth').interactive()
            st.altair_chart(line_chart, use_container_width = True)

        if stats:
            general_stats(df, sender)
        
        drop_down_menu(df)

# login_blocks = generate_login_block()
# password = login(login_blocks)

# if is_authenticated(password):
#     clean_blocks(login_blocks)
#     main()
# elif password:
#     st.info("Please enter a valid password")

main()