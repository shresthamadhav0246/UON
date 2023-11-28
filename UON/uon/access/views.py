from django.shortcuts import render
from django.http import JsonResponse
import ssl
import requests
from .models import Patient
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
# This is the view for the home page
def login(request):
       # Retrieve patient data from the database
    patients = Patient.objects.all()

    url = "https://sandbox.api.service.nhs.uk/gp-connect-access-record-fhir/FHIR/STU3/documents/Patient/<string>"
    headers = {
        "X-Correlation-ID": "<string>",
        "X-Request-ID": "7FDa8b0e-093b-309F-Eb1C-95FBe33fC9fF",
        "Accept": "application/fhir+json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        data = {"error": str(e)}
    
    return render(request, "access/login.html", {"data": data, "patients": patients})

def checkSim(request):
    # Retrieve patient data from the database
    patients_db = Patient.objects.all()

    url = "https://sandbox.api.service.nhs.uk/gp-connect-access-record-fhir/FHIR/STU3/documents/Patient/<string>"
    headers = {
        "X-Correlation-ID": "<string>",
        "X-Request-ID": "7FDa8b0e-093b-309F-Eb1C-95FBe33fC9fF",
        "Accept": "application/fhir+json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data_api = response.json()
    except requests.exceptions.RequestException as e:
        data_api = {"error": str(e)}

    # Initialize difference flags
    address_diff, dob_diff, gender_diff, phone_diff = False, False, False, False
    #new api data
    address_api_data,dob_api_data,gender_api_data,phone_api_data ='' ,'','',''
    # Compare data and mark differences
    differences = []

    for patient_db in patients_db:
        db_name = patient_db.name
        db_address = patient_db.address
        db_phone = patient_db.phone
        db_dob = datetime.strptime(str(patient_db.birth_date), "%Y-%m-%d").date()        
        print(db_dob)
        db_gender = patient_db.gender

        found_in_api = False

        for entry in data_api.get("entry", []):
            api_name = entry.get("resource", {}).get("name", [{}])[0].get("text", "")

            if db_name == api_name:
                found_in_api = True

                #api_address = entry.get("resource", {}).get("address", [{}])[0].get("line", [{}])[0]
                api_phone = entry.get("resource", {}).get("telecom", [{}])[0].get("value", "")
                api_dob_str = entry.get("resource", {}).get("birthDate", "")
                api_dob = datetime.strptime(api_dob_str, "%Y-%m-%d").date()
                api_gender = entry.get("resource", {}).get("gender", "")
                api_address_components = entry.get("resource", {}).get("address", [{}])[0]

            # Create a single address string by joining components
                api_address = ", ".join(
                 [
                    api_address_components.get("line", [{}])[0],
                    api_address_components.get("city", ""),
                    api_address_components.get("district", ""),
                    api_address_components.get("postalCode", ""),
                 ]
                )

                if db_address.replace(" ", "").lower() != api_address.replace(" ", "").lower():
                    print(db_address, api_address)
                    address_diff = True
                    address_api_data = api_address


                if db_phone != api_phone:
                    phone_diff = True
                    phone_api_data = api_phone

                if db_dob != api_dob:
                    print(db_dob, api_dob)
                    dob_diff = True
                    dob_api_data = api_dob

                if db_gender != api_gender:
                    gender_diff = True
                    gender_api_data = api_gender

                break
            else:
                return JsonResponse({"error": "Patient not found in API"})

        if not found_in_api:
            differences.append(patient_db.id)  # Store the ID of the DB record that's not in the API

    context = {
    "address_diff": [address_diff, address_api_data],
    "dob_diff": [dob_diff, dob_api_data],
    "gender_diff": [gender_diff, gender_api_data],
    "phone_diff": [phone_diff, phone_api_data],
}

    return JsonResponse(context)
@csrf_exempt
def register(request):
    if request.method == 'POST':
        # Fetch new API data
        url = "https://sandbox.api.service.nhs.uk/gp-connect-access-record-fhir/FHIR/STU3/documents/Patient/<string>"
        headers = {
            "X-Correlation-ID": "<string>",
            "X-Request-ID": "7FDa8b0e-093b-309F-Eb1C-95FBe33fC9fF",
            "Accept": "application/fhir+json",
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            api_data = response.json()
        except requests.exceptions.RequestException as e:
            api_data = {"error": str(e)}

        # Process the new API data and update the database
        for entry in api_data.get("entry", []):
            api_name = entry.get("resource", {}).get("name", [{}])[0].get("text", "")
            api_gender = entry.get("resource", {}).get("gender", "")
            api_birth_date = entry.get("resource", {}).get("birthDate", "")
            api_address = ", ".join(
                [
                    entry.get("resource", {}).get("address", [{}])[0].get("line", [{}])[0],
                    entry.get("resource", {}).get("address", [{}])[0].get("city", ""),
                    entry.get("resource", {}).get("address", [{}])[0].get("district", ""),
                    entry.get("resource", {}).get("address", [{}])[0].get("postalCode", ""),
                ]
            )
            api_phone = entry.get("resource", {}).get("telecom", [{}])[0].get("value", "")

            # Check if a record with the same name exists in the database
            existing_patient = Patient.objects.filter(name=api_name).first()

            if existing_patient:
                # Update the existing record with the new API data
                existing_patient.gender = api_gender
                existing_patient.birth_date = api_birth_date
                existing_patient.address = api_address
                existing_patient.phone = api_phone
                existing_patient.save()
            else:
                # Create a new record with the API data
                Patient.objects.create(
                    name=api_name,
                    gender=api_gender,
                    birth_date=api_birth_date,
                    address=api_address,
                    phone=api_phone,
                )

        # Return a success JSON response
        return JsonResponse({"status": "success"})
    else:
        # Handle GET requests or other HTTP methods here
        return JsonResponse({"error": "Invalid request method"}, status=405)