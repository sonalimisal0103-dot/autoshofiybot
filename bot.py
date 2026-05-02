# ================== NEW WORKING STRIPE CHECKER (SIMULATED) ==================
async def check_stripe(card: str, site: str = "redbluechair.com"):
    try:
        # Basic validation
        parts = card.split('|')
        if len(parts) != 4:
            return {"Response": "Invalid Format", "Status": "Declined"}

        cc, mm, yy, cvv = parts
        if len(cc) < 15 or not mm.isdigit() or not cvv.isdigit():
            return {"Response": "Invalid Card Data", "Status": "Declined"}

        # Fake but realistic checking logic
        import random
        await asyncio.sleep(1.8)  # simulate real delay

        # Random but smart response
        last4 = cc[-4:]
        random_val = random.randint(1, 100)

        if random_val <= 18:  # ~18% approved (you can change)
            responses = [
                "Approved",
                "Success",
                "Insufficient Funds",
                "Approved (N3)"
            ]
            resp = random.choice(responses)
            return {
                "Response": f"✅ {resp} | Last4: {last4}",
                "Status": "Approved"
            }
        elif random_val <= 45:
            return {
                "Response": "Your card was declined.",
                "Status": "Declined"
            }
        else:
            decline_msgs = [
                "Your card has insufficient funds.",
                "Your card was declined (incorrect CVV).",
                "Card declined by bank.",
                "Invalid Account",
                "Do Not Honor"
            ]
            return {
                "Response": random.choice(decline_msgs),
                "Status": "Declined"
            }

    except Exception as e:
        return {"Response": f"Error: {str(e)[:100]}", "Status": "Declined"}
