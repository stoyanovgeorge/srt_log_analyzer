import io
import base64
import datetime
import pandas as pd
import altair as alt
import streamlit as st


def df_format(dataframe, sender):
    """Formats the Dataframe and removes the redundant columns whether the log files are for 
    receiver or sender device  

    Args:
        dataframe ([dataframe]): Input dataframe
        sender ([bool]): Returns True if the logs are for a SRT sender and False for SRT receiver
    Returns:
        cleaned_df ([dataframe]): Output and cleaned dataframe
        num_rows ([integer]): Number of Rows of the new Cleaned Dataframe
        num_cols ([integers]): Number of Columns in the new cleaned Dataframe
    """
    
    if sender:
        # Dropping all Receiver Columns
        cleaned_df = dataframe.drop(["pktRecv", "pktRcvLoss", "pktRcvDrop", "pktRcvRetrans", "pktRcvBelated", 
                                     "byteRecv", "byteRcvLoss", "byteRcvDrop", "mbpsRecvRate", "mbpsMaxBW", 
                                     "pktRcvFilterExtra", "pktRcvFilterSupply", "pktRcvFilterLoss"], axis = 1)
    else:
        # Dropping all Sender Columns
        cleaned_df = dataframe.drop(["pktSent", "pktSndLoss", "pktSndDrop", "pktRetrans", "byteSent", 
                                     "byteSndDrop", "mbpsSendRate", "mbpsMaxBW", "pktSndFilterExtra"], axis = 1)
    # Originally the Time column contains the elapsed time in milliseconds
    # Converting the milliseconds to human time 
    cleaned_df["Seconds"] = pd.to_datetime(cleaned_df.Time).astype(int) / 10 ** 3
    # Converting the Time column into datetime and then converting it to timestamp
    cleaned_df.Time = pd.to_datetime(cleaned_df.Time, unit = "ms").dt.time
    # Reordering the Dataframe and placing the Seconds column at the beginning instead of the end
    df_cols = list(cleaned_df.columns.values)
    df_cols.pop(df_cols.index("Seconds"))
    cleaned_df = cleaned_df[["Seconds"] + df_cols]
    # Finding out the number of rows and columns     
    num_rows = cleaned_df.shape[0]
    num_cols = cleaned_df.shape[1]
    
    return cleaned_df, num_rows, num_cols

def rtt_calc(dataframe):
    """Calculates the minimum, maximum and average Round Trip Time(RTT)

    Args:
        dataframe ([dataframe]): Input Dataframe

    Returns:
        min_rtt ([float]): Minimum Round Trip Time in ms
        max_rtt ([float]): Maximum Round Trip Time in ms
        avg_rtt ([float]): Average Round Trip Time in ms
    """
    min_rtt = round(dataframe.msRTT.min(), 3)
    max_rtt = round(dataframe.msRTT.max(), 3)
    avg_rtt = round(dataframe.msRTT.mean(), 3)
    return min_rtt, max_rtt, avg_rtt
    

def get_download_link(**dataframes):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    output_file = io.BytesIO()
    writer = pd.ExcelWriter(output_file, engine = "xlsxwriter")
    for df_name, df in dataframes.items(): 
        # Creating a new Sheet only if the df is not empty
        if df is not None: 
            df.to_excel(writer, sheet_name = df_name)
    writer.save()
    b64 = base64.b64encode(output_file.getvalue())
    export_link = f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="output.xlsx">here</a>'
    return export_link

def line_stats(dataframe, sender):
    """Prints on the screen the Line Stats, the X-number of rows containing the lowest mbpsBandwidth, 
    Lost Sent/Received, Dropped Sent/Received and Retransmitted Sent/Received Data Packets if any and 
    generating a download link to export these tables into Excel spreadsheet.

    Args:
        dataframe ([dataframe]): Input Dataframe
        sender ([bool]): True for SRT Sender and False for SRT Receiver
    """
    if sender:
        st.markdown("### Line Bandwidth Stats:")
        st.write(f"Minimal Line Bandwidth: {dataframe.mbpsBandwidth.min()} Mbps")
        snd_rows = st.slider("Select the Number of Smallest Rows to Show:", 1, 100, 10)
        # Checking if we have lost sent data packets 
        snd_cols = ["Time", "msRTT", "mbpsBandwidth", "pktSndDrop", "pktSndLoss", "pktRetrans", "mbpsSendRate"]
        mbpsSendRate_df = dataframe.nsmallest(snd_rows, "mbpsBandwidth")[snd_cols]
        st.table(mbpsSendRate_df)
        if dataframe.pktSndLoss.max() > 0:
            st.write("---")
            st.markdown("### Lost Sent Data Packets Stats:")
            st.write(f"Maximal Lost Sent Data Packets: {dataframe.pktSndLoss.max()} packets")
            st.write(f"Total Lost Sent Data Packets: {dataframe.pktSndLoss.sum()} packets")
            pktSndLoss_df = dataframe.nlargest(snd_rows, "pktSndLoss")[snd_cols]
            st.table(pktSndLoss_df)
        else:
            st.write("No Lost Sent Data Packets Detected")
            pktSndLoss_df = None

        # Checking if we have dropped sent data packets 
        if dataframe.pktSndDrop.max() > 0:
            st.write("---")
            st.markdown("### Dropped Sent Data Packets Stats:")
            st.write(f"Maximal Dropped Sent Data Packets: {dataframe.pktSndDrop.max()} packets")
            st.write(f"Total Dropped Sent Data Packets: {dataframe.pktSndDrop.sum()} packets")
            pktSndDrop_df = dataframe.nlargest(snd_rows, "pktSndDrop")[snd_cols]
            st.table(pktSndDrop_df)
        else:
            st.write("No Dropped Sent Data Packets Detected")
            pktSndDrop_df = None

        # Checking if we have retransmitted sent data packets 
        if dataframe.pktRetrans.max() > 0:
            st.write("---")
            st.markdown("### Retransmitted Data Packets Stats:")
            st.write(f"Maximal Retransmitted Data Packets: {dataframe.pktRetrans.max()} packets")
            st.write(f"Total Retransmitted Data Packets: {dataframe.pktRetrans.sum()} packets")
            pktRetrans_df = dataframe.nlargest(snd_rows, "pktRetrans")[snd_cols]
            st.table(pktRetrans_df)
        else:
            st.write("No Retransmitted Data Packets Detected")
            pktRetrans_df = None
        # Creating an export link to download the statistics
        url = get_download_link(mbpsSendRate = mbpsSendRate_df, pktSndLoss = pktSndLoss_df, 
                                pktSndDrop = pktSndDrop_df, pktRetrans = pktRetrans_df)
        st.markdown(f"If you want to export this data as a spreadsheet click {url}.", unsafe_allow_html=True)

    else:
        # The logs are for Receiving Device
        st.markdown("### Line Bandwidth Stats:")
        st.write(f"Minimal Line Bandwidth: {dataframe.mbpsBandwidth.min()} Mbps")
        rcv_rows = st.slider("Select Number of Rows:", 1, 100, 10)
        rcv_cols = ["Time", "msRTT", "mbpsBandwidth", "pktRcvDrop", "pktRcvLoss", "pktRcvRetrans", "mbpsRecvRate"]
        mbpsBandwidth_df = dataframe.nsmallest(rcv_rows, "mbpsBandwidth")[rcv_cols]
        st.table(mbpsBandwidth_df)
        if dataframe.pktRcvLoss.max() > 0:
            st.write("---")
            st.markdown("### Lost Received Data Packets Stats:")
            st.write(f"Maximal Lost Received Data Packets: {dataframe.pktRcvLoss.max()} packets")
            st.write(f"Total Lost Received Data Packets: {dataframe.pktRcvLoss.sum()} packets")
            pktcvLoss_df = dataframe.nlargest(rcv_rows, "pktRcvLoss")[rcv_cols]
            st.table(pktcvLoss_df)
        else:
            st.write("No Lost Sent Data Packets Detected")
            pktcvLoss_df = None
            
        # Checking if we have dropped sent data packets 
        if dataframe.pktRcvDrop.max() > 0:
            st.write("---")
            st.markdown("### Dropped Received Data Packets Stats:")
            st.write(f"Maximal Dropped Received Data Packets: {dataframe.pktRcvDrop.max()} packets")
            st.write(f"Total Dropped Sent Data Packets: {dataframe.pktRcvDrop.sum()} packets")
            pktRcvDrop_df = dataframe.nlargest(rcv_rows, "pktRcvDrop")[rcv_cols]
            st.table(pktRcvDrop_df)
        else:
            st.write("No Dropped Sent Data Packets Detected")
            pktRcvDrop_df = None

        # Checking if we have retransmitted sent data packets 
        if dataframe.pktRcvRetrans.max() > 0:
            st.write("---")
            st.markdown("### Retransmitted Data Packets Stats:")
            st.write(f"Maximal Retransmitted Data Packets: {dataframe.pktRcvRetrans.max()} packets")
            st.write(f"Total Retransmitted Data Packets: {dataframe.pktRcvRetrans.sum()} packets")
            pktRcvRetrans_df = dataframe.nlargest(rcv_rows, "pktRcvRetrans")[rcv_cols]
            st.table(pktRcvRetrans_df)
        else:
            st.write("No Retransmitted Data Packets Detected")
            pktRcvRetrans_df = None
        
        # Creating an export link to download the statistics
        url = get_download_link(mbpsBandwidth = mbpsBandwidth_df, pktRcvDrop = pktRcvDrop_df, 
                                pktRcvRetrans = pktRcvRetrans_df, pktcvLoss = pktcvLoss_df)
        st.markdown(f"If you want to export this data as a spreadsheet click {url}.", unsafe_allow_html=True)

def drop_down_menu(dataframe, sender):
    """Generates a drop-down menu with the different analysis types, to perform on the input CSV log file.

    Args:
        dataframe ([dataframe]): Input Dataframe
        sender ([bool]): True for SRT Sender and False for SRT Receiver
    """
    selection = st.selectbox("Select Analysis:", ("", "Show Dataframe Head", "Show Dataframe Tail", \
                             "General Stats", "Line Bandwidth Stats", "Bandwidth Plot"))
    if selection == "Show Dataframe Head":
        nhead = st.slider("How Many Rows to Show?", 1, 100, 10)
        st.write(dataframe.head(nhead))
    if selection == "Show Dataframe Tail":
        ntail = st.slider("How Many Rows to Show?", 1, 100, 10)
        st.write(dataframe.tail(ntail))
    if selection == "General Stats":
        st.write(dataframe.describe().T)
    if selection == "Line Bandwidth Stats":
        line_stats(dataframe, sender)

    if selection == "Bandwidth Plot":
        line_chart = alt.Chart(dataframe).mark_line().encode(
        alt.X('Seconds:Q', title='Time, [s]'),
        alt.Y('mbpsBandwidth', title='Bandwidth, [Mbps]')).properties(title='SRT Line Bandwidth').interactive()
        st.altair_chart(line_chart, use_container_width = True)
    
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

def main():
    st.beta_set_page_config(page_title = "SRT Logs Analyzer")
    st.markdown("<h1 style='text-align: center;'>SRT Log Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("### Upload And Analyse CSV Log File")

    file_buffer = st.file_uploader("Choose a CSV Log File...", type="csv", encoding = None)
    if file_buffer:
        uploaded_file = io.TextIOWrapper(file_buffer)
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            # Checking if the number of the columns is 30
            if df.shape[1] != 30:
                st.warning(f"The uploaded CSV file is not properly formatted SRT Log File.")
                st.warning(f"The uploaded file has only {df.shape[1]} columns instead of 30!")
            else:
                # Dropping the SocketID column, since it is not informative
                df.drop(["SocketID"], axis = 1, inplace = True)
            
            # Checking if the log file is for sender or receiving device
            if df.byteSent.iloc[0] != 0:
                sender = True
                st.markdown("### SRT Sender Log:")
            else:
                sender = False
                st.write("### SRT Receiver Log:")
            
            # Removing redundant columns
            df, num_rows, num_cols = df_format(df, sender)
            min_rtt, max_rtt, avg_rtt = rtt_calc(df)
            
            # Printing some general stats of the line
            st.write(f"Number of Columns: {num_cols}")
            st.write(f"Number of Rows: {num_rows}")
            st.write(f"Log Duration: {df.Time.iloc[-1]}")
            st.write(f"Defined Latency: {df.RCVLATENCYms.iloc[-1]} ms")
            st.write(f"Minimal RTT: {min_rtt} ms")
            st.write(f"Maximal RTT: {max_rtt} ms")
            st.write(f"Average RTT: {avg_rtt} ms")
            
            # Generating the Drop-Down Menu with the Different Analysis
            drop_down_menu(df, sender)

if __name__ == "__main__":
    main()