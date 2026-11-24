import re

# These local records support repeatable demonstrations.
ORDERS = {
    "DEMO-1042": ("Billing", r"charged twice|duplicate (charge|payment)|double charged", "Credit", "A simulated INR 499 credit covers the second payment, SIM-702."),
    "DEMO-2077": ("Delivery", r"track|where|status|when", "Tracking lookup", "Demo tracking TR-2077 shows the parcel at the Hyderabad sorting centre. The next scan is due within one business day."),
    "DEMO-3108": ("Product quality", r"replacement|replace", "Replacement", "A replacement has been reserved from demo stock for the damaged item. Use the action reference when checking this case."),
    'DEMO-4101': ('Billing', 'invoice copy', 'Invoice', 'Your demo invoice INV-4101 totals INR 799, including tax.'),
    'DEMO-4102': ('Billing', 'coupon', 'Coupon', 'A replacement demo coupon SAVE50 has been recorded for INR 50 off the next eligible order.'),
    'DEMO-4103': ('Billing', 'points', 'Points', 'The missing 80 demo reward points have been credited to this order.'),
    'DEMO-4104': ('Delivery', 'pickup', 'Pickup', 'A new demo pickup request has been recorded for the next business day. Keep the parcel packed.'),
    'DEMO-4105': ('Product quality', 'accessory', 'Accessory', 'A demo dispatch request for the missing charging cable has been recorded.'),
    'DEMO-4106': ('Product quality', 'size', 'Exchange', 'A demo size exchange from small to the ordered medium has been recorded.'),
    'DEMO-4107': ('Billing', 'refund', 'Refund lookup', 'Demo refund RF-4107 is marked processed. Use this reference to track the existing refund.'),
    'DEMO-4108': ('Product quality', 'warranty', 'Warranty lookup', 'The demo item has standard warranty coverage through 30 November 2027.'),
    'DEMO-4109': ('Delivery', 'delivery instructions', 'Instructions', 'The demo delivery instructions now request a call on arrival.'),
    'DEMO-4110': ('Technical support', 'download', 'Download help', 'Open Order history, select the demo purchase, and choose Downloads to generate a fresh link. Your download entitlement is active.'),
    'DEMO-4111': ('Billing', 'shipping fee', 'Incorrect shipping fee', 'A simulated INR 60 delivery-fee credit was recorded.'),
    'DEMO-4112': ('Billing', 'gift card', 'Gift card balance missing', 'The unused INR 250 demo balance was restored.'),
    'DEMO-4113': ('Billing', 'student discount', 'Student discount omitted', 'The demo order shows student eligibility. A simulated INR 100 discount adjustment was recorded.'),
    'DEMO-4114': ('Billing', 'deposit', 'Deposit still held', 'The demo return inspection is complete. A simulated INR 300 deposit release was recorded.'),
    'DEMO-4115': ('Billing', 'price', 'Incorrect item price', 'The confirmed demo price was INR 450 and the invoice showed INR 500. A simulated INR 50 adjustment was recorded.'),
    'DEMO-4116': ('Delivery', 'redelivery', 'Missed delivery attempt', 'A second demo delivery attempt was scheduled for the next business day.'),
    'DEMO-4117': ('Delivery', 'collection point', 'Pickup location unclear', 'The demo parcel is at counter 2 of the Central Road collection hub.'),
    'DEMO-4118': ('Delivery', 'delivery receipt', 'Missing delivery receipt', 'Demo delivery receipt POD-4118 records delivery to the reception desk at 10:15 am.'),
    'DEMO-4119': ('Delivery', 'second parcel', 'Split shipment confusion', 'The demo order shipped in two boxes. The second parcel is in transit under TR-4119-B.'),
    'DEMO-4120': ('Delivery', 'delivery slot', 'Unavailable delivery slot', 'The demo evening delivery slot from 6 pm to 8 pm was reserved.'),
    'DEMO-4121': ('Product quality', 'colour', 'Wrong colour supplied', 'An exchange for the ordered blue item was recorded against demo inventory.'),
    'DEMO-4122': ('Product quality', 'quantity', 'Incomplete item quantity', 'The demo packing record shows one missing unit. A dispatch request for that unit was recorded.'),
    'DEMO-4123': ('Product quality', 'plug', 'Wrong plug supplied', 'A compatible adapter was reserved for this demo order.'),
    'DEMO-4124': ('Product quality', 'assembly guide', 'Missing assembly guide', 'For this demo shelf, fit the side panels to the base, secure the back panel, then insert the shelf pins and shelf.'),
    'DEMO-4125': ('Product quality', 'serial', 'Unreadable serial label', 'The demo packing record lists serial number SN-4125-A.'),
    'DEMO-4126': ('Technical support', 'activation', 'License activation limit', 'One obsolete demo device slot was released. Retry activation on the replacement laptop.'),
    'DEMO-4127': ('Technical support', 'library', 'Purchase missing from library', 'The course entitlement was linked to the demo library. Refresh Purchased courses to see it.'),
    'DEMO-4128': ('Technical support', 'subtitle', 'Incorrect subtitle language', 'English was recorded as the subtitle preference for this demo purchase.'),
    'DEMO-4129': ('Account access', 'newsletter', 'Newsletter opt-out ignored', 'The demo marketing preference was set to unsubscribed. Order notifications remain enabled.'),
    'DEMO-4130': ('Account access', 'display name', 'Incorrect display name', 'The display name on this demo profile was set to Demo Learner.')
}
GUIDANCE = {
    "Billing": "Check whether both entries are posted. Keep the invoice and transaction references for billing verification.",
    "Delivery": "Check the tracking link on your order confirmation and compare the last scan with the expected delivery date.",
    "Account access": "Request a new recovery link from the sign-in screen and use the newest email. Keep verification codes private.",
    "Technical support": "Reload the application and retry the affected step. Keep the error message if the problem continues.",
    "Product quality": "Keep the packaging and photograph the defect. Use the return or replacement option in your order history.",
    "Account security": "Use the provider's official support channel to report the activity. This case has been flagged locally.",
    "Manual review": "Include the affected service, what happened, and when it started so the issue can be routed."
}

def resolve(db, case):
    cid = case['id']
    text = case['text']
    orders = set(re.findall(r'\bDEMO-\d+\b', text.upper()))
    team = case['team']
    status = 'In progress'
    reply = GUIDANCE.get(team, GUIDANCE['Manual review'])
    if len(orders) == 1 and case['priority'] != 'High':
        order = orders.pop()
        rule = ORDERS.get(order)
        if rule and re.search(rule[1], text, re.I) and not re.search(r"\b(no|not|never|cancel|don't|do not)\b", text, re.I):
            team, _, action, reply = rule
            reference = action.upper().split()[0] + '-' + order
            db.execute('INSERT OR IGNORE INTO demo_actions(reference,kind) VALUES(?,?)',(reference,action))
            status = 'Resolved'
            reply += ' Action reference: ' + reference + '.'
    db.execute('UPDATE cases SET status=?,team=?,version=version+1 WHERE id=?',(status,team,cid))
    db.execute('INSERT INTO history(case_id,note) VALUES(?,?)',(cid,'Automatic response: '+reply))
