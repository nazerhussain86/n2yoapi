import os
import requests
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# --- Configuration from Environment Variables Only ---
def get_config_value(key_name, default=None, is_int=False):
    """Get configuration value from environment variables"""
    value = os.environ.get(key_name.upper())
    
    if value is None:
        return default

    if is_int:
        try:
            return int(value)
        except ValueError:
            print(f"Warning: Could not convert {key_name} ('{value}') to int. Using default: {default}")
            return default
    return value

# --- Fetch Configuration Values from Environment Variables ---
N2YO_API_KEY = get_config_value('N2YO_API_KEY')
SMTP_SERVER = get_config_value('SMTP_SERVER')
SMTP_PORT = get_config_value('SMTP_PORT', default=587, is_int=True)
SMTP_USERNAME = get_config_value('SMTP_USERNAME')
SMTP_PASSWORD = get_config_value('SMTP_PASSWORD')
SENDER_EMAIL = get_config_value('SENDER_EMAIL', default=SMTP_USERNAME)
RECEIVER_EMAIL = get_config_value('RECEIVER_EMAIL')

# --- API Call Parameters (Customize as needed) ---
BASE_URL = "https://api.n2yo.com/rest/v1/satellite/"
ISS_NORAD_ID = 25544
OBSERVER_LAT = 40.7128
OBSERVER_LNG = -74.0060
OBSERVER_ALT = 10
PASS_DAYS = 2
MIN_VISIBILITY_SECONDS = 300
MIN_ELEVATION_DEGREES = 40
SEARCH_RADIUS_DEGREES = 70
CATEGORY_ID = 0  # 0 for all categories


def fetch_api_data(endpoint_url):
    """Fetch data from N2YO API"""
    if not N2YO_API_KEY:
        return {"error": "N2YO_API_KEY is not configured.", "url": endpoint_url}
    
    full_url = f"{BASE_URL}{endpoint_url}&apiKey={N2YO_API_KEY}"
    try:
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "url": full_url}
    except json.JSONDecodeError as e:
        return {"error": f"JSON Decode Error: {str(e)}", "content": response.text, "url": full_url}


def get_tle_data(sat_id):
    """Get TLE (Two-Line Element) data for a satellite"""
    return fetch_api_data(f"tle/{sat_id}")


def get_positions_data(sat_id, lat, lng, alt, seconds=5):
    """Get current position data for a satellite"""
    return fetch_api_data(f"positions/{sat_id}/{lat}/{lng}/{alt}/{seconds}/")


def get_visual_passes_data(sat_id, lat, lng, alt, days, min_visibility):
    """Get visual passes data for a satellite"""
    return fetch_api_data(f"visualpasses/{sat_id}/{lat}/{lng}/{alt}/{days}/{min_visibility}/")


def get_radio_passes_data(sat_id, lat, lng, alt, days, min_elevation):
    """Get radio passes data for a satellite"""
    return fetch_api_data(f"radiopasses/{sat_id}/{lat}/{lng}/{alt}/{days}/{min_elevation}/")


def get_whats_up_data(lat, lng, alt, search_radius, category_id):
    """Get data for satellites currently above observer location"""
    return fetch_api_data(f"above/{lat}/{lng}/{alt}/{search_radius}/{category_id}/")


def send_email(subject, body_html, receiver_email, sender_email, smtp_server, smtp_port, smtp_username, smtp_password):
    """Send HTML email using SMTP"""
    if not all([receiver_email, sender_email, smtp_server, smtp_port, smtp_username, smtp_password]):
        print("Email configuration incomplete. Skipping email.")
        print(f"Debug Info: R:{receiver_email}, S:{sender_email}, Serv:{smtp_server}, P:{smtp_port}, U:{bool(smtp_username)}, PW:{bool(smtp_password)}")
        return False
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.attach(MIMEText(body_html, 'html'))
    
    try:
        print(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("Starting TLS...")
            server.starttls()
            print("Attempting login...")
            server.login(smtp_username, smtp_password)
            print("Login successful, sending email...")
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Email sent successfully to {receiver_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        print("Common solutions:")
        print("1. For Gmail: Use App Password instead of regular password")
        print("2. Enable 2-Factor Authentication and generate App Password")
        print("3. Check if username/email is correct")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def format_data_as_html(data_dict):
    """Format API data as HTML for email"""
    html_body = "<html><head><style>"
    html_body += "body {font-family: sans-serif; margin: 20px;} "
    html_body += "h1 {color: #333;} h2 {color: #555; border-bottom: 1px solid #eee; padding-bottom: 5px;} "
    html_body += "pre {background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto;} "
    html_body += ".error {color: red; font-weight: bold;}"
    html_body += "</style></head><body>"
    html_body += f"<h1>N2YO API Daily Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</h1>"
    
    for title, data in data_dict.items():
        html_body += f"<h2>{title}</h2>"
        if isinstance(data, dict) and "error" in data:
            html_body += f"<p class='error'>Error fetching data: {data['error']}</p>"
            if "url" in data: 
                html_body += f"<p>URL: {data['url']}</p>"
            if "content" in data: 
                html_body += f"<p>Content: <pre>{data['content']}</pre></p>"
        elif data:
            html_body += f"<pre>{json.dumps(data, indent=2)}</pre>"
        else:
            html_body += "<p>No data received or an unknown error occurred.</p>"
    
    html_body += "</body></html>"
    return html_body


if __name__ == "__main__":
    print("Starting N2YO API data collection...")
    
    # Check for essential configurations
    if not N2YO_API_KEY:
        print("Error: N2YO_API_KEY is not configured. Please set it in GitHub secrets.")
        exit(1)
    
    if not RECEIVER_EMAIL:
        print("Error: RECEIVER_EMAIL is not configured. Please set it in GitHub secrets.")
        exit(1)
    
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
        print("Error: SMTP configuration (server, port, username, or password) is missing. Please set them in GitHub secrets.")
        exit(1)

    print("Fetching N2YO API data...")
    all_data = {}
    
    # Collect all satellite data
    all_data["TLE Data (ISS)"] = get_tle_data(ISS_NORAD_ID)
    all_data["Positions Data (ISS)"] = get_positions_data(
        ISS_NORAD_ID, OBSERVER_LAT, OBSERVER_LNG, OBSERVER_ALT, seconds=3
    )
    all_data["Visual Passes (ISS)"] = get_visual_passes_data(
        ISS_NORAD_ID, OBSERVER_LAT, OBSERVER_LNG, OBSERVER_ALT, PASS_DAYS, MIN_VISIBILITY_SECONDS
    )
    all_data["Radio Passes (ISS)"] = get_radio_passes_data(
        ISS_NORAD_ID, OBSERVER_LAT, OBSERVER_LNG, OBSERVER_ALT, PASS_DAYS, MIN_ELEVATION_DEGREES
    )
    all_data["What's Up"] = get_whats_up_data(
        OBSERVER_LAT, OBSERVER_LNG, OBSERVER_ALT, SEARCH_RADIUS_DEGREES, CATEGORY_ID
    )
    
    print("Data collection complete. Preparing email...")
    
    # Prepare and send email
    email_subject = f"N2YO Daily Satellite Report - {datetime.utcnow().strftime('%Y-%m-%d')}"
    email_body_html = format_data_as_html(all_data)
    
    send_email(
        email_subject, email_body_html, RECEIVER_EMAIL, SENDER_EMAIL,
        SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
    )
    
    print("Script finished.")
