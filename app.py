import streamlit as st
import pandas as pd

def process_data(file1, file2):
    # Read data from files
    data1 = pd.read_csv(file1, delimiter=';')
    data2 = pd.read_excel(file2)

    # Trim column names to remove potential leading/trailing whitespace
    data1.columns = data1.columns.str.strip()
    data2.columns = data2.columns.str.strip()
    
    # Convert date columns
    data1['arrivalDate'] = pd.to_datetime(data1['arrivalDate'])
    data2['occupancyDate'] = pd.to_datetime(data2['occupancyDate'])

    # Merge on date
    merged = pd.merge(data1[['arrivalDate', 'rn', 'revNet']],
                      data2[['occupancyDate', 'roomsSold', 'roomRevenue']],
                      left_on='arrivalDate', right_on='occupancyDate', how='inner')
    merged.drop('occupancyDate', axis=1, inplace=True)
    merged.columns = ['Date', 'RN_Source1', 'Revenue_Source1', 'RN_Source2', 'Revenue_Source2']
    
    # Fill NaNs and calculate differences
    merged.fillna(0, inplace=True)
    merged['RN_Difference'] = merged['RN_Source1'] - merged['RN_Source2']
    merged['Revenue_Difference'] = round(merged['Revenue_Source1'] - merged['Revenue_Source2'], 2)
    
    return merged

def parse_hotel_name(file_name):
    
    # Split the base name by underscore
    parts = file_name.split('_')
    
    # The hotel name should be the first part of the split result
    hotel_name = parts[0]
    
    return hotel_name

st.title('Opera Cloud Discrepancy Checker')

# File upload interface
uploaded_file1 = st.file_uploader("Choose a Daily Totals file", type=['csv'])
uploaded_file2 = st.file_uploader("Choose a Statistics file", type=['xlsx'])

if uploaded_file1 and uploaded_file2:

    data = process_data(uploaded_file1, uploaded_file2)

    if not data.empty:
        st.sidebar.header("Filters")
        # Filtering option for discrepancies
        show_discrepancies_only = st.sidebar.checkbox("Show Only Discrepancies", value=True)

        # Columns to display, defaulting to selected columns
        default_columns = ['Date', 'RN_Difference', 'Revenue_Difference']
        columns_to_show = st.sidebar.multiselect("Select columns to display", data.columns, default=default_columns)
        
        filtered_data = data.loc[:, columns_to_show]
        if show_discrepancies_only:
            filtered_data = filtered_data[(data['RN_Difference'] != 0) | (data['Revenue_Difference'] != 0)]

        # KPI calculations
        current_date = pd.Timestamp.now().normalize()
        past_data = data[data['Date'] < current_date]
        future_data = data[data['Date'] >= current_date]

        # Past KPIs
        past_rn_discrepancy_abs = abs(past_data['RN_Difference'].sum())
        past_revenue_discrepancy_abs = abs(past_data['Revenue_Difference'].sum())
        past_rn_discrepancy_pct = abs(past_data['RN_Difference'].sum()) / past_data['RN_Source2'].sum() * 100
        past_revenue_discrepancy_pct = abs(past_data['Revenue_Difference'].sum()) / past_data['Revenue_Source2'].sum() * 100

        # Future KPIs
        future_rn_discrepancy_abs = abs(future_data['RN_Difference'].sum())
        future_revenue_discrepancy_abs = abs(future_data['Revenue_Difference'].sum())
        future_rn_discrepancy_pct = abs(future_data['RN_Difference'].sum()) / future_data['RN_Source2'].sum() * 100
        future_revenue_discrepancy_pct = abs(future_data['Revenue_Difference'].sum()) / future_data['Revenue_Source2'].sum() * 100

        # Display KPIs
        st.header(f"Accuracy Report for {parse_hotel_name(uploaded_file1.name)}")
        kpi_col1, kpi_col2 = st.columns(2)
        with kpi_col1:
            st.subheader("Past Discrepancies")
            st.metric("RN Accuracy (%)", f"{100-past_rn_discrepancy_pct:.2f}%")
            st.metric("Revenue Accuracy (%)", f"{100-past_revenue_discrepancy_pct:.2f}%")
            st.metric("RN Discrepancy (Absolute)", f"{past_rn_discrepancy_abs} RNs")
            st.metric("Revenue Discrepancy (Absolute)", f"{past_revenue_discrepancy_abs}")

        with kpi_col2:
            st.subheader("Future Discrepancies")
            st.metric("RN Accuracy (%)", f"{100-future_rn_discrepancy_pct:.2f}%")
            st.metric("Revenue Accuracy (%)", f"{100-future_revenue_discrepancy_pct:.2f}%")
            st.metric("RN Discrepancy (Absolute)", f"{future_rn_discrepancy_abs} RNs")
            st.metric("Revenue Discrepancy (Absolute)", f"{future_revenue_discrepancy_abs:.2f}")
            

        # Display the DataFrame
        st.header("Detailed Report")
        st.dataframe(filtered_data.style.applymap(lambda x: "background-color: yellow" if x != 0 else "", subset=['RN_Difference', 'Revenue_Difference']))
    else:
        st.error("Data could not be processed. Please check the file formats and contents.")
else:
    st.write("Please upload both files to proceed.")
