from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests
from firebase_admin import credentials, initialize_app, firestore, auth
import os

app = FastAPI()
security = HTTPBearer()

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path/to/your/firebase-adminsdk.json")
initialize_app(cred)
db = firestore.client()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=403, detail="Invalid authentication credentials")


@app.post("/api")
async def api_endpoint(request_data: dict, token: dict = Depends(verify_firebase_token)):
    user_id = token['uid']
    function_name = request_data.get('functionName')
    params = request_data.get('params', {})

    # Retrieve API key from Firestore
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    api_key = user_doc.to_dict().get('apiKey')
    if not api_key:
        raise HTTPException(status_code=400, detail="API key not found")

    # Use the API key and function_name to perform the required operation
    # This is where you'd implement your custom functionality
    result = perform_operation(function_name, params, api_key)

    return {"result": result}


def perform_operation(function_name: str, params: dict, api_key: str):
    # Implement your custom logic here
    # This function would use the api_key to interact with external services
    # or perform whatever operation is needed based on the function_name
    return f"Operation {function_name} performed successfully"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)