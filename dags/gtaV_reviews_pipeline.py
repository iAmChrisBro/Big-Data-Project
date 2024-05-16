from datetime import datetime
from airflow.decorators import dag, task
import pandas as pd
import subprocess
import sys

totalYes = 100

# Define the DAG using Airflow's decorators
@dag(schedule_interval=None, start_date=datetime(2021, 1, 1), catchup=False, tags=["big_data"])
def gtaV_reviews_project():
    """
    ### GTA V Reviews Data Pipeline
    A DAG for extracting, transforming, and loading GTA V review data from an Excel file.
    """

    @task()
    def acquire():
        """
        #### Extract task
        Ensure necessary packages are installed and extract GTA V reviews data from an Excel file.
        """
        # Ensure the package is installed
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openpyxl', 'pandas'])
    
        # Now import the package and read the data
        data = pd.read_excel('/opt/airflow/dags/GTAV_Steam_Reviews.xlsx')
        data.to_csv('intermediate.csv', index=False)  # Save to CSV
        return 'intermediate.csv'  # Pass the file path to the next task

    @task()
    def clean(file_path):
        """
        Clean and prepare GTA V review data.
        """
        # Import the package and read the CSV
        review_data = pd.read_csv(file_path)
        
        # Debugging: Print the column names to verify
        print("Columns in the DataFrame:", review_data.columns.tolist())
        
        # Check if expected columns are in the DataFrame
        expected_columns = ['voted_up', 'review']
        missing_columns = [col for col in expected_columns if col not in review_data.columns]
        if missing_columns:
            raise Exception(f"Missing columns in DataFrame: {missing_columns}")

        # Dropping rows where 'voted_up' or 'review' is missing
        review_data.dropna(subset=expected_columns, inplace=True)

        # Convert 'created' to datetime format
        review_data['created'] = pd.to_datetime(review_data['created'])

        # Selecting relevant columns
        cleaned_data = review_data[['created', 'voted_up', 'review', 'steam_purchase', 'recieved_for_free', 'author_playtime_forever']]
        cleaned_data.to_json(file_path, orient='records')
        return file_path


    @task()
    def load(file_path):
        """
        #### Load task
        Export the cleaned data to a JSON file.
        """
        # Read the cleaned data from CSV
        cleaned_data = pd.read_csv(file_path)
        
        # Exporting to JSON with line orientation for easier consumption
        cleaned_data.to_json('/opt/airflow/dags/cleaned_GTAV_Reviews.json', orient='records')

    @task()
    def calculate(file_path):
        """
        # Read cleaned data and analyze properties
        # Calculate mean, median, mode
        # Send data to visualization 
        """
        import json
        file = open(file_path)
        data = json.load(file)

        totalYes = 0
        totalNo = 0
        buyGame = 0
        notBuyGame = 0
        gotFree = 0
        playerHours = []
        totalHours = 0
        id = []
        index = 1

        for obj in data:
            if obj['voted_up']:
                totalYes += 1
            else:
                totalNo += 1
    
            if obj['steam_purchase']:
                buyGame += 1
            else:
                notBuyGame += 1

            if obj['recieved_for_free']:
                gotFree += 1


            playerHours.append(obj['author_playtime_forever']/60)
            id.append(index)
            index += 1
        
        for i in playerHours:
            totalHours += playerHours.index(i)

        index -= 1
        # Data to be written
        dictionary = {
            "ID": id,
            "PlayerHours": playerHours,
            "TotalHours": totalHours,
            "AvgHours": totalHours/index,
            "Purchased": buyGame,
            "NotPurchased": notBuyGame,
            "Users": index,
            "LikedGame": totalYes,
            "AvgLikeGame": totalYes/index,
            "NotLikedGame": totalNo,
            "AvgNotLikedGame": totalNo/index,
            "RecievedFree": gotFree,

        }
 
        # Serializing json
        file_path = json.dumps(dictionary, indent=4)
        return file_path

    @task()
    def visualization(file_path):
        """
        # Read the data passed on from calculate
        # Collect data into a json file
        # Send the data to folder in app
        """
        # Writing to calculations.json
        with open("/opt/airflow/app/calculations.json", "w") as outfile:
            outfile.write(file_path)


    # Task orchestration
    file_path = acquire()
    cleaned_file_path = clean(file_path)
    visualize = calculate(cleaned_file_path)
    visualization(visualize)

# Instantiate the DAG
gtaV_reviews_dag = gtaV_reviews_project()