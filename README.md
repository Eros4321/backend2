# Google Sign-In & Paystack Payment API

This project implements a backend service with Google OAuth 2.0 authentication and Paystack payment integration. It provides RESTful endpoints for user authentication, payment initiation, and transaction status verification.

## Setup Instructions

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment** and activate it:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables**:
    - Copy `.env.example` to a new file named `.env`.
    - Fill in your Google OAuth credentials (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`) and Paystack keys (`PAYSTACK_SECRET_KEY`).
5.  **Run Migrations**:
    ```bash
    python manage.py migrate
    ```
6.  **Run the Server**:
    ```bash
    python manage.py runserver
    ```

## API Endpoints

### Authentication
-   `GET /auth/google`: Returns the Google OAuth consent URL.
-   `GET /auth/google/callback`: Handles the OAuth callback, creates/updates the user, and returns user info.

### Payments
-   `POST /payments/paystack/initiate`: Initiates a payment transaction.
    -   Body: `{"user_id": 1, "amount": 5000}` (Amount in Kobo)
-   `GET /payments/{reference}/status`: Checks the status of a transaction.
    -   Query Param: `?refresh=true` to verify with Paystack directly.
-   `POST /payments/paystack/webhook`: Webhook endpoint for Paystack event notifications.

## Technology Choices

*   **Django REST Framework**: Chosen for its powerful serialization engine and browsable API, which significantly speeds up the development of RESTful endpoints. It handles content negotiation and authentication policies out of the box, reducing boilerplate code.
*   **Requests**: Used to make synchronous HTTP calls to Google's OAuth endpoints and Paystack's API. Its simple and intuitive API makes handling external service integrations and response parsing straightforward.
*   **Python-dotenv**: implemented to load configuration from a `.env` file into environment variables. This ensures sensitive credentials like API keys are kept separate from the codebase and not committed to version control.
