import requests
import json
import uuid

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8002"  # Assuming the service runs on port 8002 as per .env
LOGIN_URL = "https://login-api.snolep.com/login/ca"
EMAIL = "democaadmin@yopmail.com"
PASSWORD = "demo@1234"

ACCESS_TOKEN = None
AGENCY_ID = None

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "X-Agency-Id": f"{AGENCY_ID}"
}

# --- Test Data ---
service_id = None
file_id = None
service_name = f"Test Service {uuid.uuid4().hex[:6]}"

def print_response(response, test_name):
    """Helper function to print test results."""
    print(f"--- {test_name} ---")
    print(f"Status Code: {response.status_code}")
    if response.text:
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response Text:")
            print(response.text)
    else:
        print("Response Body: (No Content)")
    print("-" * (len(test_name) + 8))
    print()

def get_access_token():
    """Fetches a new access token."""
    global ACCESS_TOKEN, AGENCY_ID, HEADERS
    print("--- Fetching Access Token ---")
    payload = {
        "email": EMAIL,
        "password": PASSWORD
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(LOGIN_URL, data=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        ACCESS_TOKEN = data.get("access_token")
        AGENCY_ID = data.get("agency_id")
        HEADERS["Authorization"] = f"Bearer {ACCESS_TOKEN}"
        HEADERS["X-Agency-Id"] = AGENCY_ID
        print("Successfully fetched new access token.")
        print("-" * 29)
        print()
        return True
    else:
        print("Failed to fetch access token.")
        print_response(response, "Login")
        return False

def test_create_service():
    """Tests the POST /services/ endpoint."""
    global service_id
    print("Running: Create Service Test")
    payload = {
        "name": service_name,
        "description": "This is a test service.",
        "is_enabled": True,
        "is_checklist_completion_required": True,
        "is_recurring": True,
        "auto_task_creation_frequency": "monthly",
        "target_date_creation_date": 15,
        "assign_auto_tasks_to_users_of_respective_clients": False,
        "assign_auto_tasks_to_users": [],
        "create_document_collection_request_automatically": True,
        "billing": {
            "sac_code": "998311",
            "gst_percent": 18,
            "default_rate": 5000,
            "default_billable": True,
        },
        "checklists": [
            {"item_text": "Initial client meeting", "is_required": True},
            {"item_text": "Collect required documents"}
        ],
        "subtasks": [
            {"title": "Draft agreement", "description": "Prepare the initial draft.", "enable_workflow": True},
            {"title": "Send for review"}
        ],
        "custom_fields": []
    }
    response = requests.post(f"{BASE_URL}/services/", headers=HEADERS, json=payload)
    print_response(response, "Create Service")
    if response.status_code == 201:
        service_id = response.json().get("id")
    return response.ok

def test_list_services():
    """Tests the GET /services/ endpoint."""
    print("Running: List Services Test")
    response = requests.get(f"{BASE_URL}/services/", headers=HEADERS)
    print_response(response, "List Services")
    return response.ok

def test_get_service():
    """Tests the GET /services/{service_id} endpoint."""
    if not service_id:
        print("Skipping Get Service Test: service_id not available.")
        return False
    print(f"Running: Get Service Test (ID: {service_id})")
    response = requests.get(f"{BASE_URL}/services/{service_id}", headers=HEADERS)
    print_response(response, "Get Service")
    return response.ok

def test_update_service():
    """Tests the PATCH /services/{service_id} endpoint."""
    if not service_id:
        print("Skipping Update Service Test: service_id not available.")
        return False
    print(f"Running: Update Service Test (ID: {service_id})")
    payload = {
        "name": f"{service_name} (Updated)",
        "description": "This service has been updated.",
        "is_enabled": False
    }
    response = requests.patch(f"{BASE_URL}/services/{service_id}", headers=HEADERS, json=payload)
    print_response(response, "Update Service")
    return response.ok

def test_upload_file():
    """Tests the POST /services/{service_id}/files endpoint."""
    global file_id
    if not service_id:
        print("Skipping Upload File Test: service_id not available.")
        return False
    print(f"Running: Upload File Test (Service ID: {service_id})")
    
    # Create a dummy file for upload
    with open("test_upload.txt", "w") as f:
        f.write("This is a test file for upload.")

    file_headers = HEADERS.copy()
    del file_headers["Content-Type"] # requests will set this with boundary

    with open("test_upload.txt", "rb") as f:
        files = {"file": ("test_upload.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/services/{service_id}/files", headers=file_headers, files=files)
    
    print_response(response, "Upload File")
    if response.status_code == 200:
        file_id = response.json().get("id")
    return response.ok

def test_delete_file():
    """Tests the DELETE /services/{service_id}/files/{file_id} endpoint."""
    if not service_id or not file_id:
        print("Skipping Delete File Test: service_id or file_id not available.")
        return False
    print(f"Running: Delete File Test (Service ID: {service_id}, File ID: {file_id})")
    response = requests.delete(f"{BASE_URL}/services/{service_id}/files/{file_id}", headers=HEADERS)
    print_response(response, "Delete File")
    return response.status_code == 204

def test_delete_service():
    """Tests the DELETE /services/{service_id} endpoint."""
    if not service_id:
        print("Skipping Delete Service Test: service_id not available.")
        return False
    print(f"Running: Delete Service Test (ID: {service_id})")
    response = requests.delete(f"{BASE_URL}/services/{service_id}", headers=HEADERS)
    print_response(response, "Delete Service")
    return response.status_code == 204

def run_all_tests():
    """Executes all API tests in sequence."""
    if not get_access_token():
        print("Halting tests due to login failure.")
        return

    results = {}
    results["create_service"] = test_create_service()
    results["list_services"] = test_list_services()
    results["get_service"] = test_get_service()
    results["update_service"] = test_update_service()
    results["upload_file"] = test_upload_file()
    results["delete_file"] = test_delete_file()
    results["delete_service"] = test_delete_service()

    print("\n--- Test Summary ---")
    for test_name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
    print("--------------------")

if __name__ == "__main__":
    run_all_tests()
