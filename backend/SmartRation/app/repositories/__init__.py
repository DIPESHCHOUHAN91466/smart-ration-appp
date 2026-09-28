"""Data access: every SQL query the services need, one module per aggregate.

Services decide *what* happens (rules, messages, transactions); repositories only read and add rows
on the session they are given and never commit, so a service keeps one transaction per request.
All queries are SQLAlchemy expressions with bound parameters (no string-built SQL).
"""
