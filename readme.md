# Secondary Trading Platform

A robust platform for trading fractionalized recurring revenue contracts, built with Django and PostgreSQL.

## Overview

The Secondary Trading Platform is a financial ecosystem that enables the buying and selling of fractionalized recurring revenue contracts. The platform consists of two interconnected systems:

1. **Primary Platform**: Manages the lending of loans through recurring revenue invoices.
2. **Secondary Platform**: Enables trading of fractionalized recurring revenue contracts.

This repository contains the Secondary Platform implementation, which allows for the fractionalizing of invoices into smaller, manageable units that can be traded among investors.

## Key Features

- **User Authentication and KYC**
  - Sign-in and sign-up via mobile number and OTP validation
  - New registration with personal/business information
  - Signzy integration for KYC profile retrieval
  - Manual KYC information entry

- **Bank Account Management**
  - Link bank accounts using Boost Money integration
  - Wallet functionality for funds management

- **Invoice Management**
  - View and trade fractionalized recurring revenue contracts
  - IRR/XIRR calculations for investment valuation
  - Cash flow tracking

- **Trading**
  - Buy and sell fractionalized invoices
  - Fixed price trading
  - Bidding functionality
  - Modify or withdraw bids
  - Accept bids as a seller

- **Admin Features**
  - Contract management
  - User management
  - Transaction reporting
  - TDS reporting
  - Bid reporting
  - Admin can fractionalize invoices from primary platform

- **Super Admin Features**
  - Impersonate users
  - Generate tokens
  - Access all reports

## System Design

![NaharOm-STD](https://github.com/user-attachments/assets/09988335-44b0-4d17-9b31-0ddcc95d14bb)

## User Roles

### Admin
- Manages invoices coming from the primary platform
- Fractionalizes invoices into smaller units
- Posts fractionalized invoices for sale
- Access to detailed analytical reports and user management

### Patron (Investor)
- Can be an individual or company
- Buys and sells fractional units of recurring revenue contracts
- Manages their wallet and transactions

### Super Admin
- Has all admin capabilities plus additional oversight
- Can impersonate any registered user
- Controls user roles and access levels

## System Workflow

### User Registration Flow
1. User signs up with mobile number and OTP verification
2. KYC verification (automatic or manual)
3. Bank account linking
4. Wallet assignment
5. Access to buy & sell marketplace

### Buy/Sell Flow for Admin
1. Admin views invoices in 3 categories: unfractionalized, configured, posted for sale
2. Admin fractionalizes invoices into units
3. Admin posts fractionalized invoices for sale with pricing and dates

### Buy/Sell Flow for Users
1. View available invoices for purchase
2. Buy fractional units
3. Manage purchased units
4. Resell units if desired

### Bidding Process
1. User places bid on invoice
2. Seller reviews and accepts/rejects bid
3. Upon acceptance, funds are transferred automatically

![secondary drawio](https://github.com/user-attachments/assets/e349395c-7e7e-43fc-8bd0-1526c082a32a)

## Database Design 

![Secoundary_Trading_Platform](https://github.com/user-attachments/assets/201d210c-3032-4a88-ab7e-e6865235690d)

## Technologies Used

- **Backend**: Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)
- **Third-party Integrations**: 
  - Signzy (KYC verification)
  - Boost Money (Bank account linking)
- **Financial Calculations**: Custom IRR/XIRR implementation
- **Deployment**: Render

## API Endpoints

### Authentication
- `POST /generate-otp/`: Generate OTP for authentication
- `POST /verify-otp/`: Verify OTP and register/login user

### User Profile Management
- `GET /verify-status/<user>/`: Check KYC and bank account status
- `GET /phone-to-prefill/<user>/`: Fetch user profile from Signzy
- `POST /pan-to-gst/`: Fetch company details from PAN
- `POST /profile/`: Create/update user profile
- `GET /profile/<user>/`: Get user profile

### Bank & Wallet Management
- `POST /bank-account-details/`: Add bank account details
- `POST /credit-funds/`: Add funds to wallet
- `POST /withdraw-funds/`: Withdraw funds from wallet
- `GET /ledger/<user>/`: View transaction history
- `GET /show-funds/<user_role_id>/`: Check wallet balance

### Trading
- `GET /get-sell-purchase-details/<user>/`: Get available invoices and user transactions
- `POST /to-buy/`: Buy fractional units
- `POST /post-for-sell/`: Post units for sale

### Bidding
- `POST /check-balance-against-bid-price/`: Check if user has sufficient balance for bidding
- `POST /proceed-to-bid/`: Place a bid
- `PUT /modify-bid/`: Update a bid
- `PUT /withdraw-bid/`: Withdraw a bid
- `POST /accept-bid/`: Accept a bid as a seller

### Admin Endpoints
- `GET /appAdmin/invoice-management/<user>/`: View invoices in different states
- `POST /appAdmin/configurations/`: Fractionalize invoices
- `POST /appAdmin/post-invoice/`: Post fractionalized invoices for sale
- `GET /appAdmin/onboarding-report/<user>/`: User management
- `GET /appAdmin/transaction-report/<user>/`: View transaction reports
- `GET /appAdmin/sales-purchased-report/<user>/`: View sales and purchase reports
- `GET /appAdmin/tds-report/<user>/`: View TDS reports
- `GET /appAdmin/bid-report/<user>/`: View bidding reports
- `GET /appAdmin/trading-activity-report/<user>/`: View trading activity
- `GET /appAdmin/generate-token/<admin_id>/<user_role_id>/`: Generate token for impersonation
- `GET /appAdmin/impersonate/<admin_id>/<user_role_id>/`: Impersonate a user

## Setup and Installation

### Prerequisites
- Python 3.8+
- PostgreSQL
- Pip (Python package manager)

### Environment Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/secondary-trading-platform.git
cd secondary-trading-platform
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
DATABASE_URL=postgresql://username:password@hostname:port/database
SECRET_KEY=your_secret_key
```

### Database Setup
1. Create a PostgreSQL database
2. Apply migrations:
```bash
python manage.py migrate
```

3. Create a superuser (for admin access):
```bash
python manage.py createsuperuser
```

### Running the Server
```bash
python manage.py runserver
```

### Deployment (Render)
The application is configured for deployment on Render using the provided `Procfile`.
Base URL for the project: https://naharom-stp.onrender.com
You can fork my postman collection : [<img src="https://run.pstmn.io/button.svg" alt="Run In Postman" style="width: 128px; height: 32px;">](https://app.getpostman.com/run-collection/30178984-1a78c7e4-8662-4546-885b-b0b814e29fcb?action=collection%2Ffork&source=rip_markdown&collection-url=entityId%3D30178984-1a78c7e4-8662-4546-885b-b0b814e29fcb%26entityType%3Dcollection%26workspaceId%3D3a2ddb85-7464-4cd1-b12e-8407475d2de0)

## Project Structure

The project is organized into several Django apps:

- **UserFeatures**: Core functionality for users, including authentication, profiles, and trading
- **AdminFeatures**: Admin-specific functionality for managing users, invoices, and reports
- **IRRCalc**: Financial calculation modules for IRR/XIRR
- **ApiManagement**: Manages API statuses and third-party integrations
- **PrimaryApis**: Interfaces with the primary platform
- **SecondaryTradingPlatform**: Main Django project settings and configuration
