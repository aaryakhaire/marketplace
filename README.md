# Velora Marketplace 

Velora is a premium, high-contrast dark-themed streetwear marketplace built using **Flask** and **SQLite3**, designed with a fluid interactive motion system inspired by modern aesthetics.

---

##  Visual & Motion Profile
*   **Axiom-Inspired Dark Theme:** High-contrast layout using deep blacks (`#050505`), clean structural card frames (`#111113`), and fine white borders.
*   **Glow Ambient Lighting:** Dynamic radial backdrop pools (Teal, Orange, Purple) floating and breathing in the background.
*   **LERP Cursor Follower:** Butter-smooth mouse tracking dot and ring that dynamically scales and glows when hovering over interactive elements.
*   **Scroll Entrance Reveals:** Sequence animations using `IntersectionObserver` that reveal grid elements as they enter the screen.
*   **Continuous Marquees:** Text slogans looping horizontally.

---

##  Key Features
*   **User Accounts & Auth:** Secure registration, login, and sessions using SHA-256 password hashing.
*   **User Listings:** Users can post their streetwear listings with category, price, WhatsApp details, and image preview.
*   **Real Transactions:** Instant copping with transaction logging, order status, and item auto-marking as `SOLD`.
*   **Database Seeding:** Preloaded with realistic streetwear mock data.

---

##  Quick Start & Installation

### 1. Clone the repository
```bash
git clone https://github.com/aaryakhaire/marketplace.git
cd marketplace
```

### 2. Set up virtual environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install flask
```

### 4. Seed and Run the Application
The application automatically creates the database tables and seeds items on startup:
```bash
python app.py
```
Visit the local server at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

##  Test Credentials
You can log in with any of these sample accounts to explore order history and active profiles:

*   **Password for all accounts:** `password123`

| Username | Email | Active Listings | Role |
| :--- | :--- | :--- | :--- |
| `hypebeast_99` | `hype@velora.com` | Supreme Hoodie, Off-White Belt | Buyer & Seller |
| `skater_girl` | `skate@velora.com` | Skate Cargo Pants | Buyer & Seller |
| `vintage_collector` | `vintage@velora.com` | Oversized Corduroy Jacket | Seller |
| `retro_footwear` | `sneakers@velora.com` | Chicago Jordans (Sold) | Seller |
