from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import time
import mysql.connector
import re

# MySQL database connection parameters
db_config = {
    'user': 'root',
    'password': 'hasa',
    'host': 'localhost',
    'database': 'redbus_db'
}

# Function to insert data into MySQL database
def insert_bus_data(bus_data):
    try:
        # Establish the database connection
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # SQL Insert statement
        insert_query = """
        INSERT INTO bus_routes (route_name, route_link, busname, bustype, departing_time, duration, reaching_time, star_rating, price, seats_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Insert each record into the database
        for data in bus_data:
            cursor.execute(insert_query, data)
        
        # Commit the transaction
        conn.commit()
        print("Data inserted successfully.")
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    
    finally:
        cursor.close()
        conn.close()

# Initialize the WebDriver
driver = webdriver.Chrome()

# Initialize bus_data before the try block
bus_data = []

try:
    # Open the Redbus website
    driver.get("https://www.redbus.in/")

    # Increase wait time
    wait = WebDriverWait(driver, 20)
    
    # Input the source city
    print("Waiting for source input field...")
    src_input = wait.until(EC.element_to_be_clickable((By.ID, "src")))
    src_input.send_keys("Bangalore")
    print("Source input field found and filled")
    
    # Input the destination city
    print("Waiting for destination input field...")
    dest_input = wait.until(EC.element_to_be_clickable((By.ID, "dest")))
    dest_input.send_keys("Chennai")
    print("Destination input field found and filled")
    
    # Step 1: Click the date picker to open it
    date_picker_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'onwardCal'))
    )
    date_picker_button.click()
    
    # Click the search button
    print("Waiting for search button...")
    search_button = wait.until(EC.element_to_be_clickable((By.ID, "search_button")))
    search_button.click()
    print("Search button clicked")

    # Function to scroll down the page
    def scroll_to_bottom(driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    i = 0
    print("Fetching bus results...")
    # Loop through all pages with scrolling
    while i < 12:
        bus_data = []  # Ensure bus_data is initialized
        try:
            # Wait for bus results to load
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bus-items")))

            # Extract bus items
            bus_items = driver.find_elements(By.XPATH, '//ul[@class="bus-items"]/div/li')
            for bus_item in bus_items:
                try:
                    # Extract bus details
                    bus_name = bus_item.find_element(By.CLASS_NAME, "travels").text
                    bus_type = bus_item.find_element(By.CLASS_NAME, "bus-type").text
                    departure = bus_item.find_element(By.CLASS_NAME, "dp-time").text
                    arrival = bus_item.find_element(By.CLASS_NAME, "bp-time").text
                    price_text = bus_item.find_element(By.CLASS_NAME, "fare").text
                    available_seats = bus_item.find_element(By.CLASS_NAME, "seat-left").text
                    rating = bus_item.find_element(By.CLASS_NAME, "rating-sec").text
                    
                    # Extract duration and route_link
                    duration = bus_item.find_element(By.CLASS_NAME, "dur").text  # Adjust class name as needed
                    route_name = bus_item.find_element(By.CLASS_NAME, "dp-loc").text 
                    route_link = 'https://www.redbus.in/bus-tickets/routes-directory'
                    # Convert data to proper formats
                    departing_time = departure
                    reaching_time = arrival
                    star_rating = float(rating) if rating else 0.0
                    price = re.sub(r'[^\d.]', '', price_text)  # Remove all non-numeric characters except '.'
                    price = float(price) if price else 0.0
                    seats_available = int(available_seats.split()[0]) if available_seats else 0

                    # Store the bus data
                    bus_data.append((route_link, route_name, bus_name, bus_type, departing_time, duration, reaching_time, star_rating, price, seats_available))

                    # Check if it's a TSRTC bus
                    if "TSRTC" in bus_name:
                        # Click the "View Tickets" button
                        view_tickets_button = bus_item.find_element(By.XPATH, './/button[contains(text(), "View Tickets")]')  # Adjust XPath as needed
                        view_tickets_button.click()

                        # Wait for the ticket details to load
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ticket-details-class")))  # Adjust class name as needed
                        ticket_details = driver.find_element(By.CLASS_NAME, "ticket-details-class").text  # Replace with actual class name
                        print("Ticket Details for TSRTC Bus:", ticket_details)

                        # Optionally, store the ticket details in the bus data or a separate structure
                        bus_data[-1] += (ticket_details,)  # Append details to the last bus entry

                    if len(bus_data) > 20:
                        break
                except NoSuchElementException as e:
                    print(f"Error finding element in bus item: {e}")

            # Scroll down to load more results
            scroll_to_bottom(driver)
            time.sleep(1)
            i += 1  # Wait for results to load
        except Exception as e:
            print(f"An error occurred: {e}")

except TimeoutException as e:
    print(f"Timeout while waiting for an element: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Ensure WebDriver is closed
    driver.quit()
    print("WebDriver closed.")

# Process and insert the scraped data into the database
if bus_data:
    insert_bus_data(bus_data)
else:
    print("No bus data was scraped.")
