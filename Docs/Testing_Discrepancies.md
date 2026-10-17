# How to Test the Discrepancies UI Without Real Uploads

The ClearanceX backend is designed with a smart routing system to allow UI testing without needing a complete, real document pipeline. 

When the frontend calls the API (`GET /api/shipments/{dossier_id}/discrepancies`), the backend checks the ID. If it's a known demo ID (like `"demo-shipment"`), it automatically routes to a mock pipeline and returns synthetic discrepancy data. Otherwise, it queries the PostgreSQL database for real data.

Here are the two ways your team can test the Discrepancies UI right now:

---

## ✅ Option A: The Instant Demo Route (Recommended)

This requires zero setup and is ready to use immediately.

1. Make sure your Docker containers are running (`docker compose up`).
2. Open the application in your browser (`http://localhost:3000`).
3. You can either:
   - Go to the **Overview page** and click **"Inspect"** on any dossier row.
   - Or simply navigate directly to `http://localhost:3000/discrepancies` in your browser.
4. Because no real dossier is selected, the application automatically defaults the `shipmentId` to `"demo-shipment"`.
5. The backend will intercept this ID and generate a complete set of fake discrepancies, complete with XAI reasoning, confidence scores, and counterfactuals.

**What to verify on this screen:**
- Severity badges correctly color-code (High/Medium/Low).
- The XAI "Show Details" accordion expands and collapses smoothly.
- The filter buttons (All, High, Medium, Low) correctly sort the list.
- Clicking the "Resolve" button triggers a success toast notification and marks the item.
- The search bar filters by rule ID or description.

---

## ✅ Option B: Inject a Fake Dossier into PostgreSQL (For Database Testing)

If you specifically want to test how the UI handles a real database UUID, you can inject a blank dossier into the local database.

**Step 1:** Run this Python script inside the running backend container via PowerShell:

```powershell
docker exec -it clearancex_backend python -c "
from database.connection import SessionLocal
from database.models import Dossier
import uuid, datetime

db = SessionLocal()
dossier_id = uuid.uuid4()
d = Dossier(id=dossier_id, status='done', created_at=datetime.datetime.utcnow())
db.add(d)
db.commit()
print('Dossier ID:', dossier_id)
db.close()
"
```

**Step 2:** Copy the UUID printed in your terminal.

**Step 3:** Go to your web app, navigate to the Overview page, and find the dossier row matching that UUID. Click **Inspect**.

**Step 4:** The UI will now load the Discrepancies page using a real database UUID.
