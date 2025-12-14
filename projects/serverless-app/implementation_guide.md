
---

## 🔧 Implementation Steps (Short & Clear)

---

### **Step 1: Create Amazon Cognito User Pool**

* Go to **Amazon Cognito → Create user pool**
* Application type: **Single Page Application (SPA)**
* App name: `ImageEditApp`
* Sign-in options: **Email + Username**
* Disable self-registration
* Required attribute: **email**
* Create a test user (`User1`)

**Why:**
Provides secure authentication and JWT tokens for API access.

---

### **Step 2: Save Cognito Configuration**

* Copy and save:

  * **User Pool ID**
  * **App Client ID**

**Why:**
Required for frontend authentication configuration.

---

### **Step 3: Create DynamoDB Table**

* Service: **DynamoDB**
* Table name: `ImageGenerationTable`
* Partition key: `id` (String)
* Use default settings

**Why:**
Stores request logs, metrics, and audit data.

---

### **Step 4: Create IAM Policy for DynamoDB**

* Allow:

  * `dynamodb:PutItem`
  * `dynamodb:UpdateItem`
* Resource: `ImageGenerationTable`

**Why:**
Allows Lambda to log image generation metadata.

---

### **Step 5: Create AWS Lambda Function**

* Runtime: **Python**
* Function name: `ImageEditBackend`
* Paste the provided backend code
* Set environment variable:

  * `DYNAMODB_TABLE_NAME = ImageGenerationTable`

**Why:**
Processes requests, calls Bedrock, and logs results.

---

### **Step 6: Grant Lambda Permissions**

* Attach IAM role with:

  * DynamoDB write access
  * Amazon Bedrock invoke permissions

**Why:**
Ensures secure access to required AWS services.

---

### **Step 7: Create API Gateway**

* Service: **API Gateway**
* Create **REST API**
* API name: `ImageEditingAppBackendAPI`
* Add **POST method**
* Enable **Lambda Proxy Integration**
* Select `ImageEditBackend`

**Why:**
Exposes Lambda securely as an HTTP endpoint.

---

### **Step 8: Enable CORS**

* Enable CORS on `/` resource
* Allow:

  * POST
  * Headers: `Content-Type, Authorization`

**Why:**
Allows browser-based frontend to call the API.

---

### **Step 9: Configure Cognito Authorizer**

* Create authorizer:

  * Type: **Cognito**
  * User Pool: `ImageEditApp`
  * Token source: `Authorization`
* Attach authorizer to POST method

**Why:**
Restricts API access to authenticated users only.

---

### **Step 10: Deploy API**

* Deploy to stage: `dev`
* Copy and save **Invoke URL**

**Why:**
Makes the API publicly callable by the frontend.

---

### **Step 11: Configure Frontend**

* Open `config.js`
* Update:

  * `userPoolId`
  * `userPoolClientId`
  * `region`
  * `invokeUrl`
* Save changes

**Why:**
Connects frontend to Cognito and API Gateway.

---

### **Step 12: Deploy Frontend with AWS Amplify**

* Service: **AWS Amplify**
* Deploy without Git
* Upload updated ZIP file
* Deploy

**Why:**
Hosts and serves the web application securely.

---

### **Step 13: Test the Application**

* Open Amplify app URL
* Log in with test user
* Upload image
* Select mask
* Enter prompt
* Generate image

**Why:**
Validates end-to-end functionality.


