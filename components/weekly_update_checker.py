import json
from datetime import datetime, timedelta
import mysql.connector

def needs_weekly_update():
    from components.databases import get_db_connection
    try:
        # Step 1: Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 2: Get the latest update_date from the weekly_metadata table
        cursor.execute("SELECT update_date FROM weekly_metadata ORDER BY update_date DESC LIMIT 1")
        latest_update_date = cursor.fetchone()

        # Step 3: Check if there is a valid update_date in the database
        if not latest_update_date:
            print("⚠️ No update date found in weekly_metadata, running weekly update.")
            return True  # If no data found, run weekly update
        
        # Step 4: Compare the latest update_date with the current date
        last_update = latest_update_date[0]
        if last_update < (datetime.today() - timedelta(days=7)).date():
            return True  # Run weekly update if the last update was more than 7 days ago
        
        # No update needed if the last update is within the past 7 days
        return False
    
    except mysql.connector.Error as err:
        print(f"⚠️ Error while checking weekly update status: {err}")
        return True  # In case of any error, default to running the weekly update
    
    finally:
        # Step 5: Close the database connection
        cursor.close()
        conn.close()