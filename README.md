# 📦 AegisAI Target Service — Demo Guide (Explain Like I'm 10)

This is a **sample target application** (`orders-api`) that you can deploy to **GitHub** and **AWS** to demonstrate **AegisAI's autonomous incident response** live in action!

---

## 🎯 What Does This App Do?

Imagine you run an online store. This app processes customer orders:
- Under normal conditions, it is fast and healthy (`GET /health` returns 200 OK, latency 45ms).
- It has **Chaos Endpoints** (`POST /chaos/db-exhaustion`, `POST /chaos/memory-leak`, `POST /chaos/bad-deployment`) that intentionally create real production errors and stream them into **AWS CloudWatch**.
- **AegisAI** detects these real errors from CloudWatch & GitHub, investigates them with multi-agent debate, diagnoses the root cause, and fixes them!

---

## 🚀 5 Simple Steps to Connect Everything

### Step 1: Put This Sample Project on GitHub (2 Minutes)

1. Open your browser and go to [github.com/new](https://github.com/new).
2. Name your repo `orders-api` (or any name you like) and set it to **Public** (or Private).
3. On your computer, open a terminal inside this `sample/` folder and run:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit for orders-api v2.0.1"
   git branch -M main
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/orders-api.git
   git push -u origin main
   ```
4. **Create a GitHub Personal Access Token (PAT):**
   - Go to GitHub -> Settings -> Developer Settings -> Personal access tokens (Tokens classic).
   - Click **Generate new token**. Give it `repo` and `workflow` permissions.
   - Copy the token (starts with `ghp_...`).

---

### Step 2: Set Up AWS CloudWatch (1 Minute)

1. Log into your [AWS Management Console](https://console.aws.amazon.com/).
2. In the top search bar, type **CloudWatch** and click it.
3. In the left sidebar, click **Logs** -> **Log groups**.
4. Click the orange **Create log group** button:
   - **Log group name:** `/aws/apps/aegis-ai`
   - Click **Create**.
5. *(If you don't have AWS credentials yet)*: Go to IAM -> Users -> Security credentials -> **Create access key** (save `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`).

---

### Step 3: Run the Sample App (Deploy to Cloud or Run with Cloud Stream)

You have two easy ways to run this:

#### 🌟 Option A (Simplest & Free — Stream to CloudWatch from anywhere)
You can run this sample service directly on your computer or an EC2 instance. Because it has AWS CloudWatch integration built-in, it will stream all its real logs straight into AWS CloudWatch!

1. In this `sample/` folder, install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env`:
   ```env
   PORT=8080
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=us-east-1
   CLOUDWATCH_LOG_GROUP=/aws/apps/aegis-ai
   ```
3. Run the app:
   ```bash
   python app.py
   ```
   You will see:
   `[Init] CloudWatch logging enabled -> Group: '/aws/apps/aegis-ai'`
   `[*] Starting orders-api on http://localhost:8080`

#### Option B (Deploy to AWS ECS or App Runner)
- **AWS App Runner:** Connect your GitHub repo `orders-api`, select Python 3.11, build command `pip install -r requirements.txt`, start command `uvicorn app:app --port 8080`.
- **AWS ECS:** Build the `Dockerfile` with `docker build -t orders-api .` and push to AWS ECR.

---

### Step 4: Connect AegisAI to Your GitHub & AWS

Now tell **AegisAI** where to find your app's telemetry!

Open the main project root `.env` file (`d:/project/LANG/AGIS-AI/.env`) and add:

```env
# ── GitHub Integration ──────────────────────────────────────
GITHUB_REPO=YOUR_GITHUB_USERNAME/orders-api
GITHUB_TOKEN=ghp_yourPersonalAccessTokenHere

# ── AWS CloudWatch Integration ──────────────────────────────
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
CLOUDWATCH_LOG_GROUP=/aws/apps/aegis-ai

# ── Local Docker Target (if running container) ──────────────
DOCKER_CONTAINER_NAME=orders-api
```

---

### Step 5: How to Run the Demo for Evaluators (The "WOW" Moment)

1. **Start AegisAI backend**:
   ```bash
   .\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
   ```
2. **Open AegisAI Dashboard**:
   Open your browser to `http://localhost:8000/dashboard/`.
   Notice the **Integrations** tab will show:
   - AWS CloudWatch: **Active**
   - GitHub: **Active** (`YOUR_GITHUB_USERNAME/orders-api`)

3. **Break the Sample App (Trigger an Incident)**:
   In another terminal, run:
   ```bash
   python simulate_incident.py db_exhaustion
   ```
   *Or for a bad deployment:*
   ```bash
   python simulate_incident.py bad_deployment
   ```
   *What just happened:* The app instantly logged critical database exhaustion / crash errors directly into your live AWS CloudWatch log group!

4. **Watch AegisAI Fix It**:
   On the AegisAI dashboard, click **🚀 Run AegisAI Investigation**.

   Here is what everyone will see on screen:
   - **Log & Deployment Agents** pull the fresh error events directly from your AWS CloudWatch group and latest commits from GitHub.
   - **Investigator A** argues the incident is caused by code/deployments.
   - **Investigator B** argues it's database/resource exhaustion.
   - **Judge Agent** weighs both sides, cross-references runbooks, and delivers the definitive RCA verdict.
   - **Remediation Agent** proposes the safe fix (e.g. `restart_containers` or `rollback_deployment`).
   - The UI displays **⚠️ Human Approval Required**.
   - You click **✅ Approve**.
   - AegisAI triggers the real recovery (e.g. GitHub Actions `rollback.yml` or Docker restart)!
   - **Verification Agent** checks post-action telemetry and confirms: **🎉 Incident Resolved!**
