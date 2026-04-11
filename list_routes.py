from app import app
with app.app_context():
    rules = sorted([str(rule.endpoint) for rule in app.url_map.iter_rules()])
    for r in rules:
        print(r)
