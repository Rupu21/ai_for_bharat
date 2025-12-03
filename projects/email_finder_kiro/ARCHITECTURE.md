# Email Insights Dashboard - Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        Mobile[Mobile Browser]
    end

    subgraph "Load Balancer Layer (Production)"
        LB[Load Balancer<br/>nginx/ALB/CloudFlare]
    end

    subgraph "Application Layer"
        subgraph "FastAPI Instances"
            API1[FastAPI Instance 1<br/>Uvicorn Worker]
            API2[FastAPI Instance 2<br/>Uvicorn Worker]
            API3[FastAPI Instance N<br/>Uvicorn Worker]
        end
        
        subgraph "API Components"
            Routes[API Routes<br/>main.py]
            Middleware[Middleware<br/>CORS, GZip, Auth]
            SSE[Server-Sent Events<br/>Real-time Progress]
        end
    end

    subgraph "Service Layer"
        AuthService[Authentication Service<br/>OAuth2 Flow Management]
        GmailService[Gmail Service<br/>Email Retrieval & Parsing]
        AnalysisEngine[Analysis Engine<br/>Route to LLM/NLP]
        LoggingService[Logging Service<br/>Structured Logging]
        
        subgraph "Analysis Processors"
            LLMProcessor[LLM Processor<br/>AWS Bedrock Claude]
            NLPProcessor[NLP Processor<br/>NLTK Analysis]
        end
    end

    subgraph "Data Layer"
        Models[Data Models<br/>Email, AnalysisResult<br/>ImportantEmail]
        Config[Configuration<br/>Environment Variables<br/>Credentials]
    end

    subgraph "Session Storage (Production)"
        SessionStore[Session Store<br/>Redis/Memcached<br/>In-Memory Default]
    end

    subgraph "External Services"
        subgraph "Google Cloud"
            GoogleOAuth[Google OAuth 2.0<br/>Authentication]
            GmailAPI[Gmail API<br/>Read-only Access]
        end
        
        subgraph "AWS Services"
            Bedrock[AWS Bedrock<br/>Claude 3.7 Sonnet]
            IAM[AWS IAM<br/>Credentials & Permissions]
        end
    end

    subgraph "Monitoring & Logging (Production)"
        Logs[Log Files<br/>app.log, access.log]
        Metrics[Metrics<br/>CloudWatch/Datadog]
        Health[Health Check<br/>/health endpoint]
    end

    subgraph "Caching Layer (Production)"
        Cache[Redis Cache<br/>Analysis Results<br/>Session Data]
    end

    %% Client connections
    Browser --> LB
    Mobile --> LB
    
    %% Load balancer to API instances
    LB --> API1
    LB --> API2
    LB --> API3
    
    %% API to components
    API1 --> Routes
    API2 --> Routes
    API3 --> Routes
    Routes --> Middleware
    Middleware --> SSE
    
    %% Routes to services
    Routes --> AuthService
    Routes --> GmailService
    Routes --> AnalysisEngine
    Routes --> LoggingService
    
    %% Analysis engine routing
    AnalysisEngine --> LLMProcessor
    AnalysisEngine --> NLPProcessor
    
    %% Services to external APIs
    AuthService --> GoogleOAuth
    GmailService --> GmailAPI
    LLMProcessor --> Bedrock
    LLMProcessor --> IAM
    
    %% Services to data layer
    AuthService --> Models
    GmailService --> Models
    AnalysisEngine --> Models
    LLMProcessor --> Models
    NLPProcessor --> Models
    
    %% Configuration
    AuthService --> Config
    GmailService --> Config
    LLMProcessor --> Config
    
    %% Session management
    AuthService --> SessionStore
    Routes --> SessionStore
    
    %% Caching
    AnalysisEngine -.-> Cache
    GmailService -.-> Cache
    
    %% Monitoring
    Routes --> Logs
    LoggingService --> Logs
    Routes --> Health
    API1 --> Metrics
    API2 --> Metrics
    API3 --> Metrics
    
    %% Styling
    classDef client fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef api fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef external fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef data fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef infra fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class Browser,Mobile client
    class API1,API2,API3,Routes,Middleware,SSE api
    class AuthService,GmailService,AnalysisEngine,LLMProcessor,NLPProcessor,LoggingService service
    class GoogleOAuth,GmailAPI,Bedrock,IAM external
    class Models,Config,SessionStore data
    class LB,Cache,Logs,Metrics,Health infra
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User as User Browser
    participant LB as Load Balancer
    participant API as FastAPI
    participant Auth as Auth Service
    participant Gmail as Gmail Service
    participant Engine as Analysis Engine
    participant LLM as LLM Processor
    participant NLP as NLP Processor
    participant Google as Google APIs
    participant AWS as AWS Bedrock
    
    %% Authentication Flow
    rect rgb(230, 245, 255)
        Note over User,Google: Authentication Flow
        User->>API: Click "Login with Gmail"
        API->>Auth: Initiate OAuth Flow
        Auth->>Google: Redirect to OAuth
        Google->>User: Show Consent Screen
        User->>Google: Grant Permission
        Google->>API: OAuth Callback with Code
        API->>Auth: Exchange Code for Token
        Auth->>Auth: Store Credentials in Session
        API->>User: Redirect to Dashboard
    end
    
    %% Analysis Flow with Real-time Progress
    rect rgb(245, 255, 230)
        Note over User,AWS: Email Analysis Flow (with SSE)
        User->>API: POST /api/analyze<br/>{days_back: 7, method: "llm"}
        API->>User: SSE: "Connecting to Gmail..."
        
        API->>Auth: Validate Session
        Auth-->>API: Valid Credentials
        
        API->>User: SSE: "Retrieving emails..."
        API->>Gmail: Get Unread Emails
        Gmail->>Google: Gmail API Request
        Google-->>Gmail: Email List (max 100)
        Gmail->>Gmail: Parse Emails
        Gmail-->>API: List[Email]
        
        API->>User: SSE: "Retrieved 23 emails"
        
        API->>User: SSE: "Analyzing with LLM..."
        API->>Engine: Analyze Emails
        
        alt LLM Method
            Engine->>LLM: Process Emails
            LLM->>LLM: Format Prompt (max 50 emails)
            LLM->>AWS: Invoke Bedrock Claude
            AWS-->>LLM: Analysis Response
            LLM->>LLM: Parse JSON Response
            LLM-->>Engine: AnalysisResult
        else NLP Method
            Engine->>NLP: Process Emails
            NLP->>NLP: Extract Keywords
            NLP->>NLP: Calculate Importance
            NLP->>NLP: Generate Summary
            NLP-->>Engine: AnalysisResult
        end
        
        Engine-->>API: AnalysisResult
        API->>User: SSE: "Analysis complete!"
        API->>User: SSE: Final Results JSON
    end
```

## Component Architecture

```mermaid
graph LR
    subgraph "Presentation Layer"
        UI[HTML/CSS/JS<br/>Glassmorphic UI<br/>Real-time Updates]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Framework<br/>REST Endpoints<br/>SSE Streaming]
        Validation[Pydantic Models<br/>Request Validation]
        Middleware[Middleware Stack<br/>CORS, GZip, Auth]
    end
    
    subgraph "Business Logic Layer"
        Auth[Authentication<br/>OAuth2 Management]
        Gmail[Gmail Integration<br/>Email Retrieval]
        Analysis[Analysis Orchestration<br/>LLM/NLP Routing]
        Logging[Centralized Logging<br/>Audit Trail]
    end
    
    subgraph "Processing Layer"
        LLM[LLM Processing<br/>AWS Bedrock<br/>Claude 3.7 Sonnet]
        NLP[NLP Processing<br/>NLTK<br/>Heuristic Analysis]
    end
    
    subgraph "Data Layer"
        Models[Data Models<br/>Dataclasses<br/>Type Safety]
        Config[Configuration<br/>Environment Vars<br/>Validation]
    end
    
    UI --> FastAPI
    FastAPI --> Validation
    FastAPI --> Middleware
    Middleware --> Auth
    Middleware --> Gmail
    Middleware --> Analysis
    Middleware --> Logging
    Analysis --> LLM
    Analysis --> NLP
    Auth --> Models
    Gmail --> Models
    LLM --> Models
    NLP --> Models
    Auth --> Config
    Gmail --> Config
    LLM --> Config
    
    classDef presentation fill:#e3f2fd,stroke:#1565c0
    classDef api fill:#fff3e0,stroke:#e65100
    classDef business fill:#f3e5f5,stroke:#6a1b9a
    classDef processing fill:#e8f5e9,stroke:#2e7d32
    classDef data fill:#fce4ec,stroke:#c2185b
    
    class UI presentation
    class FastAPI,Validation,Middleware api
    class Auth,Gmail,Analysis,Logging business
    class LLM,NLP processing
    class Models,Config data
```

## Scaling Architecture (Production)

```mermaid
graph TB
    subgraph "Edge Layer"
        CDN[CDN<br/>CloudFlare/CloudFront<br/>Static Assets]
        WAF[Web Application Firewall<br/>DDoS Protection]
    end
    
    subgraph "Load Balancing"
        ALB[Application Load Balancer<br/>Health Checks<br/>SSL Termination]
    end
    
    subgraph "Application Tier - Auto Scaling Group"
        subgraph "Instance 1"
            App1[FastAPI<br/>4 Workers]
        end
        subgraph "Instance 2"
            App2[FastAPI<br/>4 Workers]
        end
        subgraph "Instance N"
            AppN[FastAPI<br/>4 Workers]
        end
    end
    
    subgraph "Caching Layer"
        Redis[Redis Cluster<br/>Session Storage<br/>Result Caching<br/>Rate Limiting]
    end
    
    subgraph "External Services"
        Google[Google APIs<br/>OAuth + Gmail]
        AWS[AWS Bedrock<br/>Claude Model]
    end
    
    subgraph "Monitoring & Observability"
        CloudWatch[CloudWatch<br/>Metrics & Alarms]
        Logs[Centralized Logging<br/>ELK/CloudWatch Logs]
        APM[APM Tool<br/>Datadog/New Relic]
    end
    
    subgraph "Security"
        Secrets[Secrets Manager<br/>AWS Secrets/Vault<br/>Credentials]
        IAM_Role[IAM Roles<br/>Service Permissions]
    end
    
    Users[Users] --> CDN
    CDN --> WAF
    WAF --> ALB
    
    ALB --> App1
    ALB --> App2
    ALB --> AppN
    
    App1 --> Redis
    App2 --> Redis
    AppN --> Redis
    
    App1 --> Google
    App2 --> Google
    AppN --> Google
    
    App1 --> AWS
    App2 --> AWS
    AppN --> AWS
    
    App1 --> Secrets
    App2 --> Secrets
    AppN --> Secrets
    
    App1 --> IAM_Role
    App2 --> IAM_Role
    AppN --> IAM_Role
    
    App1 --> CloudWatch
    App2 --> CloudWatch
    AppN --> CloudWatch
    
    App1 --> Logs
    App2 --> Logs
    AppN --> Logs
    
    App1 --> APM
    App2 --> APM
    AppN --> APM
    
    classDef edge fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef app fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef cache fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef external fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef monitor fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef security fill:#ffebee,stroke:#b71c1c,stroke-width:2px
    
    class CDN,WAF,ALB edge
    class App1,App2,AppN app
    class Redis cache
    class Google,AWS external
    class CloudWatch,Logs,APM monitor
    class Secrets,IAM_Role security
```

## Request Flow with Caching

```mermaid
flowchart TD
    Start([User Request]) --> Auth{Authenticated?}
    Auth -->|No| Login[Redirect to OAuth]
    Auth -->|Yes| CheckCache{Check Cache}
    
    Login --> OAuth[Google OAuth Flow]
    OAuth --> StoreSession[Store Session]
    StoreSession --> CheckCache
    
    CheckCache -->|Hit| ReturnCached[Return Cached Result]
    CheckCache -->|Miss| FetchEmails[Fetch from Gmail API]
    
    FetchEmails --> ParseEmails[Parse Email Data]
    ParseEmails --> ChooseMethod{Analysis Method?}
    
    ChooseMethod -->|LLM| LLMProcess[LLM Processing<br/>AWS Bedrock]
    ChooseMethod -->|NLP| NLPProcess[NLP Processing<br/>NLTK]
    
    LLMProcess --> FormatResults[Format Results]
    NLPProcess --> FormatResults
    
    FormatResults --> CacheResults[Cache Results<br/>TTL: 5 min]
    CacheResults --> StreamSSE[Stream via SSE]
    ReturnCached --> StreamSSE
    
    StreamSSE --> End([Response to User])
    
    style Start fill:#e1f5ff
    style End fill:#e1f5ff
    style Auth fill:#fff3e0
    style CheckCache fill:#f3e5f5
    style LLMProcess fill:#e8f5e9
    style NLPProcess fill:#e8f5e9
```

## Technology Stack

```mermaid
mindmap
    root((Email Insights<br/>Dashboard))
        Frontend
            HTML5
            CSS3 Glassmorphism
            Vanilla JavaScript
            Server-Sent Events
        Backend
            Python 3.9+
            FastAPI Framework
            Uvicorn ASGI Server
            Pydantic Validation
        Authentication
            Google OAuth 2.0
            Gmail API Read-only
            Session Management
        AI & Analysis
            AWS Bedrock
                Claude 3.7 Sonnet
                Anthropic API
            NLTK
                Tokenization
                Stopwords
                Frequency Analysis
        Infrastructure
            Load Balancer
                nginx
                AWS ALB
            Caching
                Redis
                In-Memory
            Monitoring
                CloudWatch
                Datadog
                Health Checks
        Security
            HTTPS/TLS
            CORS
            OAuth 2.0
            IAM Roles
            Secrets Manager
```

## Deployment Options

```mermaid
graph LR
    subgraph "Development"
        Dev[Local Development<br/>uvicorn --reload<br/>Single Process]
    end
    
    subgraph "Small Scale"
        VPS[VPS/EC2<br/>Gunicorn + nginx<br/>4 Workers<br/>Single Instance]
    end
    
    subgraph "Medium Scale"
        Container[Container Platform<br/>Docker + K8s<br/>Auto-scaling<br/>2-10 Instances]
    end
    
    subgraph "Large Scale"
        Cloud[Cloud Native<br/>AWS ECS/EKS<br/>Load Balanced<br/>10+ Instances<br/>Multi-Region]
    end
    
    Dev -->|Scale Up| VPS
    VPS -->|Scale Up| Container
    Container -->|Scale Up| Cloud
    
    style Dev fill:#e1f5ff
    style VPS fill:#fff3e0
    style Container fill:#f3e5f5
    style Cloud fill:#e8f5e9
```

## Key Architecture Decisions

### 1. **Layered Architecture**
- Clear separation of concerns
- Easy to test and maintain
- Scalable and modular

### 2. **Service Pattern**
- Each service has single responsibility
- Dependency injection for testability
- Loose coupling between components

### 3. **Real-time Communication**
- Server-Sent Events for progress updates
- Non-blocking async processing
- Better user experience

### 4. **Stateless Application**
- Sessions stored externally (Redis in production)
- Horizontal scaling friendly
- Load balancer compatible

### 5. **External Service Integration**
- Google OAuth for authentication
- Gmail API for email access
- AWS Bedrock for AI processing
- Graceful error handling

### 6. **Performance Optimizations**
- GZip compression
- Email limits (100 Gmail, 50 LLM)
- Token optimization (2048 max)
- Connection pooling
- Result caching (production)

### 7. **Security**
- OAuth 2.0 authentication
- Read-only Gmail access
- HTTPS in production
- Secrets management
- IAM role-based access

### 8. **Observability**
- Structured logging
- Health check endpoints
- Metrics collection
- Error tracking
- Audit trail
